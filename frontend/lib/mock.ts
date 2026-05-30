// frontend/lib/mock.ts
import { Certificate, TodayStats } from './types';

export const mockCertificates: Certificate[] = [
  {
    sample_id: "demo-001",
    timestamp: "2026-05-30T11:00:00Z",
    lot_id: "L-204",
    supplier: "Coop. San Juan",
    breakdown: {
      total: 312,
      count_sano: 290,
      count_partido: 10,
      count_inmaduro: 4,
      count_danado: 8,
      pct_sano: 92.9,
      pct_partido: 3.2,
      pct_inmaduro: 1.3,
      pct_danado: 2.6
    },
    verdict: "con_descuento",
    discount_pct: 4.5,
    norm: "IBNORCA NB 339",
    justification: "La muestra presenta 2.6% de grano dañado/manchado, superando el umbral de tolerancia del 2.0% estipulado por la norma. Se aplica un descuento de 4.5% según la reglamentación vigente.",
    evidence_image_url: "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=600&q=80"
  },
  {
    sample_id: "demo-002",
    timestamp: "2026-05-30T10:15:00Z",
    lot_id: "L-205",
    supplier: "Agropecuaria El Torno",
    breakdown: {
      total: 285,
      count_sano: 275,
      count_partido: 6,
      count_inmaduro: 2,
      count_danado: 2,
      pct_sano: 96.5,
      pct_partido: 2.1,
      pct_inmaduro: 0.7,
      pct_danado: 0.7
    },
    verdict: "aprobado",
    discount_pct: 0.0,
    norm: "IBNORCA NB 339",
    justification: "Muestra de soya de excelente calidad. Los granos dañados representan el 0.7%, manteniéndose por debajo de la primera tolerancia del 1.5%. Aprobado sin descuento comercial.",
    evidence_image_url: "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&w=600&q=80"
  },
  {
    sample_id: "demo-003",
    timestamp: "2026-05-30T09:40:00Z",
    lot_id: "L-206",
    supplier: "Hacienda Las Madres",
    breakdown: {
      total: 340,
      count_sano: 282,
      count_partido: 20,
      count_inmaduro: 22,
      count_danado: 16,
      pct_sano: 82.9,
      pct_partido: 5.9,
      pct_inmaduro: 6.5,
      pct_danado: 4.7
    },
    verdict: "rechazado",
    discount_pct: 100.0,
    norm: "IBNORCA NB 339",
    justification: "El lote es RECHAZADO. El nivel de grano dañado por hongo/humedad (4.7%) excede el límite máximo de tolerancia absoluta (4.0%). Alto riesgo latente de propagación de moho en silo.",
    evidence_image_url: "https://images.unsplash.com/photo-1592982537447-7440770cbfc9?auto=format&fit=crop&w=600&q=80"
  },
  {
    sample_id: "demo-004",
    timestamp: "2026-05-30T08:10:00Z",
    lot_id: "L-207",
    supplier: "Sindicato Agrario Pailón",
    breakdown: {
      total: 298,
      count_sano: 280,
      count_partido: 12,
      count_inmaduro: 4,
      count_danado: 2,
      pct_sano: 94.0,
      pct_partido: 4.0,
      pct_inmaduro: 1.3,
      pct_danado: 0.7
    },
    verdict: "aprobado",
    discount_pct: 0.0,
    norm: "IBNORCA NB 339",
    justification: "La soya cumple con los parámetros básicos. Granos dañados dentro del rango de aceptación óptimo (0.7%). Lote aprobado para almacenamiento general.",
    evidence_image_url: "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&w=600&q=80"
  }
];

export const mockStats: TodayStats = {
  total_samples: 4,
  approved: 2,
  with_discount: 1,
  rejected: 1,
  avg_pct_danado: 2.18
};
