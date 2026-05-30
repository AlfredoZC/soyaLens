// frontend/lib/types.ts

export type GrainClass = "sano" | "partido" | "inmaduro" | "danado";

export interface ClassBreakdown {
  total: number;
  count_sano: number;
  count_partido: number;
  count_inmaduro: number;
  count_danado: number;
  pct_sano: number;
  pct_partido: number;
  pct_inmaduro: number;
  pct_danado: number;
}

export interface Certificate {
  sample_id: string;
  timestamp: string;
  lot_id?: string;
  supplier?: string;
  breakdown: ClassBreakdown;
  verdict: "aprobado" | "con_descuento" | "rechazado";
  discount_pct: number;   // 0.0 a 100.0
  norm: string;           // ej. "IBNORCA NB 339"
  justification: string;  // texto en español generado por la IA
  evidence_image_url: string;
}

export interface TodayStats {
  total_samples: number;
  approved: number;
  with_discount: number;
  rejected: number;
  avg_pct_danado: number;
}
