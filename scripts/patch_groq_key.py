import os

with open("config.toml", "r", encoding="utf-8") as f:
    text = f.read()

target = 'groq_api_key = ""'
groq_key = os.getenv("GROQ_API_KEY", "")
replacement = f'groq_api_key = "{groq_key}"\ngroq_model_name = "llama-3.3-70b-versatile"'


if target in text:
    text = text.replace(target, replacement, 1)
    with open("config.toml", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: Groq cadastrado com sucesso!")
else:
    print("TARGET NOT FOUND")
