import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, r"c:\Users\Uni-CvFCT-EdmilsonGi\Documents\projectoD\money")
import autoviral_brain


class TestBloqueioFactualCodigo(unittest.TestCase):

    def test_01_bloqueia_se_arquivo_inexistente(self):
        """Valida bloqueio rigoroso se o arquivo JSON não existir."""
        res = autoviral_brain.verificar_bloqueio_factual(json_path="caminho_totalmente_inexistente.json")
        self.assertEqual(res["status"], "bloqueado")
        self.assertIn("arquivo_inexistente", res["pendencias"])

    def test_02_bloqueia_se_json_corrompido(self):
        """Valida bloqueio se o arquivo contiver JSON inválido ou corrompido."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f:
            f.write("{ este json está corrompido e sem fechar chaves")
            temp_path = f.name
        try:
            res = autoviral_brain.verificar_bloqueio_factual(json_path=temp_path)
            self.assertEqual(res["status"], "bloqueado")
            self.assertIn("json_invalido", res["pendencias"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_03_bloqueia_com_pendente_ou_sem_fonte(self):
        """Valida que qualquer frase com 'pendente' ou 'sem_fonte' bloqueia imediatamente."""
        dados = {
            "politica_bloqueio": {
                "bloqueia_renderizacao_se": ["pendente", "sem_fonte"],
                "exige_aprovacao_humana_se": ["verificado_copia"],
                "renderizacao_automatica_permitida_se": ["verificado_original"]
            },
            "frases_guião": [
                {"id": "F1", "frase": "Frase 1", "estado": "verificado_original"},
                {"id": "F2", "frase": "Frase 2", "estado": "pendente"}, # BLOQUEANTE!
            ],
            "visuais": {"estado": "aprovado"}
        }
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f:
            json.dump(dados, f)
            temp_path = f.name
        try:
            res = autoviral_brain.verificar_bloqueio_factual(json_path=temp_path)
            self.assertEqual(res["status"], "bloqueado")
            self.assertIn("F2 (pendente)", res["pendencias"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_04_bloqueia_com_visuais_pendentes(self):
        """Valida que visuais pendentes geram bloqueio total da renderização."""
        dados = {
            "politica_bloqueio": {
                "bloqueia_renderizacao_se": ["pendente", "sem_fonte"],
                "exige_aprovacao_humana_se": ["verificado_copia"],
                "renderizacao_automatica_permitida_se": ["verificado_original"]
            },
            "frases_guião": [
                {"id": "F1", "frase": "Frase 1", "estado": "verificado_original"},
            ],
            "visuais": {"estado": "pendente"} # BLOQUEANTE!
        }
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f:
            json.dump(dados, f)
            temp_path = f.name
        try:
            res = autoviral_brain.verificar_bloqueio_factual(json_path=temp_path)
            self.assertEqual(res["status"], "bloqueado")
            self.assertIn("visuais (pendente)", res["pendencias"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_05_exige_aprovacao_humana_com_verificado_copia(self):
        """Valida que todas as frases em 'verificado_copia' sem aprovado_por/aprovado_em abortam com 'aprovacao_humana_pendente'."""
        dados = {
            "politica_bloqueio": {
                "bloqueia_renderizacao_se": ["pendente", "sem_fonte"],
                "exige_aprovacao_humana_se": ["verificado_copia"],
                "renderizacao_automatica_permitida_se": ["verificado_original"]
            },
            "frases_guião": [
                {"id": "F1", "frase": "Frase 1", "estado": "verificado_copia"},
                {"id": "F2", "frase": "Frase 2", "estado": "verificado_copia"},
            ],
            "visuais": {"estado": "revisao"}
        }
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f:
            json.dump(dados, f)
            temp_path = f.name
        try:
            res = autoviral_brain.verificar_bloqueio_factual(json_path=temp_path)
            self.assertEqual(res["status"], "aprovacao_humana_pendente")
            self.assertIn("falta_aprovacao_humana", res["pendencias"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_05b_permite_aprovacao_humana_com_assinatura_valida(self):
        """Valida que frases em 'verificado_copia' são liberadas apenas se houver aprovado_por e aprovado_em válidos."""
        dados = {
            "politica_bloqueio": {
                "bloqueia_renderizacao_se": ["pendente", "sem_fonte"],
                "exige_aprovacao_humana_se": ["verificado_copia"],
                "renderizacao_automatica_permitida_se": ["verificado_original"]
            },
            "frases_guião": [
                {"id": "F1", "frase": "Frase 1", "estado": "verificado_copia"},
                {"id": "F2", "frase": "Frase 2", "estado": "verificado_copia"},
            ],
            "visuais": {"estado": "revisao"},
            "aprovado_por": "Editor Chefe",
            "aprovado_em": "2026-10-20 17:00:00"
        }
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f:
            json.dump(dados, f)
            temp_path = f.name
        try:
            res = autoviral_brain.verificar_bloqueio_factual(json_path=temp_path)
            self.assertEqual(res["status"], "permitido_com_aprovacao_humana")
            self.assertEqual(res["aprovado_por"], "Editor Chefe")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_07_processar_video_aborta_efetivamente_no_bloqueio(self):
        """Valida no código de app_render_studio que processar_video() aborta e marca status como Erro."""
        import app_render_studio
        task_id = "test_task_abort_check"
        app_render_studio.TASKS[task_id] = {"status": "Iniciando..."}

        # Chama processar_video com o piloto real (que está em 'verificado_copia' e visuais 'pendente')
        app_render_studio.processar_video(
            task_id=task_id,
            titulo="Quem Realmente Protege Messi?",
            tipo="short"
        )

        status_final = app_render_studio.TASKS[task_id]["status"]
        self.assertTrue(status_final.startswith("Erro: Bloqueio Editorial Ativo"))

    def test_08_verificar_frases_proibidas_no_roteiro(self):
        """Valida que roteiros com termos proibidos como 'salário', 'farsa' ou 'a MLS proibiu' são detectados."""
        roteiro_violador = "Milhões de euros e o salário astronômico de 250 mil dólares! A MLS proibiu ele de jogar e a farsa foi descoberta!"
        proibidas = autoviral_brain.verificar_frases_proibidas_roteiro(roteiro_violador)
        self.assertIn("salario", proibidas)
        self.assertIn("a_mls_proibiu", proibidas)
        self.assertIn("farsa", proibidas)

        roteiro_limpo = "Yassine Cheuko é um lutador de artes marciais registrado como funcionário do Inter Miami."
        proibidas_limpo = autoviral_brain.verificar_frases_proibidas_roteiro(roteiro_limpo)
        self.assertEqual(len(proibidas_limpo), 0)

    def test_06_permite_apenas_se_todas_originais(self):
        """Valida liberação total apenas quando 100% das frases são 'verificado_original' e visuais aprovados."""
        dados = {
            "politica_bloqueio": {
                "bloqueia_renderizacao_se": ["pendente", "sem_fonte"],
                "exige_aprovacao_humana_se": ["verificado_copia"],
                "renderizacao_automatica_permitida_se": ["verificado_original"]
            },
            "frases_guião": [
                {"id": "F1", "frase": "Frase 1", "estado": "verificado_original"},
                {"id": "F2", "frase": "Frase 2", "estado": "verificado_original"},
                {"id": "F3", "frase": "Frase 3", "estado": "opiniao"},
            ],
            "visuais": {"estado": "aprovado"}
        }
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f:
            json.dump(dados, f)
            temp_path = f.name
        try:
            res = autoviral_brain.verificar_bloqueio_factual(json_path=temp_path)
            self.assertEqual(res["status"], "permitido")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
