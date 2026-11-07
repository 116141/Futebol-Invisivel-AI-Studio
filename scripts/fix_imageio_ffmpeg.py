import shutil
import os

src = r"C:\Users\Uni-CvFCT-EdmilsonGi\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
dest = r"C:\Users\Uni-CvFCT-EdmilsonGi\Documents\projectoD\money\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

print("Origem existe:", os.path.exists(src))
print("Destino existe:", os.path.exists(dest))

shutil.copy2(src, dest)
print("SUCCESS: Binário FFmpeg substituído com perfeição!")
