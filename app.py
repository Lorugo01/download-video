"""
YouTube Video Downloader - Backend
Utiliza Flask + yt-dlp para download de vídeos
Python 3.10+ | Flask 3.0.0 | yt-dlp 2024.12.13
"""

import os
import re
import json
import threading
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# Diretório para downloads temporários
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Cache de progresso de downloads
download_progress = {}


def get_ydl_opts_base():
    """
    Retorna configurações base do yt-dlp para melhor compatibilidade.
    Configuração simplificada que funciona sem autenticação.
    Suprime warnings conhecidos que não afetam a funcionalidade.
    """
    return {
        'quiet': True,
        'no_warnings': True,  # Suprime warnings (JS runtime, SABR streaming, etc.)
        'ignoreerrors': False,
        # Não especificar player_client - deixar yt-dlp escolher automaticamente
        # Isso geralmente funciona melhor com as atualizações do YouTube
    }


def sanitize_filename(filename: str) -> str:
    """
    Remove caracteres inválidos do nome do arquivo para Windows.
    Remove também caracteres de controle e limita o tamanho.
    """
    if not filename:
        return 'video'
    
    # Remover caracteres inválidos do Windows
    # Windows não permite: < > : " / \ | ? * e caracteres de controle (0-31)
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(invalid_chars, '_', filename)
    
    # Remover espaços múltiplos e espaços no início/fim
    filename = re.sub(r'\s+', ' ', filename).strip()
    
    # Remover pontos no final (Windows não permite)
    filename = filename.rstrip('. ')
    
    # Limitar tamanho (Windows tem limite de 260 caracteres para caminhos completos)
    # Deixar espaço para extensão e caminho
    max_length = 200
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip()
    
    # Se ficou vazio após sanitização, usar nome padrão
    if not filename:
        filename = 'video'
    
    return filename


def progress_hook(d):
    """Hook para capturar progresso do download."""
    if d['status'] == 'downloading':
        video_id = d.get('info_dict', {}).get('id', 'unknown')
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        
        if total > 0:
            percent = (downloaded / total) * 100
            download_progress[video_id] = {
                'status': 'downloading',
                'percent': round(percent, 1),
                'speed': d.get('speed', 0),
                'eta': d.get('eta', 0)
            }
    elif d['status'] == 'finished':
        video_id = d.get('info_dict', {}).get('id', 'unknown')
        download_progress[video_id] = {
            'status': 'finished',
            'percent': 100
        }


@app.route('/')
def index():
    """Página principal."""
    return render_template('index.html')


@app.route('/api/info', methods=['POST'])
def get_video_info():
    """
    Obtém informações do vídeo e formatos disponíveis.
    
    Request Body:
        url (str): URL do vídeo do YouTube
    
    Returns:
        JSON com título, thumbnail, duração e formatos disponíveis
    """
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL não fornecida'}), 400
        
        # Configuração do yt-dlp para extrair informações
        ydl_opts = get_ydl_opts_base()
        ydl_opts['extract_flat'] = False
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        # Processar formatos disponíveis
        # Agrupar por altura e pegar o melhor de cada qualidade
        formats_by_height = {}
        
        for f in info.get('formats', []):
            # Filtrar apenas formatos com vídeo
            if f.get('vcodec') == 'none':
                continue
            
            height = f.get('height')
            if not height:
                continue
            
            format_id = f.get('format_id')
            ext = f.get('ext', 'mp4')
            filesize = f.get('filesize') or f.get('filesize_approx', 0)
            vbr = f.get('vbr') or f.get('tbr') or 0  # Video bitrate
            
            # Guardar o formato com maior bitrate/tamanho para cada altura
            if height not in formats_by_height:
                formats_by_height[height] = {
                    'format_id': format_id,
                    'quality': f"{height}p",
                    'height': height,
                    'ext': ext,
                    'filesize': filesize,
                    'filesize_str': format_size(filesize) if filesize else 'Tamanho desconhecido',
                    'has_audio': f.get('acodec') != 'none',
                    'vbr': vbr
                }
            else:
                # Substituir se tiver maior bitrate ou tamanho
                existing = formats_by_height[height]
                if vbr > existing.get('vbr', 0) or (filesize > existing.get('filesize', 0) and vbr >= existing.get('vbr', 0)):
                    formats_by_height[height] = {
                        'format_id': format_id,
                        'quality': f"{height}p",
                        'height': height,
                        'ext': ext,
                        'filesize': filesize,
                        'filesize_str': format_size(filesize) if filesize else 'Tamanho desconhecido',
                        'has_audio': f.get('acodec') != 'none',
                        'vbr': vbr
                    }
        
        # Converter para lista e ordenar por qualidade (maior primeiro)
        formats = list(formats_by_height.values())
        formats.sort(key=lambda x: x['height'], reverse=True)
        
        # Selecionar qualidades comuns disponíveis
        final_formats = []
        target_heights = [2160, 1440, 1080, 720, 480, 360, 240]
        
        for target in target_heights:
            for f in formats:
                if f['height'] == target:
                    # Remover campo vbr interno antes de retornar
                    fmt = {k: v for k, v in f.items() if k != 'vbr'}
                    final_formats.append(fmt)
                    break
        
        # Adicionar opção de apenas áudio
        final_formats.append({
            'format_id': 'bestaudio',
            'quality': 'Apenas Áudio',
            'height': 0,
            'ext': 'mp3',
            'filesize': 0,
            'filesize_str': 'MP3',
            'has_audio': True,
            'audio_only': True
        })
        
        result = {
            'id': info.get('id'),
            'title': info.get('title'),
            'thumbnail': info.get('thumbnail'),
            'duration': info.get('duration'),
            'duration_str': format_duration(info.get('duration', 0)),
            'channel': info.get('channel') or info.get('uploader'),
            'view_count': info.get('view_count', 0),
            'formats': final_formats
        }
        
        return jsonify(result)
    
    except yt_dlp.DownloadError as e:
        return jsonify({'error': f'Erro ao obter informações: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


@app.route('/api/download', methods=['POST'])
def download_video():
    """
    Inicia o download do vídeo com a qualidade selecionada.
    
    Request Body:
        url (str): URL do vídeo
        format_id (str): ID do formato escolhido
        quality (str): Label da qualidade (ex: 1080p)
    
    Returns:
        JSON com status do download
    """
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        format_id = data.get('format_id')
        quality = data.get('quality', 'best')
        
        if not url:
            return jsonify({'error': 'URL não fornecida'}), 400
        
        # Determinar formato de saída
        is_audio_only = data.get('audio_only', False)
        
        # Configuração base
        ydl_opts = get_ydl_opts_base()
        ydl_opts['progress_hooks'] = [progress_hook]
        
        if is_audio_only:
            # Configuração para apenas áudio (MP3)
            ydl_opts.update({
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
            })
        else:
            # Configuração para vídeo
            # Usar formato que combina melhor vídeo + áudio
            format_str = f'bestvideo[height<={quality.replace("p", "")}]+bestaudio/best[height<={quality.replace("p", "")}]/best'
            
            ydl_opts.update({
                'format': format_str,
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s_%(height)sp.%(ext)s'),
                'merge_output_format': 'mp4',
            })
        
        # Extrair informações primeiro para obter o nome do arquivo
        info_opts = get_ydl_opts_base()
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id')
            title = sanitize_filename(info.get('title', 'video'))
        
        download_progress[video_id] = {'status': 'starting', 'percent': 0}
        
        # Garantir que o título não seja muito longo para o caminho completo
        # Windows tem limite de ~260 caracteres para caminhos
        max_title_length = 150  # Deixar espaço para caminho, extensão e sufixos
        if len(title) > max_title_length:
            title = title[:max_title_length].rstrip()
        
        # Atualizar template de saída com título sanitizado
        if is_audio_only:
            ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, f'{title}.%(ext)s')
        else:
            ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, f'{title}_%(height)sp.%(ext)s')
        
        # Verificar se o caminho completo não é muito longo
        test_path = ydl_opts['outtmpl'].replace('%(ext)s', 'mp4').replace('%(height)s', '1080')
        if len(test_path) > 250:
            # Se ainda for muito longo, encurtar mais o título
            remaining = 250 - len(DOWNLOAD_DIR) - 20  # 20 para extensão e sufixos
            title = title[:remaining].rstrip() if remaining > 0 else 'video'
            if is_audio_only:
                ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, f'{title}.%(ext)s')
            else:
                ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, f'{title}_%(height)sp.%(ext)s')
        
        # Realizar download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Encontrar arquivo baixado
        downloaded_file = None
        for f in os.listdir(DOWNLOAD_DIR):
            if title[:30] in f:  # Comparar início do título
                downloaded_file = os.path.join(DOWNLOAD_DIR, f)
                break
        
        if downloaded_file and os.path.exists(downloaded_file):
            return jsonify({
                'success': True,
                'video_id': video_id,
                'filename': os.path.basename(downloaded_file),
                'message': 'Download concluído!'
            })
        else:
            return jsonify({'error': 'Arquivo não encontrado após download'}), 500
    
    except yt_dlp.DownloadError as e:
        error_msg = str(e)
        # Tratar erros específicos de arquivo inválido
        if 'Invalid argument' in error_msg or 'Errno 22' in error_msg:
            return jsonify({
                'error': 'Erro ao salvar arquivo: nome do arquivo inválido. Tente novamente ou escolha outro vídeo.'
            }), 400
        return jsonify({'error': f'Erro no download: {error_msg}'}), 400
    except OSError as e:
        # Erros do sistema operacional (arquivo inválido, permissões, etc)
        if e.errno == 22:  # Invalid argument
            return jsonify({
                'error': 'Erro ao salvar arquivo: nome do arquivo contém caracteres inválidos. Tente novamente.'
            }), 400
        return jsonify({'error': f'Erro do sistema: {str(e)}'}), 500
    except Exception as e:
        error_msg = str(e)
        # Capturar outros erros relacionados a arquivos
        if 'Invalid argument' in error_msg or 'Errno 22' in error_msg:
            return jsonify({
                'error': 'Erro ao salvar arquivo: nome inválido. Tente novamente.'
            }), 400
        return jsonify({'error': f'Erro interno: {error_msg}'}), 500


@app.route('/api/progress/<video_id>')
def get_progress(video_id):
    """Retorna o progresso do download."""
    progress = download_progress.get(video_id, {'status': 'unknown', 'percent': 0})
    return jsonify(progress)


@app.route('/api/file/<filename>')
def serve_file(filename):
    """Serve o arquivo para download pelo navegador."""
    try:
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if os.path.exists(filepath):
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename
            )
        return jsonify({'error': 'Arquivo não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cleanup', methods=['POST'])
def cleanup_files():
    """Remove arquivos antigos do diretório de downloads."""
    try:
        count = 0
        for f in os.listdir(DOWNLOAD_DIR):
            filepath = os.path.join(DOWNLOAD_DIR, f)
            if os.path.isfile(filepath):
                os.remove(filepath)
                count += 1
        return jsonify({'message': f'{count} arquivos removidos'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def format_size(bytes_size: int) -> str:
    """Formata tamanho em bytes para string legível."""
    if bytes_size == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB']
    unit_index = 0
    size = float(bytes_size)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: int) -> str:
    """Formata duração em segundos para HH:MM:SS."""
    if not seconds:
        return "00:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


if __name__ == '__main__':
    print("\n" + "="*50)
    print(" YouTube Video Downloader")
    print("="*50)
    print(f" Downloads salvos em: {DOWNLOAD_DIR}")
    print(" Acesse: http://localhost:5000")
    print("="*50 + "\n")
    
    # threaded=True permite processar polling de progresso durante downloads
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)

