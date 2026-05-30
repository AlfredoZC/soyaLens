// frontend/lib/api.ts
import { Certificate, TodayStats } from './types';
import { mockCertificates, mockStats } from './mock';

const API_BASE = typeof window !== 'undefined' 
  ? (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") 
  : "http://localhost:8000";

// Utilidad para verificar si estamos en modo Demo
export function getApiMode(): 'mock' | 'real' {
  if (typeof window === 'undefined') return 'mock';
  return (localStorage.getItem('soyalens_api_mode') as 'mock' | 'real') || 'mock';
}

export function setApiMode(mode: 'mock' | 'real') {
  if (typeof window !== 'undefined') {
    localStorage.setItem('soyalens_api_mode', mode);
  }
}

// Inicializar base de datos local en LocalStorage si no existe
function getLocalHistory(): Certificate[] {
  if (typeof window === 'undefined') return mockCertificates;
  const history = localStorage.getItem('soyalens_history');
  if (!history) {
    localStorage.setItem('soyalens_history', JSON.stringify(mockCertificates));
    return mockCertificates;
  }
  return JSON.parse(history);
}

export async function analyzeSample(image: File, lotId?: string, supplier?: string): Promise<Certificate> {
  const mode = getApiMode();

  if (mode === 'mock') {
    // Simular latencia de red e IA
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Leer imagen local a base64
    let imageUrl = "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&w=600&q=80";
    if (image) {
      imageUrl = await new Promise((resolve) => {
        const r = new FileReader();
        r.onload = () => resolve(r.result as string);
        r.readAsDataURL(image);
      });
    }

    const total = 250 + Math.floor(Math.random() * 150);
    const pct_danado = +(Math.random() * 5).toFixed(1);
    const pct_partido = +(Math.random() * 8).toFixed(1);
    const pct_inmaduro = +(Math.random() * 4).toFixed(1);
    const pct_sano = +(100 - (pct_danado + pct_partido + pct_inmaduro)).toFixed(1);

    const count_danado = Math.round(total * (pct_danado / 100));
    const count_partido = Math.round(total * (pct_partido / 100));
    const count_inmaduro = Math.round(total * (pct_inmaduro / 100));
    const count_sano = total - (count_danado + count_partido + count_inmaduro);

    let verdict: 'aprobado' | 'con_descuento' | 'rechazado' = 'aprobado';
    let discount_pct = 0.0;
    let justification = "";

    if (pct_danado > 4.0) {
      verdict = 'rechazado';
      discount_pct = 100.0;
      justification = `Lote RECHAZADO por control de calidad. El nivel de grano dañado por hongo/humedad (${pct_danado}%) excede el límite máximo de tolerancia absoluta (4.0%).`;
    } else if (pct_danado > 2.0 || pct_partido > 5.0) {
      verdict = 'con_descuento';
      discount_pct = +((pct_danado - 2.0) * 1.5 + (pct_partido - 5.0) * 0.4).toFixed(2);
      if (discount_pct <= 0) discount_pct = 1.5;
      justification = `Muestra aprobada con observaciones. La presencia de grano dañado (${pct_danado}%) excede el límite base del 2.0%. Se aplica una deducción económica del ${discount_pct}%.`;
    } else {
      verdict = 'aprobado';
      justification = `Lote APROBADO para almacenamiento general. La muestra analizada cumple con las tolerancias de la norma IBNORCA NB 339 con daños mínimos (${pct_danado}%).`;
    }

    const newCert: Certificate = {
      sample_id: `demo-${Date.now().toString().slice(-4)}`,
      timestamp: new Date().toISOString(),
      lot_id: lotId || `L-${Math.floor(200 + Math.random() * 100)}`,
      supplier: supplier || "Proveedor Demo",
      breakdown: {
        total, count_sano, count_partido, count_inmaduro, count_danado,
        pct_sano, pct_partido, pct_inmaduro, pct_danado
      },
      verdict,
      discount_pct,
      norm: "IBNORCA NB 339",
      justification,
      evidence_image_url: imageUrl
    };

    // Guardar en base de datos local
    const history = getLocalHistory();
    history.push(newCert);
    localStorage.setItem('soyalens_history', JSON.stringify(history));

    return newCert;
  } else {
    const form = new FormData();
    form.append("image", image);
    if (lotId) form.append("lot_id", lotId);
    if (supplier) form.append("supplier", supplier);

    const res = await fetch(`${API_BASE}/api/v1/analyze`, { method: "POST", body: form });
    if (!res.ok) throw new Error((await res.json()).error || "Error del servidor");
    
    const cert: Certificate = await res.json();
    // Guardar también copia local
    try {
      const history = getLocalHistory();
      if (!history.find(h => h.sample_id === cert.sample_id)) {
        history.push(cert);
        localStorage.setItem('soyalens_history', JSON.stringify(history));
      }
    } catch(e) {}
    return cert;
  }
}

export async function getSamples(limit = 50): Promise<{ items: Certificate[]; total: number }> {
  const mode = getApiMode();
  if (mode === 'mock') {
    const history = getLocalHistory();
    const sorted = [...history].sort((a,b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return { items: sorted.slice(0, limit), total: sorted.length };
  } else {
    try {
      const res = await fetch(`${API_BASE}/api/v1/samples?limit=${limit}`);
      if (!res.ok) throw new Error("Error en servidor");
      return res.json();
    } catch (e) {
      // Fallback local
      const history = getLocalHistory();
      return { items: history, total: history.length };
    }
  }
}

export async function getStatsToday(): Promise<TodayStats> {
  const mode = getApiMode();
  if (mode === 'mock') {
    const history = getLocalHistory();
    const today = new Date().toDateString();
    const todaySamples = history.filter(s => new Date(s.timestamp).toDateString() === today);
    
    const total = todaySamples.length;
    const approved = todaySamples.filter(s => s.verdict === 'aprobado').length;
    const with_discount = todaySamples.filter(s => s.verdict === 'con_descuento').length;
    const rejected = todaySamples.filter(s => s.verdict === 'rechazado').length;
    
    const avg_pct_danado = total > 0 
      ? +(todaySamples.reduce((acc, s) => acc + s.breakdown.pct_danado, 0) / total).toFixed(2)
      : 0.0;

    return { total_samples: total, approved, with_discount, rejected, avg_pct_danado };
  } else {
    try {
      const res = await fetch(`${API_BASE}/api/v1/stats/today`);
      if (!res.ok) throw new Error("Error");
      return res.json();
    } catch (e) {
      // Cálculo local
      const history = getLocalHistory();
      const total = history.length;
      const approved = history.filter(s => s.verdict === 'aprobado').length;
      const with_discount = history.filter(s => s.verdict === 'con_descuento').length;
      const rejected = history.filter(s => s.verdict === 'rechazado').length;
      const avg_pct_danado = total > 0 
        ? +(history.reduce((acc, s) => acc + s.breakdown.pct_danado, 0) / total).toFixed(2)
        : 0.0;
      return { total_samples: total, approved, with_discount, rejected, avg_pct_danado };
    }
  }
}

export async function checkServerHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      const data = await res.json();
      return data.status === 'ok';
    }
    return false;
  } catch (e) {
    return false;
  }
}
