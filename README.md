# 🎬 YouTube Video Downloader

Sistema web para download de vídeos do YouTube com seleção de qualidade.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red)

## ✨ Funcionalidades

- 📥 Download de vídeos do YouTube
- 🎯 Seleção de qualidade (360p até 4K)
- 🎵 Opção de download apenas do áudio (MP3)
- 📊 Exibe informações do vídeo antes do download
- 🎨 Interface moderna e responsiva
- 🔄 Suporta links normais, shorts e youtu.be

## 📋 Pré-requisitos

- **Python 3.10+**
- **FFmpeg** (necessário para mesclar vídeo + áudio em alta qualidade)

### Instalando FFmpeg no Windows

1. Baixe o FFmpeg: https://www.gyan.dev/ffmpeg/builds/
2. Extraia para `C:\ffmpeg`
3. Adicione `C:\ffmpeg\bin` ao PATH do sistema

Ou via winget:
```powershell
winget install FFmpeg
```

Ou via Chocolatey:
```powershell
choco install ffmpeg
```

## 🚀 Instalação

1. **Clone o repositório:**
```powershell
git clone https://github.com/Lorugo01/download-video.git
cd download-video
```

2. **Crie um ambiente virtual (recomendado):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. **Instale as dependências:**
```powershell
pip install -r requirements.txt
```

## ▶️ Executando

```powershell
python app.py
```

Acesse: **http://localhost:5000**

## 📁 Estrutura do Projeto

```
download-video/
├── app.py              # Backend Flask
├── requirements.txt    # Dependências Python
├── README.md           # Este arquivo
├── .gitignore          # Arquivos ignorados pelo Git
├── downloads/          # Pasta de downloads (criada automaticamente, ignorada pelo Git)
├── templates/
│   └── index.html      # Template HTML
└── static/
    ├── css/
    │   └── style.css   # Estilos CSS
    └── js/
        └── app.js      # JavaScript frontend
```

> **Nota:** A pasta `downloads/` é criada automaticamente na primeira execução e está configurada no `.gitignore` para não ser versionada no repositório.

## 🔧 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Página principal |
| POST | `/api/info` | Obtém informações do vídeo |
| POST | `/api/download` | Inicia download do vídeo |
| GET | `/api/progress/<id>` | Status do progresso |
| GET | `/api/file/<filename>` | Serve arquivo para download |
| POST | `/api/cleanup` | Limpa arquivos temporários |

## 📝 Exemplo de Uso

1. Abra o navegador em `http://localhost:5000`
2. Cole o link do YouTube
3. Aguarde carregar as informações
4. Escolha a qualidade desejada
5. Clique em "Baixar Vídeo"
6. Salve o arquivo quando concluir

## ⚠️ Observações

- Downloads de vídeos em alta qualidade (1080p+) requerem FFmpeg
- O yt-dlp baixa separadamente vídeo e áudio e depois mescla
- Vídeos protegidos por DRM não podem ser baixados
- Use apenas para conteúdo que você tem permissão para baixar

## 🛠️ Tecnologias

- **Backend:** Python, Flask, yt-dlp
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Design:** Tema escuro com acentos em coral/laranja

## 📄 Licença

Este projeto é apenas para fins educacionais. Respeite os termos de serviço do YouTube.

