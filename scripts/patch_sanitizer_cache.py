def patch_sanitizer():
    with open('app/services/channel_sanitizer.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '    try:\n        yt = youtube_uploader.get_authenticated_service(canal_nome=canal)'
    
    replacement = '''    import time
    # Cache de auditoria: só executa auditoria pesada a cada 4 horas por canal para não queimar cota
    now_ts = time.time()
    if not hasattr(auditar_e_sanear_canal, '_ultimo_check'):
        auditar_e_sanear_canal._ultimo_check = {}
    if now_ts - auditar_e_sanear_canal._ultimo_check.get(canal, 0) < 14400 and not dry_run:
        relatorio["motivo"] = "Auditoria pulada: última varredura há menos de 4 horas (preservação de cota)"
        return relatorio

    try:
        auditar_e_sanear_canal._ultimo_check[canal] = now_ts
        yt = youtube_uploader.get_authenticated_service(canal_nome=canal)'''

    text_norm = text.replace('\r\n', '\n')
    target_norm = target.replace('\r\n', '\n')
    replacement_norm = replacement.replace('\r\n', '\n')

    if target_norm in text_norm:
        res = text_norm.replace(target_norm, replacement_norm, 1).replace('\n', '\r\n')
        with open('app/services/channel_sanitizer.py', 'w', encoding='utf-8', newline='') as f:
            f.write(res)
        print("Sucesso: channel_sanitizer otimizado com cache de 4 horas!")
    else:
        print("Target nao encontrado em channel_sanitizer")

if __name__ == '__main__':
    patch_sanitizer()
