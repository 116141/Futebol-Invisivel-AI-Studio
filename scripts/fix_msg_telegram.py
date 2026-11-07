import os

with open("app/services/video_scheduler.py", "r", encoding="utf-8") as f:
    text = f.read()

# Fix multi-line f-string broken by line endings
broken_target = '''        try:
            msg_telegram = (
                f"🚀 *VÍDEO PUBLICADO NO PICO DE AUDIÊNCIA!*\\n
\\n
"
                f"📺 *Canal:* `{canal.upper()}`\\n
"
                f"⏰ *Horário Cabo Verde:* `{slot_atingido['hora']:02d}:{slot_atingido['minuto']:02d}`\\n
"
                f"🎯 *Formato:* `{'DOCUMENTÁRIO INVESTIGATIVO (16:9)' if video_escolhido['is_doc'] else 'SHORT VERTICAL (9:16)'}`\\n
"
                f"🌍 *Momento da Audiência:* `{slot_atingido['rotulo']}`\\n
"
                f"🎬 *Título:* _{video_escolhido['titulo']}_\\n
"
                f"✨ *Qualidade:* `{video_escolhido['resolucao']}` (HD nativo garantido)\\n
"
                f"⏳ *Tempo de Maturação:* `{video_escolhido['minutos_maturacao']} min em esteira`\\n
"
                f"🔗 *Link:* https://youtu.be/{vid_id}\\n
\\n
"
                f"🟢 _O algoritmo já possui HD e legendas indexadas para entrega máxima!_"
            )
            telegram_reporter.enviar_mensagem_telegram(msg_telegram)
        except Exception:
            pass'''

clean_msg = '''        try:
            msg_telegram = (
                "🚀 *VÍDEO PUBLICADO NO PICO DE AUDIÊNCIA!*\\n\\n"
                f"📺 *Canal:* `{canal.upper()}`\\n"
                f"⏰ *Horário Cabo Verde:* `{slot_atingido['hora']:02d}:{slot_atingido['minuto']:02d}`\\n"
                f"🎯 *Formato:* `{'DOCUMENTÁRIO INVESTIGATIVO (16:9)' if video_escolhido['is_doc'] else 'SHORT VERTICAL (9:16)'}`\\n"
                f"🌍 *Momento da Audiência:* `{slot_atingido['rotulo']}`\\n"
                f"🎬 *Título:* _{video_escolhido['titulo']}_\\n"
                f"✨ *Qualidade:* `{video_escolhido['resolucao']}` (HD nativo garantido)\\n"
                f"⏳ *Tempo de Maturação:* `{video_escolhido['minutos_maturacao']} min em esteira`\\n"
                f"🔗 *Link:* https://youtu.be/{vid_id}\\n\\n"
                "🟢 _O algoritmo já possui HD e legendas indexadas para entrega máxima!_"
            )
            telegram_reporter.enviar_mensagem_telegram(msg_telegram)
        except Exception:
            pass'''

# Let's locate 'msg_telegram = (' and 'telegram_reporter.enviar_mensagem_telegram(msg_telegram)'
start_needle = "        try:\n            msg_telegram = ("
end_needle = "            telegram_reporter.enviar_mensagem_telegram(msg_telegram)\n        except Exception:\n            pass"

if start_needle in text and end_needle in text:
    part1 = text[:text.index(start_needle)]
    part2 = text[text.index(end_needle) + len(end_needle):]
    new_text = part1 + clean_msg + part2
    with open("app/services/video_scheduler.py", "w", encoding="utf-8") as f:
        f.write(new_text)
    print("SUCCESS: msg_telegram corrigido com sucesso!")
else:
    print("NEEDLE NOT FOUND, looking via lines...")
    lines = text.splitlines(keepends=True)
    start_i = None
    end_i = None
    for i, l in enumerate(lines):
        if "msg_telegram = (" in l:
            start_i = i - 1  # include 'try:'
        if start_i is not None and "telegram_reporter.enviar_mensagem_telegram" in l:
            end_i = i + 3    # include 'except Exception:\n pass\n'
            break
    if start_i and end_i:
        new_lines = lines[:start_i] + [clean_msg + "\n"] + lines[end_i:]
        with open("app/services/video_scheduler.py", "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print("SUCCESS via lines!")
