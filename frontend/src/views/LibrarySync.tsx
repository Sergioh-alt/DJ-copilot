import { useState, useEffect } from 'react';
import * as api from '../api/client';

interface Track {
  id: number; title: string; artist: string; bpm: number; key: string;
  camelot_code: string; energy: number; bass_intensity: number;
  vocal_presence: number; groove_density: number; assigned_engine: string;
  user_corrected_engine: string | null; duration: number; analyzed: boolean;
  key: string;
}

const formatDuration = (sec: number) => {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
};

interface Props { onTrackClick: (id: number) => void; }

export default function LibrarySync({ onTrackClick }: Props) {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [xmlPath, setXmlPath] = useState('');
  const [audioPath, setAudioPath] = useState('');
  const [activeTab, setActiveTab] = useState<string>('ALL');

  // [SEC] Abstracción Dinámica O(n): Calculamos los géneros únicos sin peticiones extra.
  const uniqueEngines = ['ALL', ...Array.from(new Set(tracks.map(t => t.user_corrected_engine || t.assigned_engine).filter(Boolean)))].sort();
  const displayedTracks = activeTab === 'ALL' ? tracks : tracks.filter(t => (t.user_corrected_engine || t.assigned_engine) === activeTab);

  const loadTracks = async () => {
    try {
      const data = await api.getTracks();
      setTracks(data.tracks);
    } catch { /* ignore */ }
  };

  const handleClearLibrary = async () => {
    if (!window.confirm('¿Estás seguro de que quieres borrar TODA la librería? Esta acción no se puede deshacer.')) return;
    setLoading(true);
    setMessage('Vaciando librería...');
    try {
      await api.clearLibrary();
      setMessage('✅ Librería vaciada correctamente.');
      setTracks([]);
    } catch (e: any) {
      setMessage(`❌ Error: ${e.message}`);
    }
    setLoading(false);
  };

  const handleDeleteTrack = async (e: React.MouseEvent, trackId: number) => {
    e.stopPropagation();
    if (!window.confirm('¿Eliminar este track de la librería?')) return;
    try {
      await api.deleteTrack(trackId);
      loadTracks();
    } catch { /* ignore */ }
  };

  const handlePickAndAnalyze = async () => {
    setMessage('Esperando a que selecciones tus carpetas...');
    try {
      const { paths } = await api.pickFolder();
      if (!paths || paths.length === 0) {
        setMessage('⚠️ No seleccionaste ninguna carpeta.');
        return;
      }
      
      setLoading(true);
      // [SEC] Encolamos los paths. El backend responderá HTTP 202 Inmediato.
      for (const path of paths) {
        setMessage(`🔎 Encolando trabajo en backend: ${path}...`);
        await api.analyzeAudio(path);
      }
      // El useEffect de polling tomará el control del progreso visual
    } catch (e: any) {
      setMessage(`❌ Error de red/encolado: ${e.message}`);
      setLoading(false);
    }
  };

  // [SEC] Polling seguro del estado asíncrono
  useEffect(() => {
    loadTracks();
    const interval = window.setInterval(async () => {
      try {
        const status = await api.getAnalyzeStatus();
        if (status.is_processing) {
          setLoading(true);
          setMessage(`⏳ ${status.message} (${status.analyzed}/${status.total} procesados, ${status.errors} errores)`);
        } else {
          setLoading(prev => {
            if (prev) {
              loadTracks();
              setMessage(status.total > 0 ? `✅ Análisis de fondo completado. ${status.analyzed} procesados, ${status.errors} errores.` : '');
            }
            return false;
          });
        }
      } catch { /* Ignorar fallos de red esporádicos en el polling */ }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleGenerateExamples = async () => {
    setLoading(true);
    setMessage('Generando audio sintético y XML de ejemplo...');
    try {
      const result = await api.generateExamples();
      setMessage(`✅ Ejemplos generados: ${result.audio_files.length} archivos de audio + XML`);
    } catch (e: any) {
      setMessage(`❌ Error: ${e.message}`);
    }
    setLoading(false);
  };

  const handleImportXML = async () => {
    setLoading(true);
    setMessage('Importando XML de Rekordbox...');
    try {
      const result = await api.importRekordboxXML(xmlPath);
      setMessage(`✅ Importados ${result.tracks_imported} tracks. Playlists: ${result.playlists_found.join(', ') || 'ninguna'}`);
      loadTracks();
    } catch (e: any) {
      setMessage(`❌ Error: ${e.message}`);
    }
    setLoading(false);
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setMessage('Encolando tarea de análisis con IA...');
    try {
      // [SEC] Delegamos al worker de backend sin bloquear el navegador
      await api.analyzeAudio(audioPath);
    } catch (e: any) {
      setMessage(`❌ Error al solicitar análisis: ${e.message}`);
      setLoading(false);
    }
  };

  const handleRebuildAffinity = async () => {
    setLoading(true);
    setMessage('Recalculando Grafo de Afinidad...');
    try {
      const result = await api.rebuildAffinity();
      setMessage(`✅ Grafo construido: ${result.tracks_processed} tracks, ${result.links_created} enlaces`);
    } catch (e: any) {
      setMessage(`❌ Error: ${e.message}`);
    }
    setLoading(false);
  };

  const handleEngineChange = async (trackId: number, engine: string) => {
    try {
      await api.overrideEngine(trackId, engine);
      loadTracks();
    } catch { /* ignore */ }
  };

  const engineBadge = (engine: string, corrected: string | null) => {
    const effective = corrected || engine;
    const cls = effective === 'techno' ? 'engine-techno' :
                effective === 'reggaeton' ? 'engine-reggaeton' : 
                effective === 'salsa' ? 'engine-reggaeton' : // Reuse color
                effective === 'tech_house' ? 'engine-unknown' : 'engine-unknown';
    return <span className={`engine-badge ${cls}`}>{effective.toUpperCase().replace('_', ' ')}</span>;
  };

  return (
    <div className="animate-in">
      <div className="view-header">
        <h2>📚 Library Sync</h2>
        <p>Importa tu librería de Rekordbox, analiza tracks y construye el Grafo de Afinidad</p>
      </div>

      {/* Tabs (Zero Trust - Native RAM Filter) */}
      {uniqueEngines.length > 1 && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', overflowX: 'auto', paddingBottom: '4px' }}>
          {uniqueEngines.map(engine => (
            <button
              key={engine}
              onClick={() => setActiveTab(engine)}
              style={{
                padding: '6px 16px',
                borderRadius: '20px',
                border: 'none',
                background: activeTab === engine ? 'var(--accent-purple)' : 'rgba(255,255,255,0.05)',
                color: activeTab === engine ? '#fff' : 'var(--text-muted)',
                fontWeight: 600,
                fontSize: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {engine.toUpperCase().replace('_', ' ')}
            </button>
          ))}
        </div>
      )}

      {/* Actions Panel */}
      <div className="card mb-16">
        <div className="flex gap-16 items-center" style={{ flexWrap: 'wrap' }}>
          
          <button className="btn btn-primary" onClick={handlePickAndAnalyze} disabled={loading}
            style={{ padding: '12px 24px', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '20px' }}>📂</span> Importar Carpeta de Música
          </button>

          <button className="btn btn-secondary" onClick={handleRebuildAffinity} disabled={loading}>
            🕸️ Recalcular Afinidad
          </button>

          <button className="btn" onClick={handleClearLibrary} disabled={loading} 
            style={{ background: 'rgba(239,68,68,0.1)', color: 'rgb(239,68,68)', border: '1px solid rgba(239,68,68,0.2)' }}>
            🗑️ Vaciar Librería
          </button>

        </div>

        {message && (
          <div style={{ marginTop: '12px', padding: '10px', borderRadius: 'var(--radius-sm)',
            background: message.includes('✅') ? 'rgba(16,185,129,0.1)' :
              message.includes('❌') ? 'rgba(239,68,68,0.1)' : 'rgba(139,92,246,0.1)',
            fontSize: '13px' }}>
            {loading && <span className="spinner" style={{ display: 'inline-block', marginRight: '8px', width: '14px', height: '14px' }}></span>}
            {message}
          </div>
        )}
      </div>

      {/* Track Table */}
      {tracks.length > 0 && (
        <div className="card">
          <div className="flex justify-between items-center mb-16">
            <h3 style={{ fontSize: '15px', fontWeight: 600 }}>
              Librería ({displayedTracks.length} tracks en esta vista)
            </h3>
          </div>

          <table className="track-table">
            <thead>
              <tr>
                <th>Título</th>
                <th>BPM</th>
                <th>Key</th>
                <th>Duración</th>
                <th>Energía</th>
                <th>Graves</th>
                <th>Vocal</th>
                <th>Engine</th>
                <th>Cambiar</th>
                <th>Estado</th>
                <th style={{ width: '40px' }}></th>
              </tr>
            </thead>
            <tbody>
              {displayedTracks.map(t => (
                <tr key={t.id} onClick={() => onTrackClick(t.id)} style={{ cursor: 'pointer' }}>
                  <td style={{ fontWeight: 600 }}>{t.title}</td>
                  <td>{t.bpm > 0 ? t.bpm.toFixed(1) : '—'}</td>
                  <td>
                    <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{t.key}/{t.camelot_code}</span>
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{formatDuration(t.duration)}</td>
                  <td>
                    <div className="energy-bar">
                      <div className="energy-bar-fill" style={{ width: `${t.energy * 100}%` }}></div>
                    </div>
                  </td>
                  <td>{(t.bass_intensity * 100).toFixed(0)}%</td>
                  <td>{(t.vocal_presence * 100).toFixed(0)}%</td>
                  <td>{engineBadge(t.assigned_engine, t.user_corrected_engine)}</td>
                  <td onClick={e => e.stopPropagation()}>
                    <select
                      className="engine-select"
                      value={t.user_corrected_engine || t.assigned_engine}
                      onChange={e => handleEngineChange(t.id, e.target.value)}
                    >
                      <option value="techno">Techno</option>
                      <option value="reggaeton">Reggaetón</option>
                      <option value="house">House</option>
                      <option value="melodic_techno">Melodic Techno</option>
                      <option value="salsa">Salsa</option>
                      <option value="tech_house">Tech House</option>
                      <option value="unknown">Auto</option>
                    </select>
                  </td>
                  <td>
                    <span className={`status-dot ${t.analyzed ? 'status-online' : 'status-offline'}`}></span>
                  </td>
                  <td onClick={e => handleDeleteTrack(e, t.id)}>
                    <button className="btn-icon" style={{ color: 'var(--text-muted)', fontSize: '16px' }}>×</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tracks.length === 0 && !loading && (
        <div className="card" style={{ textAlign: 'center', padding: '60px' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎵</div>
          <h3 style={{ marginBottom: '8px' }}>No hay tracks en la librería</h3>
          <p className="text-muted text-sm">
            Haz clic en "Generar Ejemplos" para crear audio sintético de prueba, o importa tu XML de Rekordbox.
          </p>
        </div>
      )}
    </div>
  );
}
