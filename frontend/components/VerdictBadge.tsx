// frontend/components/VerdictBadge.tsx
import React from 'react';

interface VerdictBadgeProps {
  verdict: 'aprobado' | 'con_descuento' | 'rechazado';
}

export const VerdictBadge: React.FC<VerdictBadgeProps> = ({ verdict }) => {
  const config = {
    aprobado: {
      text: 'Aprobado',
      styles: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.15)]',
      icon: (
        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
      )
    },
    con_descuento: {
      text: 'Con Descuento',
      styles: 'bg-amber-500/10 text-amber-400 border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.15)]',
      icon: (
        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
        </svg>
      )
    },
    rechazado: {
      text: 'Rechazado',
      styles: 'bg-red-500/10 text-red-400 border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.15)]',
      icon: (
        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      )
    }
  };

  const current = config[verdict] || config.aprobado;

  return (
    <div className={`flex items-center px-4 py-2 border rounded-full text-sm font-bold uppercase tracking-wider ${current.styles}`}>
      {current.icon}
      {current.text}
    </div>
  );
};
