import re

def patch_uploader():
    with open('app/services/youtube_uploader.py', 'r', encoding='utf-8') as f:
        text = f.read()

    text_norm = text.replace('\r\n', '\n')
    
    old_code = '''    # Sanitização universal de tags na entrada da API do YouTube
    tags_limpas = []
    char_acc = 0
    if tags:
        for tg in tags:
            proibidos = ["<", ">", "#", ",", "\\n", "\\r", "\\t"]
            t_clean = str(tg)
            for char_p in proibidos:
                t_clean = t_clean.replace(char_p, "")
            t_clean = t_clean.strip()
            t_clean = t_clean[:60].strip()
            if not t_clean or len(t_clean) < 2:
                continue
            custo = len(t_clean) + (1 if tags_limpas else 0)
            if char_acc + custo <= 470 and len(tags_limpas) < 40:
                tags_limpas.append(t_clean)
                char_acc += custo
            elif char_acc >= 460:
                break'''

    new_code = '''    # Sanitização universal de tags na entrada da API do YouTube
    tags_limpas = []
    char_acc = 0
    if tags:
        import re
        for tg in tags:
            t_clean = str(tg)
            # Remove caracteres proibidos e pontuações que a API do YouTube rejeita em keywords (como : ? ! # < > etc)
            t_clean = re.sub(r'[<>#,\\n\\r\\t:?!\"\'`~\\\\/|]', '', t_clean)
            t_clean = re.sub(r'\\s+', ' ', t_clean).strip()
            t_clean = t_clean[:60].strip()
            if not t_clean or len(t_clean) < 2:
                continue
            custo = len(t_clean) + (1 if tags_limpas else 0)
            if char_acc + custo <= 470 and len(tags_limpas) < 40:
                tags_limpas.append(t_clean)
                char_acc += custo
            elif char_acc >= 460:
                break'''

    if old_code in text_norm:
        res = text_norm.replace(old_code, new_code, 1).replace('\n', '\r\n')
        with open('app/services/youtube_uploader.py', 'w', encoding='utf-8', newline='') as f:
            f.write(res)
        print("SUCESSO: youtube_uploader.py atualizado!")
    else:
        print("ALVO NAO ENCONTRADO em youtube_uploader.py")

    with open('app_render_studio.py', 'r', encoding='utf-8') as f:
        studio_text = f.read()
    
    studio_norm = studio_text.replace('\r\n', '\n')
    old_studio = '''    for t in lista_final_candidatos:
        proibidos = ["<", ">", "#", ",", "\\n", "\\r", "\\t"]
        t_san = str(t)
        for char_p in proibidos:
            t_san = t_san.replace(char_p, "")
        t_san = t_san.strip()
        t_san = t_san[:60].strip()
        if not t_san or len(t_san) < 2:
            continue
        custo = len(t_san) + (1 if tags_list else 0)
        if char_count + custo <= 480 and len(tags_list) < 45:
            tags_list.append(t_san)
            char_count += custo
        elif char_count >= 465:
            break'''

    new_studio = '''    for t in lista_final_candidatos:
        t_san = str(t)
        t_san = re.sub(r'[<>#,\\n\\r\\t:?!\"\'`~\\\\/|]', '', t_san)
        t_san = re.sub(r'\\s+', ' ', t_san).strip()
        t_san = t_san[:60].strip()
        if not t_san or len(t_san) < 2:
            continue
        custo = len(t_san) + (1 if tags_list else 0)
        if char_count + custo <= 480 and len(tags_list) < 45:
            tags_list.append(t_san)
            char_count += custo
        elif char_count >= 465:
            break'''

    if old_studio in studio_norm:
        res_s = studio_norm.replace(old_studio, new_studio, 1).replace('\n', '\r\n')
        with open('app_render_studio.py', 'w', encoding='utf-8', newline='') as f:
            f.write(res_s)
        print("SUCESSO: app_render_studio.py atualizado!")
    else:
        print("ALVO NAO ENCONTRADO em app_render_studio.py")

if __name__ == '__main__':
    patch_uploader()
