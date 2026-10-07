import os
import shutil
import glob
from loguru import logger

def limpar_materiais_temporarios(manter_apenas_videos_finais=True):
    """
    Remove imagens temporárias, recortes, clipes intermediários e caches
    de renderização em 'storage/tasks/', preservando apenas os vídeos finais
    prontos em 'canais/canal_01_futebol_invisivel/videos_prontos/'.
    """
    logger.info("Iniciando limpeza de memória e arquivos temporários...")
    
    # 1. Pastas de materiais (fotos e clips temporários)
    materiais_dir = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos")
    if os.path.exists(materiais_dir):
        tamanho_liberado = 0
        for root, dirs, files in os.walk(materiais_dir):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    tamanho_liberado += os.path.getsize(fp)
                except Exception:
                    pass
        try:
            shutil.rmtree(materiais_dir)
            os.makedirs(materiais_dir, exist_ok=True)
            logger.success(f"Diretório de materiais temporários limpo! Espaço liberado: ~{tamanho_liberado / (1024*1024):.2f} MB")
        except Exception as e:
            logger.warning(f"Erro ao limpar materiais_fotos_videos: {e}")

    # 2. Pasta de tarefas intermediárias do MoneyPrinterTurbo (storage/tasks)
    storage_tasks = os.path.join("storage", "tasks")
    if os.path.exists(storage_tasks):
        tasks = glob.glob(os.path.join(storage_tasks, "*"))
        tasks_liberados = 0
        for task in tasks:
            try:
                shutil.rmtree(task)
                tasks_liberados += 1
            except Exception:
                pass
        logger.success(f"Limpeza de storage/tasks concluída: {tasks_liberados} tarefas intermediárias apagadas!")

    logger.success("Limpeza concluída! Apenas os vídeos finais em 'videos_prontos/' foram preservados.")

if __name__ == "__main__":
    limpar_materiais_temporarios()
