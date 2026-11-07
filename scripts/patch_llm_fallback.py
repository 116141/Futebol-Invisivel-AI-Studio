with open("app/services/llm.py", "r", encoding="utf-8") as f:
    text = f.read()

# Implementar fallback automático para o Groq se o provedor principal falhar
target_block = '''    for i in range(_max_retries):
        try:
            if app_config is None:
                response = _generate_response(prompt=prompt)
            else:
                response = _generate_response(prompt=prompt, app_config=app_config)
            if response:
                final_script = format_response(response)
            else:
                logging.error("gpt returned an empty response")

            # Some upstream providers may return quota errors as plain text.
            if final_script and "当日额度已消耗完" in final_script:
                raise ValueError(final_script)

            if final_script:
                break
        except Exception as e:
            logger.error(f"failed to generate script: {e}")

        if i < _max_retries:
            logger.warning(f"failed to generate video script, trying again... {i + 1}")'''

replacement_block = '''    for i in range(_max_retries):
        try:
            if app_config is None:
                response = _generate_response(prompt=prompt)
            else:
                response = _generate_response(prompt=prompt, app_config=app_config)
            if response:
                final_script = format_response(response)
            else:
                logging.error("llm returned an empty response")

            if final_script and "当日额度已消耗完" in final_script:
                raise ValueError(final_script)

            if final_script and "Error:" not in final_script:
                break
        except Exception as e:
            logger.error(f"failed to generate script com provedor principal: {e}")
            # FALLBACK MULTI-IA AUTOMÁTICO: Tenta imediatamente o Groq se o principal oscilar
            try:
                logger.info("🔄 Acionando Fallback Multi-IA com Groq...")
                fallback_cfg = config.app.copy()
                fallback_cfg["llm_provider"] = "groq"
                fallback_cfg["groq_model_name"] = "openai/gpt-oss-120b"
                resp_groq = _generate_response(prompt=prompt, app_config=fallback_cfg)
                if resp_groq and "Error:" not in resp_groq:
                    final_script = format_response(resp_groq)
                    logger.success("✅ Roteiro gerado com sucesso via Fallback Groq!")
                    break
            except Exception as e_fb:
                logger.error(f"Fallback Groq também falhou: {e_fb}")

        if i < _max_retries:
            logger.warning(f"failed to generate video script, trying again... {i + 1}")'''

if target_block in text:
    text = text.replace(target_block, replacement_block, 1)
    with open("app/services/llm.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: Fallback Multi-IA integrado com sucesso em llm.py!")
else:
    print("FAILED: target_block not found in llm.py")
