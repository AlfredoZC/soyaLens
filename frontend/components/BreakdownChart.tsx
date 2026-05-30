// frontend/components/BreakdownChart.tsx
import React from 'react';
import { ClassBreakdown } from '../lib/types';

interface BreakdownChartProps {
  breakdown: ClassBreakdown;
}

export const BreakdownChart: React.FC<BreakdownChartProps> = ({ breakdown }) => {
  const { pct_sano, pct_partido, pct_inmaduro, pct_danado } = breakdown;

  // Parámetros para la dona SVG
  const radius = 35;
  const circumference = 2 * Math.PI * radius; // ~219.91

  // Cálculo de acumulados para los desplazamientos (offsets)
  const segments = [
    { label: 'Sano', value: pct_sano, color: '#10b981' }, // Verde
    { label: 'Partido', value: pct_partido, color: '#3b82f6' }, // Azul
    { label: 'Inmaduro', value: pct_inmaduro, color: '#f59e0b' }, // Naranja
    { label: 'Dañado', value: pct_danado, color: '#ef4444' } // Rojo
  ];

  let accumulatedPercentage = 0;

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6 w-full">
      {/* Gráfico circular SVG */}
      <div className="relative w-40 h-40 flex items-center justify-center flex-shrink-0">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          {/* Círculo de fondo */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="transparent"
            stroke="#1e293b"
            strokeWidth="10"
          />
          {/* Segmentos de color */}
          {segments.map((seg, idx) => {
            if (seg.value <= 0) return null;
            const strokeLength = (seg.value / 100) * circumference;
            const strokeOffset = circumference - (accumulatedPercentage / 100) * circumference;
            accumulatedPercentage += seg.value;

            return (
              <circle
                key={idx}
                cx="50"
                cy="50"
                r={radius}
                fill="transparent"
                stroke={seg.color}
                strokeWidth="10"
                strokeDasharray={`${strokeLength} ${circumference}`}
                strokeDashoffset={strokeOffset}
                strokeLinecap="round"
                className="transition-all duration-1000 ease-out"
              />
            );
          })}
        </svg>
        {/* Texto interno de la dona */}
        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className="text-2xl font-extrabold text-white leading-none">{breakdown.total}</span>
          <span className="text-[10px] text-slate-400 uppercase tracking-widest mt-1">Granos</span>
        </div>
      </div>

      {/* Leyenda con barra de progreso detallada */}
      <div className="flex-1 w-full space-y-3">
        {segments.map((seg, idx) => (
          <div key={idx} className="space-y-1">
            <div className="flex items-center justify-between text-xs font-semibold">
              <div className="flex items-center">
                <span 
                  className="w-3 h-3 rounded-sm mr-2 block" 
                  style={{ backgroundColor: seg.color }}
                />
                <span className="text-slate-300">{seg.label}</span>
              </div>
              <span className="text-white font-bold">{seg.value.toFixed(1)}%</span>
            </div>
            {/* Barra de progreso visual */}
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div 
                className="h-full rounded-full transition-all duration-1000"
                style={{ 
                  backgroundColor: seg.color,
                  width: `${seg.value}%`
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
