// Agente de Rutas - Lógica Principal

// Configuración de la API
// Si se abre el HTML con file://, window.location.origin no es válido.
// Usamos localhost por defecto y permitimos override con ?api=http://host:puerto
const API_QUERY_OVERRIDE = new URLSearchParams(window.location.search).get('api');
const DEFAULT_API_BASE = 'http://localhost:8001';
const ORIGIN_IS_HTTP = window.location.protocol.startsWith('http');
const API_BASE_URL = (API_QUERY_OVERRIDE && API_QUERY_OVERRIDE.trim())
    || (ORIGIN_IS_HTTP ? window.location.origin : DEFAULT_API_BASE);
const API_ROUTE_ENDPOINT = `${API_BASE_URL.replace(/\/$/, '')}/api/route`;

// Referencias DOM
const elements = {
    form: document.getElementById('routeForm'),
    input: document.getElementById('routeInput'),
    submitBtn: document.getElementById('submitBtn'),
    loadingContainer: document.getElementById('loadingContainer'),
    errorContainer: document.getElementById('errorContainer'),
    errorMessage: document.getElementById('errorMessage'),
    resultsContainer: document.getElementById('resultsContainer'),
    originSpan: document.getElementById('origin'),
    totalDistance: document.getElementById('totalDistance'),
    totalTime: document.getElementById('totalTime'),
    destinationsCount: document.getElementById('destinationsCount'),
    locationList: document.getElementById('locationList'),
    stepsList: document.getElementById('stepsList'),
};

// Ejemplos de consultas
const examples = [
    "Estoy en Lima Centro, necesito ir a Miraflores, San Isidro y Barranco",
    "Hoy voy a hacer 3 entregas, una en calle Los Olivos 123, Barranco, otra en jiron Sucre 456, Magdalena y otra en Av. Larco 789, Miraflores",
    "Desde Callao, visitaré San Miguel, Pueblo Libre, Jesús María y volver a casa",
    "Ruta desde Surco: La Molina, Ate, Santa Anita y San Borja",
];

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    populateExamples();
});

function setupEventListeners() {
    elements.form.addEventListener('submit', handleSubmit);
}

function populateExamples() {
    const examplesList = document.getElementById('examplesList');
    examplesList.innerHTML = examples
        .map(example => `<li onclick="fillExample('${example.replace(/'/g, "\\'")}')">${example}</li>`)
        .join('');
}

function fillExample(text) {
    elements.input.value = text;
    elements.input.focus();
}

async function handleSubmit(e) {
    e.preventDefault();

    const query = elements.input.value.trim();
    if (!query) {
        showError('Por favor, ingresa una descripción de la ruta');
        return;
    }

    // Reset UI
    hideError();
    hideResults();
    showLoading();
    setButtonLoading(true);

    try {
        const response = await fetch(API_ROUTE_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Error al calcular la ruta');
        }

        displayResults(data);
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'No se pudo conectar con el servidor');
    } finally {
        hideLoading();
        setButtonLoading(false);
    }
}

function showLoading() {
    elements.loadingContainer.classList.remove('hidden');
}

function hideLoading() {
    elements.loadingContainer.classList.add('hidden');
}

function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorContainer.classList.remove('hidden');
    
        if (data.google_maps_url) {
            resultDiv.innerHTML += `<p><a href="${data.google_maps_url}" target="_blank" rel="noopener" class="gmaps-link">Ver ruta en Google Maps 🚗</a></p>`;
        }
    setTimeout(() => {
        hideError();
    }, 8000);
}

function hideError() {
    elements.errorContainer.classList.add('hidden');
}

function showResults() {
    elements.resultsContainer.classList.remove('hidden');
}

function hideResults() {
    elements.resultsContainer.classList.add('hidden');
}

function setButtonLoading(isLoading) {
    elements.submitBtn.disabled = isLoading;
    if (isLoading) {
        elements.submitBtn.classList.add('loading');
        elements.submitBtn.textContent = 'Calculando...';
    } else {
        elements.submitBtn.classList.remove('loading');
        elements.submitBtn.innerHTML = '🗺️ Calcular Ruta Óptima';
    }
}

function displayResults(data) {
    // Header
    elements.originSpan.textContent = data.origin;

    // Stats
    elements.totalDistance.textContent = data.total_distance_km.toFixed(1);
    elements.totalTime.textContent = formatMinutes(data.estimated_time_min);
    elements.destinationsCount.textContent = data.optimized_order.length - 1;

    // Locations
    elements.locationList.innerHTML = data.optimized_order
        .map((location, index) => `
            <div class="location-item">
                <div class="location-number">${index + 1}</div>
                <div class="location-name">${location}</div>
            </div>
        `)
        .join('');

    // Steps
    elements.stepsList.innerHTML = data.steps
        .map((step, index) => `
            <div class="step">
                <div class="step-icon">🚗</div>
                <div class="step-content">
                    <div class="step-title">
                        ${step.from} → ${step.to}
                    </div>
                    <div class="step-details">
                        <div class="step-detail">
                            <span>📏</span>
                            <span>${step.distance}</span>
                        </div>
                        <div class="step-detail">
                            <span>⏱️</span>
                            <span>${step.time}</span>
                        </div>
                    </div>
                </div>
            </div>
        `)
        .join('');

    showResults();
    
    // Mostrar botón/enlace a Google Maps en el div dedicado
    const gmapsDiv = document.getElementById('gmapsLink');
    if (gmapsDiv) {
        gmapsDiv.innerHTML = '';
        if (data.google_maps_url) {
            gmapsDiv.innerHTML = `<a href="${data.google_maps_url}" target="_blank" rel="noopener" class="btn-primary" style="display:inline-block;margin-top:20px;text-decoration:none;text-align:center;">🗺️ Ver ruta en Google Maps</a>`;
        }
    }
    
    // Scroll suave a resultados
    setTimeout(() => {
        elements.resultsContainer.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }, 100);
}

function formatMinutes(minutes) {
    if (minutes < 60) {
        return `${minutes} min`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins === 0 ? `${hours}h` : `${hours}h ${mins}min`;
}

// Manejo de errores globales
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    showError('Ocurrió un error inesperado. Por favor, intenta nuevamente.');
});
