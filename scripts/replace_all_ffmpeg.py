import shutil
import os

src = r"C:\Users\Uni-CvFCT-EdmilsonGi\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"

destinos = [
    r"C:\Users\Uni-CvFCT-EdmilsonGi\AppData\Roaming\Python\Python312\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe",
    r"C:\Users\Uni-CvFCT-EdmilsonGi\Documents\projectoD\money\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
]

for d in destinos:
    if os.path.exists(os.path.dirname(d)):
        shutil.copy2(src, d)
        print(f"Copiado com sucesso para: {d}")

print("TODAS AS CÓPIAS DO FFMPEG CORROMPIDO FORAM SUBSTITUÍDAS!")
