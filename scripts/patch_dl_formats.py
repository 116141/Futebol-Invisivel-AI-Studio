def patch_formats():
    with open('app_render_studio.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if 'f.startswith("source_") and f.endswith(".mp4")' in line:
            new_lines.append(line.replace('f.endswith(".mp4")', '(f.endswith(".mp4") or f.endswith(".mkv") or f.endswith(".webm"))'))
        else:
            new_lines.append(line)
            
    with open('app_render_studio.py', 'w', encoding='utf-8', newline='') as f:
        f.writelines(new_lines)
    print("Sucesso: formatos aceitos expandidos!")

if __name__ == '__main__':
    patch_formats()
