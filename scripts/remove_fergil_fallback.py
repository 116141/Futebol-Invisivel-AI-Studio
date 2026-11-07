with open("app_render_studio.py", "r", encoding="utf-8") as f:
    text = f.read()

target_fergil_fallback = '''            except Exception:
                if is_doc:
                    roteiro = (
                        f"Em um mercado dominado por incertezas, a trajetória de {titulo} revela como as maiores fortunas são construídas ou perdidas em silêncio. "
                        "Capítulo um: O momento da ruptura. Nos bastidores do poder, decisões que parecem impulsivas para o público quase sempre respondem a um cálculo frio de risco e sobrevivência corporativa. "
                        "Capítulo dois: A psicologia dos titãs da indústria. Enquanto investidores comuns se desesperam com oscilações diárias, os grandes operadores manipulam o fluxo de capital e antecipam tendências antes de qualquer manchete de jornal. "
                        "Capítulo três: A lição definitiva de liderança. O verdadeiro patrimônio não está apenas nos números da conta bancária, mas na capacidade de tomar decisões de alto impacto sob pressão extrema. "
                        "Se você quer elevar a sua visão estratégica e dominar os bastidores do dinheiro e dos negócios, deixe seu like, inscreva-se agora no canal FERGIL e comente abaixo qual é a sua análise sobre esta decisão."
                    )
                else:
                    roteiro = (
                        f"Larry Ellison acabou de perder doze bilhões de dólares em apenas vinte e quatro horas com a queda da Oracle. "
                        "Mas para quem joga o jogo do longo prazo, a volatilidade não destrói quem tem visão estratégica. "
                        "O erro de novatos é entrar em pânico nos momentos de queda, enquanto os maiores investidores usam o caos a seu favor. "
                        "Se você quer dominar a sua mente e construir liberdade financeira real, inscreva-se na FERGIL e comente sua opinião abaixo!"
                    )'''

replacement_fergil = '''            except Exception as e_fer_gen:
                msg_fer_err = f"Bloqueio Editorial FERGIL: Falha ao gerar roteiro factual via IA ({e_fer_gen}). Proibido usar texto genérico ou modelo fixo."
                logger.error(msg_fer_err)
                TASKS[task_id]["status"] = f"Erro: {msg_fer_err}"
                autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
                return'''

if target_fergil_fallback in text:
    text = text.replace(target_fergil_fallback, replacement_fergil, 1)
    with open("app_render_studio.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: Fallback genérico do FERGIL extirpado!")
else:
    print("FAILED: target_fergil_fallback not found")
