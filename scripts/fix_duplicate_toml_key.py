with open("config.toml", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
saw_groq_model = False
for line in lines:
    if line.strip().startswith("groq_model_name ="):
        if not saw_groq_model:
            new_lines.append('groq_model_name = "llama-3.3-70b-versatile"\n')
            saw_groq_model = True
        else:
            continue  # remove duplicate key
    else:
        new_lines.append(line)

with open("config.toml", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("SUCCESS: Chave duplicada removida do config.toml!")
