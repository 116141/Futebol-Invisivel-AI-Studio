import os
import sys
import re
import uuid
import shutil
import subprocess
import imageio_ffmpeg
from loguru import logger
from fastapi import FastAPI, BackgroundTasks, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import yt_dlp
from app.services import voice, llm

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(FFMPEG)
if ffmpeg_dir not in os.environ["PATH"]:
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]

SHORTS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "shorts")
DOCS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios")
os.makedirs(SHORTS_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

app = FastAPI(title="Futebol Invisível AI Studio")

TASKS = {}

def processar_video(task_id: str, titulo: str, tipo: str):
    try:
        is_doc = (tipo == "doc")
        aspect_ratio = "16:9" if is_doc else "9:16"
        res_scale = "1920:1080" if is_doc else "1080:1920"
        target_dir = DOCS_DIR if is_doc else SHORTS_DIR
        
        TASKS[task_id]["status"] = "Gerando Roteiro Investigativo Factual..."
        
        tempo_desc = "um super documentário investigativo de 2 a 3 minutos com capítulos" if is_doc else "um SHORT vertical viral de 45 a 55 segundos"
        prompt_script = f"""
        Você é o roteirista investigativo do canal @FutebolInvisivelOficial no YouTube.
        Crie o roteiro em português (pt-BR) para {tempo_desc} sobre o tema: '{titulo}'.
        DIRETRIZES:
        - Comece IMEDIATAMENTE com uma afirmação ou revelação de impacto nos primeiros segundos.
        - Fale de bastidores, valores monetários, polêmicas, documentos oficiais e consequências.
        - Termine com uma pergunta provocativa convidando a debater nos comentários e se inscrever no canal Futebol Invisível.
        - Apenas o texto puro da narração, sem marcadores de cena como [Narrador] ou [Cena].
        """
        
        try:
            roteiro_gerado = llm.generate_script(prompt_script)
            roteiro_limpo = re.sub(r'\[.*?\]', '', roteiro_gerado).strip()
            roteiro_limpo = roteiro_limpo.replace('**', '').replace('##', '')
            if len(roteiro_limpo) > 60 and "Error:" not in roteiro_limpo and "503" not in roteiro_limpo:
                roteiro = roteiro_limpo
            else:
                raise ValueError("Erro de resposta da IA")
        except Exception:
            if is_doc:
                roteiro = (
                    f"A investigação completa que abalou os bastidores do futebol mundial sobre {titulo}! "
                    "Capítulo um: Os bastidores e o nascimento da crise. "
                    "Longe dos gramados e dos holofotes da televisão, acordos secretos e decisões financeiras "
                    "orquestradas por dirigentes e empresários mudaram para sempre o rumo desta história. "
                    "Capítulo dois: O peso dos valores e a repercussão nos tribunais. "
                    "Documentos fiscais e relatórios confidenciais vieram à tona revelando cifras astronômicas "
                    "e pressões que a opinião pública jamais imaginou. "
                    "E você? Acredita que esse foi o maior escândalo recente ou apenas a ponta do iceberg? "
                    "Deixe sua resposta nos comentários e se inscreva no canal Futebol Invisível!"
                )
            else:
                roteiro = (
                    f"A verdade que ninguém tem coragem de falar sobre {titulo}! "
                    "Nos bastidores do futebol europeu, os acordos secretos e decisões fora das quatro linhas "
                    "mudaram completamente o rumo desta história que revoltou a torcida mundial. "
                    "Valores astronômicos e pressões internas foram revelados pelas investigações da imprensa internacional. "
                    f"Na sua opinião: você acha isso justo ou armação dos bastidores? "
                    "Comente agora a sua resposta e se inscreva no Futebol Invisível!"
                )
            
        TASKS[task_id]["roteiro"] = roteiro
        TASKS[task_id]["status"] = "Gerando Narração e Sincronia de Legendas..."
        
        temp_dir = f"temp_web_build_{task_id[:8]}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Áudio
        audio_path = os.path.join(temp_dir, "audio.mp3")
        sm = voice.azure_tts_v1(roteiro, "pt-BR-AntonioNeural", 1.0, audio_path)
        srt_content = sm.get_srt() if sm else ""
        
        # Download de Vídeos
        TASKS[task_id]["status"] = "Buscando e Baixando Vídeos Reais no YouTube..."
        ydl_opts = {
            'format': 'best',
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'outtmpl': os.path.join(temp_dir, 'source_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'max_downloads': 1
        }
        
        queries = [
            f"ytsearch1:{titulo} soccer football highlights",
            f"ytsearch1:{titulo} match skills goals"
        ]
        for q in queries:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(q, download=True)
            except Exception as e:
                logger.info(f"Busca: {e}")
                
        downloaded = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.startswith("source_") and f.endswith(".mp4")]
        if not downloaded:
            raise Exception("Não foi possível encontrar vídeos no YouTube para este tema.")
            
        TASKS[task_id]["status"] = f"Cortando Clipes em {aspect_ratio} e Editando..."
        
        clip_files = []
        clip_idx = 1
        offsets = [10, 20, 30, 45, 60, 75, 90, 110, 130] if is_doc else [10, 20, 30, 45, 60]
        max_clips = 12 if is_doc else 6
        
        for v in downloaded:
            for off in offsets:
                c_out = os.path.join(temp_dir, f"clip_{clip_idx:02d}.mp4")
                if is_doc:
                    # Formato 16:9 widescreen para documentários
                    vf_filter = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30"
                else:
                    # Formato 9:16 vertical para shorts
                    vf_filter = "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30"
                
                cmd = [
                    FFMPEG, "-y", "-ss", str(off), "-i", v, "-t", "4.0", "-an",
                    "-vf", vf_filter,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
                    c_out
                ]
                subprocess.run(cmd, capture_output=True)
                if os.path.exists(c_out) and os.path.getsize(c_out) > 50000:
                    clip_files.append(c_out)
                    clip_idx += 1
                if len(clip_files) >= max_clips:
                    break
            if len(clip_files) >= max_clips:
                break
                
        if len(clip_files) < 2:
            raise Exception("Não foi possível gerar clipes suficientes.")
            
        concat_txt = os.path.join(temp_dir, "concat.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for c in clip_files:
                f.write(f"file '{os.path.abspath(c).replace('\\', '/')}'\n")
                
        concat_video = os.path.join(temp_dir, "combined.mp4")
        subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", concat_video], capture_output=True)
        
        # Legendas
        blocks = [b.strip() for b in srt_content.strip().split("\n\n") if b.strip()]
        word_entries = []
        for b in blocks:
            lines = b.splitlines()
            if len(lines) >= 3:
                timing = lines[1]
                text = " ".join(lines[2:]).strip()
                m = re.match(r"(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)", timing)
                if m:
                    def to_ass_time(srt_t):
                        h, mn, s = srt_t.split(":")
                        sec, ms = s.split(",")
                        return f"{int(h)}:{mn}:{sec}.{ms[:2]}"
                    word_entries.append({
                        "start": to_ass_time(m.group(1)),
                        "end": to_ass_time(m.group(2)),
                        "text": text
                    })

        res_x = 1920 if is_doc else 1080
        res_y = 1080 if is_doc else 1920
        font_size = 54 if is_doc else 80
        margin_v = 70 if is_doc else 400

        header = (
            f"[Script Info]\nScriptType: v4.00+\nPlayResX: {res_x}\nPlayResY: {res_y}\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: Default,Impact,{font_size},&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,40,40,{margin_v},1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )
        events = []
        chunk_size = 6 if is_doc else 4
        for i in range(0, len(word_entries), chunk_size):
            chunk = word_entries[i:i+chunk_size]
            t_start = chunk[0]["start"]
            t_end = chunk[-1]["end"]
            phrase = " ".join([c["text"].upper() for c in chunk])
            events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{phrase}")

        ass_file = "temp_render_studio.ass"
        with open(ass_file, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(events))
            
        # Render Final
        prefix = "DOCUMENTARIO" if is_doc else "SHORT"
        TASKS[task_id]["status"] = f"Renderizando {prefix} em Full HD ({aspect_ratio})..."
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', titulo)[:30]
        final_filename = f"{prefix}_{clean_name}_{task_id[:6]}.mp4"
        final_path = os.path.join(target_dir, final_filename)
        
        cmd_render = [
            FFMPEG, "-y",
            "-stream_loop", "-1", "-i", concat_video,
            "-i", audio_path,
            "-vf", f"ass={ass_file}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            final_path
        ]
        res = subprocess.run(cmd_render, capture_output=True, text=True)
        if os.path.exists(ass_file):
            os.remove(ass_file)

        if os.path.exists(final_path) and os.path.getsize(final_path) > 1000000:
            TASKS[task_id]["status"] = "CONCLUÍDO"
            TASKS[task_id]["file_path"] = final_path
            TASKS[task_id]["file_name"] = final_filename
            logger.success(f"{prefix} CONCLUÍDO: {final_path}")
        else:
            TASKS[task_id]["status"] = f"Erro na renderização final: {res.stderr[:200]}"
            
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        logger.error(f"Erro na tarefa {task_id}: {e}")
        TASKS[task_id]["status"] = f"Erro: {str(e)}"

# === INTERFACE WEB DUPLA (SHORTS + DOCUMENTÁRIOS) ===
HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Futebol Invisível AI Studio</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0b1120; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .card-custom { background: #1e293b; border: 1px solid #334155; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .btn-gold { background: linear-gradient(135deg, #eab308, #ca8a04); color: #000; font-weight: 700; border: none; }
        .btn-gold:hover { background: linear-gradient(135deg, #facc15, #eab308); color: #000; }
        .btn-doc { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: #fff; font-weight: 700; border: none; }
        .btn-doc:hover { background: linear-gradient(135deg, #60a5fa, #2563eb); color: #fff; }
        .glow { text-shadow: 0 0 15px rgba(234, 179, 8, 0.4); }
        .form-check-input:checked { background-color: #eab308; border-color: #eab308; }
    </style>
</head>
<body class="py-5">
    <div class="container" style="max-width: 820px;">
        <div class="text-center mb-5">
            <h1 class="fw-bold glow text-warning">⚽ FUTEBOL INVISÍVEL AI STUDIO</h1>
            <p class="text-secondary fs-5">Fábrica Automática de Documentários (16:9) e Shorts Virais (9:16)</p>
        </div>

        <div class="card card-custom p-4 mb-4">
            <h4 class="mb-3 text-light">🚀 Criar Vídeo Inteligente em 1 Clique</h4>
            <form id="createForm">
                <div class="mb-3">
                    <label class="form-label text-light fw-bold">1. Digite o TEMA ou TÍTULO da investigação:</label>
                    <input type="text" id="tituloInput" class="form-control form-control-lg bg-dark text-light border-secondary" 
                           placeholder="Ex: As 115 Violações do Manchester City / A revolta de CR7 / Gols absurdos de Raphinha" required>
                </div>

                <div class="mb-4">
                    <label class="form-label text-light fw-bold">2. Escolha o Formato:</label>
                    <div class="row g-3">
                        <div class="col-md-6">
                            <div class="p-3 bg-dark rounded border border-secondary d-flex align-items-center">
                                <input class="form-check-input me-3" type="radio" name="tipoVideo" id="tipoShort" value="short" checked>
                                <label class="form-check-label text-light" for="tipoShort">
                                    <strong>📱 YOUTUBE SHORTS (9:16)</strong><br>
                                    <small class="text-secondary">Viral vertical, rápido (45-55s), cortes dinâmicos.</small>
                                </label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="p-3 bg-dark rounded border border-secondary d-flex align-items-center">
                                <input class="form-check-input me-3" type="radio" name="tipoVideo" id="tipoDoc" value="doc">
                                <label class="form-check-label text-light" for="tipoDoc">
                                    <strong>🎬 DOCUMENTÁRIO LONGO (16:9)</strong><br>
                                    <small class="text-secondary">Horizontal TV, narrativa profunda com capítulos.</small>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <button type="submit" class="btn btn-gold btn-lg w-100" id="btnSubmit">⚡ GERAR VÍDEO COMPLETO AGORA</button>
            </form>
        </div>

        <div class="card card-custom p-4 mb-4">
            <h5 class="text-warning mb-3">📋 Vídeos Sendo Gerados e Prontos (Ao Vivo):</h5>
            <div id="listaTarefas" class="list-group">
                <div class="text-secondary small p-3 text-center">Nenhum vídeo em andamento no momento.</div>
            </div>
        </div>

        <div id="progressCard" class="card card-custom p-4 d-none mb-4">
            <h5 class="text-warning">Status do Vídeo Atual:</h5>
            <div class="d-flex align-items-center my-3">
                <div class="spinner-border text-warning me-3" role="status" id="spinner"></div>
                <span id="statusText" class="fs-5 text-light fw-bold">Iniciando...</span>
            </div>
            <div id="roteiroBox" class="p-3 bg-dark rounded border border-secondary text-secondary small d-none mb-3"></div>
            <div id="downloadBox" class="d-none">
                <a id="btnDownload" href="#" class="btn btn-success btn-lg w-100 fw-bold">📥 BAIXAR VÍDEO PRONTO (FULL HD)</a>
            </div>
        </div>
    </div>

    <script>
        const form = document.getElementById('createForm');
        const progressCard = document.getElementById('progressCard');
        const statusText = document.getElementById('statusText');
        const spinner = document.getElementById('spinner');
        const roteiroBox = document.getElementById('roteiroBox');
        const downloadBox = document.getElementById('downloadBox');
        const btnDownload = document.getElementById('btnDownload');
        const btnSubmit = document.getElementById('btnSubmit');
        const listaTarefas = document.getElementById('listaTarefas');

        async function carregarTarefas() {
            try {
                const res = await fetch('/api/tarefas');
                const tarefas = await res.json();
                const keys = Object.keys(tarefas);
                if (keys.length === 0) {
                    listaTarefas.innerHTML = '<div class="text-secondary small p-3 text-center">Nenhum vídeo gerado ainda.</div>';
                    return;
                }
                let html = '';
                keys.reverse().forEach(id => {
                    const t = tarefas[id];
                    const isPronto = t.status === "CONCLUÍDO";
                    const isErro = t.status.startsWith("Erro");
                    const badgeClass = isPronto ? "bg-success" : (isErro ? "bg-danger" : "bg-warning text-dark");
                    const icon = t.tipo === "doc" ? "🎬 DOC" : "📱 SHORT";
                    
                    html += `
                        <div class="list-group-item bg-dark border-secondary text-light p-3 mb-2 rounded d-flex justify-content-between align-items-center flex-wrap gap-2">
                            <div>
                                <span class="badge bg-secondary me-2">${icon}</span>
                                <strong class="fs-6">${t.titulo}</strong><br>
                                <span class="badge ${badgeClass} mt-1">${t.status}</span>
                            </div>
                            <div>
                                ${isPronto ? `<a href="/api/download/${id}" class="btn btn-success btn-sm fw-bold px-3">📥 BAIXAR MP4</a>` : ''}
                            </div>
                        </div>
                    `;
                });
                listaTarefas.innerHTML = html;
            } catch (e) {
                console.error(e);
            }
        }

        setInterval(carregarTarefas, 3000);
        carregarTarefas();

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const titulo = document.getElementById('tituloInput').value;
            const tipo = document.querySelector('input[name="tipoVideo"]:checked').value;

            btnSubmit.disabled = true;
            progressCard.classList.remove('d-none');
            downloadBox.classList.add('d-none');
            roteiroBox.classList.add('d-none');
            spinner.classList.remove('d-none');
            statusText.innerText = "Criando tarefa no servidor...";

            const res = await fetch('/api/criar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ titulo, tipo })
            });
            const data = await res.json();
            const taskId = data.task_id;
            carregarTarefas();

            const interval = setInterval(async () => {
                const check = await fetch(`/api/status/${taskId}`);
                const task = await check.json();
                statusText.innerText = task.status;

                if (task.roteiro) {
                    roteiroBox.innerText = "Roteiro: " + task.roteiro;
                    roteiroBox.classList.remove('d-none');
                }

                if (task.status === "CONCLUÍDO") {
                    clearInterval(interval);
                    spinner.classList.add('d-none');
                    statusText.innerText = "✅ VÍDEO 100% PRONTO EM FULL HD!";
                    btnDownload.href = `/api/download/${taskId}`;
                    downloadBox.classList.remove('d-none');
                    btnSubmit.disabled = false;
                    carregarTarefas();
                } else if (task.status.startsWith("Erro")) {
                    clearInterval(interval);
                    spinner.classList.add('d-none');
                    btnSubmit.disabled = false;
                    carregarTarefas();
                }
            }, 3000);
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE

@app.get("/api/tarefas")
def listar_tarefas():
    return TASKS

@app.post("/api/criar")
def criar_video(background_tasks: BackgroundTasks, titulo: str = Form(...), tipo: str = Form("short")):
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        "titulo": titulo,
        "tipo": tipo,
        "status": "Iniciando processo...",
        "roteiro": "",
        "file_path": None,
        "file_name": None
    }
    background_tasks.add_task(processar_video, task_id, titulo, tipo)
    return {"task_id": task_id}

@app.get("/api/status/{task_id}")
def status_video(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return TASKS[task_id]

@app.get("/api/download/{task_id}")
def download_video(task_id: str):
    task = TASKS.get(task_id)
    if not task or not task.get("file_path") or not os.path.exists(task["file_path"]):
        raise HTTPException(status_code=404, detail="Arquivo não pronto")
    return FileResponse(task["file_path"], media_type="video/mp4", filename=task["file_name"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8505))
    host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    logger.info(f"Iniciando Futebol Invisível Studio em http://{host}:{port} ...")
    uvicorn.run(app, host=host, port=port)
