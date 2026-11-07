with open("app/services/video_scheduler.py", "r", encoding="utf-8") as f:
    text = f.read()

# Replace the broken multi-line string in enviar_aviso_previo_pico_telegram
start_s = "        msg = ("
end_s = "        sucesso = telegram_reporter.enviar_mensagem_telegram(msg)"

clean_msg = '''        msg = (
            "👀 *AVISO PRÉVIO: VÍDEO AGENDADO PARA O PRÓXIMO PICO!*\\n\\n"
            f"Olá! Daqui a cerca de *{minutos_ate_pico} minutos* teremos pico de audiência e este vídeo está na vez para ser liberado ao público:\\n\\n"
            f"📺 *Canal:* `{canal.upper()}`\\n"
            f"⏰ *Horário do Pico:* `{proximo_slot['hora']:02d}:{proximo_slot['minuto']:02d}` (Cabo Verde)\\n"
            f"🎯 *Momento:* _{proximo_slot['rotulo']}_\\n"
            f"🎬 *Formato:* `{formato_str}`\\n"
            f"📌 *Título:* _{titulo}_\\n"
            f"✨ *Qualidade:* `{video_escolhido.get('resolucao', '1080p HD')}`\\n"
            f"⏳ *Tempo de Maturação:* `{video_escolhido.get('minutos_maturacao', 0)} min em esteira (100% Indexado)`\\n\\n"
            f"🔗 *Dê uma olhada antes de ir ao ar:*\\n"
            f"• Preview Não-Listado: https://youtu.be/{vid_id}\\n"
            f"• Edição / Capa no Studio: https://studio.youtube.com/video/{vid_id}/edit\\n\\n"
            "💡 _Se estiver tudo aprovado, não precisa fazer nada. O robô publicará automaticamente no horário exato do pico!_"
        )
'''

lines = text.splitlines(keepends=True)
s_idx = None
e_idx = None
for i, l in enumerate(lines):
    if "msg = (" in l and i > 400:
        s_idx = i
    if s_idx is not None and "sucesso = telegram_reporter.enviar_mensagem_telegram(msg)" in l:
        e_idx = i
        break

if s_idx is not None and e_idx is not None:
    new_lines = lines[:s_idx] + [clean_msg] + lines[e_idx:]
    with open("app/services/video_scheduler.py", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("SUCCESS: msg limpa aplicada!")
else:
    print(f"FAILED to find indices: s_idx={s_idx}, e_idx={e_idx}")
