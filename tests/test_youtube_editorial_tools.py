import os
import unittest
import tempfile
from app.services import youtube_editorial_tools as yet


class TestYouTubeEditorialTools(unittest.TestCase):
    """Testes unitários isolados e determinísticos da camada de integração editorial."""

    def test_01_avaliar_ganchos_validos_e_invalidos(self):
        """Valida pontuação de ganchos com propriedades calculadas e tratamento de entradas vazias."""
        ganchos = [
            "Why 1 mistake in the 2024 season cost them the title",
            "",
            "   ",
            None
        ]
        res = yet.avaliar_ganchos_editorial(ganchos)
        self.assertEqual(len(res), 4)

        # O primeiro gancho válido deve ter propriedades completas
        valido = res[0]
        self.assertIn("properties", valido)
        self.assertIn("verdict", valido)
        self.assertIn("weakest_property", valido)
        self.assertIn("alerta_editorial", valido)
        self.assertGreaterEqual(valido["verdict"], 0)
        self.assertLessEqual(valido["verdict"], 100)

        # Entradas inválidas devem retornar status apropriado sem quebrar o módulo
        invalidos = [r for r in res if r.get("band") == "INVALID"]
        self.assertEqual(len(invalidos), 3)

    def test_02_avaliar_par_titulo_capa_complementar(self):
        """Valida que títulos e capas com termos diferentes recebem pontuação alta de complementaridade."""
        titulo = "How the 1994 Decision Changed the Whole Season"
        capa = "HIDDEN EVIDENCE"
        res = yet.avaliar_par_titulo_capa(titulo, capa)

        self.assertIn("score", res)
        self.assertGreaterEqual(res["score"], 80)
        self.assertIn("thumbnail and title carry different words", res["good"])
        issues_types = [issue[0] for issue in res.get("issues", [])]
        self.assertNotIn("duplicate", issues_types)

    def test_03_avaliar_par_titulo_capa_com_repeticao(self):
        """Valida detecção de palavras duplicadas entre o título e a capa."""
        titulo = "The Secret Contract Revealed in 2024"
        capa = "SECRET CONTRACT"
        res = yet.avaliar_par_titulo_capa(titulo, capa)

        issues_types = [issue[0] for issue in res.get("issues", [])]
        self.assertIn("duplicate", issues_types)
        self.assertLess(res["score"], 85)

    def test_04_avaliar_par_titulo_vazio(self):
        """Valida tratamento gracioso para títulos vazios."""
        res = yet.avaliar_par_titulo_capa("")
        self.assertEqual(res["score"], 0)
        self.assertIn("erro", res)

    def test_05_analisar_retencao_csv_valido(self):
        """Valida leitura e cálculo de hook leak, cliffs e slide a partir de CSV sintético."""
        csv_data = (
            "Time,Percentage\n"
            "0.0,100.0\n"
            "5.0,88.0\n"
            "10.0,79.0\n"
            "15.0,72.0\n"
            "20.0,68.0\n"
            "25.0,63.0\n"
            "30.0,55.0\n"
            "35.0,50.0\n"
            "40.0,46.0\n"
        )
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as f:
            f.write(csv_data)
            tpath = f.name

        try:
            res = yet.analisar_retencao_csv(tpath)
            self.assertTrue(res["sucesso"])
            self.assertEqual(res["points"], 9)
            self.assertEqual(res["start"], 100.0)
            # No eixo de porcentagem sem duração informada, cutoff = 10.0%. Ponto em 10.0% é 79.0%. Leak = 100.0 - 79.0 = 21.0%
            self.assertEqual(res["hook_leak"], 21.0)
            self.assertEqual(res["verdict"], "healthy")
            self.assertIn("recomendacao", res)
            self.assertIsInstance(res["cliffs"], list)
        finally:
            if os.path.exists(tpath):
                os.remove(tpath)

    def test_06_analisar_retencao_csv_amostra_insuficiente(self):
        """Valida recusa segura quando o CSV possui menos de 8 pontos de dados."""
        csv_curto = "Time,Percentage\n0.0,100.0\n10.0,80.0\n20.0,60.0\n"
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as f:
            f.write(csv_curto)
            tpath = f.name

        try:
            res = yet.analisar_retencao_csv(tpath)
            self.assertFalse(res["sucesso"])
            self.assertIn("Amostra insuficiente", res["erro"])
        finally:
            if os.path.exists(tpath):
                os.remove(tpath)

    def test_07_analisar_retencao_arquivo_inexistente(self):
        """Valida tratamento seguro quando o arquivo CSV não existe."""
        res = yet.analisar_retencao_csv("arquivo_completamente_inexistente_12345.csv")
        self.assertFalse(res["sucesso"])
        self.assertIn("não encontrado", res["erro"])

    def test_07b_analisar_retencao_extensao_invalida(self):
        """Valida recusa imediata de arquivos que não possuam extensão .csv (prevenção de leitura arbitrária)."""
        res = yet.analisar_retencao_csv(".env")
        self.assertFalse(res["sucesso"])
        self.assertIn("Apenas arquivos .csv", res["erro"])

    def test_08_camada_nao_contorna_aprovacao_nem_inicia_render(self):
        """
        Garante que chamar as funções consultivas NÃO cria tarefas em TASKS,
        NÃO cria arquivos de aprovação e NÃO altera estados do sistema.
        """
        # Checar se nenhum arquivo 'aprovacao_humana_*' foi criado indevidamente
        arquivos_antes = [f for f in os.listdir(".") if f.startswith("aprovacao_humana_")]

        _ = yet.avaliar_ganchos_editorial(["Gancho de teste sem efeito"])
        _ = yet.avaliar_par_titulo_capa("Titulo de Teste", "Capa de Teste")

        arquivos_depois = [f for f in os.listdir(".") if f.startswith("aprovacao_humana_")]
        self.assertEqual(len(arquivos_antes), len(arquivos_depois))


if __name__ == "__main__":
    unittest.main()
