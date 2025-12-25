/**
 * YouTube Video Downloader - Frontend
 * Gerencia a interface e comunicação com o backend
 */

// Estado da aplicação
const state = {
    currentVideo: null,
    selectedFormat: null,
    isDownloading: false
};

// Elementos DOM
const elements = {
    urlInput: document.getElementById('urlInput'),
    searchBtn: document.getElementById('searchBtn'),
    loadingState: document.getElementById('loadingState'),
    errorState: document.getElementById('errorState'),
    errorMessage: document.getElementById('errorMessage'),
    retryBtn: document.getElementById('retryBtn'),
    videoCard: document.getElementById('videoCard'),
    videoThumbnail: document.getElementById('videoThumbnail'),
    videoDuration: document.getElementById('videoDuration'),
    videoTitle: document.getElementById('videoTitle'),
    videoChannel: document.getElementById('videoChannel'),
    videoViews: document.getElementById('videoViews'),
    qualitySection: document.getElementById('qualitySection'),
    qualityGrid: document.getElementById('qualityGrid'),
    progressSection: document.getElementById('progressSection'),
    progressPercent: document.getElementById('progressPercent'),
    progressFill: document.getElementById('progressFill'),
    progressInfo: document.getElementById('progressInfo'),
    completeSection: document.getElementById('completeSection'),
    downloadFilename: document.getElementById('downloadFilename'),
    downloadLink: document.getElementById('downloadLink'),
    newDownloadBtn: document.getElementById('newDownloadBtn')
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    elements.urlInput.focus();
});

/**
 * Configura os event listeners
 */
function setupEventListeners() {
    // Botão de busca
    elements.searchBtn.addEventListener('click', handleSearch);
    
    // Enter no input
    elements.urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
    
    // Botão de tentar novamente
    elements.retryBtn.addEventListener('click', handleSearch);
    
    // Botão de novo download
    elements.newDownloadBtn.addEventListener('click', resetApp);
    
    // Detectar cole de URL
    elements.urlInput.addEventListener('paste', () => {
        setTimeout(() => {
            const url = elements.urlInput.value.trim();
            if (isValidYouTubeUrl(url)) {
                handleSearch();
            }
        }, 100);
    });
}

/**
 * Verifica se é uma URL válida do YouTube
 */
function isValidYouTubeUrl(url) {
    const patterns = [
        /^(https?:\/\/)?(www\.)?youtube\.com\/watch\?v=[\w-]+/,
        /^(https?:\/\/)?(www\.)?youtu\.be\/[\w-]+/,
        /^(https?:\/\/)?(www\.)?youtube\.com\/shorts\/[\w-]+/
    ];
    return patterns.some(pattern => pattern.test(url));
}

/**
 * Trata a busca de informações do vídeo
 */
async function handleSearch() {
    const url = elements.urlInput.value.trim();
    
    if (!url) {
        showError('Por favor, insira uma URL do YouTube');
        return;
    }
    
    if (!isValidYouTubeUrl(url)) {
        showError('URL inválida. Use um link do YouTube válido.');
        return;
    }
    
    // Mostrar loading
    hideAllSections();
    elements.loadingState.classList.remove('hidden');
    
    try {
        const response = await fetch('/api/info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Erro ao buscar informações');
        }
        
        state.currentVideo = { ...data, url };
        displayVideoInfo(data);
        
    } catch (error) {
        console.error('Erro:', error);
        showError(error.message);
    }
}

/**
 * Exibe informações do vídeo
 */
function displayVideoInfo(video) {
    hideAllSections();
    
    // Atualizar card do vídeo
    elements.videoThumbnail.src = video.thumbnail;
    elements.videoThumbnail.alt = video.title;
    elements.videoDuration.textContent = video.duration_str;
    elements.videoTitle.textContent = video.title;
    elements.videoChannel.textContent = video.channel;
    elements.videoViews.querySelector('span').textContent = formatViews(video.view_count);
    
    // Mostrar card
    elements.videoCard.classList.remove('hidden');
    
    // Renderizar opções de qualidade
    renderQualityOptions(video.formats);
    elements.qualitySection.classList.remove('hidden');
}

/**
 * Renderiza as opções de qualidade
 */
function renderQualityOptions(formats) {
    elements.qualityGrid.innerHTML = '';
    
    // Remover botões de download existentes
    const existingBtns = elements.qualitySection.querySelectorAll('.btn-download');
    existingBtns.forEach(btn => btn.remove());
    
    formats.forEach((format, index) => {
        const option = document.createElement('div');
        option.className = 'quality-option';
        
        // Adicionar classes especiais
        if (format.height >= 1080) option.classList.add('hd');
        if (format.height >= 2160) option.classList.add('uhd');
        if (format.audio_only) option.classList.add('audio-only');
        
        // Selecionar primeira opção por padrão
        if (index === 0) {
            option.classList.add('selected');
            state.selectedFormat = format;
        }
        
        option.innerHTML = `
            <div class="quality-label">${format.quality}</div>
            <div class="quality-size">${format.filesize_str}</div>
        `;
        
        option.addEventListener('click', () => selectQuality(option, format));
        elements.qualityGrid.appendChild(option);
    });
    
    // Adicionar botão de download
    const downloadBtn = document.createElement('button');
    downloadBtn.className = 'btn-download';
    downloadBtn.id = 'downloadBtn';
    downloadBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M7 10L12 15L17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Baixar Vídeo
    `;
    downloadBtn.addEventListener('click', handleDownload);
    elements.qualitySection.appendChild(downloadBtn);
}

/**
 * Seleciona uma qualidade
 */
function selectQuality(element, format) {
    // Remover seleção anterior
    document.querySelectorAll('.quality-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    
    // Adicionar nova seleção
    element.classList.add('selected');
    state.selectedFormat = format;
    
    // Atualizar texto do botão
    const btn = document.getElementById('downloadBtn');
    if (btn) {
        btn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 10L12 15L17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Baixar ${format.audio_only ? 'Áudio' : 'Vídeo'} (${format.quality})
        `;
    }
}

/**
 * Inicia o download
 */
async function handleDownload() {
    if (state.isDownloading || !state.currentVideo || !state.selectedFormat) {
        return;
    }
    
    state.isDownloading = true;
    const videoId = state.currentVideo.id;
    let progressInterval = null;
    
    // Mostrar progresso
    elements.videoCard.classList.add('hidden');
    elements.qualitySection.classList.add('hidden');
    elements.progressSection.classList.remove('hidden');
    
    updateProgress(0, 'Iniciando download...');
    
    // Iniciar polling de progresso
    progressInterval = setInterval(async () => {
        try {
            const progressResponse = await fetch(`/api/progress/${videoId}`);
            const progressData = await progressResponse.json();
            
            if (progressData.status === 'downloading') {
                const percent = progressData.percent || 0;
                const speed = progressData.speed ? formatSpeed(progressData.speed) : '';
                const eta = progressData.eta ? formatETA(progressData.eta) : '';
                
                let info = 'Baixando...';
                if (speed) info += ` | ${speed}`;
                if (eta) info += ` | ETA: ${eta}`;
                
                updateProgress(percent, info);
            } else if (progressData.status === 'finished') {
                updateProgress(100, 'Processando arquivo...');
            }
        } catch (e) {
            // Ignorar erros de polling
        }
    }, 500);
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: state.currentVideo.url,
                format_id: state.selectedFormat.format_id,
                quality: state.selectedFormat.quality,
                audio_only: state.selectedFormat.audio_only || false
            })
        });
        
        // Parar polling
        if (progressInterval) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Erro no download');
        }
        
        updateProgress(100, 'Download concluído!');
        
        // Mostrar tela de conclusão
        setTimeout(() => {
            showComplete(data.filename);
        }, 500);
        
    } catch (error) {
        // Parar polling em caso de erro
        if (progressInterval) {
            clearInterval(progressInterval);
        }
        console.error('Erro no download:', error);
        showError(error.message);
    } finally {
        state.isDownloading = false;
    }
}

/**
 * Formata velocidade de download
 */
function formatSpeed(bytesPerSec) {
    if (!bytesPerSec) return '';
    
    if (bytesPerSec >= 1024 * 1024) {
        return `${(bytesPerSec / (1024 * 1024)).toFixed(1)} MB/s`;
    }
    if (bytesPerSec >= 1024) {
        return `${(bytesPerSec / 1024).toFixed(1)} KB/s`;
    }
    return `${bytesPerSec.toFixed(0)} B/s`;
}

/**
 * Formata tempo restante
 */
function formatETA(seconds) {
    if (!seconds || seconds <= 0) return '';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    }
    if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    }
    return `${secs}s`;
}

/**
 * Atualiza a barra de progresso
 */
function updateProgress(percent, info) {
    elements.progressPercent.textContent = `${Math.round(percent)}%`;
    elements.progressFill.style.width = `${percent}%`;
    elements.progressInfo.textContent = info;
}

/**
 * Mostra tela de download concluído
 */
function showComplete(filename) {
    hideAllSections();
    
    elements.downloadFilename.textContent = filename;
    elements.downloadLink.href = `/api/file/${encodeURIComponent(filename)}`;
    elements.completeSection.classList.remove('hidden');
}

/**
 * Mostra mensagem de erro
 */
function showError(message) {
    hideAllSections();
    elements.errorMessage.textContent = message;
    elements.errorState.classList.remove('hidden');
}

/**
 * Esconde todas as seções de estado
 */
function hideAllSections() {
    elements.loadingState.classList.add('hidden');
    elements.errorState.classList.add('hidden');
    elements.videoCard.classList.add('hidden');
    elements.qualitySection.classList.add('hidden');
    elements.progressSection.classList.add('hidden');
    elements.completeSection.classList.add('hidden');
}

/**
 * Reseta a aplicação para novo download
 */
function resetApp() {
    state.currentVideo = null;
    state.selectedFormat = null;
    state.isDownloading = false;
    
    elements.urlInput.value = '';
    hideAllSections();
    elements.urlInput.focus();
}

/**
 * Formata número de visualizações
 */
function formatViews(views) {
    if (!views) return '0 visualizações';
    
    if (views >= 1000000000) {
        return `${(views / 1000000000).toFixed(1)}B visualizações`;
    }
    if (views >= 1000000) {
        return `${(views / 1000000).toFixed(1)}M visualizações`;
    }
    if (views >= 1000) {
        return `${(views / 1000).toFixed(1)}K visualizações`;
    }
    return `${views} visualizações`;
}

