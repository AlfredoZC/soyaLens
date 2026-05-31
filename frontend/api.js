// api.js - Gestión de llamadas API y simulación de datos (Mocks)

const API_BASE_URL = 'http://localhost:8000';

// Configuración inicial en LocalStorage
if (!localStorage.getItem('soyalens_api_mode')) {
    localStorage.setItem('soyalens_api_mode', 'mock'); // 'mock' o 'real'
}

// Datos de semilla iniciales para que el Dashboard no esté vacío
const SEED_SAMPLES = [
    {
        sample_id: "sample-101",
        timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
        lot_id: "LOT-A52",
        supplier: "Agropecuaria del Oriente",
        breakdown: {
            total: 350,
            count_sano: 329,
            count_partido: 12,
            count_dañado: 3,
            count_inmaduro: 6,
            pct_sano: 94.0,
            pct_partido: 3.4,
            pct_dañado: 0.9,
            pct_inmaduro: 1.7
        },
        verdict: "aprobado",
        discount_pct: 0.0,
        norm: "IBNORCA NB 339",
        justification: "El lote cumple ampliamente con los estándares de calidad. La presencia de grano dañado por hongos (0.9%) está muy por debajo del límite de tolerancia del 2.0%. Aprobado sin observaciones.",
        evidence_image_url: "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&w=600&q=80"
    },
    {
        sample_id: "sample-102",
        timestamp: new Date(Date.now() - 3600000 * 4).toISOString(),
        lot_id: "LOT-B18",
        supplier: "Coop. San Juan de Yapacaní",
        breakdown: {
            total: 280,
            count_sano: 248,
            count_partido: 21,
            count_dañado: 8,
            count_inmaduro: 3,
            pct_sano: 88.6,
            pct_partido: 7.5,
            pct_dañado: 2.8,
            pct_inmaduro: 1.1
        },
        verdict: "con_descuento",
        discount_pct: 4.2,
        norm: "IBNORCA NB 339",
        justification: "Se detectó 2.8% de grano con hongos (excede el estándar del 2%). Adicionalmente, el grano partido alcanza 7.5%. Se aplica un descuento compensatorio del 4.2% sobre el precio de liquidación.",
        evidence_image_url: "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=600&q=80"
    },
    {
        sample_id: "sample-103",
        timestamp: new Date(Date.now() - 3600000 * 7).toISOString(),
        lot_id: "LOT-C04",
        supplier: "Hacienda La Estancia",
        breakdown: {
            total: 310,
            count_sano: 260,
            count_partido: 15,
            count_dañado: 17,
            count_inmaduro: 18,
            pct_sano: 83.9,
            pct_partido: 4.8,
            pct_dañado: 5.5,
            pct_inmaduro: 5.8
        },
        verdict: "rechazado",
        discount_pct: 100.0,
        norm: "IBNORCA NB 339",
        justification: "El lote es RECHAZADO debido a que el grano con hongos alcanza el 5.5% (límite máximo permitido para recepción: 4.0%). Alto riesgo de contaminación por micotoxinas y propagación en silos de almacenamiento.",
        evidence_image_url: "https://images.unsplash.com/photo-1592982537447-7440770cbfc9?auto=format&fit=crop&w=600&q=80"
    },
    {
        sample_id: "sample-104",
        timestamp: new Date(Date.now() - 3600000 * 12).toISOString(),
        lot_id: "LOT-D99",
        supplier: "Agronegocios El Trébol",
        breakdown: {
            total: 410,
            count_sano: 390,
            count_partido: 12,
            count_dañado: 2,
            count_inmaduro: 6,
            pct_sano: 95.1,
            pct_partido: 2.9,
            pct_dañado: 0.5,
            pct_inmaduro: 1.5
        },
        verdict: "aprobado",
        discount_pct: 0.0,
        norm: "IBNORCA NB 339",
        justification: "Muestra de calidad excepcional. El grano sano representa el 95.1% de la muestra. Presencia insignificante de patógenos y daños mecánicos.",
        evidence_image_url: "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&w=600&q=80"
    }
];

// Inicializar base de datos local si no existe
if (!localStorage.getItem('soyalens_history')) {
    localStorage.setItem('soyalens_history', JSON.stringify(SEED_SAMPLES));
}

// Convertir archivo a base64 para guardarlo en la BD mock local
function fileToDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
        reader.readAsDataURL(file);
    });
}

export const SoyaLensAPI = {
    // Obtener el modo de la API actual (mock o real)
    getMode() {
        return localStorage.getItem('soyalens_api_mode');
    },

    // Establecer el modo
    setMode(mode) {
        if (mode === 'mock' || mode === 'real') {
            localStorage.setItem('soyalens_api_mode', mode);
        }
    },

    // Obtener todas las muestras
    async getSamples(limit = 50) {
        const mode = this.getMode();
        if (mode === 'mock') {
            const history = JSON.parse(localStorage.getItem('soyalens_history'));
            // Ordenar por fecha descendente
            const sorted = history.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            return {
                items: sorted.slice(0, limit),
                total: sorted.length
            };
        } else {
            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/samples?limit=${limit}`);
                if (!response.ok) throw new Error('Error al obtener datos del servidor');
                return await response.json();
            } catch (error) {
                console.error('API Error, cayendo a local storage:', error);
                // Fallback a localStorage si el backend falla en modo real
                const history = JSON.parse(localStorage.getItem('soyalens_history'));
                return {
                    items: history.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, limit),
                    total: history.length,
                    is_fallback: true
                };
            }
        }
    },

    // Obtener una muestra por ID
    async getSampleById(id) {
        const mode = this.getMode();
        if (mode === 'mock') {
            const history = JSON.parse(localStorage.getItem('soyalens_history'));
            const sample = history.find(s => s.sample_id === id);
            if (!sample) throw new Error('Muestra no encontrada');
            return sample;
        } else {
            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/samples/${id}`);
                if (!response.ok) throw new Error('Error al obtener la muestra del servidor');
                return await response.json();
            } catch (error) {
                console.error('API Error, buscando en local:', error);
                const history = JSON.parse(localStorage.getItem('soyalens_history'));
                const sample = history.find(s => s.sample_id === id);
                if (!sample) throw new Error('Muestra no encontrada en el almacenamiento local');
                return sample;
            }
        }
    },

    // Analizar una nueva muestra de soya
    async analyzeSample(imageFile, lotId, supplier) {
        const mode = this.getMode();
        const lot = lotId || `LOTE-${Math.floor(100 + Math.random() * 900)}`;
        const prov = supplier || "Proveedor Genérico";

        if (mode === 'mock') {
            // Simular retraso de procesamiento de IA de 2.2 segundos para la animación
            await new Promise(resolve => setTimeout(resolve, 2200));

            // En modo mock usamos una URL placeholder — NO guardamos el base64
            // porque puede superar los 5MB del límite de localStorage del navegador.
            const evidenceUrl = "";

            // Generar porcentajes y conteos simulados
            const total = Math.floor(250 + Math.random() * 150);
            
            // Decidir un tipo de calidad de soya aleatoria para la demo
            const randType = Math.random();
            let pct_dañado, pct_partido, pct_inmaduro;

            if (randType < 0.5) {
                // Soya Aprobada (Sana)
                pct_dañado = +(Math.random() * 1.3).toFixed(1);
                pct_partido = +(Math.random() * 4).toFixed(1);
                pct_inmaduro = +(Math.random() * 2).toFixed(1);
            } else if (randType < 0.8) {
                // Soya con Descuento (Hongos moderados o daño moderado)
                pct_dañado = +(1.5 + Math.random() * 2.3).toFixed(1);
                pct_partido = +(3.0 + Math.random() * 6).toFixed(1);
                pct_inmaduro = +(1.0 + Math.random() * 3).toFixed(1);
            } else {
                // Soya Rechazada (Hongos muy altos > 4.0%)
                pct_dañado = +(4.1 + Math.random() * 3).toFixed(1);
                pct_partido = +(5.0 + Math.random() * 10).toFixed(1);
                pct_inmaduro = +(3.0 + Math.random() * 5).toFixed(1);
            }

            const pct_sano = +(100 - (pct_dañado + pct_partido + pct_inmaduro)).toFixed(1);

            const count_dañado = Math.round(total * (pct_dañado / 100));
            const count_partido = Math.round(total * (pct_partido / 100));
            const count_inmaduro = Math.round(total * (pct_inmaduro / 100));
            const count_sano = total - (count_dañado + count_partido + count_inmaduro);

            // Determinar veredicto y descuento según norma IBNORCA NB 339
            let verdict = "aprobado";
            let discount_pct = 0.0;
            let justification = "";

            if (pct_dañado > 4.0) {
                verdict = "rechazado";
                discount_pct = 100.0; // Rechazado por completo
                justification = `Lote RECHAZADO por control de calidad. El nivel de grano dañado por hongo (${pct_dañado}%) excede el límite máximo de tolerancia de la norma IBNORCA NB 339 (4.0%). Representa un alto riesgo de fermentación y contaminación por aflatoxinas en silos de almacenamiento masivo.`;
            } else if (pct_dañado > 1.5 || pct_partido > 5.0) {
                verdict = "con_descuento";
                // Cálculo de penalización: 1.8% por cada 1% de hongo + 0.3% por cada 1% de partido
                const hongoPen = Math.max(0, (pct_dañado - 1.5) * 1.8);
                const partidoPen = Math.max(0, (pct_partido - 5.0) * 0.4);
                discount_pct = +(hongoPen + partidoPen + (pct_inmaduro > 2.0 ? 0.8 : 0)).toFixed(2);
                if (discount_pct === 0) discount_pct = 1.5; // Descuento base si cae en esta categoría
                justification = `Muestra aprobada con observaciones de calidad. Se identificó un nivel de grano dañado por hongo del ${pct_dañado}% (límite base de tolerancia: 1.5%) y grano partido del ${pct_partido}%. Se aplica un descuento regulatorio del ${discount_pct}% sobre la liquidación económica del lote.`;
            } else {
                verdict = "aprobado";
                discount_pct = 0.0;
                justification = `Lote APROBADO para almacenamiento y procesamiento. La muestra analizada cumple con las tolerancias de la norma IBNORCA NB 339. Presencia de grano dañado por hongo (${pct_dañado}%) y grano partido (${pct_partido}%) en niveles óptimos.`;
            }

            const newCertificate = {
                sample_id: `sample-${Date.now().toString().slice(-4)}`,
                timestamp: new Date().toISOString(),
                lot_id: lot,
                supplier: prov,
                breakdown: {
                    total,
                    count_sano,
                    count_partido,
                    count_dañado,
                    count_inmaduro,
                    pct_sano,
                    pct_partido,
                    pct_dañado,
                    pct_inmaduro
                },
                verdict,
                discount_pct,
                norm: "IBNORCA NB 339",
                justification,
                evidence_image_url: evidenceUrl
            };

            // Guardar en el historial local (sin la evidence_image_url para ahorrar espacio)
            try {
                const history = JSON.parse(localStorage.getItem('soyalens_history') || '[]');
                const slim = { ...newCertificate, evidence_image_url: '' }; // omitir base64
                history.push(slim);
                // Mantener solo los últimos 30 registros para no llenar localStorage
                const trimmed = history.slice(-30);
                localStorage.setItem('soyalens_history', JSON.stringify(trimmed));
            } catch (e) {
                console.warn('localStorage lleno, limpiando historial antiguo...', e);
                localStorage.setItem('soyalens_history', JSON.stringify([newCertificate]));
            }

            return newCertificate;

        } else {
            // MODO REAL: Petición HTTP al Backend FastAPI
            const formData = new FormData();
            formData.append('image', imageFile);
            formData.append('lot_id', lot);
            formData.append('supplier', prov);

            const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || `Error en el análisis (${response.status})`);
            }

            const response_json = await response.json();

            // Respaldar en localStorage SOLO el certificado (sin detections — puede ser enorme)
            try {
                const certOnly = response_json.certificate || response_json;
                const history = JSON.parse(localStorage.getItem('soyalens_history') || '[]');
                if (!history.find(h => h.sample_id === certOnly.sample_id)) {
                    history.push({ ...certOnly, evidence_image_url: '' }); // omitir URL grande
                    localStorage.setItem('soyalens_history', JSON.stringify(history.slice(-30)));
                }
            } catch (e) {
                console.warn('Error al sincronizar historial local:', e);
            }

            return response_json;

        }
    },

    // Obtener estadísticas del día
    async getTodayStats() {
        const mode = this.getMode();
        if (mode === 'mock') {
            const history = JSON.parse(localStorage.getItem('soyalens_history'));
            
            // Filtrar las del día de hoy
            const todayStr = new Date().toDateString();
            const todaySamples = history.filter(s => new Date(s.timestamp).toDateString() === todayStr);

            const total = todaySamples.length;
            const approved = todaySamples.filter(s => s.verdict === 'aprobado').length;
            const with_discount = todaySamples.filter(s => s.verdict === 'con_descuento').length;
            const rejected = todaySamples.filter(s => s.verdict === 'rechazado').length;
            
            // Promedio de hongos en el día
            const avg_pct_dañado = total > 0 
                ? +(todaySamples.reduce((acc, s) => acc + s.breakdown.pct_dañado, 0) / total).toFixed(2)
                : 0.0;

            return {
                total_samples: total,
                approved,
                with_discount,
                rejected,
                avg_pct_dañado
            };
        } else {
            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/stats/today`);
                if (!response.ok) throw new Error('Error al obtener estadísticas del servidor');
                return await response.json();
            } catch (error) {
                console.error('API Error, calculando estadísticas locales:', error);
                // Fallback a estadísticas locales
                this.setMode('mock');
                const stats = await this.getTodayStats();
                this.setMode('real'); // Restauramos modo
                return stats;
            }
        }
    },

    // Verificar salud del backend
    async checkHealth() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            if (response.ok) {
                const data = await response.json();
                return data.status === 'ok';
            }
            return false;
        } catch (error) {
            return false;
        }
    }
};
