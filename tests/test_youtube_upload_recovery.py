import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
import autoviral_brain
from app.services import youtube_uploader, autopilot_manager
import app_render_studio

class TestYouTubeUploadRecovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Usa banco isolado de teste para não esvaziar o banco de produção!
        autoviral_brain.DB_PATH = "data/test_autoviral_memory.db"
        autoviral_brain.init_db()
        os.makedirs("canais/temp_test_media", exist_ok=True)
        cls.fake_mp4 = "canais/temp_test_media/fake_video.mp4"
        # Cria arquivo fictício de teste com mais de 1 MB
        with open(cls.fake_mp4, "wb") as f:
            f.write(b"0" * (1024 * 1024 + 100)) # 1 MB + 100 bytes

    @classmethod
    def tearDownClass(cls):
        if os.path.exists("canais/temp_test_media"):
            import shutil
            shutil.rmtree("canais/temp_test_media", ignore_errors=True)
        if os.path.exists("data/test_autoviral_memory.db"):
            try:
                os.remove("data/test_autoviral_memory.db")
            except Exception:
                pass
        autoviral_brain.DB_PATH = os.path.join(autoviral_brain.DB_DIR, "autoviral_memory.db")

    def setUp(self):
        # Limpa tarefas do banco para isolamento entre testes
        autoviral_brain.limpar_tarefas_db()
        app_render_studio.TASKS.clear()
        # Garante canais limpos de bloqueio (incluindo o canal global '*')
        autoviral_brain.liberar_bloqueio_upload_canal("*", motivo_liberacao="test_setup")
        autoviral_brain.liberar_bloqueio_upload_canal("fergil", motivo_liberacao="test_setup")
        autoviral_brain.liberar_bloqueio_upload_canal("futebol", motivo_liberacao="test_setup")
        autoviral_brain.liberar_bloqueio_upload_canal("moda", motivo_liberacao="test_setup")

    # =========================================================================
    # TESTE A: Upload bem-sucedido (Resposta 200 OK com video_id)
    # =========================================================================
    @patch("app.services.youtube_uploader.get_authenticated_service")
    def test_a_upload_sucesso(self, mock_get_auth):
        mock_yt = MagicMock()
        mock_get_auth.return_value = mock_yt
        mock_req = MagicMock()
        mock_req.next_chunk.return_value = (None, {"id": "TEST_VID_OK_123"})
        mock_yt.videos().insert.return_value = mock_req

        res = youtube_uploader.upload_video_youtube(
            file_path=self.fake_mp4,
            title="Video Teste A",
            description="Descricao Teste",
            canal_nome="futebol",
            task_id="task_test_a"
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["video_id"], "TEST_VID_OK_123")
        self.assertIn("TEST_VID_OK_123", res["video_url"])

    # =========================================================================
    # TESTE B: uploadLimitExceeded (HTTP 400 - Preservação e RENDERIZADO_AGUARDANDO_UPLOAD)
    # =========================================================================
    @patch("app.services.youtube_uploader.get_authenticated_service")
    def test_b_upload_limit_exceeded(self, mock_get_auth):
        mock_resp = MagicMock()
        mock_resp.status = 400
        content = b'{"error": {"errors": [{"message": "The user has exceeded the number of videos they may upload.", "domain": "youtube.video", "reason": "uploadLimitExceeded"}], "code": 400}}'
        mock_yt = MagicMock()
        mock_get_auth.return_value = mock_yt
        mock_req = MagicMock()
        mock_req.next_chunk.side_effect = HttpError(mock_resp, content)
        mock_yt.videos().insert.return_value = mock_req

        task_id = "task_test_b"
        app_render_studio.TASKS[task_id] = {
            "task_id": task_id,
            "titulo": "Video Teste B",
            "file_path": self.fake_mp4,
            "canal_destino": "fergil",
            "status": "Iniciando...",
            "tipo": "short"
        }
        autoviral_brain.salvar_tarefa_db(task_id, app_render_studio.TASKS[task_id])

        with self.assertRaises(Exception):
            app_render_studio.api_upload_video_youtube(task_id, privacy="unlisted")

        # Validações estritas do Requisito B
        t_pos = autoviral_brain.carregar_tarefas_db(10).get(task_id)
        self.assertEqual(t_pos["status"], "RENDERIZADO_AGUARDANDO_UPLOAD")
        self.assertTrue(os.path.exists(self.fake_mp4)) # MP4 preservado intacto

        # Valida bloqueio persistido no banco de dados para fergil
        st_fergil = autoviral_brain.obter_status_upload_canal("fergil")
        self.assertTrue(st_fergil["bloqueado"])
        self.assertEqual(st_fergil["ultimo_erro_motivo"], "uploadLimitExceeded")
        self.assertEqual(st_fergil["ultimo_erro_codigo"], 400)

    # =========================================================================
    # TESTE C: OAuth Inválido (HTTP 401 - Não deve confundir com uploadLimitExceeded)
    # =========================================================================
    def test_c_oauth_invalido(self):
        mock_resp = MagicMock()
        mock_resp.status = 401
        content = b'{"error": "invalid_grant", "error_description": "Token has been expired or revoked."}'
        ex = HttpError(mock_resp, content)
        diag = youtube_uploader.classificar_erro_youtube(ex)
        self.assertEqual(diag["categoria"], "OAUTH_INVALID")
        self.assertEqual(diag["motivo_api"], "invalid_grant")
        self.assertEqual(diag["http_code"], 401)
        self.assertNotEqual(diag["categoria"], "UPLOAD_LIMIT_EXCEEDED")

    # =========================================================================
    # TESTE D: Erro de Rede / Timeout (Falha de conexão sem bloqueio de cota)
    # =========================================================================
    def test_d_erro_de_rede(self):
        ex = TimeoutError("The read operation timed out")
        diag = youtube_uploader.classificar_erro_youtube(ex)
        self.assertEqual(diag["categoria"], "NETWORK_ERROR")
        self.assertIsNone(diag["http_code"])
        self.assertNotEqual(diag["categoria"], "UPLOAD_LIMIT_EXCEEDED")

    # =========================================================================
    # TESTE E: Reprocessamento Idempotente de Upload
    # =========================================================================
    @patch("app.services.youtube_uploader.get_authenticated_service")
    def test_e_reprocessar_upload_sem_rerenderizar(self, mock_get_auth):
        mock_yt = MagicMock()
        mock_get_auth.return_value = mock_yt
        mock_req = MagicMock()
        mock_req.next_chunk.return_value = (None, {"id": "VID_REPROCESSADO_777"})
        mock_yt.videos().insert.return_value = mock_req

        task_id = "task_test_e"
        app_render_studio.TASKS[task_id] = {
            "task_id": task_id,
            "titulo": "Video Teste E",
            "file_path": self.fake_mp4,
            "canal_destino": "futebol",
            "status": "RENDERIZADO_AGUARDANDO_UPLOAD",
            "tipo": "doc"
        }
        autoviral_brain.salvar_tarefa_db(task_id, app_render_studio.TASKS[task_id])

        # Executa reprocessamento exclusivo de upload (sem IA nem FFmpeg)
        res = app_render_studio.reprocessar_upload(task_id, privacy="unlisted")
        self.assertEqual(res["video_id"], "VID_REPROCESSADO_777")
        t_final = autoviral_brain.carregar_tarefas_db(10).get(task_id)
        self.assertEqual(t_final["status"], "POSTADO NO YOUTUBE (UNLISTED)")
        self.assertEqual(t_final["youtube_video_id"], "VID_REPROCESSADO_777")

    # =========================================================================
    # TESTES ADICIONAIS P A V (COMPLEMENTOS OBRIGATÓRIOS)
    # =========================================================================

    # Teste P: Isolamento Multicanal (FERGIL bloqueado não impede Futebol)
    def test_p_isolamento_multicanal(self):
        autoviral_brain.registrar_bloqueio_upload_canal("fergil", 400, "uploadLimitExceeded", "Limite FERGIL")
        st_fergil = autoviral_brain.obter_status_upload_canal("fergil")
        st_futebol = autoviral_brain.obter_status_upload_canal("futebol")

        self.assertTrue(st_fergil["bloqueado"])
        self.assertFalse(st_futebol["bloqueado"]) # Futebol permanece 100% livre

    # Teste Q: Validação de MP4 inválido (menor que 1 MB ou inexistente)
    def test_q_validacao_mp4_invalido(self):
        corrupted_mp4 = "canais/temp_test_media/corrupted.mp4"
        with open(corrupted_mp4, "wb") as f:
            f.write(b"0" * 500) # apenas 500 bytes

        task_id = "task_test_q"
        app_render_studio.TASKS[task_id] = {
            "task_id": task_id,
            "titulo": "Video Teste Q",
            "file_path": corrupted_mp4,
            "canal_destino": "futebol",
            "status": "RENDERIZADO_AGUARDANDO_UPLOAD"
        }
        autoviral_brain.salvar_tarefa_db(task_id, app_render_studio.TASKS[task_id])

        with self.assertRaises(Exception) as ctx:
            app_render_studio.reprocessar_upload(task_id)
        self.assertIn("menor que 1 MB", str(ctx.exception.detail))

    # Teste R: Idempotência por Marcador Remoto [task_id:xxx] na descrição
    @patch("app.services.youtube_uploader.get_authenticated_service")
    def test_r_idempotencia_marcador_remoto(self, mock_get_auth):
        task_id = "task_test_r_999"
        app_render_studio.TASKS[task_id] = {
            "task_id": task_id,
            "titulo": "Video Teste R",
            "file_path": self.fake_mp4,
            "canal_destino": "futebol",
            "status": "RENDERIZADO_AGUARDANDO_UPLOAD"
        }
        autoviral_brain.salvar_tarefa_db(task_id, app_render_studio.TASKS[task_id])

        # Mock da playlist de uploads contendo o vídeo já gravado com o marcador [task_id:task_test_r_999]
        mock_yt = MagicMock()
        mock_get_auth.return_value = mock_yt
        mock_yt.channels().list().execute.return_value = {
            "items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UU_FAKE"}}}]
        }
        mock_yt.playlistItems().list().execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "resourceId": {"videoId": "VID_JA_POSTADO_COM_MARCADOR"},
                        "title": "Video Teste R",
                        "description": f"Descricao do video com marcador [task_id:{task_id}] gravado."
                    }
                }
            ]
        }

        res_esc = autopilot_manager.escoar_fila_aguardando_upload(canal="futebol")
        self.assertEqual(res_esc["pulados"], 1)
        self.assertEqual(res_esc["escoados"], 0) # Não enviou novo vídeo

        # Verifica se o banco foi sincronizado com o ID remoto encontrado
        t_upd = autoviral_brain.carregar_tarefas_db(10).get(task_id)
        self.assertEqual(t_upd["status"], "POSTADO NO YOUTUBE (UNLISTED)")
        self.assertEqual(t_upd["youtube_video_id"], "VID_JA_POSTADO_COM_MARCADOR")

    # Teste S: Detecção de Título Coincidente sem Marcador -> DUPLICADO_SUSPEITO
    @patch("app.services.youtube_uploader.get_authenticated_service")
    def test_s_duplicado_suspeito(self, mock_get_auth):
        task_id = "task_test_s_888"
        app_render_studio.TASKS[task_id] = {
            "task_id": task_id,
            "titulo": "Titulo Identico Sem Marcador",
            "file_path": self.fake_mp4,
            "canal_destino": "futebol",
            "status": "RENDERIZADO_AGUARDANDO_UPLOAD"
        }
        autoviral_brain.salvar_tarefa_db(task_id, app_render_studio.TASKS[task_id])

        mock_yt = MagicMock()
        mock_get_auth.return_value = mock_yt
        mock_yt.channels().list().execute.return_value = {
            "items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UU_FAKE"}}}]
        }
        mock_yt.playlistItems().list().execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "resourceId": {"videoId": "VID_OUTRO_TITULO_IGUAL"},
                        "title": "Titulo Identico Sem Marcador",
                        "description": "Descricao sem marcador de task id algum."
                    }
                }
            ]
        }

        res_esc = autopilot_manager.escoar_fila_aguardando_upload(canal="futebol")
        self.assertEqual(res_esc["pulados"], 1)

        t_upd = autoviral_brain.carregar_tarefas_db(10).get(task_id)
        self.assertEqual(t_upd["status"], "DUPLICADO_SUSPEITO")

    # Teste T: Interrupção imediata da fila no primeiro uploadLimitExceeded com renovação de backoff
    @patch("app.services.youtube_uploader.get_authenticated_service")
    def test_t_interrupcao_fila_no_primeiro_limite(self, mock_get_auth):
        # Cria 3 tarefas na fila
        for i in range(1, 4):
            tid = f"task_test_t_{i}"
            app_render_studio.TASKS[tid] = {
                "task_id": tid,
                "titulo": f"Video Fila {i}",
                "file_path": self.fake_mp4,
                "canal_destino": "fergil",
                "status": "RENDERIZADO_AGUARDANDO_UPLOAD",
                "criado_em": f"2026-11-06 10:0{i}:00"
            }
            autoviral_brain.salvar_tarefa_db(tid, app_render_studio.TASKS[tid])

        mock_resp = MagicMock()
        mock_resp.status = 400
        content = b'{"error": {"errors": [{"reason": "uploadLimitExceeded", "message": "limit"}]}}'
        mock_yt = MagicMock()
        mock_get_auth.return_value = mock_yt
        mock_yt.channels().list().execute.return_value = {"items": []}
        mock_req = MagicMock()
        mock_req.next_chunk.side_effect = HttpError(mock_resp, content)
        mock_yt.videos().insert.return_value = mock_req

        res_esc = autopilot_manager.escoar_fila_aguardando_upload(canal="fergil")
        self.assertEqual(res_esc["falhas"], 1)
        self.assertEqual(res_esc["escoados"], 0)

        # Canal deve estar bloqueado com backoff atualizado
        st_bloq = autoviral_brain.obter_status_upload_canal("fergil")
        self.assertTrue(st_bloq["bloqueado"])
        self.assertEqual(st_bloq["total_falhas_consecutivas"], 1)

    # Teste U: Respeito ao Limite de Uploads por Ciclo (ex: 2 envios por vez)
    @patch("app.services.youtube_uploader.get_authenticated_service")
    @patch("time.sleep") # Mock do sleep para testes rápidos
    def test_u_limite_uploads_por_ciclo(self, mock_sleep, mock_get_auth):
        # 3 tarefas pendentes
        for i in range(1, 4):
            tid = f"task_test_u_{i}"
            app_render_studio.TASKS[tid] = {
                "task_id": tid,
                "titulo": f"Video Ciclo {i}",
                "file_path": self.fake_mp4,
                "canal_destino": "futebol",
                "status": "RENDERIZADO_AGUARDANDO_UPLOAD",
                "criado_em": f"2026-11-06 09:0{i}:00"
            }
            autoviral_brain.salvar_tarefa_db(tid, app_render_studio.TASKS[tid])

        mock_yt = MagicMock()
        mock_get_auth.return_value = mock_yt
        mock_yt.channels().list().execute.return_value = {"items": []}
        mock_req = MagicMock()
        mock_req.next_chunk.return_value = (None, {"id": "VID_OK_CICLO"})
        mock_yt.videos().insert.return_value = mock_req

        autopilot_manager.AUTOPILOT_CONFIG["max_uploads_por_ciclo"] = 2
        res_esc = autopilot_manager.escoar_fila_aguardando_upload(canal="futebol")

        self.assertEqual(res_esc["escoados"], 2) # Exatamente 2 escoados

    # Teste V: Proteção Global contra QUOTA_EXCEEDED
    @patch("app.services.youtube_uploader.get_authenticated_service")
    def test_v_protecao_quota_exceeded(self, mock_get_auth):
        mock_resp = MagicMock()
        mock_resp.status = 403
        content = b'{"error": {"errors": [{"reason": "quotaExceeded", "message": "The request cannot be completed because you have exceeded your quota."}]}}'
        mock_yt = MagicMock()
        mock_get_auth.return_value = mock_yt
        mock_yt.channels().list().execute.side_effect = HttpError(mock_resp, content)

        res_esc = autopilot_manager.escoar_fila_aguardando_upload(canal="futebol")
        self.assertEqual(res_esc["escoados"], 0)

    # =========================================================================
    # TESTES DE ROBUSTEZ E SEGURANÇA REFINADOS
    # =========================================================================

    # 1. Distinção exata: quotaExceeded 403 vs uploadLimitExceeded 400
    def test_distincao_quota_vs_upload_limit(self):
        resp_403 = MagicMock(status=403)
        body_403 = b'{"error": {"errors": [{"reason": "quotaExceeded", "message": "quota"}]}}'
        diag_403 = youtube_uploader.classificar_erro_youtube(HttpError(resp_403, body_403))
        self.assertEqual(diag_403["categoria"], "QUOTA_EXCEEDED")
        self.assertEqual(diag_403["http_code"], 403)

        resp_400 = MagicMock(status=400)
        body_400 = b'{"error": {"errors": [{"reason": "uploadLimitExceeded", "message": "limit"}]}}'
        diag_400 = youtube_uploader.classificar_erro_youtube(HttpError(resp_400, body_400))
        self.assertEqual(diag_400["categoria"], "UPLOAD_LIMIT_EXCEEDED")
        self.assertEqual(diag_400["http_code"], 400)

    # 2. RefreshError verificado por isinstance antes do texto -> OAUTH_INVALID
    def test_google_auth_refresh_error(self):
        err = RefreshError("The credentials failed to refresh.")
        diag = youtube_uploader.classificar_erro_youtube(err)
        self.assertEqual(diag["categoria"], "OAUTH_INVALID")

    # 3. HTTP 5xx (500, 502, 503) com retry e backoff classificado como NETWORK_ERROR
    def test_http_5xx_server_errors(self):
        for code in (500, 502, 503, 504):
            resp = MagicMock(status=code)
            body = b'{"error": {"message": "Server Error"}}'
            diag = youtube_uploader.classificar_erro_youtube(HttpError(resp, body))
            self.assertEqual(diag["categoria"], "NETWORK_ERROR")
            self.assertEqual(diag["http_code"], code)

    # 4. Canal bloqueado não chama a API do YouTube
    @patch("app.services.youtube_uploader.get_authenticated_service")
    def test_canal_bloqueado_nao_chama_api(self, mock_get_auth):
        autoviral_brain.registrar_bloqueio_upload_canal("futebol", 400, "uploadLimitExceeded", "Canal bloqueado")
        res = autopilot_manager.escoar_fila_aguardando_upload(canal="futebol")
        self.assertEqual(res["escoados"], 0)
        mock_get_auth.assert_not_called()

    # 5. Persistência do bloqueio entre novas conexões
    def test_persistencia_bloqueio_entre_conexoes(self):
        autoviral_brain.registrar_bloqueio_upload_canal("fergil", 400, "uploadLimitExceeded", "Bloqueio persistido", horas_bloqueio=8.0)
        
        # Abre nova conexão SQLite isolada para verificar
        conn = autoviral_brain.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM canal_upload_status WHERE canal = 'fergil'")
        row = cur.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["bloqueado"], 1)
        self.assertEqual(row["backoff_horas"], 8.0)
        self.assertEqual(row["ultimo_erro_motivo"], "uploadLimitExceeded")

    # 6. Expiração com relógio injetável (now_fn)
    def test_expiracao_com_relogio_injetavel(self):
        # Bloqueia por 4 horas a partir de agora
        autoviral_brain.registrar_bloqueio_upload_canal("moda", 400, "uploadLimitExceeded", "Limite", horas_bloqueio=4.0)
        
        # Relógio 2 horas depois: ainda bloqueado
        relogio_2h = lambda: datetime.now() + timedelta(hours=2)
        st_2h = autoviral_brain.obter_status_upload_canal("moda", now_fn=relogio_2h)
        self.assertTrue(st_2h["bloqueado"])
        self.assertFalse(st_2h["expirado"])

        # Relógio 5 horas depois: expirado!
        relogio_5h = lambda: datetime.now() + timedelta(hours=5)
        st_5h = autoviral_brain.obter_status_upload_canal("moda", now_fn=relogio_5h)
        self.assertFalse(st_5h["bloqueado"])
        self.assertTrue(st_5h["expirado"])

    # 7. Duplo clique com tarefa criada há 5 horas (criado_em preservado no FIFO!)
    def test_duplo_clique_com_tarefa_antiga(self):
        tid = "task_antiga_5h"
        data_5h_atras = (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
        app_render_studio.TASKS[tid] = {
            "task_id": tid,
            "titulo": "Video Antigo de 5 Horas",
            "file_path": self.fake_mp4,
            "canal_destino": "futebol",
            "status": "RENDERIZADO_AGUARDANDO_UPLOAD",
            "criado_em": data_5h_atras
        }
        autoviral_brain.salvar_tarefa_db(tid, app_render_studio.TASKS[tid])

        # Primeiro processo ganha reserva
        sucesso_1 = autoviral_brain.tentar_iniciar_upload_atomico(tid, timeout_minutos=30)
        self.assertTrue(sucesso_1)

        # Verifica que criado_em permanece rigorosamente o mesmo de 5 horas atrás (ordem FIFO intacta!)
        t_db = autoviral_brain.carregar_tarefas_db(10).get(tid)
        self.assertEqual(t_db["criado_em"], data_5h_atras)
        self.assertIsNotNone(t_db["upload_iniciado_em"])

        # Segundo processo simultâneo: BLOQUEADO
        sucesso_2 = autoviral_brain.tentar_iniciar_upload_atomico(tid, timeout_minutos=30)
        self.assertFalse(sucesso_2)

    # 8. Timeout de 30 minutos sobre upload_iniciado_em
    def test_timeout_upload_iniciado_em(self):
        tid = "task_timeout_35m"
        data_criacao = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        app_render_studio.TASKS[tid] = {
            "task_id": tid,
            "titulo": "Video Abandonado Há 35 Minutos",
            "file_path": self.fake_mp4,
            "canal_destino": "futebol",
            "status": "RENDERIZADO_AGUARDANDO_UPLOAD",
            "criado_em": data_criacao
        }
        autoviral_brain.salvar_tarefa_db(tid, app_render_studio.TASKS[tid])

        # Simula processo que iniciou upload há 35 minutos e caiu
        autoviral_brain.tentar_iniciar_upload_atomico(tid, timeout_minutos=30)
        inicio_abandonado = (datetime.now() - timedelta(minutes=35)).strftime("%Y-%m-%d %H:%M:%S")
        conn = autoviral_brain.get_conn()
        conn.execute("UPDATE videos_gerados SET upload_iniciado_em = ? WHERE task_id = ?", (inicio_abandonado, tid))
        conn.commit()
        conn.close()

        # Novo processo tenta pegar: como passaram 35 min (> 30 min), recupera com sucesso!
        recuperado = autoviral_brain.tentar_iniciar_upload_atomico(tid, timeout_minutos=30)
        self.assertTrue(recuperado)

        # criado_em continua o mesmo original!
        t_pos = autoviral_brain.carregar_tarefas_db(10).get(tid)
        self.assertEqual(t_pos["criado_em"], data_criacao)

    # 9. Rejeição de task_id com Path Traversal (../)
    def test_rejeicao_task_id_path_traversal(self):
        with self.assertRaises(Exception) as ctx:
            app_render_studio.reprocessar_upload("../etc/passwd")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("path traversal", str(ctx.exception.detail))

    # 10. Guarda Estrita Anti-Duplicação (mesma fonte, URL ou título em qualquer estado, incluindo ARQUIVADO)
    def test_guarda_anti_duplicacao_estrita(self):
        tid = "task_dup_guard_test"
        app_render_studio.TASKS[tid] = {
            "task_id": tid,
            "titulo": "Vestido Exclusivo de Seda Pura Elegante",
            "canal_destino": "moda",
            "product_id": "100500999999",
            "link_afiliado": "https://s.click.aliexpress.com/e/_DkFake?spm=123",
            "status": "ARQUIVADO"
        }
        autoviral_brain.salvar_tarefa_db(tid, app_render_studio.TASKS[tid])

        # A) Rejeita por Product ID idêntico (mesmo em ARQUIVADO)
        res_pid = autoviral_brain.verificar_video_duplicado("Outro Nome Qualquer", canal="moda", product_id="100500999999")
        self.assertIsNotNone(res_pid)
        self.assertIn("Produto duplicado", res_pid)

        # B) Rejeita por URL de produto/notícia idêntica
        res_url = autoviral_brain.verificar_video_duplicado("Outro Nome", canal="moda", fonte_url="https://s.click.aliexpress.com/e/_DkFake")
        self.assertIsNotNone(res_url)
        self.assertIn("Fonte URL duplicada", res_url)

        # C) Rejeita por Título Normalizado idêntico
        res_tit = autoviral_brain.verificar_video_duplicado("VESTIDO EXCLUSIVO DE SEDA PURA ELEGANTE!!!", canal="moda")
        self.assertIsNotNone(res_tit)
        self.assertIn("Título idêntico", res_tit)

        # D) Permite tema inédito
        res_ok = autoviral_brain.verificar_video_duplicado("Bolsa Feminina Couro Legítimo Vintage", canal="moda", product_id="100500888888")
        self.assertIsNone(res_ok)

if __name__ == "__main__":
    unittest.main()
