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
from fastapi.staticfiles import StaticFiles
import yt_dlp
from app.services import voice, llm

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(FFMPEG)
if ffmpeg_dir not in os.environ["PATH"]:
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]

OUTPUT_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "shorts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="Futebol Invisível AI Studio")

# Estado de tarefas na memória
TASKS = {}

def processar_video_por_titulo(task_id: str, titulo: str):
    try:
        TASKS[task_id]["status"] = "Gerando Roteiro Investigativo..."
        
        # 1. Gerar Roteiro Investigativo Factual
        prompt_script = f"""
        Você é o roteirista investigativo do canal @FutebolInvisivelOficial no YouTube.
        Crie um roteiro em português (pt-BR) de SHORT (40 a 50 segundos de leitura) sobre o tema: '{titulo}'.
        REGRAS RIGOROSAS:
        - Comece IMEDIATAMENTE com uma afirmação ou pergunta de alto impacto/choque nos primeiros 2 segundos.
        - Fale de fatos, bastidores, polêmicas e valores reais.
        - Termine com uma pergunta provocativa para gerar centenas de comentários e peça inscrição no canal Futebol Invisível.
        - Não coloque títulos nem marcações de cena (ex: [Cena], [Narrador]). Apenas o texto puro da narração para o locutor falar.
        """
        
        try:
            roteiro = llm.generate_script(prompt_script)
            # Limpa qualquer formatação markdown
            roteiro = re.sub(r'\[.*?\]', '', roteiro).strip()
            roteiro = roteiro.replace('**', '').replace('##', '')
            if len(roteiro) < 50:
                raise ValueError("Roteiro muito curto")
        except Exception:
            # Fallback inteligente e investigativo se a API de IA não responder
            roteiro = (
                f"A verdade que ninguém tem coragem de falar sobre {titulo}! "
                "Nos bastidores do futebol europeu, os acordos secretos e decisões fora das quatro linhas "
                "mudaram completamente o rumo desta história que revoltou a torcida mundial. "
                "Valores astronômicos e pressões internas foram revelados pelas investigações da imprensa internacional. "
                f"Na sua opinião: você acha isso justo ou armação dos bastidores? "
                "Comente agora a sua resposta e se inscreva no Futebol Invisível!"
            )
            
        TASKS[task_id]["roteiro"] = roteiro
        TASKS[task_id]["status"] = "Gerando Narração e Legendas..."
        
        temp_dir = f"temp_web_build_{task_id[:8]}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 2. Áudio e Legendas via Edge TTS
        audio_path = os.path.join(temp_dir, "audio.mp3")
        sm = voice.azure_tts_v1(roteiro, "pt-BR-AntonioNeural", 1.0, audio_path)
        srt_content = sm.get_srt() if sm else ""
        
        # 3. Baixar Vídeos Reais no YouTube
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
            f"ytsearch1:{titulo} skills goals"
        ]
        
        for q in queries:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(q, download=True)
            except Exception as e:
                logger.info(f"Busca: {e}")
                
        downloaded = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.startswith("source_") and f.endswith(".mp4")]
        
        TASKS[task_id]["status"] = "Recortando Clipes em 9:16 e Editando..."
        
        # 4. Fatiar clipes de 3-4 segundos mutando áudio
        clip_files = []
        clip_idx = 1
        offsets = [10, 20, 30, 45, 60]
        
        for v in downloaded:
            for off in offsets[:3]:
                c_out = os.path.join(temp_dir, f"clip_{clip_idx:02d}.mp4")
                cmd = [
                    FFMPEG, "-y", "-ss", str(off), "-i", v, "-t", "4.0", "-an",
                    "-vf", "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
                    c_out
                ]
                subprocess.run(cmd, capture_output=True)
                if os.path.exists(c_out) and os.path.getsize(c_out) > 50000:
                    clip_files.append(c_out)
                    clip_idx += 1
                if len(clip_files) >= 6:
                    break
            if len(clip_files) >= 6:
                break
                
        # Se não tiver clipes suficientes, fallback para foto do canal
        if len(clip_files) < 3:
            raise Exception("Não foi possível coletar clipes suficientes do YouTube para o tema.")
            
        concat_txt = os.path.join(temp_dir, "concat.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for c in clip_files:
                f.write(f"file '{os.path.abspath(c).replace('\\', '/')}'\n")
                
        concat_video = os.path.join(temp_dir, "combined.mp4")
        subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", concat_video], capture_output=True)
        
        # 5. Criar Legendas ASS Dinâmicas Amarelas
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

        header = (
            "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Impact,80,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,40,40,400,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )
        events = []
        chunk_size = 4
        for i in range(0, len(word_entries), chunk_size):
            chunk = word_entries[i:i+chunk_size]
            t_start = chunk[0]["start"]
            t_end = chunk[-1]["end"]
            phrase = " ".join([c["text"].upper() for c in chunk])
            events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{phrase}")

        ass_file = os.path.join(temp_dir, "subs.ass")
        with open(ass_file, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(events))
            
        # 6. Renderizar Short Final
        TASKS[task_id]["status"] = "Renderizando Short Final em Full HD..."
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', titulo)[:30]
        final_filename = f"SHORT_{clean_name}_{task_id[:6]}.mp4"
        final_path = os.path.join(OUTPUT_DIR, final_filename)
        
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
        
        if os.path.exists(final_path) and os.path.getsize(final_path) > 1000000:
            TASKS[task_id]["status"] = "CONCLUÍDO"
            TASKS[task_id]["file_path"] = final_path
            TASKS[task_id]["file_name"] = final_filename
            logger.success(f"VÍDEO CONCLUÍDO COM SUCESSO: {final_path}")
        else:
            TASKS[task_id]["status"] = f"Erro na renderização final: {res.stderr[:200]}"
            
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        logger.error(f"Erro na tarefa {task_id}: {e}")
        TASKS[task_id]["status"] = f"Erro: {str(e)}"

# === INTERFACE WEB ELEGANTE ===
HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Futebol Invisível AI Studio</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .card-custom { background: #1e293b; border: 1px solid #334155; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .btn-gold { background: linear-gradient(135deg, #eab308, #ca8a04); color: #000; font-weight: 700; border: none; }
        .btn-gold:hover { background: linear-gradient(135deg, #facc15, #eab308); color: #000; }
        .badge-status { font-size: 0.9rem; padding: 8px 12px; border-radius: 8px; }
        .glow { text-shadow: 0 0 15px rgba(234, 179, 8, 0.4); }
    </style>
</head>
<body class="py-5">
    <div class="container" style="max-width: 800px;">
        <div class="text-center mb-5">
            <h1 class="fw-bold glow text-warning">⚽ FUTEBOL INVISÍVEL AI</h1>
            <p class="text-secondary fs-5">Fábrica Automática de Shorts Virais com Vídeos Reais da Internet</p>
        </div>

        <div class="card card-custom p-4 mb-4">
            <h4 class="mb-3">🚀 Criar Novo Short em 1 Clique</h4>
            <form id="createForm">
                <div class="mb-3">
                    <label class="form-label text-light">Digite apenas o TEMA ou TÍTULO do vídeo:</label>
                    <input type="text" id="tituloInput" class="form-control form-control-lg bg-dark text-light border-secondary" 
                           placeholder="Ex: Raphinha destruindo no Barcelona / A revolta de CR7 / Dribles de Vini Jr" required>
                    <div class="form-text text-secondary">O sistema vai criar o roteiro, narrar, buscar os vídeos reais no YouTube, cortar e legendar em 9:16 automaticamente.</div>
                </div>
                <button type="submit" class="btn btn-gold btn-lg w-100" id="btnSubmit">🎬 GERAR VÍDEO COMPLETO AGORA</button>
            </form>
        </div>

        <div id="progressCard" class="card card-custom p-4 d-none">
            <h5 class="text-warning">Status da Produção:</h5>
            <div class="d-flex align-items-center my-3">
                <div class="spinner-border text-warning me-3" role="status" id="spinner"></div>
                <span id="statusText" class="fs-5 text-light fw-bold">Iniciando...</span>
            </div>
            <div id="roteiroBox" class="p-3 bg-dark rounded border border-secondary text-secondary small d-none mb-3"></div>
            <div id="downloadBox" class="d-none">
                <a id="btnDownload" href="#" class="btn btn-success btn-lg w-100 fw-bold">📥 BAIXAR SHORT PRONTO (MP4)</a>
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

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const titulo = document.getElementById('tituloInput').value;
            btnSubmit.disabled = true;
            progressCard.classList.remove('d-none');
            downloadBox.classList.add('d-none');
            roteiroBox.classList.add('d-none');
            spinner.classList.remove('d-none');
            statusText.innerText = "Criando tarefa no servidor...";

            const res = await fetch('/api/criar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ titulo })
            });
            const data = await res.json();
            const taskId = data.task_id;

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
                } else if (task.status.startsWith("Erro")) {
                    clearInterval(interval);
                    spinner.classList.add('d-none');
                    btnSubmit.disabled = false;
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

@app.post("/api/criar")
def criar_short(background_tasks: BackgroundTasks, titulo: str = Form(...)):
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        "titulo": titulo,
        "status": "Iniciando processo...",
        "roteiro": "",
        "file_path": None,
        "file_name": None
    }
    background_tasks.add_task(processar_video_por_titulo, task_id, titulo)
    return {"task_id": task_id}

@app.get("/api/status/{task_id}")
def status_short(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return TASKS[task_id]

@app.get("/api/download/{task_id}")
def download_short(task_id: str):
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
