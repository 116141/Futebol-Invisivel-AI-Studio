import os
import sys
import time
import webbrowser
import subprocess

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)
    
    print("=" * 60)
    print("      AI STUDIO - FUTEBOL & ALANA CRUZ MODA")
    print("=" * 60)
    print("\nIniciando servidor local em http://127.0.0.1:8505 ...")
    
    # Abre navegador automaticamente após 1.5s
    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:8505")
        
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Executa o studio diretamente pelo python do venv
    python_exe = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
    app_script = os.path.join(root_dir, "app_render_studio.py")
    
    if os.path.exists(python_exe) and os.path.exists(app_script):
        subprocess.run([python_exe, app_script])
    else:
        # Fallback para ambiente compilado ou python padrão
        import uvicorn
        from app_render_studio import app
        uvicorn.run(app, host="127.0.0.1", port=8505)

if __name__ == "__main__":
    main()
