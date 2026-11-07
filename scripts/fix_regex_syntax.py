def fix():
    pattern_chars = r'[<>#,\n\r\t:?!"\'`~\\/|]'
    
    with open('app_render_studio.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if 't_san = re.sub(' in line:
            lines[i] = '        t_san = re.sub(r\'[<>#,\\n\\r\\t:?!"`~\\\\/|\' + "\']", "", t_san)\n'
            break
    with open('app_render_studio.py', 'w', encoding='utf-8', newline='') as f:
        f.writelines(lines)

    with open('app/services/youtube_uploader.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if 't_clean = re.sub(' in line:
            lines[i] = '            t_clean = re.sub(r\'[<>#,\\n\\r\\t:?!"`~\\\\/|\' + "\']", "", t_clean)\n'
            break
    with open('app/services/youtube_uploader.py', 'w', encoding='utf-8', newline='') as f:
        f.writelines(lines)

if __name__ == '__main__':
    fix()
