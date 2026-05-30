// frontend/components/CertificateCard.tsx
import React from 'react';
import { Certificate } from '../lib/types';
import { VerdictBadge } from './VerdictBadge';
import { BreakdownChart } from './BreakdownChart';

interface CertificateCardProps {
  certificate: Certificate;
  onClose?: () => void;
}

export const CertificateCard: React.FC<CertificateCardProps> = ({ certificate, onClose }) => {
  const { sample_id, timestamp, lot_id, supplier, breakdown, verdict, discount_pct, norm, justification, evidence_image_url } = certificate;

  const dateObj = new Date(timestamp);
  const formattedDate = dateObj.toLocaleDateString('es-BO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl w-full max-w-4xl mx-auto print:border-none print:shadow-none print:bg-white print:text-black">
      {/* Cabecera del Certificado */}
      <div className="p-6 border-b border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 print:border-black print:pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 print:hidden animate-pulse"></span>
            <h2 className="text-xl font-extrabold text-white tracking-tight font-heading print:text-black print:text-2xl">
              CERTIFICADO DE CALIDAD DE SOYA
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1 print:text-slate-700">
            SoyaLens Auditor ID: <span className="font-mono font-bold text-slate-300 print:text-black">{sample_id}</span> &bull; {formattedDate}
          </p>
        </div>
        
        {/* Veredicto */}
        <div className="print:block">
          <VerdictBadge verdict={verdict} />
        </div>
      </div>

      {/* Tarjeta de Descuento Destacada */}
      <div className={`mx-6 mt-6 p-4 rounded-xl border flex flex-col items-center justify-center text-center 
        ${verdict === 'aprobado' ? 'bg-emerald-500/5 border-emerald-500/10 text-emerald-400' : ''}
        ${verdict === 'con_descuento' ? 'bg-amber-500/5 border-amber-500/10 text-amber-400' : ''}
        ${verdict === 'rechazado' ? 'bg-red-500/5 border-red-500/10 text-red-400' : ''}
        print:bg-slate-100 print:border-slate-300 print:text-black`}
      >
        <span className="text-3xl font-black font-heading tracking-tight">
          {verdict === 'rechazado' ? 'RECHAZADO' : `${discount_pct.toFixed(2)}%`}
        </span>
        <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 mt-1 print:text-slate-600">
          {verdict === 'rechazado' ? 'Lote no apto para almacenamiento' : 'Descuento total aplicado al precio'}
        </span>
      </div>

      {/* Grid de Contenido */}
      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Columna Izquierda: Imagen de Evidencia */}
        <div className="flex flex-col space-y-3">
          <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider print:text-black">
            Evidencia de Auditoría Óptica
          </h3>
          <div className="aspect-[4/3] rounded-xl overflow-hidden border border-slate-800 bg-slate-950 relative print:border-slate-300">
            <img 
              src={evidence_image_url} 
              alt="Muestra de soya" 
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-2 right-2 bg-black/60 backdrop-blur-sm px-2 py-1 rounded text-[10px] font-mono text-slate-300 print:hidden">
              Muestra física original
            </div>
          </div>
          <p className="text-[10px] text-slate-500 text-center leading-relaxed print:text-slate-600">
            Foto almacenada permanentemente en Supabase Storage como evidencia auditable de calidad.
          </p>
        </div>

        {/* Columna Derecha: Detalles Técnicos y Gráfico */}
        <div className="flex flex-col space-y-6 justify-between">
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider print:text-black">
              Mapeo de Calidad de Granos
            </h3>
            
            <div className="grid grid-cols-2 gap-4 bg-slate-950/40 border border-slate-800 p-4 rounded-xl print:bg-slate-50 print:border-slate-300">
              <div>
                <span className="text-[9px] uppercase tracking-wider text-slate-500 block">Lote de Soya</span>
                <span className="text-sm font-bold text-white print:text-black">{lot_id || 'N/A'}</span>
              </div>
              <div>
                <span className="text-[9px] uppercase tracking-wider text-slate-500 block">Proveedor</span>
                <span className="text-sm font-bold text-white print:text-black">{supplier || 'N/A'}</span>
              </div>
              <div>
                <span className="text-[9px] uppercase tracking-wider text-slate-500 block">Granos Detectados</span>
                <span className="text-sm font-bold text-white print:text-black">{breakdown.total} unidades</span>
              </div>
              <div>
                <span className="text-[9px] uppercase tracking-wider text-slate-500 block">Estándar Aplicado</span>
                <span className="text-sm font-bold text-white print:text-black">{norm}</span>
              </div>
            </div>
          </div>

          {/* Gráfico circular de distribución */}
          <div className="bg-slate-950/20 border border-slate-800/60 p-4 rounded-xl print:border-slate-300">
            <BreakdownChart breakdown={breakdown} />
          </div>
        </div>
      </div>

      {/* Explicación/Justificación del Agente IA */}
      <div className="mx-6 mb-6 p-5 bg-gradient-to-r from-cyan-500/5 to-blue-500/5 border border-cyan-500/10 rounded-xl relative overflow-hidden print:bg-slate-50 print:border-slate-300">
        <div className="absolute top-4 right-4 bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider print:border-black print:text-black">
          Gemini 3 Flash
        </div>
        <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-2 print:text-black">
          Justificación Técnico-Comercial de la IA
        </h4>
        <p className="text-sm leading-relaxed text-slate-300 print:text-black">
          {justification}
        </p>
      </div>

      {/* Botones de Acción */}
      <div className="p-6 border-t border-slate-800 flex justify-end gap-3 print:hidden">
        {onClose && (
          <button 
            onClick={onClose}
            className="px-5 py-2.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-950 text-slate-300 hover:text-white font-semibold text-sm transition-all"
          >
            Cerrar Reporte
          </button>
        )}
        <button 
          onClick={() => window.print()}
          className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 text-black hover:brightness-110 font-bold text-sm shadow-[0_4px_12px_rgba(6,182,212,0.2)] transition-all"
        >
          Imprimir Certificado
        </button>
      </div>
    </div>
  );
};
