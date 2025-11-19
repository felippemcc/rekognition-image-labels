// Configuração da URL da API
// IMPORTANTE: Ajuste esta URL de acordo com seu backend
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';


// Elementos do DOM
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewSection = document.getElementById('previewSection');
const imagePreview = document.getElementById('imagePreview');
const removeBtn = document.getElementById('removeBtn');
const actionSection = document.getElementById('actionSection');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const labelsContainer = document.getElementById('labelsContainer');
const confidenceSlider = document.getElementById('confidenceSlider');
const confidenceValue = document.getElementById('confidenceValue');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');
const errorSection = document.getElementById('errorSection');
const errorText = document.getElementById('errorText');
const retryBtn = document.getElementById('retryBtn');

// Variável para armazenar o arquivo selecionado
let selectedFile = null;
let analysisResults = [];

// Event Listeners
uploadArea.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileSelect);
removeBtn.addEventListener('click', resetUpload);
analyzeBtn.addEventListener('click', analyzeImage);
newAnalysisBtn.addEventListener('click', resetUpload);
retryBtn.addEventListener('click', resetUpload);
confidenceSlider.addEventListener('input', updateConfidenceFilter);

// Drag and Drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

// Funções
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    // Validar tipo de arquivo
    if (!file.type.match('image/(jpeg|png)')) {
        showError('Por favor, selecione apenas arquivos JPG ou PNG.');
        return;
    }

    // Validar tamanho (5MB)
    if (file.size > 5 * 1024 * 1024) {
        showError('O arquivo deve ter no máximo 5MB.');
        return;
    }

    selectedFile = file;
    displayPreview(file);
}

function displayPreview(file) {
    const reader = new FileReader();
    
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        uploadArea.style.display = 'none';
        previewSection.style.display = 'block';
        actionSection.style.display = 'block';
        hideError();
    };
    
    reader.readAsDataURL(file);
}

function resetUpload() {
    selectedFile = null;
    fileInput.value = '';
    imagePreview.src = '';
    uploadArea.style.display = 'block';
    previewSection.style.display = 'none';
    actionSection.style.display = 'none';
    resultsSection.style.display = 'none';
    loadingSection.style.display = 'none';
    errorSection.style.display = 'none';
    confidenceSlider.value = 0;
    confidenceValue.textContent = '0%';
}

async function analyzeImage() {
    if (!selectedFile) {
        showError('Nenhuma imagem selecionada.');
        return;
    }

    // Mostrar loading
    actionSection.style.display = 'none';
    loadingSection.style.display = 'block';
    hideError();

    try {
        // Converter imagem para base64
        const base64Image = await fileToBase64(selectedFile);

        // Preparar payload JSON
        const payload = {
            image: base64Image,
            min_confidence: 80  // Você pode tornar isso configurável depois
        };

        // Fazer requisição para o backend
        const response = await fetch(`${API_URL}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao analisar a imagem');
        }

        const data = await response.json();
        
        // Verificar se a resposta foi bem-sucedida
        if (!data.success) {
            throw new Error(data.error || 'Erro ao processar a imagem');
        }

        analysisResults = data.labels || [];

        // Exibir resultados
        displayResults(analysisResults);

    } catch (error) {
        console.error('Erro:', error);
        showError(error.message || 'Erro ao conectar com o servidor. Verifique se o backend está rodando.');
        loadingSection.style.display = 'none';
        actionSection.style.display = 'block';
    }
}

// Função auxiliar para converter arquivo para base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
        reader.readAsDataURL(file);
    });
}

function displayResults(labels) {
    loadingSection.style.display = 'none';
    resultsSection.style.display = 'block';

    // Ordenar labels por confiança (maior para menor)
    // Suporta ambos os formatos: Confidence e confidence
    const sortedLabels = labels.sort((a, b) => {
        const confA = a.Confidence || a.confidence;
        const confB = b.Confidence || b.confidence;
        return confB - confA;
    });

    // Renderizar labels
    renderLabels(sortedLabels);
}

function renderLabels(labels) {
    labelsContainer.innerHTML = '';

    if (labels.length === 0) {
        labelsContainer.innerHTML = '<p style="text-align: center; color: var(--text-light); grid-column: 1 / -1;">Nenhum resultado encontrado com este nível de confiança.</p>';
        return;
    }

    labels.forEach((label, index) => {
        const card = createLabelCard(label, index);
        labelsContainer.appendChild(card);
    });
}

function createLabelCard(label, index) {
    const card = document.createElement('div');
    card.className = 'label-card';
    card.style.animationDelay = `${index * 0.05}s`;

    const name = document.createElement('div');
    name.className = 'label-name';
    name.textContent = label.Name || label.name;

    const confidenceContainer = document.createElement('div');
    confidenceContainer.className = 'label-confidence';

    const confidenceBar = document.createElement('div');
    confidenceBar.className = 'confidence-bar';

    const confidenceFill = document.createElement('div');
    confidenceFill.className = 'confidence-fill';
    const confidenceValue = label.Confidence || label.confidence;
    confidenceFill.style.width = `${confidenceValue}%`;

    const confidenceText = document.createElement('span');
    confidenceText.className = 'confidence-text';
    confidenceText.textContent = `${confidenceValue.toFixed(1)}%`;

    confidenceBar.appendChild(confidenceFill);
    confidenceContainer.appendChild(confidenceBar);
    confidenceContainer.appendChild(confidenceText);

    card.appendChild(name);
    card.appendChild(confidenceContainer);

    return card;
}

function updateConfidenceFilter() {
    const minConfidence = parseInt(confidenceSlider.value);
    confidenceValue.textContent = `${minConfidence}%`;

    // Filtrar labels (suporta ambos os formatos: Confidence e confidence)
    const filteredLabels = analysisResults.filter(label => {
        const conf = label.Confidence || label.confidence;
        return conf >= minConfidence;
    });
    renderLabels(filteredLabels);
}

function showError(message) {
    errorText.textContent = message;
    errorSection.style.display = 'block';
}

function hideError() {
    errorSection.style.display = 'none';
}

// Mensagem no console
console.log('🚀 Frontend AWS Rekognition inicializado!');
console.log('📡 API URL:', API_URL);