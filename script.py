import yt_dlp
import os
import sys
import winreg

def get_resource_path(relative_path):
    """Retorna o caminho correto do arquivo, mesmo quando empacotado"""
    try:
        # PyInstaller cria uma pasta temp e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_download_path():
    """Retorna o caminho da pasta Downloads padrão"""
    if os.name == 'nt':
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    return os.path.join(os.path.expanduser('~'), 'Downloads')

def download_youtube_video(url, caminho_destino=None):
    if not caminho_destino or caminho_destino.strip() == "":
        caminho_destino = get_download_path()
        print(f"Usando pasta Downloads: {caminho_destino}")
    
    if not os.path.exists(caminho_destino):
        os.makedirs(caminho_destino)
    
    # Configura o caminho do ffmpeg embutido
    ffmpeg_path = get_resource_path('ffmpeg.exe')
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        'outtmpl': os.path.join(caminho_destino, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'ffmpeg_location': ffmpeg_path,  # Usa o ffmpeg embutido
        'quiet': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Baixando: {url}")
            ydl.download([url])
            print("\nDownload concluído!")
            input("Pressione Enter para fechar...")
    except Exception as e:
        print(f"Erro: {e}")
        input("Pressione Enter para fechar...")

if __name__ == "__main__":
    print("=== YouTube Downloader ===\n")
    video_url = input("URL do vídeo: ")
    caminho = input("Caminho (vazio = Downloads): ").strip()
    download_youtube_video(video_url, caminho)
