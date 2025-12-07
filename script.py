import yt_dlp
import os
import sys
import winreg

def get_resource_path(relative_path):
    """Retorna o caminho correto do arquivo, mesmo quando empacotado"""
    try:
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

def detectar_plataforma(url):
    """Detecta se é YouTube, Instagram ou outra plataforma"""
    url_lower = url.lower()
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    else:
        return 'outro'

def download_video(url, caminho_destino=None):
    if not caminho_destino or caminho_destino.strip() == "":
        caminho_destino = get_download_path()
        print(f"Usando pasta Downloads: {caminho_destino}")
    
    if not os.path.exists(caminho_destino):
        os.makedirs(caminho_destino)
    
    # Detecta a plataforma
    plataforma = detectar_plataforma(url)
    print(f"Plataforma detectada: {plataforma.upper()}")
    
    # Configura o ffmpeg embutido
    ffmpeg_path = get_resource_path('ffmpeg.exe')
    
    # Configurações base
    ydl_opts = {
        'outtmpl': os.path.join(caminho_destino, '%(title)s.%(ext)s'),
        'ffmpeg_location': ffmpeg_path,
        'quiet': False,
    }
    
    # Configurações específicas por plataforma
    if plataforma == 'youtube':
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best'
        ydl_opts['merge_output_format'] = 'mp4'
    elif plataforma == 'instagram':
        ydl_opts['format'] = 'best'
    else:
        ydl_opts['format'] = 'best'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\nBaixando de: {url}")
            ydl.download([url])
            print("\n✓ Download concluído com sucesso!")
            return True
    except Exception as e:
        print(f"\n✗ Erro ao baixar: {e}")
        if plataforma == 'instagram' and 'login' in str(e).lower():
            print("\nDICA: Alguns conteúdos do Instagram podem precisar de login.")
            print("Tente abrir o link no navegador primeiro para confirmar que está acessível.")
        return False

def menu_principal():
    """Menu principal com loop para múltiplos downloads"""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')  # Limpa a tela
        print("=" * 50)
        print("  DOWNLOADER - YouTube & Instagram")
        print("=" * 50)
        print("\nSuporta:")
        print("  • Vídeos do YouTube")
        print("  • Reels do Instagram")
        print("  • Posts do Instagram")
        print("=" * 50)
        print()
        
        video_url = input("Cole a URL: ")
        caminho = input("Caminho (vazio = Downloads): ").strip()
        print()
        
        # Faz o download
        download_video(video_url, caminho)
        
        # Menu de opções após o download
        while True:
            print("\n" + "=" * 50)
            print("O que deseja fazer?")
            print("  [1] Baixar outro vídeo")
            print("  [2] Fechar programa")
            print("=" * 50)
            opcao = input("\nEscolha uma opção (1 ou 2): ").strip()
            
            if opcao == '1':
                break  # Sai do loop interno e volta ao menu principal
            elif opcao == '2':
                print("\nEncerrando... Até logo! 👋")
                sys.exit(0)  # Fecha o programa
            else:
                print("❌ Opção inválida! Digite 1 ou 2.")

if __name__ == "__main__":
    menu_principal()
