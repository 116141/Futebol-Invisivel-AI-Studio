with open("config.toml", "r", encoding="utf-8") as f:
    text = f.read()

target = 'groq_model_name = "llama-3.3-70b-versatile"'
replacement = 'groq_model_name = "openai/gpt-oss-120b"'

if target in text:
    text = text.replace(target, replacement, 1)
    with open("config.toml", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: Modelo padrão do Groq ajustado para openai/gpt-oss-120b!")
else:
    print("TARGET NOT FOUND")
