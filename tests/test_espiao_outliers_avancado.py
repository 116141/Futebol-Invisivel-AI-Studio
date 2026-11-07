import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, r"c:\Users\Uni-CvFCT-EdmilsonGi\Documents\projectoD\money")
import autoviral_brain


class TestEspiaoOutliersAvancado(unittest.TestCase):

    def setUp(self):
        # Inicializa o banco de dados e limpa a tabela radar_snapshots para testes isolados
        autoviral_brain.init_db()
        conn = autoviral_brain.get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM radar_snapshots WHERE video_id LIKE 'test_%'")
        conn.commit()
        conn.close()

    def test_01_classificar_formato_video(self):
        """Valida classificação precisa de Shorts até 180s, vídeos longos e casos incertos."""
        # 1. Short clássico de 40s da aba /shorts
        self.assertEqual(
            autoviral_brain.classificar_formato_video({"duration": 40, "width": 1080, "height": 1920}, "https://yt.com/@c/shorts"),
            "short"
        )
        # 2. Short moderno de 120s vertical (9:16) da aba /shorts
        self.assertEqual(
            autoviral_brain.classificar_formato_video({"duration": 120, "width": 1080, "height": 1920}, "https://yt.com/@c/shorts"),
            "short"
        )
        # 3. Short quadrado (1:1) de 90s da aba /shorts
        self.assertEqual(
            autoviral_brain.classificar_formato_video({"duration": 90, "width": 1080, "height": 1080}, "https://yt.com/@c/shorts"),
            "short"
        )
        # 4. Caso contraditório: vídeo de 15 minutos (900s) listado na aba /shorts -> deve ser 'incerto'
        self.assertEqual(
            autoviral_brain.classificar_formato_video({"duration": 900, "width": 1080, "height": 1920}, "https://yt.com/@c/shorts"),
            "incerto"
        )
        # 5. Caso contraditório: vídeo horizontal (1920x1080) longo listado na aba /shorts
        self.assertEqual(
            autoviral_brain.classificar_formato_video({"duration": 150, "width": 1920, "height": 1080}, "https://yt.com/@c/shorts"),
            "incerto"
        )
        # 6. Vídeo longo padrão (16:9, 10 minutos) da aba /videos
        self.assertEqual(
            autoviral_brain.classificar_formato_video({"duration": 600, "width": 1920, "height": 1080}, "https://yt.com/@c/videos"),
            "video_longo"
        )
        # 7. Short vertical de 45s publicado na aba /videos -> detectado como 'short'
        self.assertEqual(
            autoviral_brain.classificar_formato_video({"duration": 45, "width": 1080, "height": 1920}, "https://yt.com/@c/videos"),
            "short"
        )

    def test_02_radar_snapshots_velocidade_e_aceleracao(self):
        """Valida gravação idempotente de snapshots, cálculo de velocidade e aceleração real."""
        vid = "test_vid_dinamica_01"
        base_ts = 1792500000

        # Snapshot 1: Primeira observação (10.000 views)
        d1 = autoviral_brain.calcular_dinamica_crescimento_snapshots(vid, 10000, base_ts, "Canal Teste")
        self.assertEqual(d1["status_dinamica"], "primeira_observacao")
        self.assertIsNone(d1["velocidade_intervalo_views_hora"])
        self.assertIsNone(d1["aceleracao_views_hora2"])

        # Teste de idempotência: chamar novamente com o mesmo timestamp não duplica
        d1_dup = autoviral_brain.calcular_dinamica_crescimento_snapshots(vid, 10000, base_ts, "Canal Teste")
        self.assertEqual(d1_dup["total_snapshots"], 1)

        # Snapshot 2: Duas horas depois (+7200s), vídeo subiu para 16.000 views (+6.000 views)
        # Velocidade esperada: 6.000 views / 2 horas = 3.000 views/hora
        ts2 = base_ts + 7200
        d2 = autoviral_brain.calcular_dinamica_crescimento_snapshots(vid, 16000, ts2, "Canal Teste")
        self.assertEqual(d2["status_dinamica"], "velocidade_calculada")
        self.assertEqual(d2["velocidade_intervalo_views_hora"], 3000.0)
        self.assertIsNone(d2["aceleracao_views_hora2"]) # ainda não há 2 intervalos comparáveis

        # Snapshot 3: Mais duas horas depois (+7200s), vídeo explodiu para 28.000 views (+12.000 views)
        # Velocidade no segundo intervalo: 12.000 / 2h = 6.000 views/hora
        # Aceleração = (6000 - 3000) / 2h = 1500 views/hora²
        ts3 = ts2 + 7200
        d3 = autoviral_brain.calcular_dinamica_crescimento_snapshots(vid, 28000, ts3, "Canal Teste")
        self.assertEqual(d3["status_dinamica"], "aceleracao_calculada")
        self.assertEqual(d3["velocidade_intervalo_views_hora"], 6000.0)
        self.assertEqual(d3["aceleracao_views_hora2"], 1500.0)

    def test_03_radar_snapshots_intervalo_curto_e_inconsistencia(self):
        """Valida que intervalos menores que 10 min ou contagens decrescentes são tratados com segurança."""
        vid = "test_vid_edge_cases"
        base_ts = 1792500000

        # Snapshot 1: inicial
        autoviral_brain.calcular_dinamica_crescimento_snapshots(vid, 5000, base_ts, "Canal Edge")

        # Intervalo muito curto: 3 minutos depois (180s)
        d_curto = autoviral_brain.calcular_dinamica_crescimento_snapshots(vid, 5050, base_ts + 180, "Canal Edge")
        self.assertEqual(d_curto["status_dinamica"], "intervalo_muito_curto")
        self.assertIsNone(d_curto["velocidade_intervalo_views_hora"])

        # Contagem inconsistente: YouTube removeu bot views e contagem caiu de 5000 para 4500 após 1h
        d_inconsistente = autoviral_brain.calcular_dinamica_crescimento_snapshots(vid, 4500, base_ts + 3600, "Canal Edge")
        self.assertEqual(d_inconsistente["status_dinamica"], "contagem_inconsistente")
        self.assertIsNone(d_inconsistente["velocidade_intervalo_views_hora"])

    def test_04_contrato_de_retorno_e_diagnostico(self):
        """Valida estrutura do contrato de retorno contendo outliers, diagnostico_canais e erros."""
        mock_info = {
            "channel": "Canal Contrato",
            "entries": [
                {"id": "v1", "title": "Outlier 1", "view_count": 80000, "duration": 40, "timestamp": 1792400000, "upload_date": "20261018", "width": 1080, "height": 1920},
                {"id": "v2", "title": "Normal 1", "view_count": 4000, "duration": 40, "timestamp": 1792400000, "upload_date": "20261018", "width": 1080, "height": 1920},
                {"id": "v3", "title": "Normal 2", "view_count": 4000, "duration": 40, "timestamp": 1792400000, "upload_date": "20261018", "width": 1080, "height": 1920},
            ]
        }
        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            mock_inst = MagicMock()
            mock_inst.extract_info.return_value = mock_info
            mock_ydl.return_value.__enter__.return_value = mock_inst

            res = autoviral_brain.espionar_canais_concorrentes(
                canais_handles=["https://www.youtube.com/@CanalContrato/shorts"]
            )
            self.assertIsInstance(res, dict)
            self.assertIn("outliers", res)
            self.assertIn("diagnostico_canais", res)
            self.assertIn("erros", res)

            outlier = res["outliers"][0]
            self.assertIn("media_historica_views_hora", outlier)
            self.assertIn("velocidade_intervalo_views_hora", outlier)
            self.assertIn("aceleracao_views_hora2", outlier)
            self.assertIn("status_dinamica", outlier)
            self.assertEqual(outlier["formato"], "short")


if __name__ == "__main__":
    unittest.main()
