// app.js - Controlador principal del frontend de SoyaLens
import { SoyaLensAPI } from './api.js';

// Elementos del DOM
const tabs = document.querySelectorAll('.tab-link');
const tabContents = document.querySelectorAll('.tab-content');
const btnModeMock = document.getElementById('btn-mode-mock');
const btnModeReal = document.getElementById('btn-mode-real');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');

// Formulario de análisis y subida
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const dropZoneInfo = document.getElementById('drop-zone-info');
const imagePreviewContainer = document.getElementById('image-preview-container');
const imagePreview = document.getElementById('image-preview');
const inputLotId = document.getElementById('input-lot-id');
const inputSupplier = document.getElementById('input-supplier');
const btnSubmitAnalysis = document.getElementById('btn-submit-analysis');
const analyzeForm = document.getElementById('analyze-form');

// Certificado
const navBtnCertificate = document.getElementById('nav-btn-certificate');
const certSampleId = document.getElementById('cert-sample-id');
const certTimestamp = document.getElementById('cert-timestamp');
const certVerdictBadge = document.getElementById('cert-verdict-badge');
const certDiscountTicker = document.getElementById('cert-discount-ticker');
const certDiscountVal = document.getElementById('cert-discount-val');
const certCanvas = document.getElementById('cert-canvas');  // Canvas para imagen + bboxes
const certLotId = document.getElementById('cert-lot-id');
const certSupplier = document.getElementById('cert-supplier');
const certTotalGrains = document.getElementById('cert-total-grains');
const certNorm = document.getElementById('cert-norm');
const certJustification = document.getElementById('cert-justification');
const pctSanoLbl = document.getElementById('pct-sano-lbl');
const pctPartidoLbl = document.getElementById('pct-partido-lbl');
const pctDanadoLbl = document.getElementById('pct-danado-lbl');
const pctInmaduroLbl = document.getElementById('pct-inmaduro-lbl');
const btnPrintCert = document.getElementById('btn-print-cert');
const btnNewAnalysis = document.getElementById('btn-new-analysis');

// Dashboard
const kpiTotalVal = document.getElementById('kpi-total-val');
const kpiApprovedVal = document.getElementById('kpi-approved-val');
const kpiDiscountVal = document.getElementById('kpi-discount-val');
const kpiRejectedVal = document.getElementById('kpi-rejected-val');
const tableSearch = document.getElementById('table-search');
const tableFilter = document.getElementById('table-filter');
const dashboardTableBody = document.getElementById('dashboard-table-body');
const toastContainer = document.getElementById('toast-container');

// Estado local en memoria de la UI
let selectedFile = null;
let currentCertificate = null;
let donutChartInstance = null;
let healthCheckInterval = null;
let loadedSamples = []; // Caché local para filtrado rápido

// 1. GESTIÓN DE NOTIFICACIONES (TOASTS)
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    if (type === 'error') {
        toast.style.borderLeftColor = 'var(--color-rechazado)';
    } else if (type === 'success') {
        toast.style.borderLeftColor = 'var(--color-sano)';
    } else if (type === 'warning') {
        toast.style.borderLeftColor = 'var(--color-partido)';
    }
    toast.textContent = message;
    toastContainer.appendChild(toast);

    // Auto-eliminar después de 4 segundos
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'opacity 0.4s, transform 0.4s';
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

// 2. CONTROL DE NAVEGACIÓN (SPA TABS)
function switchTab(tabId) {
    tabContents.forEach(content => {
        content.classList.remove('active');
    });
    tabs.forEach(tab => {
        tab.classList.remove('active');
    });

    const activeContent = document.getElementById(tabId);
    const activeTabButton = document.querySelector(`[data-tab="${tabId}"]`);
    
    if (activeContent && activeTabButton) {
        activeContent.classList.add('active');
        activeTabButton.classList.add('active');
    }

    // Refrescar el dashboard si se entra a esa pestaña
    if (tabId === 'tab-dashboard') {
        loadDashboardData();
    }
}

tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        if (!tab.disabled) {
            switchTab(tab.getAttribute('data-tab'));
        }
    });
});

// 3. CONTROL DEL MODO DE API (DEMO / REAL)
async function updateConnectionStatus() {
    const mode = SoyaLensAPI.getMode();
    
    if (mode === 'mock') {
        btnModeMock.classList.add('active');
        btnModeReal.classList.remove('active');
        statusDot.className = 'status-dot'; // Sin clase online
        statusDot.style.background = 'var(--color-partido)';
        statusDot.style.boxShadow = '0 0 8px var(--color-partido)';
        statusText.textContent = 'Simulado';
    } else {
        btnModeMock.classList.remove('active');
        btnModeReal.classList.add('active');
        
        // Verificar estado real del servidor
        const isOnline = await SoyaLensAPI.checkHealth();
        if (isOnline) {
            statusDot.className = 'status-dot online';
            statusDot.style.background = 'var(--color-sano)';
            statusDot.style.boxShadow = '0 0 8px var(--color-sano)';
            statusText.textContent = 'Servidor Conectado';
        } else {
            statusDot.className = 'status-dot';
            statusDot.style.background = 'var(--color-rechazado)';
            statusDot.style.boxShadow = '0 0 8px var(--color-rechazado)';
            statusText.textContent = 'Servidor Offline';
            showToast('El servidor de la API está desconectado. Las peticiones fallarán o se usarán datos mock.', 'error');
        }
    }
}

// Escuchador del selector de modo
document.getElementById('mode-selector').addEventListener('click', async (e) => {
    const button = e.target.closest('.mode-btn');
    if (!button) return;

    const newMode = button.getAttribute('data-mode');
    SoyaLensAPI.setMode(newMode);
    
    if (newMode === 'real') {
        showToast('Intentando conectar con el servidor FastAPI (localhost:8000)...');
    } else {
        showToast('Cambiado a Modo Demostración local (IA Simulada).', 'success');
    }
    
    await updateConnectionStatus();
    loadDashboardData(); // Recargar datos según el modo activo
});

// 4. GESTIÓN DE SUBIDA / DRAG & DROP
function resetUploadZone() {
    selectedFile = null;
    fileInput.value = '';
    imagePreview.src = '';
    imagePreviewContainer.style.display = 'none';
    dropZoneInfo.style.display = 'flex';
    btnSubmitAnalysis.disabled = true;
}

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        showToast('Por favor, selecciona un archivo de imagen válido (JPG/PNG).', 'error');
        return;
    }
    
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        imagePreviewContainer.style.display = 'block';
        dropZoneInfo.style.display = 'none';
        btnSubmitAnalysis.disabled = false;
        showToast('Imagen cargada con éxito. Lista para auditoría.', 'success');
    };
    reader.readAsDataURL(file);
}

dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    });
});

dropZone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

// 5. ENVÍO DEL ANÁLISIS A LA IA
analyzeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    const lotId = inputLotId.value.trim();
    const supplier = inputSupplier.value.trim();

    // Activar estados visuales de procesamiento
    dropZone.classList.add('laser-active');
    btnSubmitAnalysis.disabled = true;
    inputLotId.disabled = true;
    inputSupplier.disabled = true;

    try {
        const response = await SoyaLensAPI.analyzeSample(selectedFile, lotId, supplier);
        
        // La API real devuelve { certificate, detections }; el mock devuelve el certificado directamente
        const certificate = response.certificate || response;
        const detections = response.detections || [];
        currentCertificate = certificate;

        // Capturar la imagen subida por el usuario ANTES de limpiar el formulario
        // (resetUploadZone borra imagePreview.src)
        const localImageSrc = imagePreview.src || '';

        // Limpiar formulario para el próximo análisis
        inputLotId.value = '';
        inputSupplier.value = '';
        resetUploadZone();

        // Si el certificado no tiene URL de evidencia (mock o error), usar la imagen local
        if (!certificate.evidence_image_url && localImageSrc) {
            certificate.evidence_image_url = localImageSrc;
        }

        // Cargar certificado en la vista (con bounding boxes si hay detecciones)
        renderCertificate(certificate, detections);

        // Habilitar y redirigir a la pestaña de Certificado
        navBtnCertificate.disabled = false;
        switchTab('tab-certificate');
        
        showToast('¡Análisis completado! Certificado generado con éxito.', 'success');
    } catch (err) {
        console.error(err);
        showToast(err.message || 'Error al conectar con la API de IA.', 'error');
    } finally {
        // Desactivar animaciones de carga
        dropZone.classList.remove('laser-active');
        btnSubmitAnalysis.disabled = false;
        inputLotId.disabled = false;
        inputSupplier.disabled = false;
    }
});

// Paleta de colores por clase de grano (debe coincidir con el donut chart y la leyenda)
const BBOX_COLORS = {
    sano:     '#10b981',
    partido:  '#f59e0b',
    dañado:   '#ef4444',
    inmaduro: '#a855f7',
};

/**
 * Dibuja la imagen de evidencia en el canvas y superpone los bounding boxes
 * de cada detección con un color distinto según la clase de grano.
 * @param {string} imageUrl - URL pública de la imagen en Supabase Storage
 * @param {Array} detections - Lista de {class_name, confidence, bbox: [x1,y1,x2,y2]}
 */
function drawDetections(imageUrl, detections) {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
        certCanvas.width  = img.naturalWidth;
        certCanvas.height = img.naturalHeight;
        const ctx = certCanvas.getContext('2d');

        // 1. Dibujar la imagen base
        ctx.drawImage(img, 0, 0);

        // 2. Dibujar cada bounding box
        detections.forEach(det => {
            const [x1, y1, x2, y2] = det.bbox;
            const w = x2 - x1;
            const h = y2 - y1;
            const color = BBOX_COLORS[det.class_name] || '#ffffff';

            // Rect exterior
            ctx.strokeStyle = color;
            ctx.lineWidth = Math.max(2, img.naturalWidth / 600); // Escala relativa
            ctx.strokeRect(x1, y1, w, h);

            // Etiqueta de clase sobre el rect
            const fontSize = Math.max(10, img.naturalWidth / 120);
            ctx.font = `bold ${fontSize}px Inter, sans-serif`;
            const label = `${det.class_name} ${(det.confidence * 100).toFixed(0)}%`;
            const textW = ctx.measureText(label).width;

            // Fondo de la etiqueta
            ctx.fillStyle = color;
            ctx.fillRect(x1, y1 - fontSize - 4, textW + 8, fontSize + 6);

            // Texto de la etiqueta
            ctx.fillStyle = '#000000';
            ctx.fillText(label, x1 + 4, y1 - 4);
        });
    };
    img.onerror = () => {
        // Si la imagen no carga (ej. modo mock sin URL real), limpiar el canvas
        const ctx = certCanvas.getContext('2d');
        certCanvas.width  = 400;
        certCanvas.height = 300;
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(0, 0, 400, 300);
        ctx.fillStyle = '#475569';
        ctx.font = '16px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Imagen no disponible', 200, 150);
    };
    img.src = imageUrl || '';
    if (!imageUrl) img.onerror();
}

// 6. RENDERIZACIÓN DEL CERTIFICADO Y DONUT CHART
function renderCertificate(cert, detections = []) {
    certSampleId.textContent = cert.sample_id;
    
    // Formatear Fecha
    const dateObj = new Date(cert.timestamp);
    certTimestamp.textContent = dateObj.toLocaleString('es-BO', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit'
    });

    // Dibujar imagen + bounding boxes en el canvas
    drawDetections(cert.evidence_image_url, detections);

    // Metadatos
    certLotId.textContent = cert.lot_id || 'SIN IDENTIFICAR';
    certSupplier.textContent = cert.supplier || 'PROVEEDOR GENERAL';
    certTotalGrains.textContent = `${cert.breakdown.total} granos`;
    certNorm.textContent = cert.norm || 'IBNORCA NB 339';

    // Veredicto y Estilo
    certVerdictBadge.className = `verdict-badge ${cert.verdict}`;
    
    if (cert.verdict === 'aprobado') {
        certVerdictBadge.textContent = 'APROBADO';
        certDiscountTicker.className = 'discount-ticker approved';
        certDiscountTicker.style.borderColor = 'rgba(16, 185, 129, 0.2)';
        certDiscountVal.textContent = '0.00%';
        certDiscountVal.style.color = 'var(--color-sano)';
    } else if (cert.verdict === 'con_descuento') {
        certVerdictBadge.textContent = 'CON DESCUENTO';
        certDiscountTicker.className = 'discount-ticker con-descuento';
        certDiscountTicker.style.borderColor = 'rgba(245, 158, 11, 0.2)';
        certDiscountVal.textContent = `${cert.discount_pct.toFixed(2)}%`;
        certDiscountVal.style.color = 'var(--color-descuento)';
    } else {
        certVerdictBadge.textContent = 'RECHAZADO';
        certDiscountTicker.className = 'discount-ticker rechazado';
        certDiscountTicker.style.borderColor = 'rgba(239, 68, 68, 0.2)';
        certDiscountVal.textContent = 'RECHAZADO';
        certDiscountVal.style.color = 'var(--color-rechazado)';
    }

    // Porcentajes en Leyenda — usamos el contrato: pct_dañado/count_dañado (con ñ)
    const b = cert.breakdown;
    const pctDanado = b.pct_dañado ?? b.pct_danado ?? 0;
    const countDanado = b.count_dañado ?? b.count_danado ?? 0;
    pctSanoLbl.textContent = `${b.pct_sano.toFixed(1)}% (${b.count_sano} uds)`;
    pctPartidoLbl.textContent = `${b.pct_partido.toFixed(1)}% (${b.count_partido} uds)`;
    pctDanadoLbl.textContent = `${pctDanado.toFixed(1)}% (${countDanado} uds)`;
    pctInmaduroLbl.textContent = `${b.pct_inmaduro.toFixed(1)}% (${b.count_inmaduro} uds)`;

    // Justificación LLM
    certJustification.textContent = cert.justification;

    // Crear/Actualizar Gráfico Donut
    updateDonutChart(cert.breakdown);
}

function updateDonutChart(breakdown) {
    const ctx = document.getElementById('donutChart').getContext('2d');
    
    if (donutChartInstance) {
        donutChartInstance.destroy();
    }

    const pctDanado = breakdown.pct_dañado ?? breakdown.pct_danado ?? 0;
    donutChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Sano', 'Partido', 'Dañado', 'Inmaduro'],
            datasets: [{
                data: [
                    breakdown.pct_sano,
                    breakdown.pct_partido,
                    pctDanado,
                    breakdown.pct_inmaduro
                ],
                backgroundColor: [
                    '#10b981', // Sano
                    '#f59e0b', // Partido
                    '#ef4444', // Dañado
                    '#a855f7'  // Inmaduro
                ],
                borderColor: '#121622',
                borderWidth: 2,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false // Leyenda custom en HTML
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#fff',
                    bodyColor: '#f1f5f9',
                    borderColor: 'rgba(255,255,255,0.08)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${context.raw.toFixed(1)}%`;
                        }
                    }
                }
            },
            cutout: '72%'
        }
    });
}

// Botones de acción del Certificado
btnPrintCert.addEventListener('click', () => window.print());
btnNewAnalysis.addEventListener('click', () => {
    switchTab('tab-analyze');
    resetUploadZone();
});

// 7. CARGAR Y RENDERIZAR EL DASHBOARD
async function loadDashboardData() {
    try {
        // Cargar Estadísticas del Día
        const stats = await SoyaLensAPI.getTodayStats();
        kpiTotalVal.textContent = stats.total_samples;
        kpiApprovedVal.textContent = stats.approved;
        kpiDiscountVal.textContent = stats.with_discount;
        kpiRejectedVal.textContent = stats.rejected;

        // Cargar Historial
        const historyData = await SoyaLensAPI.getSamples();
        loadedSamples = historyData.items;
        
        renderHistoryTable(loadedSamples);
    } catch (e) {
        console.error("Error al cargar datos del dashboard", e);
        showToast("Error al cargar las métricas del dashboard.", "error");
    }
}

function renderHistoryTable(samples) {
    dashboardTableBody.innerHTML = '';

    if (samples.length === 0) {
        dashboardTableBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 30px;">
                    No hay auditorías registradas en este modo.
                </td>
            </tr>
        `;
        return;
    }

    samples.forEach(sample => {
        const dateObj = new Date(sample.timestamp);
        const fechaFormateada = dateObj.toLocaleDateString('es-BO', {
            day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
        });

        const tr = document.createElement('tr');
        
        let badgeClass = 'aprobado';
        let veredictoTexto = 'Aprobado';
        if (sample.verdict === 'con_descuento') {
            badgeClass = 'con_descuento';
            veredictoTexto = 'Descuento';
        } else if (sample.verdict === 'rechazado') {
            badgeClass = 'rechazado';
            veredictoTexto = 'Rechazado';
        }

        // Soporta tanto la respuesta del backend real (con ñ) como del mock (legacy)
        const danadoPct = (sample.breakdown
            ? (sample.breakdown.pct_dañado ?? sample.breakdown.pct_danado ?? sample.breakdown.pct_hongo)
            : (sample.pct_dañado ?? sample.pct_danado ?? sample.pct_hongo)) ?? 0;
        const discountVal = sample.verdict === 'rechazado' ? 'RECHAZADO' : `${sample.discount_pct.toFixed(2)}%`;

        tr.innerHTML = `
            <td>${fechaFormateada}</td>
            <td><strong>${sample.lot_id || 'N/A'}</strong></td>
            <td>${sample.supplier || 'N/A'}</td>
            <td>${danadoPct.toFixed(1)}%</td>
            <td style="font-weight: 600;">${discountVal}</td>
            <td><span class="badge ${badgeClass}">${veredictoTexto}</span></td>
            <td class="action-cell">
                <button class="btn-icon btn-view-sample" data-id="${sample.sample_id}" title="Ver Certificado">
                    <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                </button>
            </td>
        `;

        // Evento para ver muestra individual
        tr.querySelector('.btn-view-sample').addEventListener('click', async (e) => {
            const sampleId = e.currentTarget.getAttribute('data-id');
            try {
                const sample = await SoyaLensAPI.getSampleById(sampleId);
                renderCertificate(sample);
                navBtnCertificate.disabled = false;
                switchTab('tab-certificate');
            } catch (err) {
                showToast(err.message, 'error');
            }
        });

        dashboardTableBody.appendChild(tr);
    });
}

// 8. FILTROS Y BÚSQUEDA DEL DASHBOARD
function filterHistory() {
    const searchText = tableSearch.value.toLowerCase().trim();
    const verdictFilter = tableFilter.value;

    const filtered = loadedSamples.filter(sample => {
        // Filtro por texto (Lote o Proveedor)
        const matchText = (sample.lot_id || '').toLowerCase().includes(searchText) || 
                            (sample.supplier || '').toLowerCase().includes(searchText);
        
        // Filtro por veredicto
        const matchVerdict = verdictFilter === 'all' || sample.verdict === verdictFilter;

        return matchText && matchVerdict;
    });

    renderHistoryTable(filtered);
}

tableSearch.addEventListener('input', filterHistory);
tableFilter.addEventListener('change', filterHistory);

// 9. INICIALIZACIÓN
async function init() {
    await updateConnectionStatus();
    loadDashboardData();
    
    // Configurar sondeo periódico (cada 10 segundos) para actualizar estado de conexión
    healthCheckInterval = setInterval(async () => {
        const mode = SoyaLensAPI.getMode();
        if (mode === 'real') {
            await updateConnectionStatus();
        }
    }, 10000);
}

// Iniciar aplicación
document.addEventListener('DOMContentLoaded', init);
