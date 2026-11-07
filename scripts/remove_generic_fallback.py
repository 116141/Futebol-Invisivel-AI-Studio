with open("app_render_studio.py", "r", encoding="utf-8") as f:
    text = f.read()

# Substituir os fallbacks genéricos de futebol por uma exceção estrita que aborta se não houver fatos reais
target_block = '''                    else:
                        raise ValueError("Resposta da IA vazia ou com erro de API.")
                except Exception as e_gen:
                    logger.warning(f"LLM falhou ou sem cota ({e_gen}). Acionando gerador estruturado...")
                    if is_doc:
                        roteiro = pegada_escolhida.get("fallback_doc", f"Documentário investigativo exclusivo sobre {titulo}.")
                    else:
                        palavras_t = [p for p in titulo.split() if len(p) > 3]
                        assunto = " ".join(palavras_t[:3]) if palavras_t else "esse episódio"
                        # Fallback dinâmico alternado baseado na pegada para nunca ficar com a mesma frase
                        if "ESCÂNDALO" in estilo_nome_usado:
                            roteiro = f"Milhões em jogo e um acordo secreto que ninguém podia imaginar sobre {assunto}! Uma cláusula confidencial vazou e abalou as estruturas do clube. Enquanto a diretoria tenta abafar o caso, os números reais vieram à tona. Você concorda com essa decisão? Comente no Futebol Invisível!"
                        elif "TRAIÇÃO" in estilo_nome_usado:
                            roteiro = f"O clima ferveu nos bastidores e o elenco rachou por causa de {assunto}! Discussões acaloradas que a transmissão escondeu expuseram uma guerra de egos insustentável. As consequências prometem mudar todo o rumo da temporada. De que lado você fica? Diga nos comentários do Futebol Invisível!"
                        else:
                            roteiro = f"A reviravolta histórica envolvendo {assunto} chocou o mundo do futebol! Quando todos duvidavam da capacidade de resposta, os fatos comprovaram o peso da camisa e a superação em campo. Você esperava por esse desfecho? Deixe sua opinião no Futebol Invisível!"'''

new_block = '''                    else:
                        raise ValueError("Resposta da IA vazia, com erro de API ou sem dados factuais suficientes.")
                except Exception as e_gen:
                    msg_bloqueio_factual = f"Bloqueio Editorial Estrito: Falha ao gerar roteiro factual autêntico via IA ({e_gen}). Proibido usar roteiros genéricos ou inventados."
                    logger.error(msg_bloqueio_factual)
                    TASKS[task_id]["status"] = f"Erro: {msg_bloqueio_factual}"
                    autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
                    return'''

if target_block in text:
    text = text.replace(target_block, new_block, 1)
    with open("app_render_studio.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: Fallback genérico de futebol extirpado!")
else:
    print("FAILED: target_block not found in app_render_studio.py")
