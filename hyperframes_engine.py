import os
import sys
import json
import asyncio
import subprocess
from loguru import logger
from PIL import Image

FFMPEG_BIN_DIR = r"C:\Users\Uni-CvFCT-EdmilsonGi\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"
FFMPEG_EXE = os.path.join(FFMPEG_BIN_DIR, "ffmpeg.exe") if os.path.exists(FFMPEG_BIN_DIR) else "ffmpeg"
FFPROBE_EXE = os.path.join(FFMPEG_BIN_DIR, "ffprobe.exe") if os.path.exists(FFMPEG_BIN_DIR) else "ffprobe"

def ensure_ffmpeg_path():
    if os.path.exists(FFMPEG_BIN_DIR) and FFMPEG_BIN_DIR not in os.environ.get("PATH", ""):
        os.environ["PATH"] = FFMPEG_BIN_DIR + os.pathsep + os.environ.get("PATH", "")

def get_audio_duration(audio_path: str) -> float:
    ensure_ffmpeg_path()
    try:
        cmd = [
            FFPROBE_EXE,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception as e:
        logger.warning(f"Erro ao obter duração do áudio com ffprobe: {e}. Usando fallback 35.0s")
        return 35.0

async def _synthesize_edge_tts(text: str, voice_name: str, out_audio_path: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice_name)
    subtitles = []
    
    with open(out_audio_path, "wb") as f_out:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f_out.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                # offset e duration estão em centenas de nanossegundos (10^7 = 1s)
                start_sec = chunk["offset"] / 10_000_000.0
                dur_sec = chunk["duration"] / 10_000_000.0
                subtitles.append({
                    "text": chunk["text"].strip(),
                    "start": start_sec,
                    "duration": dur_sec
                })
    return subtitles

def generate_narration_with_subtitles(text: str, voice_name: str, out_path: str):
    logger.info(f"[HyperFrames TTS] Sintetizando voz e sincronizando legendas: '{voice_name}'...")
    raw_subtitles = asyncio.run(_synthesize_edge_tts(text, voice_name, out_path))
    duration = get_audio_duration(out_path)
    
    # Quebrar sentenças longas em micro-frases de 3 a 5 palavras para efeito viral
    short_cues = []
    for s in raw_subtitles:
        words = s["text"].split()
        if len(words) <= 5:
            short_cues.append(s)
        else:
            # Divide em fatias de 3 a 5 palavras
            chunk_size = 4
            num_chunks = (len(words) + chunk_size - 1) // chunk_size
            chunk_dur = s["duration"] / num_chunks
            for i in range(num_chunks):
                sub_words = words[i * chunk_size : (i + 1) * chunk_size]
                short_cues.append({
                    "text": " ".join(sub_words),
                    "start": s["start"] + (i * chunk_dur),
                    "duration": chunk_dur
                })
                
    logger.success(f"[HyperFrames TTS] Áudio gerado: {out_path} ({duration:.2f}s) com {len(short_cues)} micro-legendas.")
    return duration, short_cues

def build_hyperframes_html(
    title: str,
    image_filenames: list,
    cues: list,
    audio_filename: str,
    total_duration: float,
    logo_filename: str = None
) -> str:
    """
    Gera HTML com cortes de cena a cada ~3s, Ken Burns dinâmico,
    logo oficial discreto e legendas curtas (3-5 palavras) sincronizadas.
    """
    num_images = max(1, len(image_filenames))
    dur_per_scene = total_duration / num_images
    
    html_scenes = []
    gsap_timelines = []

    # 1. CENAS COM FOTOS REAIS (CORTES A CADA 3-4 SEGUNDOS)
    for i, img_name in enumerate(image_filenames):
        idx = i + 1
        scene_id = f"scene-{idx}"
        img_id = f"img-{idx}"
        start = i * dur_per_scene
        dur = dur_per_scene

        # Alternar movimentos de câmera
        if i % 3 == 0:
            scale_from, scale_to = 1.05, 1.22
            x_from, x_to = 0, 0
            y_from, y_to = 0, -35
        elif i % 3 == 1:
            scale_from, scale_to = 1.25, 1.08
            x_from, x_to = -25, 25
            y_from, y_to = -20, 10
        else:
            scale_from, scale_to = 1.10, 1.26
            x_from, x_to = 20, -20
            y_from, y_to = 20, -25

        scene_markup = f"""
      <!-- Cena {idx}: Foto Real ({start:.2f}s até {start+dur:.2f}s) -->
      <div id="{scene_id}" class="scene clip" data-start="{start:.2f}" data-duration="{dur:.2f}">
        <div class="bg-container">
          <img id="{img_id}" class="bg-image" src="{img_name}" alt="Cena {idx}" />
        </div>
        <div class="vignette-overlay"></div>
      </div>
        """
        html_scenes.append(scene_markup)

        # Animação GSAP da foto nesta cena
        gsap_timelines.append(f"""
      // Câmera Cena {idx}
      tl.fromTo("#{img_id}", 
        {{ scale: {scale_from}, x: {x_from}, y: {y_from} }}, 
        {{ scale: {scale_to}, x: {x_to}, y: {y_to}, duration: {dur:.2f}, ease: "none" }}, 
        {start:.2f}
      );
        """)

    # 2. GANCHO INICIAL (APARECE NOS PRIMEIROS 3.5s E SOME)
    hook_duration = min(3.8, dur_per_scene)
    hook_markup = f"""
      <div id="hook-badge" class="channel-badge clip" data-start="0.1" data-duration="{hook_duration - 0.2:.2f}">
        <div class="channel-badge-dot"></div>
        <span class="channel-badge-text">FUTEBOL INVISÍVEL | DOSSIÊ</span>
      </div>

      <div id="hook-title-box" class="hook-container clip" data-start="0.2" data-duration="{hook_duration - 0.4:.2f}">
        <h1 class="hook-title">{title.upper()}</h1>
      </div>
    """

    gsap_timelines.append(f"""
      // Gancho Inicial (0s a {hook_duration:.2f}s)
      tl.fromTo("#hook-badge", {{ opacity: 0, y: -40 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "back.out(1.7)" }}, 0.1);
      tl.fromTo("#hook-title-box", {{ opacity: 0, scale: 1.3, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.45, ease: "power4.out" }}, 0.25);
      tl.to(["#hook-badge", "#hook-title-box"], {{ opacity: 0, y: -20, duration: 0.35 }}, {hook_duration - 0.4:.2f});
    """)

    # 3. MICRO-LEGENDAS DINÂMICAS SINCRONIZADAS COM A FALA (CURTAS E COMPACTAS)
    subtitles_markup = []
    for j, cue in enumerate(cues):
        sub_id = f"sub-{j+1}"
        sub_start = cue["start"]
        sub_dur = max(0.4, cue["duration"])
        words = cue["text"].upper().split()
        
        # Destacar a última ou penúltima palavra em amarelo ouro
        highlighted_words = []
        for w_idx, w in enumerate(words):
            if w_idx == len(words) - 1 and len(words) > 1:
                highlighted_words.append(f'<span class="sub-highlight">{w}</span>')
            else:
                highlighted_words.append(w)
        formatted_text = " ".join(highlighted_words)

        sub_markup = f"""
      <div id="{sub_id}" class="subtitle-cue clip" data-start="{sub_start:.2f}" data-duration="{sub_dur:.2f}">
        <div class="subtitle-pill">{formatted_text}</div>
      </div>
        """
        subtitles_markup.append(sub_markup)

        gsap_timelines.append(f"""
      tl.fromTo("#{sub_id}", 
        {{ opacity: 0, scale: 0.85, y: 15 }}, 
        {{ opacity: 1, scale: 1, y: 0, duration: 0.18, ease: "power2.out" }}, 
        {sub_start:.2f}
      );
      tl.to("#{sub_id}", 
        {{ opacity: 0, scale: 0.95, duration: 0.12 }}, 
        {sub_start + sub_dur - 0.12:.2f}
      );
        """)

    all_scenes_str = "\n".join(html_scenes)
    all_subs_str = "\n".join(subtitles_markup)
    all_gsap_str = "\n".join(gsap_timelines)

    logo_watermark_html = ""
    if logo_filename:
        logo_watermark_html = f"""
    <!-- Marca d'Água Oficial Futebol Invisível -->
    <div class="watermark-logo">
      <img src="{logo_filename}" alt="Logo Futebol Invisível" class="watermark-img" />
    </div>
        """

    audio_tag = f"""<audio src="{audio_filename}" data-start="0" data-duration="{total_duration:.2f}" data-volume="1"></audio>""" if audio_filename else ""

    html_template = f"""<!doctype html>
<html lang="pt-BR" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@800;900&family=Inter:wght@400;600;700&display=swap');

      * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }}

      html, body {{
        width: 1080px;
        height: 1920px;
        overflow: hidden;
        background: #000000;
        font-family: 'Montserrat', sans-serif;
        color: #ffffff;
      }}

      #root {{
        position: relative;
        width: 1080px;
        height: 1920px;
        overflow: hidden;
      }}

      .scene {{
        position: absolute;
        inset: 0;
        width: 1080px;
        height: 1920px;
      }}

      .bg-container {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
      }}

      .bg-image {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        filter: brightness(0.85) contrast(1.12);
      }}

      /* Vinheta suave que não esconde o protagonista */
      .vignette-overlay {{
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at center, rgba(0,0,0,0) 35%, rgba(0,0,0,0.8) 100%),
                    linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, transparent 20%, transparent 70%, rgba(0,0,0,0.85) 100%);
        pointer-events: none;
      }}

      /* Badge superior no gancho */
      .channel-badge {{
        position: absolute;
        top: 140px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 28px;
        background: rgba(10, 10, 15, 0.9);
        border: 2px solid #eab308;
        border-radius: 9999px;
        box-shadow: 0 0 25px rgba(234, 179, 8, 0.4);
        z-index: 500;
      }}

      .channel-badge-dot {{
        width: 14px;
        height: 14px;
        background: #ef4444;
        border-radius: 50%;
        box-shadow: 0 0 10px #ef4444;
      }}

      .channel-badge-text {{
        font-size: 24px;
        font-weight: 900;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #fef08a;
      }}

      /* Título do Gancho nos primeiros segundos */
      .hook-container {{
        position: absolute;
        top: 240px;
        left: 60px;
        right: 60px;
        text-align: center;
        z-index: 500;
      }}

      .hook-title {{
        font-size: 68px;
        font-weight: 900;
        line-height: 1.12;
        text-transform: uppercase;
        color: #ffffff;
        text-shadow: 0 8px 30px rgba(0, 0, 0, 0.95), 0 2px 4px #000;
      }}

      /* Marca d'água no canto superior */
      .watermark-logo {{
        position: absolute;
        top: 45px;
        right: 45px;
        width: 95px;
        height: 95px;
        border-radius: 50%;
        overflow: hidden;
        border: 3px solid rgba(234, 179, 8, 0.9);
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.85);
        z-index: 1000;
      }}

      .watermark-img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
      }}

      /* Legendas Dinâmicas Curtas (3 a 5 palavras no terço inferior) */
      .subtitle-cue {{
        position: absolute;
        bottom: 240px;
        left: 50px;
        right: 50px;
        text-align: center;
        z-index: 600;
        pointer-events: none;
      }}

      .subtitle-pill {{
        display: inline-block;
        padding: 14px 28px;
        font-family: 'Montserrat', sans-serif;
        font-size: 52px;
        font-weight: 900;
        line-height: 1.15;
        text-transform: uppercase;
        color: #ffffff;
        background: rgba(0, 0, 0, 0.85);
        border: 2px solid rgba(255, 255, 255, 0.25);
        border-radius: 14px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.9);
        text-shadow: 0 4px 10px rgba(0,0,0,0.9);
      }}

      .sub-highlight {{
        color: #facc15;
        text-shadow: 0 0 25px rgba(250, 204, 21, 0.7);
      }}
    </style>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="main"
      data-start="0"
      data-duration="{total_duration:.2f}"
      data-width="1080"
      data-height="1920"
    >
      {logo_watermark_html}
      {audio_tag}
      {all_scenes_str}
      {hook_markup}
      {all_subs_str}
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});

      {all_gsap_str}

      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>"""
    return html_template

def produce_hyperframes_video(
    title: str,
    script: str,
    image_paths: list,
    voice_name: str = "pt-BR-AntonioNeural",
    task_id: str = None,
    output_mp4: str = None
) -> str:
    """
    Pipeline com cortes a cada 3-4s e legendas curtas sincronizadas.
    """
    import shutil
    ensure_ffmpeg_path()
    
    if not task_id:
        import time
        task_id = str(int(time.time()))
        
    project_dir = os.path.abspath(os.path.join("storage", "hyperframes_runs", task_id))
    os.makedirs(project_dir, exist_ok=True)
    
    # 1. Áudio com sincronização de legendas curtas
    audio_file = os.path.join(project_dir, "narration.mp3")
    duration, cues = generate_narration_with_subtitles(script, voice_name, audio_file)
    
    # 2. Copiar imagens para o diretório do projeto
    dest_image_names = []
    for i, orig_img in enumerate(image_paths):
        dest_img_name = f"cena_{i+1:02d}.jpg"
        dest_path = os.path.join(project_dir, dest_img_name)
        shutil.copy(orig_img, dest_path)
        dest_image_names.append(dest_img_name)
        
    # Copiar logo / watermark oficial
    logo_filename = None
    workspace_logo = "perfil_futebol_invisivel.jpg"
    if os.path.exists(workspace_logo):
        logo_filename = "logo_canal.jpg"
        shutil.copy(workspace_logo, os.path.join(project_dir, logo_filename))

    # 3. Gerar index.html otimizado
    html_content = build_hyperframes_html(
        title=title,
        image_filenames=dest_image_names,
        cues=cues,
        audio_filename="narration.mp3",
        total_duration=duration,
        logo_filename=logo_filename
    )
    
    index_html_path = os.path.join(project_dir, "index.html")
    with open(index_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    # package.json básico
    pkg_json = {
        "name": f"futebol-invisivel-{task_id}",
        "private": True,
        "type": "module"
    }
    with open(os.path.join(project_dir, "package.json"), "w", encoding="utf-8") as f:
        json.dump(pkg_json, f, indent=2)

    # 4. Renderizar via CLI
    if not output_mp4:
        out_dir = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos")
        os.makedirs(out_dir, exist_ok=True)
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()[:30]
        output_mp4 = os.path.abspath(os.path.join(out_dir, f"{task_id}_{safe_title.replace(' ', '_')}.mp4"))

    render_cmd = f"npx hyperframes render -o \"{output_mp4}\" --fps 30"
    logger.info(f"[HyperFrames] Renderizando vídeo 9:16 dinâmico para: {output_mp4}...")
    
    ps_cmd = [
        "powershell", "-NoProfile", "-Command",
        f"$env:PATH = '{FFMPEG_BIN_DIR};' + $env:PATH; Set-Location '{project_dir}'; {render_cmd}"
    ]
    
    res = subprocess.run(ps_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        logger.error(f"[HyperFrames] Falha no render: {res.stderr}\n{res.stdout}")
        raise RuntimeError(f"Erro ao renderizar vídeo com HyperFrames: {res.stderr}")
        
    logger.success(f"[HyperFrames] VÍDEO FINAL ENTREGUE EM: {output_mp4}")
    return output_mp4
