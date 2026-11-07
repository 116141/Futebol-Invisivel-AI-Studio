import os

with open("app_render_studio.py", "r", encoding="utf-8") as f:
    text = f.read()

endpoint_code = '''
@app.get("/api/relatorio/acao_proprietario")
async def api_relatorio_acao_proprietario(request: Request, despachar_telegram: bool = False):
    """
    Endpoint para consulta e despacho do Relatório '🚨 AÇÃO DO PROPRIETÁRIO'.
    Retorna o JSON estruturado e o texto formatado para visualização imediata.
    """
    verificar_acesso_autorizado(request)
    from app.services import owner_action_report
    dados = owner_action_report.coletar_dados_acao_proprietario()
    texto = owner_action_report.formatar_relatorio_acao_proprietario()
    
    despachado = False
    if despachar_telegram:
        despachado = owner_action_report.disparar_relatorio_acao_proprietario()

    return {
        "status": "sucesso",
        "tem_acao_obrigatoria": dados["tem_acao_obrigatoria"],
        "despachado_telegram": despachado,
        "texto_formatado": texto,
        "dados": dados
    }
'''

target = "    return api_upload_video_youtube(task_id=task_id, privacy=privacy)\n"

if target in text:
    text = text.replace(target, target + endpoint_code, 1)
    with open("app_render_studio.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: endpoint adicionado ao app_render_studio.py!")
else:
    print("FAILED: target não encontrado")
