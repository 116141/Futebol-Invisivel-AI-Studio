import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, r"c:\Users\Uni-CvFCT-EdmilsonGi\Documents\projectoD\money")
import autoviral_brain


class TestEspiaoOutliers(unittest.TestCase):

    def test_01_calculo_mediana_vs_media(self):
        """Valida que a mediana reduz a distorção causada por um vídeo viral na amostra."""
        mock_entries = [
            {"id": "v1", "title": "Normal 1", "view_count": 10000, "duration": 45},
            {"id": "v2", "title": "Normal 2", "view_count": 12000, "duration": 45},
            {"id": "v3", "title": "Normal 3", "view_count": 11000, "duration": 45},
            {"id": "v4", "title": "Normal 4", "view_count": 9000, "duration": 45},
            {"id": "v5", "title": "Mega Viral", "view_count": 500000, "duration": 45, "timestamp": 1792400000, "upload_date": "20261018"},
        ]
        mock_info = {
            "channel": "Canal Teste",
            "entries": mock_entries
        }

        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            mock_inst = MagicMock()
            mock_inst.extract_info.return_value = mock_info
            mock_ydl.return_value.__enter__.return_value = mock_inst

            res = autoviral_brain.espionar_canais_concorrentes(
                canais_handles=["https://www.youtube.com/@CanalTeste/shorts"],
                multiplicador_minimo=2.0,
                max_dias_idade=None
            )

            diag = res["diagnostico_canais"][0]
            self.assertEqual(diag["mediana_views"], 11000)
            self.assertEqual(diag["media_views"], 108400)
            self.assertEqual(len(res["outliers"]), 1)
            outlier = res["outliers"][0]
            # 500.000 / 11.000 = ~45.45x
            self.assertEqual(outlier["multiplicador_mediana"], 45.45)
            # Na média tradicional seria apenas 500.000 / 108.400 = 4.61x
            self.assertEqual(outlier["multiplicador_media"], 4.61)

    def test_02_amostra_vazia(self):
        """Valida comportamento quando um canal não tem vídeos com métricas."""
        mock_info = {
            "channel": "Canal Vazio",
            "entries": []
        }
        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            mock_inst = MagicMock()
            mock_inst.extract_info.return_value = mock_info
            mock_ydl.return_value.__enter__.return_value = mock_inst

            res = autoviral_brain.espionar_canais_concorrentes(
                canais_handles=["https://www.youtube.com/@CanalVazio/shorts"]
            )
            self.assertEqual(len(res["outliers"]), 0)
            self.assertEqual(len(res["erros"]), 1)
            self.assertIn("Nenhum vídeo com métricas", res["erros"][0]["erro"])

    def test_03_canal_indisponivel_404(self):
        """Valida tratamento de erro por canal sem interromper o resto da recolha."""
        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            mock_inst = MagicMock()
            # O primeiro dá erro/None (404), o segundo retorna dados normais
            def extract_side_effect(url, download=False):
                if "404" in url:
                    return None
                return {
                    "channel": "Canal OK",
                    "entries": [{"id": "v1", "title": "Video OK", "view_count": 50000, "duration": 40, "timestamp": 1792400000}]
                }
            mock_inst.extract_info.side_effect = extract_side_effect
            mock_ydl.return_value.__enter__.return_value = mock_inst

            res = autoviral_brain.espionar_canais_concorrentes(
                canais_handles=[
                    "https://www.youtube.com/@Inexistente404/shorts",
                    "https://www.youtube.com/@CanalOK/shorts"
                ],
                max_dias_idade=None
            )
            self.assertEqual(len(res["erros"]), 1)
            self.assertIn("indisponível", res["erros"][0]["erro"])
            self.assertEqual(len(res["diagnostico_canais"]), 1)
            self.assertEqual(res["diagnostico_canais"][0]["canal"], "Canal OK")

    def test_04_separacao_de_formatos_shorts_vs_longos(self):
        """Valida que Shorts não são misturados com vídeos longos."""
        # Amostra com mediana baixa (5000) para o Short Real (50.000) ser 10x outlier
        mock_info_shorts = {
            "channel": "Canal Shorts",
            "entries": [
                {"id": "s1", "title": "Short Real", "view_count": 50000, "duration": 35, "timestamp": 1792400000, "upload_date": "20261018"},
                {"id": "s2", "title": "Short Normal 1", "view_count": 5000, "duration": 45, "timestamp": 1792400000, "upload_date": "20261018"},
                {"id": "s3", "title": "Short Normal 2", "view_count": 5000, "duration": 45, "timestamp": 1792400000, "upload_date": "20261018"},
                {"id": "s4", "title": "Short Normal 3", "view_count": 4000, "duration": 45, "timestamp": 1792400000, "upload_date": "20261018"},
                {"id": "l1", "title": "Longo Infiltrado", "view_count": 80000, "duration": 900, "timestamp": 1792400000, "upload_date": "20261018"}, # 15 min!
            ]
        }
        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            mock_inst = MagicMock()
            mock_inst.extract_info.return_value = mock_info_shorts
            mock_ydl.return_value.__enter__.return_value = mock_inst

            res = autoviral_brain.espionar_canais_concorrentes(
                canais_handles=["https://www.youtube.com/@CanalShorts/shorts"],
                multiplicador_minimo=2.0,
                max_dias_idade=None
            )
            titulos_outliers = [o["titulo"] for o in res["outliers"]]
            self.assertIn("Short Real", titulos_outliers)
            self.assertNotIn("Longo Infiltrado", titulos_outliers)

    def test_05_filtro_configuravel_de_idade(self):
        """Valida que o filtro de idade descarta vídeos virais antigos quando ativado."""
        # Amostra com mediana 1000 para o viral de 100.000 ser 100x outlier
        mock_info = {
            "channel": "Canal Idade",
            "entries": [
                {"id": "v1", "title": "Viral Antigo 120 dias", "view_count": 100000, "duration": 30, "timestamp": 1782000000, "upload_date": "20260601"},
                {"id": "v2", "title": "Normal 1", "view_count": 1000, "duration": 30, "timestamp": 1792400000, "upload_date": "20261018"},
                {"id": "v3", "title": "Normal 2", "view_count": 1000, "duration": 30, "timestamp": 1792400000, "upload_date": "20261018"},
            ]
        }
        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            mock_inst = MagicMock()
            mock_inst.extract_info.return_value = mock_info
            mock_ydl.return_value.__enter__.return_value = mock_inst

            # Com limite de 60 dias, o vídeo de 120 dias deve ser ignorado
            res_com_filtro = autoviral_brain.espionar_canais_concorrentes(
                canais_handles=["https://www.youtube.com/@CanalIdade/shorts"],
                max_dias_idade=60
            )
            self.assertEqual(len(res_com_filtro["outliers"]), 0)

            # Sem limite de idade (None), o vídeo deve ser incluído
            res_sem_filtro = autoviral_brain.espionar_canais_concorrentes(
                canais_handles=["https://www.youtube.com/@CanalIdade/shorts"],
                max_dias_idade=None
            )
            self.assertEqual(len(res_sem_filtro["outliers"]), 1)
            self.assertEqual(res_sem_filtro["outliers"][0]["titulo"], "Viral Antigo 120 dias")


if __name__ == "__main__":
    unittest.main()
