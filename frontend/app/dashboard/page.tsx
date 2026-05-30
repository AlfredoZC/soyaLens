// frontend/app/dashboard/page.tsx
"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { Certificate, TodayStats } from '../../lib/types';
import { getSamples, getStatsToday, getApiMode, setApiMode, checkServerHealth } from '../../lib/api';
import { CertificateCard } from '../../components/CertificateCard';

export default function DashboardPage() {
  const [samples, setSamples] = useState<Certificate[]>([]);
  const [stats, setStats] = useState<TodayStats>({
    total_samples: 0,
    approved: 0,
    with_discount: 0,
    rejected: 0,
    avg_pct_danado: 0
  });

  const [selectedSample, setSelectedSample] = useState<Certificate | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterVerdict, setFilterVerdict] = useState<'all' | 'aprobado' | 'con_descuento' | 'rechazado'>('all');
  const [apiMode, setApiModeState] = useState<'mock' | 'real'>('mock');
  const [serverOnline, setServerOnline] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Cargar datos del dashboard
  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const mode = getApiMode();
      setApiModeState(mode);

      // Verificar si el servidor FastAPI está vivo en modo real
      if (mode === 'real') {
        const isOnline = await checkServerHealth();
        setServerOnline(isOnline);
      } else {
        setServerOnline(false);
      }

      // Obtener historial y estadísticas (automáticamente detecta el modo en lib/api.ts)
      const historyData = await getSamples();
      const statsData = await getStatsToday();
      
      setSamples(historyData.items);
      setStats(statsData);
    } catch (err: any) {
      console.error(err);
      setError("Error al cargar los datos del panel. Verifica el servidor.");
    } finally {
      setLoading(false);
    }
  };

  // Cargar al montar el componente
  useEffect(() => {
    loadDashboardData();

    // Sondeo de estado del servidor cada 10 segundos
    const interval = setInterval(async () => {
      const mode = getApiMode();
      if (mode === 'real') {
        const isOnline = await checkServerHealth();
        setServerOnline(isOnline);
      }
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  // Alternar el modo de API (Demo / Real)
  const handleToggleMode = async (mode: 'mock' | 'real') => {
    setApiMode(mode);
    setApiModeState(mode);
    await loadDashboardData();
  };

  // Filtrado reactivo en memoria
  const filteredSamples = useMemo(() => {
    return samples.filter(sample => {
      const textMatch = 
        (sample.lot_id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (sample.supplier || '').toLowerCase().includes(searchTerm.toLowerCase());
      
      const verdictMatch = filterVerdict === 'all' || sample.verdict === filterVerdict;

      return textMatch && verdictMatch;
    });
  }, [samples, searchTerm, filterVerdict]);

  return (
    <div className="min-h-screen bg-[#0a0d14] text-slate-100 p-6 md:p-8 font-sans">
      
      {/* HEADER DE CONTROL */}
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-6 pb-6 border-b border-slate-800 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight font-heading">
            Panel de Control de Calidad
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Historial de auditorías ópticas de soya y control de rendimiento diario.
          </p>
        </div>

        {/* Conexión y Selector de Modo */}
        <div className="flex items-center gap-4 flex-wrap">
          {/* Selector de Modo */}
          <div className="bg-slate-900 border border-slate-800 p-1 rounded-full flex">
            <button
              onClick={() => handleToggleMode('mock')}
              className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all duration-300 ${
                apiMode === 'mock' 
                  ? 'bg-gradient-to-r from-cyan-400 to-blue-500 text-black shadow-lg' 
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Modo Demo
            </button>
            <button
              onClick={() => handleToggleMode('real')}
              className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all duration-300 ${
                apiMode === 'real' 
                  ? 'bg-gradient-to-r from-cyan-400 to-blue-500 text-black shadow-lg' 
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              API Servidor
            </button>
          </div>

          {/* Indicador de Estado */}
          <div className="flex items-center gap-2 bg-slate-900/60 border border-slate-800 px-4 py-2 rounded-full text-xs">
            <span className={`w-2.5 h-2.5 rounded-full ${
              apiMode === 'mock' 
                ? 'bg-amber-400 animate-pulse' 
                : (serverOnline ? 'bg-emerald-400 animate-pulse' : 'bg-red-500')
            }`} />
            <span className="font-semibold text-slate-300">
              {apiMode === 'mock' ? 'Simulado' : (serverOnline ? 'Servidor Conectado' : 'Servidor Offline')}
            </span>
          </div>
        </div>
      </div>

      {/* RUTA DE CONTENIDO PRINCIPAL */}
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* FILA DE ESTADÍSTICAS (KPIs) */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          
          <div className="bg-slate-900/40 border border-slate-800/80 backdrop-blur-md rounded-2xl p-5 relative overflow-hidden before:absolute before:left-0 before:top-0 before:h-full before:w-1 before:bg-cyan-500">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 block">Total Muestras</span>
            <span className="text-3xl font-extrabold text-white mt-2 block">{stats.total_samples}</span>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/80 backdrop-blur-md rounded-2xl p-5 relative overflow-hidden before:absolute before:left-0 before:top-0 before:h-full before:w-1 before:bg-emerald-500">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 block">Aprobadas</span>
            <span className="text-3xl font-extrabold text-emerald-400 mt-2 block">{stats.approved}</span>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/80 backdrop-blur-md rounded-2xl p-5 relative overflow-hidden before:absolute before:left-0 before:top-0 before:h-full before:w-1 before:bg-amber-500">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 block">Con Descuento</span>
            <span className="text-3xl font-extrabold text-amber-400 mt-2 block">{stats.with_discount}</span>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/80 backdrop-blur-md rounded-2xl p-5 relative overflow-hidden before:absolute before:left-0 before:top-0 before:h-full before:w-1 before:bg-red-500">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 block">Rechazadas</span>
            <span className="text-3xl font-extrabold text-red-400 mt-2 block">{stats.rejected}</span>
          </div>

          <div className="col-span-2 lg:col-span-1 bg-slate-900/40 border border-slate-800/80 backdrop-blur-md rounded-2xl p-5 relative overflow-hidden before:absolute before:left-0 before:top-0 before:h-full before:w-1 before:bg-purple-500">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 block">Promedio Daño</span>
            <span className="text-3xl font-extrabold text-purple-400 mt-2 block">{stats.avg_pct_danado.toFixed(2)}%</span>
          </div>
          
        </div>

        {/* TABLA HISTÓRICA */}
        <div className="bg-slate-900/20 border border-slate-800/80 backdrop-blur-md rounded-2xl p-6 shadow-xl">
          
          {/* Controles de Búsqueda y Filtros */}
          <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-4 mb-6">
            <h2 className="text-lg font-bold text-white font-heading">
              Historial de Auditorías
            </h2>

            <div className="flex flex-col sm:flex-row gap-3">
              {/* Buscador */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Buscar lote o proveedor..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full sm:w-64 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-all"
                />
              </div>

              {/* Filtro por veredicto */}
              <select
                value={filterVerdict}
                onChange={(e: any) => setFilterVerdict(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-cyan-500"
              >
                <option value="all">Todos los Veredictos</option>
                <option value="aprobado">Aprobado</option>
                <option value="con_descuento">Con Descuento</option>
                <option value="rechazado">Rechazado</option>
              </select>
            </div>
          </div>

          {/* Tabla Responsive */}
          <div className="overflow-x-auto rounded-xl border border-slate-800/80 bg-slate-950/20">
            {loading ? (
              <div className="py-20 text-center text-slate-400 flex flex-col items-center justify-center gap-3">
                <div className="w-8 h-8 border-4 border-cyan-400/20 border-l-cyan-400 rounded-full animate-spin" />
                <span>Consultando base de datos...</span>
              </div>
            ) : error ? (
              <div className="py-20 text-center text-red-400">
                <p>{error}</p>
                <button 
                  onClick={loadDashboardData}
                  className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs rounded-lg text-white font-bold"
                >
                  Reintentar
                </button>
              </div>
            ) : filteredSamples.length === 0 ? (
              <div className="py-20 text-center text-slate-500 text-sm">
                No se encontraron registros de soya que coincidan con la búsqueda.
              </div>
            ) : (
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900/30 text-slate-400 font-medium">
                    <th className="p-4">Fecha y Hora</th>
                    <th className="p-4">Identificador Lote</th>
                    <th className="p-4">Proveedor</th>
                    <th className="p-4 text-center">Grano Dañado</th>
                    <th className="p-4 text-center">Descuento</th>
                    <th className="p-4 text-center">Veredicto</th>
                    <th className="p-4 text-center">Certificado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {filteredSamples.map((sample) => {
                    const date = new Date(sample.timestamp);
                    const dateFormatted = date.toLocaleString('es-BO', {
                      day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
                    });

                    // Estilo de badge de veredicto
                    const verdictConfig = {
                      aprobado: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
                      con_descuento: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
                      rechazado: 'bg-red-500/10 text-red-400 border-red-500/20'
                    };

                    const textVerdict = {
                      aprobado: 'Aprobado',
                      con_descuento: 'Descuento',
                      rechazado: 'Rechazado'
                    };

                    return (
                      <tr key={sample.sample_id} className="hover:bg-slate-900/20 transition-colors">
                        <td className="p-4 text-slate-400 font-mono text-xs">{dateFormatted}</td>
                        <td className="p-4 font-bold text-white">{sample.lot_id || 'N/A'}</td>
                        <td className="p-4 text-slate-300">{sample.supplier || 'N/A'}</td>
                        <td className="p-4 text-center text-slate-300 font-semibold">
                          {sample.breakdown.pct_danado.toFixed(1)}%
                        </td>
                        <td className="p-4 text-center text-slate-100 font-bold">
                          {sample.verdict === 'rechazado' ? (
                            <span className="text-red-400">100% (Rechazo)</span>
                          ) : (
                            <span>{sample.discount_pct.toFixed(2)}%</span>
                          )}
                        </td>
                        <td className="p-4 text-center">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${verdictConfig[sample.verdict]}`}>
                            {textVerdict[sample.verdict]}
                          </span>
                        </td>
                        <td className="p-4 text-center">
                          <button
                            onClick={() => setSelectedSample(sample)}
                            className="p-2 hover:bg-slate-800/80 rounded-lg text-slate-400 hover:text-cyan-400 transition-colors"
                            title="Ver Certificado Completo"
                          >
                            <svg className="w-5 h-5 mx-auto" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"></path>
                              <circle cx="12" cy="12" r="3"></circle>
                            </svg>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

        </div>

      </div>

      {/* MODAL DE VISTA DEL CERTIFICADO DETALLADO */}
      {selectedSample && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto animate-fade-in">
          <div className="relative max-h-[90vh] overflow-y-auto w-full max-w-4xl rounded-2xl scrollbar-thin">
            
            {/* Botón de cierre superior externo */}
            <button 
              onClick={() => setSelectedSample(null)}
              className="absolute top-4 right-4 z-10 p-2 bg-slate-950/80 hover:bg-slate-900 border border-slate-800 text-slate-400 hover:text-white rounded-full transition-all print:hidden"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>

            <CertificateCard 
              certificate={selectedSample} 
              onClose={() => setSelectedSample(null)} 
            />
          </div>
        </div>
      )}

    </div>
  );
}
