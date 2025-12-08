import yt_dlp
import os
import sys
import winreg
import subprocess
import json

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

def get_video_duration(video_path, ffmpeg_path):
    """Obtém a duração do vídeo em segundos"""
    try:
        ffprobe_path = ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe')
        cmd = [
            ffprobe_path,
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except Exception as e:
        print(f"Erro ao obter duração: {e}")
        return None

def compress_video(input_path, output_path, ffmpeg_path, target_size_mb=100):
    """Comprime o vídeo para o tamanho alvo especificado"""
    print(f"\n🔄 Comprimindo vídeo para {target_size_mb}MB...")
    
    # Obtém a duração do vídeo
    duration = get_video_duration(input_path, ffmpeg_path)
    if not duration:
        print("❌ Não foi possível obter a duração do vídeo.")
        return False
    
    print(f"   Duração: {int(duration//60)}min {int(duration%60)}s")
    
    # Calcula o bitrate necessário
    # Fórmula: Bitrate (kbit/s) = (Tamanho em MB × 8192) / Duração em segundos
    # Subtraímos espaço para áudio (128 kbps)
    target_size_kb = target_size_mb * 1024
    audio_bitrate = 128  # kbps
    video_bitrate = int((target_size_kb * 8) / duration) - audio_bitrate
    
    if video_bitrate < 100:
        print(f"⚠️  Vídeo muito longo! Bitrate calculado muito baixo ({video_bitrate}kbps).")
        print("   A qualidade pode ficar muito ruim. Deseja continuar? (S/N): ", end='')
        if input().strip().upper() != 'S':
            return False
    
    print(f"   Bitrate calculado: {video_bitrate}kbps")
    
    # Comando ffmpeg para comprimir
    cmd = [
        ffmpeg_path,
        '-i', input_path,
        '-c:v', 'libx264',
        '-b:v', f'{video_bitrate}k',
        '-b:a', f'{audio_bitrate}k',
        '-vf', 'scale=-2:min(ih\\,720)',  # Limita altura a 720p mantendo proporção
        '-preset', 'medium',
        '-y',  # Sobrescreve se existir
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True)
        
        # Verifica o tamanho final
        final_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✓ Vídeo comprimido com sucesso!")
        print(f"   Tamanho final: {final_size_mb:.2f}MB")
        
        # Remove o arquivo original
        os.remove(input_path)
        print(f"   Arquivo original removido.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao comprimir: {e}")
        return False

def download_video(url, caminho_destino=None, comprimir=False):
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
            
            # Obtém informações e baixa
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            
            print("\n✓ Download concluído com sucesso!")
            
            # Se o usuário quer comprimir
            if comprimir:
                # Verifica o tamanho atual
                current_size_mb = os.path.getsize(video_path) / (1024 * 1024)
                print(f"\nTamanho atual: {current_size_mb:.2f}MB")
                
                if current_size_mb <= 100:
                    print("✓ Vídeo já está abaixo de 100MB! Compressão não necessária.")
                else:
                    # Cria nome para arquivo comprimido
                    base, ext = os.path.splitext(video_path)
                    compressed_path = f"{base}_compressed{ext}"
                    
                    # Comprime
                    if compress_video(video_path, compressed_path, ffmpeg_path, 100):
                        # Renomeia o comprimido para o nome original
                        os.rename(compressed_path, video_path)
            
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
        os.system('cls' if os.name == 'nt' else 'clear')
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
        
        # Pergunta se quer comprimir
        print("\nDeseja comprimir o vídeo para no máximo 100MB? (S/N): ", end='')
        comprimir = input().strip().upper() == 'S'
        
        print()
        
        # Faz o download
        download_video(video_url, caminho, comprimir)
        
        # Menu de opções após o download
        while True:
            print("\n" + "=" * 50)
            print("O que deseja fazer?")
            print("  [1] Baixar outro vídeo")
            print("  [2] Fechar programa")
            print("=" * 50)
            opcao = input("\nEscolha uma opção (1 ou 2): ").strip()
            
            if opcao == '1':
                break
            elif opcao == '2':
                print("\nEncerrando... Até logo! 👋")
                sys.exit(0)
            else:
                print("❌ Opção inválida! Digite 1 ou 2.")

if __name__ == "__main__":
    menu_principal()
