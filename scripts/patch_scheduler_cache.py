def patch_scheduler_cache():
    with open('app/services/video_scheduler.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '''def auditar_esteira_e_maturacao(canal: str = "futebol") -> Dict:'''
    replacement = '''def auditar_esteira_e_maturacao(canal: str = "futebol", force_refresh: bool = False) -> Dict:
    import time
    now_ts = time.time()
    if not hasattr(auditar_esteira_e_maturacao, '_cache'):
        auditar_esteira_e_maturacao._cache = {}
        auditar_esteira_e_maturacao._cache_ts = {}
        
    # Se ja temos em cache ha menos de 45 minutos e nao foi forcado, retorna cache para economizar cota da API
    if not force_refresh and canal in auditar_esteira_e_maturacao._cache:
        if now_ts - auditar_esteira_e_maturacao._cache_ts.get(canal, 0) < 2700:
            return auditar_esteira_e_maturacao._cache[canal]'''

    text_norm = text.replace('\r\n', '\n')
    target_norm = target.replace('\r\n', '\n')
    replacement_norm = replacement.replace('\r\n', '\n')

    if target_norm in text_norm:
        res = text_norm.replace(target_norm, replacement_norm, 1)
        
        # Salvar resultado no cache antes do return
        target_ret = '        return resultado\n\n    except Exception as e:'
        replacement_ret = '''        auditar_esteira_e_maturacao._cache[canal] = resultado
        auditar_esteira_e_maturacao._cache_ts[canal] = time.time()
        return resultado

    except Exception as e:'''
        target_ret_norm = target_ret.replace('\r\n', '\n')
        replacement_ret_norm = replacement_ret.replace('\r\n', '\n')
        res = res.replace(target_ret_norm, replacement_ret_norm, 1)

        with open('app/services/video_scheduler.py', 'w', encoding='utf-8', newline='') as f:
            f.write(res.replace('\n', '\r\n'))
        print("Sucesso: video_scheduler otimizado com cache de esteira de 45 minutos!")
    else:
        print("Target nao encontrado em video_scheduler")

if __name__ == '__main__':
    patch_scheduler_cache()
