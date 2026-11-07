def clean():
    with open('app_render_studio.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # Remover linha 2045 (índice 2044) e linha 2044
    new_lines = []
    for l in lines:
        if '\\:\\?\\!' in l:
            continue
        new_lines.append(l)
    with open('app_render_studio.py', 'w', encoding='utf-8', newline='') as f:
        f.writelines(new_lines)

    with open('app/services/youtube_uploader.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    new_lines_u = []
    for l in lines:
        if '\\:\\?\\!' in l:
            continue
        new_lines_u.append(l)
    with open('app/services/youtube_uploader.py', 'w', encoding='utf-8', newline='') as f:
        f.writelines(new_lines_u)

if __name__ == '__main__':
    clean()
