with open("app/services/llm.py", "r", encoding="utf-8") as f:
    text = f.read()

# Substituir o bloco de geração do generate_script para interceptar "Error:" e acionar o Groq
target_loop = '''    for i in range(_max_retries):
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

new_loop = '''    for i in range(_max_retries):
        try:
            if app_config is None:
                response = _generate_response(prompt=prompt)
            else:
                response = _generate_response(prompt=prompt, app_config=app_config)

            if response and not response.strip().startswith("Error:"):
                final_script = format_response(response)
                if final_script and "当日额度已消耗完" not in final_script:
                    break
            else:
                logger.warning(f"Provedor principal falhou ({response[:80] if response else 'vazio'}). Tentando Fallback Multi-IA com Groq...")
                # FALLBACK MULTI-IA AUTOMÁTICO: Groq assume imediatamente se o principal devolver erro ou falhar
                try:
                    fallback_cfg = (app_config or config.app).copy()
                    fallback_cfg["llm_provider"] = "groq"
                    fallback_cfg["groq_model_name"] = "openai/gpt-oss-120b"
                    resp_groq = _generate_response(prompt=prompt, app_config=fallback_cfg)
                    if resp_groq and not resp_groq.strip().startswith("Error:"):
                        final_script = format_response(resp_groq)
                        logger.success("✅ [MULTI-IA] Roteiro gerado com sucesso via Fallback Groq!")
                        break
                except Exception as e_fb:
                    logger.error(f"Fallback Groq falhou: {e_fb}")

        except Exception as e:
            logger.error(f"Exceção no provedor principal: {e}")
            try:
                logger.info("🔄 Acionando Fallback Multi-IA com Groq após exceção...")
                fallback_cfg = (app_config or config.app).copy()
                fallback_cfg["llm_provider"] = "groq"
                fallback_cfg["groq_model_name"] = "openai/gpt-oss-120b"
                resp_groq = _generate_response(prompt=prompt, app_config=fallback_cfg)
                if resp_groq and not resp_groq.strip().startswith("Error:"):
                    final_script = format_response(resp_groq)
                    logger.success("✅ [MULTI-IA] Roteiro gerado com sucesso via Fallback Groq!")
                    break
            except Exception as e_fb:
                logger.error(f"Fallback Groq falhou: {e_fb}")

        if i < _max_retries and (not final_script or final_script.strip().startswith("Error:")):
            logger.warning(f"failed to generate video script, trying again... {i + 1}")'''

if target_loop in text:
    text = text.replace(target_loop, new_loop, 1)
    with open("app/services/llm.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: Mecanismo de contingência Multi-IA aperfeiçoado!")
else:
    print("FAILED: target_loop não encontrado")
