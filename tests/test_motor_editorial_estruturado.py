import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services import llm
import autoviral_brain
import app_render_studio


class TestMotorEditorialEstruturado(unittest.TestCase):
    """
    Testes unitários isolados para a Fase G:
      - Validação de contagem de palavras narradas.
      - Deteção de introduções proibidas.
      - Validação das 3 micro-missões e sinalizadores narrativos.
      - Limite de tentativas sem ciclos infinitos.
      - Complementaridade entre título e capa (anti-repetição literal).
      - Preservação intacta da trava factual.
    IMPORTANTE: Preparado para validação futura sem execução de chamadas externas de LLM ou renderizações.
    """

    def test_01_contagem_palavras_narradas_ignora_metadados(self):
        """Valida que contar_palavras_narradas conta apenas texto falado, ignorando tags."""
        texto_com_tags = "[MISSÃO 1] Lionel Messi assinou novo acordo confidencial. (Cena 1: estádio à noite) [F1]"
        qtd = llm.contar_palavras_narradas(texto_com_tags)
        # Palavras contadas: Lionel, Messi, assinou, novo, acordo, confidencial = 6
        self.assertEqual(qtd, 6)

    def test_02_detecta_introducoes_proibidas_no_inicio(self):
        """Valida que chavões vazios no início do roteiro são rejeitados."""
        roteiro_ruim = (
            "Neste vídeo você vai ver como o jogador tomou a maior decisão da sua vida no futebol europeu. "
            "A diretoria convocou reunião de urgência nos bastidores para fechar os novos valores contratuais. "
            "E no final de tudo a história mudou de rumo completamente após o anúncio da federação esportiva."
        )
        res = llm.validar_estrutura_editorial_roteiro(roteiro_ruim, min_palavras=30, max_palavras=60)
        self.assertFalse(res["valido"])
        self.assertIn("violacao_introducao", res["detalhes"])

    def test_03_valida_roteiro_estruturado_com_open_loop_e_faixa_palavras(self):
        """
        Valida que um texto narrado estruturado com 3 períodos, sem introduções vazias,
        com Open Loop e dentro da faixa configurada é aprovado.
        (Usa dados sintéticos identificados explicitamente como teste).
        """
        roteiro_sintetico_valido = (
            "Três cláusulas confidenciais colocaram o atleta fictício no centro de uma disputa jurídica intensa e complexa. "
            "A auditoria independente encontrou divergências graves nos contratos assinados, mas quando os peritos abriram "
            "as planilhas anexas, a surpresa nos bastidores foi imediata. Documentos revelaram termos que a diretoria "
            "tentou abafar durante meses, gerando punições severas no tribunal esportivo. E foi assim que tudo começou com..."
        )
        qtd = llm.contar_palavras_narradas(roteiro_sintetico_valido)
        res = llm.validar_estrutura_editorial_roteiro(roteiro_sintetico_valido, min_palavras=60, max_palavras=85)
        self.assertTrue(res["valido"], f"Deveria ser válido: {res.get('motivo')} (qtd={qtd})")
        self.assertTrue(res["detalhes"]["tem_open_loop"])
        self.assertTrue(res["detalhes"]["total_sentencas"] >= 3)

    def test_04_rejeita_roteiro_fora_da_faixa_de_palavras(self):
        """Valida que roteiros muito curtos ou longos são reprovados pela contagem."""
        roteiro_curto = "O atleta assinou o contrato ontem à tarde e todos comemoraram a vitória no campeonato."
        res_curto = llm.validar_estrutura_editorial_roteiro(roteiro_curto, min_palavras=68, max_palavras=82)
        self.assertFalse(res_curto["valido"])
        self.assertIn("fora do intervalo", res_curto["motivo"])

    def test_05_complementaridade_titulo_capa_detecta_repeticao_excessiva(self):
        """Valida que título e capa com texto idêntico são apontados como repetitivos."""
        titulo = "A Fraude das Contas no Futebol"
        capa_repetida = "A Fraude das Contas no Futebol"
        res_repetido = llm.validar_complementaridade_titulo_capa(titulo, capa_repetida)
        self.assertFalse(res_repetido["complementar"])
        self.assertIn("Repetição excessiva", res_repetido["motivo"])

        capa_complementar = "DOCUMENTOS SECRETOS E PUNIÇÃO!"
        res_ok = llm.validar_complementaridade_titulo_capa(titulo, capa_complementar)
        self.assertTrue(res_ok["complementar"])

    def test_06_trava_factual_permanece_ativa_e_intacta(self):
        """Garante que as proteções de segurança e trava factual continuam operando estritamente."""
        res = autoviral_brain.verificar_bloqueio_factual()
        self.assertEqual(res["status"], "bloqueado")
        self.assertIn("task_id_obrigatorio", res["pendencias"])

    def test_07_geracao_com_gancho_rejeita_fallback_silencioso_quando_esgota_tentativas(self):
        """
        Valida que generate_script_with_hook() levanta ValueError e NÃO retorna
        fallback silencioso quando todas as tentativas de validação falham.
        Usa mock local isolado de generate_script para não fazer chamadas de rede.
        """
        from unittest.mock import patch

        texto_reprovado = "Texto curtíssimo e inválido."
        with patch.object(llm, "_generate_response", return_value=texto_reprovado):
            with self.assertRaises(ValueError) as ctx:
                llm.generate_script_with_hook(
                    video_subject="Assunto Teste",
                    gancho_escolhido="Gancho Teste"
                )
            self.assertIn("Falha na validação editorial do roteiro", str(ctx.exception))

    def test_08_processar_video_aborta_pre_tts_se_roteiro_diverge_do_hash_aprovado(self):
        """
        Valida que processar_video() aborta imediatamente antes de invocar TTS
        se o roteiro divergir do hash aprovado formalmente.
        """
        import json
        from unittest.mock import patch

        task_id = "task_teste_hash_pre_tts_999"
        app_render_studio.TASKS[task_id] = {"status": "Iniciando..."}

        roteiro_aprovado = "Frase aprovada pelo comitê editorial com precisão cirúrgica."
        hash_aprovado = autoviral_brain.calcular_hash_conteudo(roteiro_aprovado)

        dados_factual = {
            "politica_bloqueio": {"bloqueia_renderizacao_se": ["pendente", "sem_fonte"]},
            "frases_guião": [
                {"id": "F1", "frase": "Frase aprovada pelo comitê editorial com precisão cirúrgica.", "estado": "verificado_copia"}
            ],
            "visuais": {"estado": "aprovado"}
        }
        json_str = json.dumps(dados_factual)
        hash_json = autoviral_brain.calcular_hash_conteudo(json_str)

        dados_aprovacao = {
            "aprovado_por": "Editor Chefe Humano",
            "aprovado_em": "2026-10-20 20:00:00",
            "hash_guiao_aprovado": hash_aprovado,
            "hash_json_aprovado": hash_json
        }

        factual_file = f"verificacao_factual_{task_id}.json"
        aprovacao_file = f"aprovacao_humana_{task_id}.json"

        with open(factual_file, "w", encoding="utf-8") as f:
            f.write(json_str)
        with open(aprovacao_file, "w", encoding="utf-8") as f:
            json.dump(dados_aprovacao, f)

        # Roteiro gerado pelo mock diverge propositadamente do aprovado
        roteiro_divergente = "Frase alterada pelo modelo de linguagem sem revalidação humana."

        try:
            with patch.object(llm, "generate_script", return_value=roteiro_divergente):
                with patch("app.services.voice.azure_tts_v1") as mock_tts:
                    app_render_studio.processar_video(
                        task_id=task_id,
                        titulo="Assunto Teste",
                        tipo="short"
                    )
                    # O áudio TTS NUNCA deve ser chamado se o hash diverge
                    mock_tts.assert_not_called()

            status_final = app_render_studio.TASKS[task_id]["status"]
            self.assertTrue(status_final.startswith("Erro: Bloqueio Editorial"))
        finally:
            if os.path.exists(factual_file):
                os.remove(factual_file)
            if os.path.exists(aprovacao_file):
                os.remove(aprovacao_file)

    def test_09_geracao_minuta_editorial_cria_tarefa_pendente_sem_iniciar_tts_ou_render(self):
        """
        Valida Etapa 1 da Fase K:
        A rota /api/editorial/revisar gera a minuta, associa fatos e define status PENDENTE DE REVISÃO,
        sem disparar TTS ou renderização.
        """
        from unittest.mock import patch
        
        texto_minuta = (
            "Três cláusulas confidenciais colocaram o atleta fictício no centro de uma disputa jurídica intensa e complexa nos tribunais esportivos europeus. "
            "A auditoria independente encontrou divergências graves nos contratos assinados, mas quando os peritos abriram "
            "as planilhas anexas, a surpresa nos bastidores foi imediata. Documentos revelaram termos que a diretoria "
            "tentou abafar durante meses, gerando punições severas no tribunal esportivo. E foi assim que tudo começou com..."
        )
        with patch.object(llm, "generate_script", return_value=texto_minuta):
            with patch("app.services.voice.azure_tts_v1") as mock_tts:
                res = app_render_studio.api_editorial_revisar(
                    titulo="Segurança de Messi e Contratos",
                    gancho_escolhido="auto",
                    tema_factual="messi yassine cheuko"
                )
                mock_tts.assert_not_called()
                self.assertEqual(res["status"], "PENDENTE DE REVISÃO")
                self.assertIn("task_id", res)
                task_id = res["task_id"]
                self.assertEqual(app_render_studio.TASKS[task_id]["status"], "PENDENTE DE REVISÃO")
                self.assertTrue(os.path.exists(res["json_path"]))

    def test_10_aprovacao_rejeita_tentativa_sem_autorizacao(self):
        """
        Valida que a rota de aprovação rejeita requests sem a API key de editor autorizada
        ou com credencial inválida, e bloqueia se o servidor não tiver credencial configurada.
        """
        from fastapi import HTTPException
        from unittest.mock import patch
        
        body_invalido = {
            "task_id": "qualquer_id",
            "roteiro_texto": "Texto qualquer de teste para validação de acesso.",
            "api_key": "chave_falsa_invalida"
        }
        
        # 1. Com chave configurada no ambiente, rejeita chave falsa
        with patch.dict(os.environ, {"EDITORIAL_API_KEY": "chave_secreta_teste_2026"}):
            with self.assertRaises(HTTPException) as ctx:
                app_render_studio.api_editorial_aprovar(body_invalido)
            self.assertEqual(ctx.exception.status_code, 403)

        # 2. Sem chave configurada no servidor, falha de forma segura bloqueando qualquer tentativa
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(app_render_studio, "_obter_editorial_api_key", return_value=None):
                with self.assertRaises(HTTPException) as ctx_sem_cfg:
                    app_render_studio.api_editorial_aprovar(body_invalido)
                self.assertEqual(ctx_sem_cfg.exception.status_code, 403)
                self.assertIn("não configurado", ctx_sem_cfg.exception.detail)

    def test_11_aprovacao_valida_assina_hashes_e_renderizar_exige_aprovacao(self):
        """
        Valida Etapa 3 e 4 da Fase K:
        - Aprovação formal assina hashes SHA-256 no arquivo aprovacao_humana_{task_id}.json.
        - Renderização exige aprovação prévia e chave válida configurada.
        """
        import json
        from unittest.mock import patch
        from fastapi import BackgroundTasks

        task_id = "task_teste_fluxo_k_123"
        texto_valido = (
            "Disseram que o segurança de Messi era Navy SEAL. "
            "Segundo o Daily Mail, ninguém o encontrou nos registos. "
            "Segundo o clube, é funcionário da Inter Miami. "
            "E foi assim que os arquivos revelaram que a história começou com..."
        )

        dados_factual = {
            "politica_bloqueio": {"bloqueia_renderizacao_se": ["pendente", "sem_fonte"]},
            "frases_guião": [
                {"id": "F1", "frase": "Disseram que o segurança de Messi era Navy SEAL.", "estado": "verificado_copia"},
                {"id": "F2", "frase": "Segundo o Daily Mail, ninguém o encontrou nos registos.", "estado": "verificado_copia"},
                {"id": "F3", "frase": "Segundo o clube, é funcionário da Inter Miami.", "estado": "verificado_copia"}
            ],
            "visuais": {"estado": "aprovado"}
        }
        factual_file = f"verificacao_factual_{task_id}.json"
        aprovacao_file = f"aprovacao_humana_{task_id}.json"

        with open(factual_file, "w", encoding="utf-8") as f:
            json.dump(dados_factual, f)

        app_render_studio.TASKS[task_id] = {
            "titulo": "Investigação Messi",
            "tipo": "short",
            "status": "PENDENTE DE REVISÃO",
            "roteiro": texto_valido,
            "json_path": factual_file,
            "versao_minuta": 1
        }

        chave_teste = "chave_secreta_para_testes_unitarios_2026"
        try:
            with patch.dict(os.environ, {"EDITORIAL_API_KEY": chave_teste}):
                # 1. Tentar renderizar antes da aprovação deve falhar
                bg = BackgroundTasks()
                from fastapi import HTTPException
                with self.assertRaises(HTTPException) as ctx_rend:
                    app_render_studio.api_editorial_renderizar(
                        background_tasks=bg,
                        body={"task_id": task_id, "api_key": chave_teste}
                    )
                self.assertEqual(ctx_rend.exception.status_code, 400)

                # 2. Executar aprovação formal válida
                body_aprov = {
                    "task_id": task_id,
                    "roteiro_texto": texto_valido,
                    "editor_nome": "Editor Responsável",
                    "api_key": chave_teste
                }
                res_aprov = app_render_studio.api_editorial_aprovar(body_aprov)
                self.assertEqual(res_aprov["status"], "APROVADO PARA RENDERIZAÇÃO")
                self.assertTrue(os.path.exists(aprovacao_file))

                # 3. Agora a renderização é autorizada e muda status para EM RENDERIZAÇÃO
                res_rend = app_render_studio.api_editorial_renderizar(
                    background_tasks=bg,
                    body={"task_id": task_id, "api_key": chave_teste}
                )
                self.assertEqual(res_rend["status"], "EM RENDERIZAÇÃO")

        finally:
            if os.path.exists(factual_file):
                os.remove(factual_file)
            if os.path.exists(aprovacao_file):
                os.remove(aprovacao_file)


if __name__ == "__main__":
    unittest.main()
