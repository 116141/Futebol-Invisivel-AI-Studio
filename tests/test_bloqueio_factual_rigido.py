import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, r"c:\Users\Uni-CvFCT-EdmilsonGi\Documents\projectoD\money")
import autoviral_brain
import app_render_studio


class TestBloqueioFactualRigido(unittest.TestCase):

    def test_01_bloqueia_sem_arquivo_especifico_da_tarefa(self):
        """Valida que se task_id não tem verificacao_factual_{task_id}.json, BLOQUEIA IMEDIATAMENTE."""
        task_id = "tarefa_sem_json_especifico_999"
        res = autoviral_brain.verificar_bloqueio_factual(task_id=task_id)
        self.assertEqual(res["status"], "bloqueado")
        self.assertIn("arquivo_inexistente", res["pendencias"])
        self.assertEqual(res["json_path"], f"verificacao_factual_{task_id}.json")

    def test_02_bloqueia_se_task_id_e_json_path_vazios(self):
        """Valida que chamar verificar_bloqueio_factual() sem parâmetros bloqueia preventivamente."""
        res = autoviral_brain.verificar_bloqueio_factual()
        self.assertEqual(res["status"], "bloqueado")
        self.assertIn("task_id_obrigatorio", res["pendencias"])

    def test_03_caminho_positivo_aprovacao_humana_externa_com_hashes(self):
        """
        Valida (1) e (2): Caminho positivo de aprovação humana.
        A aprovação reside em arquivo externo (aprovacao_humana_{task_id}.json) com quem, quando e ambos os hashes.
        """
        roteiro = "Disseram que o segurança de Messi era Navy SEAL. Segundo o Daily Mail, ninguém o encontrou nos registos."
        hash_guiao_correto = autoviral_brain.calcular_hash_conteudo(roteiro)

        dados_factual = {
            "politica_bloqueio": {
                "bloqueia_renderizacao_se": ["pendente", "sem_fonte"]
            },
            "frases_guião": [
                {"id": "F1", "frase": "Disseram que o segurança de Messi era Navy SEAL.", "estado": "verificado_copia"},
                {"id": "F2", "frase": "Segundo o Daily Mail, ninguém o encontrou nos registos.", "estado": "verificado_copia"}
            ],
            "visuais": {"estado": "revisao"}
        }
        json_str = json.dumps(dados_factual)
        hash_json_correto = autoviral_brain.calcular_hash_conteudo(json_str)

        dados_aprovacao = {
            "aprovado_por": "Editor Chefe Humano",
            "aprovado_em": "2026-10-20 18:30:00",
            "hash_guiao_aprovado": hash_guiao_correto,
            "hash_json_aprovado": hash_json_correto
        }

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f_fact:
            f_fact.write(json_str)
            fact_path = f_fact.name

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f_aprov:
            json.dump(dados_aprovacao, f_aprov)
            aprov_path = f_aprov.name

        try:
            res_ok = autoviral_brain.verificar_bloqueio_factual(
                roteiro_texto=roteiro,
                json_path=fact_path,
                aprovacao_path=aprov_path
            )
            self.assertEqual(res_ok["status"], "permitido_com_aprovacao_humana")
            self.assertEqual(res_ok["aprovado_por"], "Editor Chefe Humano")
        finally:
            if os.path.exists(fact_path):
                os.remove(fact_path)
            if os.path.exists(aprov_path):
                os.remove(aprov_path)

    def test_04_bloqueia_se_json_adulterado_apos_aprovacao(self):
        """Valida (2) e (7): Se o JSON factual for alterado após a aprovação humana, o hash não bate e BLOQUEIA."""
        roteiro = "Disseram que o segurança de Messi era Navy SEAL. Segundo o Daily Mail, ninguém o encontrou nos registos."
        hash_guiao_correto = autoviral_brain.calcular_hash_conteudo(roteiro)

        dados_factual = {
            "politica_bloqueio": {"bloqueia_renderizacao_se": ["pendente", "sem_fonte"]},
            "frases_guião": [
                {"id": "F1", "frase": "Disseram que o segurança de Messi era Navy SEAL.", "estado": "verificado_copia"},
                {"id": "F2", "frase": "Segundo o Daily Mail, ninguém o encontrou nos registos.", "estado": "verificado_copia"}
            ],
            "visuais": {"estado": "revisao"}
        }
        json_str_original = json.dumps(dados_factual)
        hash_json_original = autoviral_brain.calcular_hash_conteudo(json_str_original)

        dados_aprovacao = {
            "aprovado_por": "Editor Chefe Humano",
            "aprovado_em": "2026-10-20 18:30:00",
            "hash_guiao_aprovado": hash_guiao_correto,
            "hash_json_aprovado": hash_json_original
        }

        # Alteração no JSON factual após a assinatura
        dados_factual["frases_guião"].append({"id": "F99", "frase": "Frase infiltrada sem nova assinatura.", "estado": "verificado_original"})
        json_str_adulterado = json.dumps(dados_factual)

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f_fact:
            f_fact.write(json_str_adulterado)
            fact_path = f_fact.name

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f_aprov:
            json.dump(dados_aprovacao, f_aprov)
            aprov_path = f_aprov.name

        try:
            res = autoviral_brain.verificar_bloqueio_factual(
                roteiro_texto=roteiro,
                json_path=fact_path,
                aprovacao_path=aprov_path
            )
            self.assertEqual(res["status"], "bloqueado")
            self.assertIn("hash_json_adulterado", res["pendencias"])
            self.assertIn("JSON factual foi adulterado após a aprovação humana", res["motivo"])
        finally:
            if os.path.exists(fact_path):
                os.remove(fact_path)
            if os.path.exists(aprov_path):
                os.remove(aprov_path)

    def test_05_bloqueia_se_guiao_adulterado_apos_aprovacao(self):
        """Valida (2): Se o roteiro/guião for alterado após a aprovação humana, BLOQUEIA."""
        roteiro_original = "Disseram que o segurança de Messi era Navy SEAL. Segundo o Daily Mail, ninguém o encontrou nos registos."
        hash_guiao_original = autoviral_brain.calcular_hash_conteudo(roteiro_original)

        dados_factual = {
            "politica_bloqueio": {"bloqueia_renderizacao_se": ["pendente", "sem_fonte"]},
            "frases_guião": [
                {"id": "F1", "frase": "Disseram que o segurança de Messi era Navy SEAL.", "estado": "verificado_copia"},
                {"id": "F2", "frase": "Segundo o Daily Mail, ninguém o encontrou nos registos.", "estado": "verificado_copia"}
            ],
            "visuais": {"estado": "revisao"}
        }
        json_str = json.dumps(dados_factual)
        hash_json = autoviral_brain.calcular_hash_conteudo(json_str)

        dados_aprovacao = {
            "aprovado_por": "Editor Chefe Humano",
            "aprovado_em": "2026-10-20 18:30:00",
            "hash_guiao_aprovado": hash_guiao_original,
            "hash_json_aprovado": hash_json
        }

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f_fact:
            f_fact.write(json_str)
            fact_path = f_fact.name

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f_aprov:
            json.dump(dados_aprovacao, f_aprov)
            aprov_path = f_aprov.name

        try:
            roteiro_adulterado = roteiro_original + " E ele lutou em cinco guerras secretas."
            res = autoviral_brain.verificar_bloqueio_factual(
                roteiro_texto=roteiro_adulterado,
                json_path=fact_path,
                aprovacao_path=aprov_path
            )
            self.assertEqual(res["status"], "bloqueado")
            self.assertIn("hash_guiao_adulterado", res["pendencias"])
        finally:
            if os.path.exists(fact_path):
                os.remove(fact_path)
            if os.path.exists(aprov_path):
                os.remove(aprov_path)

    def test_06_mapeamento_ids_frases_factuais_e_bloqueio_de_frases_sem_id(self):
        """Valida (3): Cada frase factual tem de ter ID correspondente no JSON. Frases factuais sem ID bloqueiam."""
        # Caso 1: Roteiro com afirmação factual inventada sem ID nem correspondência no JSON -> BLOQUEIA
        roteiro_com_afirmacao_sem_id = (
            "Disseram que o segurança de Messi era Navy SEAL. "
            "Segundo o Daily Mail, ninguém o encontrou nos registos. "
            "Ele comprou uma mansão milionária em Miami na semana passada e assinou novo acordo."
        )
        res_invalido = autoviral_brain.verificar_roteiro_mapeia_frases_verificadas(
            roteiro_com_afirmacao_sem_id,
            "verificacao_factual_piloto.json"
        )
        self.assertFalse(res_invalido["valido"])
        self.assertIn("frases_sem_id", res_invalido)
        self.assertTrue(len(res_invalido["frases_sem_id"]) > 0)

        # Caso 2: Roteiro onde todas as afirmações mapeiam para IDs cadastrados -> VÁLIDO
        roteiro_valido = (
            "Disseram que o segurança de Messi era Navy SEAL. "
            "Segundo o Daily Mail, ninguém o encontrou nos registos. "
            "Segundo o clube, é funcionário da Inter Miami."
        )
        res_valido = autoviral_brain.verificar_roteiro_mapeia_frases_verificadas(
            roteiro_valido,
            "verificacao_factual_piloto.json"
        )
        self.assertTrue(res_valido["valido"])
        self.assertTrue(all(k in ["F1", "F2", "F4"] for k in res_valido["cobertura"]))

    def test_07_padroes_proibidos_com_variantes_pt_br_e_sem_falsos_positivos(self):
        """
        Valida (4):
          - Captura formulações alternativas e variantes de Português do Brasil (PT-BR).
          - NÃO gera falso positivo para menções benignas de economia/notícias gerais.
        """
        # Variantes proibidas em PT-BR e reformulações que DEVEM ser bloqueadas
        frases_proibidas = [
            ("O segurança embolsa por volta de duzentos mil dólares por mês.", "salario"),
            ("Ele fatura rios de dinheiro cuidando do camisa 10.", "salario"),
            ("A remuneração astronômica dele gerou comentários no vestiário.", "salario"),
            ("O custo anual do segurança ultrapassa milhões de reais.", "valor_contrato"),
            ("Foi David Beckham que bancou a vinda do guarda-costas.", "contratado_por_beckham"),
            ("Segundo o técnico Tata Martino, não há nada confirmado.", "citacao_direta_martino"),
            ("A MLS barrou o guarda-costas de pisar na lateral.", "a_mls_proibiu"),
            ("Houve uma proibição formal da MLS contra sua permanência.", "a_mls_proibiu"),
            ("Tudo não passou de uma farsa montada nas redes sociais.", "farsa"),
            ("Um esquema fraudulento montado para atrair visualizações.", "fraude"),
            ("Ele mentiu descaradamente sobre o passado militar.", "mentiu"),
            ("O farsante foi completamente desmascarado pelos repórteres.", "desmascarado"),
        ]
        for texto, termo_esperado in frases_proibidas:
            encontradas = autoviral_brain.verificar_frases_proibidas_roteiro(texto)
            self.assertTrue(len(encontradas) > 0, f"Deveria ter bloqueado o texto: '{texto}'")
            self.assertIn(termo_esperado, encontradas)

        # Falsos positivos que NÃO DEVEM ser bloqueados (notícias benignas de economia / sociedade)
        frases_benignas = [
            "O salário mínimo no Brasil subiu este ano após votação do congresso nacional.",
            "O governo estuda uma política para o salário médio dos trabalhadores da indústria.",
            "A economia global registrou alta na média salarial segundo dados do banco central."
        ]
        for texto in frases_benignas:
            encontradas = autoviral_brain.verificar_frases_proibidas_roteiro(texto)
            self.assertEqual(len(encontradas), 0, f"Falso positivo incorreto em texto benigno: '{texto}' (encontrou: {encontradas})")

    def test_08_valida_afiliado_moda_com_dominio_permitido_e_produto_real(self):
        """
        Valida (5):
          - Rejeita domínios estranhos ou ausência de produto real.
          - Aceita estritamente aliexpress.com e s.click.aliexpress.com com product_id real.
        """
        # 1. Tentativa com domínio não autorizado (bypass)
        task_id_fake = "task_bypass_dominio_invalido"
        app_render_studio.TASKS[task_id_fake] = {"status": "Iniciando..."}
        app_render_studio.processar_video(
            task_id=task_id_fake,
            titulo="Vestido Elegante",
            tipo="afiliado_moda",
            promo_raw="Confira o produto em https://phishing-site.com/item/12345"
        )
        self.assertTrue(app_render_studio.TASKS[task_id_fake]["status"].startswith("Erro: Tentativa de desvio detectada"))

        # 2. Tentativa sem nenhum produto nem link
        task_id_vazio = "task_bypass_sem_nada"
        app_render_studio.TASKS[task_id_vazio] = {"status": "Iniciando..."}
        app_render_studio.processar_video(
            task_id=task_id_vazio,
            titulo="Vestido Sem Link",
            tipo="afiliado_moda"
        )
        self.assertTrue(app_render_studio.TASKS[task_id_vazio]["status"].startswith("Erro: Tentativa de desvio detectada"))

    def test_09_processar_video_aborta_editorial_sem_aprovacao_humana(self):
        """Valida (1) e (7): processar_video() aborta vídeo editorial que não tem aprovação humana."""
        task_id = "task_editorial_sem_aprovacao_777"
        app_render_studio.TASKS[task_id] = {"status": "Iniciando..."}

        # Cria arquivo factual mas sem aprovação humana
        dados_factual = {
            "politica_bloqueio": {"bloqueia_renderizacao_se": ["pendente", "sem_fonte"]},
            "frases_guião": [
                {"id": "F1", "frase": "Disseram que o segurança de Messi era Navy SEAL.", "estado": "verificado_copia"}
            ],
            "visuais": {"estado": "pendente"}
        }
        json_path = f"verificacao_factual_{task_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dados_factual, f)

        try:
            app_render_studio.processar_video(
                task_id=task_id,
                titulo="História do Segurança de Messi",
                tipo="short"
            )
            status_final = app_render_studio.TASKS[task_id]["status"]
            self.assertTrue(status_final.startswith("Erro: Bloqueio Editorial Ativo"))
            self.assertIn("Existem pendências factuais ou visuais bloqueantes", status_final)
        finally:
            if os.path.exists(json_path):
                os.remove(json_path)

    def test_10_processar_video_aborta_pre_tts_se_hash_roteiro_nao_confere(self):
        """
        Valida que se o vídeo tiver aprovação humana inicial, mas o roteiro a ser narrado
        não bater exatamente com o hash_guiao_aprovado na checagem pré-TTS, o processo é abortado.
        """
        from unittest.mock import patch

        task_id = "task_editorial_adulterado_pre_tts_888"
        app_render_studio.TASKS[task_id] = {"status": "Iniciando..."}

        roteiro_original = "Frase autorizada estritamente pelo editor-chefe para o canal."
        hash_original = autoviral_brain.calcular_hash_conteudo(roteiro_original)

        dados_factual = {
            "politica_bloqueio": {"bloqueia_renderizacao_se": ["pendente", "sem_fonte"]},
            "frases_guião": [
                {"id": "F1", "frase": "Frase autorizada estritamente pelo editor-chefe para o canal.", "estado": "verificado_copia"}
            ],
            "visuais": {"estado": "aprovado"}
        }
        json_str = json.dumps(dados_factual)
        hash_json = autoviral_brain.calcular_hash_conteudo(json_str)

        dados_aprovacao = {
            "aprovado_por": "Editor Chefe Humano",
            "aprovado_em": "2026-10-20 20:30:00",
            "hash_guiao_aprovado": hash_original,
            "hash_json_aprovado": hash_json
        }

        factual_file = f"verificacao_factual_{task_id}.json"
        aprovacao_file = f"aprovacao_humana_{task_id}.json"

        with open(factual_file, "w", encoding="utf-8") as f:
            f.write(json_str)
        with open(aprovacao_file, "w", encoding="utf-8") as f:
            json.dump(dados_aprovacao, f)

        # Roteiro novo gerado que diverge do hash aprovado
        roteiro_modificado = "Frase adulterada que tenta ir para a narração sem nova aprovação."

        try:
            from app.services import llm
            with patch.object(llm, "generate_script", return_value=roteiro_modificado):
                with patch("app.services.voice.azure_tts_v1") as mock_tts:
                    app_render_studio.processar_video(
                        task_id=task_id,
                        titulo="Assunto Teste",
                        tipo="short"
                    )
                    # TTS não pode ser chamado
                    mock_tts.assert_not_called()

            status_final = app_render_studio.TASKS[task_id]["status"]
            self.assertTrue(status_final.startswith("Erro: Bloqueio Editorial"))
        finally:
            if os.path.exists(factual_file):
                os.remove(factual_file)
            if os.path.exists(aprovacao_file):
                os.remove(aprovacao_file)


if __name__ == "__main__":
    unittest.main()
