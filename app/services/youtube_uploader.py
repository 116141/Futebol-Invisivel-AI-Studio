import os
import json
import re
from loguru import logger
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    InstalledAppFlow = None
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

def classificar_erro_youtube(ex: Exception) -> dict:
    """
    Classifica categoricamente qualquer exceção da API do YouTube sem ambiguidades:
    - UPLOAD_LIMIT_EXCEEDED: Limite diário de vídeos do canal atingido (HTTP 400 reason: uploadLimitExceeded).
    - QUOTA_EXCEEDED: Cota de 10.000 pontos do projeto GCP excedida (HTTP 403 reason: quotaExceeded).
    - OAUTH_INVALID: Token revogado ou expirado (HTTP 401/403 invalid_grant).
    - METADATA_INVALID: Tags ou metadados inválidos (HTTP 400 invalidTags/invalidTitle).
    - NETWORK_ERROR: Timeout, falha de DNS ou socket.
    - UNKNOWN_ERROR: Demais exceções.
    """
    err_str = str(ex).lower()
    http_code = getattr(ex, "status_code", None)
    if hasattr(ex, "resp") and hasattr(ex.resp, "status"):
        try:
            http_code = int(ex.resp.status)
        except Exception:
            pass

    details_str = ""
    if hasattr(ex, "content"):
        try:
            if isinstance(ex.content, bytes):
                details_str = ex.content.decode("utf-8", errors="ignore")
            else:
                details_str = str(ex.content)
        except Exception:
            pass
    if not details_str and hasattr(ex, "error_details"):
        details_str = str(ex.error_details)
    
    full_text = f"{err_str} {details_str.lower()}"

    # 1. UPLOAD_LIMIT_EXCEEDED
    if "uploadlimitexceeded" in full_text or "the user has exceeded the number of videos they may upload" in full_text or "limite de upload do canal" in full_text:
        return {
            "categoria": "UPLOAD_LIMIT_EXCEEDED",
            "motivo_api": "uploadLimitExceeded",
            "http_code": http_code or 400,
            "mensagem": "Limite diário de novos uploads do canal atingido pelo YouTube.",
            "detalhes_brutos": str(ex)
        }

    # 2. QUOTA_EXCEEDED
    if "quotaexceeded" in full_text or "quota exceeded" in full_text or "cota diária da api do google cloud excedida" in full_text:
        return {
            "categoria": "QUOTA_EXCEEDED",
            "motivo_api": "quotaExceeded",
            "http_code": http_code or 403,
            "mensagem": "Cota global diária da API do Google Cloud excedida (quotaExceeded).",
            "detalhes_brutos": str(ex)
        }

    # 3. OAUTH_INVALID (Verificação por isinstance antes do texto)
    try:
        from google.auth.exceptions import RefreshError
        is_refresh_error = isinstance(ex, RefreshError)
    except Exception:
        is_refresh_error = False

    if is_refresh_error or "refresherror" in full_text or "invalid_grant" in full_text or "token has been expired or revoked" in full_text or ("unauthorized" in full_text and http_code == 401):
        return {
            "categoria": "OAUTH_INVALID",
            "motivo_api": "invalid_grant",
            "http_code": http_code or 401,
            "mensagem": "Autenticação OAuth inválida ou token revogado.",
            "detalhes_brutos": str(ex)
        }

    # 4. METADATA_INVALID
    if "invalidtags" in full_text or "invalid video keywords" in full_text:
        return {
            "categoria": "METADATA_INVALID",
            "motivo_api": "invalidTags",
            "http_code": http_code or 400,
            "mensagem": "Palavras-chave ou tags inválidas na requisição.",
            "detalhes_brutos": str(ex)
        }

    # 5. NETWORK_ERROR / 5xx (inclui 500, 502, 503, 504 - retry com backoff)
    network_keywords = ["timed out", "timeout", "connection refused", "gaierror", "servernotfound", "remotedisconnected", "unable to find the server", "backenderror", "service unavailable"]
    if http_code and 500 <= http_code < 600:
        return {
            "categoria": "NETWORK_ERROR",
            "motivo_api": f"http_{http_code}_server_error",
            "http_code": http_code,
            "mensagem": f"Erro temporário de servidor do YouTube (HTTP {http_code}). Retentativa automática com backoff.",
            "detalhes_brutos": str(ex)
        }
    if any(k in full_text for k in network_keywords):
        return {
            "categoria": "NETWORK_ERROR",
            "motivo_api": "network_timeout",
            "http_code": None,
            "mensagem": "Falha de rede ou timeout na conexão com a API do YouTube.",
            "detalhes_brutos": str(ex)
        }

    # 6. UNKNOWN_ERROR
    return {
        "categoria": "UNKNOWN_ERROR",
        "motivo_api": "unknown",
        "http_code": http_code,
        "mensagem": str(ex),
        "detalhes_brutos": str(ex)
    }

def get_authenticated_service(canal_nome: str = "futebol"):
    """Obtém ou renova as credenciais de OAuth2 do YouTube dedicadas por canal."""
    os.makedirs("storage", exist_ok=True)
    if canal_nome == "moda":
        client_file = "client_secrets_moda.json"
        token_file = "storage/youtube_oauth_token_moda.json"
    elif canal_nome in ("fergil", "negocios"):
        client_file = "client_secrets_fergil.json"
        token_file = "storage/youtube_oauth_token_fergil.json"
    else:
        client_file = "client_secrets_futebol.json"
        token_file = "storage/youtube_oauth_token_futebol.json"
        
    if not os.path.exists(client_file):
        client_file = "client_secrets.json"
        token_file = "storage/youtube_oauth_token.json"
        
    creds = None
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        except Exception:
            creds = None
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
                
        if not creds:
            if not os.path.exists(client_file):
                raise FileNotFoundError(f"Arquivo de credenciais {client_file} não encontrado no sistema.")
            flow = InstalledAppFlow.from_client_secrets_file(client_file, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_file, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
            
    return build("youtube", "v3", credentials=creds)


def upload_video_youtube(
    file_path: str,
    title: str,
    description: str,
    tags: list = None,
    category_id: str = "17",
    privacy_status: str = "unlisted",
    thumbnail_path: str = None,
    canal_nome: str = None,
    task_id: str = None
) -> dict:
    """Faz o upload oficial de vídeo completo e thumbnail no YouTube com rastreamento task_id."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {file_path}")
        
    if not canal_nome:
        if category_id == "26":
            canal_nome = "moda"
        elif category_id == "27":
            canal_nome = "fergil"
        else:
            canal_nome = "futebol"
            
    youtube = get_authenticated_service(canal_nome=canal_nome)
    
    # Sanitização universal de tags na entrada da API do YouTube
    # A API do YouTube impõe limites rígidos para bytes UTF-8 em tags (<= 350-400 bytes totais)
    # e proíbe caracteres de controle, aspas, pontuações especiais, símbolos e tags muito longas.
    tags_limpas = []
    char_acc = 0
    if tags:
        import re
        for tg in tags:
            t_clean = str(tg)
            # Remove caracteres proibidos e pontuações que a API do YouTube rejeita em keywords (como : ? ! # < > etc)
            t_clean = re.sub(r'[<>#,\n\r\t:?!"`~\\/|' + "']", "", t_clean)
            t_clean = re.sub(r'\s+', ' ', t_clean).strip()
            # Remove ponto final que pode vir de final de frases
            t_clean = t_clean.rstrip(".")
            t_clean = t_clean[:40].strip()
            if not t_clean or len(t_clean) < 2:
                continue
            custo = len(t_clean.encode('utf-8')) + (1 if tags_limpas else 0)
            if char_acc + custo <= 320 and len(tags_limpas) < 25:
                tags_limpas.append(t_clean)
                char_acc += custo
            elif char_acc >= 300 or len(tags_limpas) >= 25:
                break
                
    if not tags_limpas:
        tags_limpas = ["shorts", "viral"]

    # Injeta marcador task_id na descrição se fornecido e ainda não presente
    desc_final = description or ""
    if task_id and f"[task_id:{task_id}]" not in desc_final:
        desc_final = f"{desc_final}\n\n[task_id:{task_id}]"

    body = {
        "snippet": {
            "title": title[:100],
            "description": desc_final[:5000],
            "tags": tags_limpas,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    response = None
    try:
        while response is None:
            status, response = request.next_chunk()
    except Exception as e_upload:
        err_msg = str(e_upload).lower()
        if "invalidtags" in err_msg or "invalid video keywords" in err_msg:
            logger.warning(f"YouTube rejeitou tags {tags_limpas}. Fazendo retry imediato com tags mínimas de segurança...")
            body["snippet"]["tags"] = ["shorts", "futebol" if canal_nome == "futebol" else ("negocios" if canal_nome == "fergil" else "moda")]
            media_retry = MediaFileUpload(file_path, chunksize=-1, resumable=True)
            request_retry = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media_retry
            )
            response = None
            while response is None:
                status, response = request_retry.next_chunk()
        else:
            raise e_upload
        
    video_id = response.get("id")
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # BLOQUEIO ABSOLUTO DE CAPAS AUTOMÁTICAS (DIRETRIZ DO PROPRIETÁRIO):
    # O sistema NUNCA deve gerar nem enviar miniaturas/capas pelo YouTube.
    # O próprio proprietário fará o envio manual de todas as capas personalizadas.
    thumb_uploaded = False
            
    return {
        "status": "success",
        "video_id": video_id,
        "video_url": video_url,
        "thumbnail_uploaded": thumb_uploaded
    }
