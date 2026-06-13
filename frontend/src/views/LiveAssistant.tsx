import { useState, useEffect } from 'react';
import * as api from '../api/client';

interface Track {
  id: number; title: string; artist: string; bpm: number; key: string;
  camelot_code: string; energy: number; bass_intensity: number; mid_intensity: number;
  high_intensity: number; vocal_presence: number; groove_density: number;
  assigned_engine: string; user_corrected_engine: string | null; duration: number;
  analyzed: boolean; energy_curve: number[]; drop_positions: number[];
  breakdown_positions: number[];
}

interface EQAlertData {
  level: string; frequency_band: string; message: string; action: string; value: number;
}

interface Props { onTrackClick: (id: number) => void; }

const formatDuration = (sec: number) => {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
};

const FeatureBar = ({ label, value, color }: { label: string; value: number; color: string }) => (
  <div style={{ marginBottom: '8px' }}>
    <div className="flex justify-between" style={{ fontSize: '10px', marginBottom: '2px' }}>
      <span className="text-muted">{label}</span>
      <span style={{ fontWeight: 600 }}>{(value * 100).toFixed(0)}%</span>
    </div>
    <div style={{ height: '4px', background: 'var(--bg-tertiary)', borderRadius: '2px', overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${value * 100}%`, background: color, borderRadius: '2px', transition: 'width 0.5s ease' }}></div>
    </div>
  </div>
);

const DeckCard = ({ track, title, color }: { track: Track; title: string; color: string }) => {
  const effective = track.user_corrected_engine || track.assigned_engine;
  return (
    <div className="card" style={{ flex: 1, borderTop: `4px solid ${color}`, minWidth: '0' }}>
      <div className="flex justify-between items-center mb-8">
        <h3 style={{ fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', color }}>{title}</h3>
        <span className="text-muted text-xs">{formatDuration(track.duration)}</span>
      </div>
      
      <div style={{ marginBottom: '12px' }}>
        <div style={{ fontSize: '14px', fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{track.title}</div>
        <div className="text-muted text-xs">{track.artist}</div>
      </div>

      <div className="flex gap-12 mb-12">
        <div>
          <div className="text-muted" style={{ fontSize: '9px' }}>BPM</div>
          <div style={{ fontSize: '18px', fontWeight: 800 }}>{track.bpm.toFixed(1)}</div>
        </div>
        <div>
          <div className="text-muted" style={{ fontSize: '9px' }}>KEY</div>
          <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--accent-cyan)' }}>{track.camelot_code}</div>
        </div>
        <div className={`engine-badge engine-${effective}`} style={{ alignSelf: 'flex-end', fontSize: '9px', padding: '2px 6px' }}>
          {effective.toUpperCase()}
        </div>
      </div>

      <FeatureBar label="Energía" value={track.energy} color="var(--accent-purple)" />
      
      {track.energy_curve?.length > 0 && (
        <div style={{ height: '30px', width: '100%', background: 'rgba(255,255,255,0.03)', borderRadius: '4px', margin: '8px 0' }}>
          <svg width="100%" height="100%" preserveAspectRatio="none" viewBox={`0 0 ${track.energy_curve.length} 1`}>
            <path
              d={`M 0 1 ${track.energy_curve.map((v, i) => `L ${i} ${1 - v}`).join(' ')} L ${track.energy_curve.length} 1 Z`}
              fill={color} fillOpacity="0.1" stroke={color} strokeWidth="0.05" vectorEffect="non-scaling-stroke"
            />
          </svg>
        </div>
      )}

      <div className="flex gap-4 mt-8" style={{ flexWrap: 'wrap' }}>
        {track.drop_positions?.slice(0, 2).map((p, i) => (
          <span key={i} className="engine-badge engine-techno" style={{ fontSize: '9px', padding: '2px 6px' }}>🔥 {formatDuration(p)}</span>
        ))}
        {track.breakdown_positions?.slice(0, 1).map((p, i) => (
          <span key={i} className="engine-badge engine-reggaeton" style={{ fontSize: '9px', padding: '2px 6px' }}>💎 {formatDuration(p)}</span>
        ))}
      </div>
    </div>
  );
};

// [SEC] Componente Nativo de Búsqueda: Eliminamos la necesidad de instalar librerías como 'react-select', 
// reduciendo la superficie de ataque y la fatiga de dependencias.
const TrackSearch = ({ tracks, onSelect, placeholder }: { tracks: Track[], onSelect: (id: number) => void, placeholder: string }) => {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  
  // Sanitización básica y filtrado eficiente O(n)
  const filtered = query 
    ? tracks.filter(t => t.title.toLowerCase().includes(query.toLowerCase()) || t.artist.toLowerCase().includes(query.toLowerCase())) 
    : tracks;

  return (
    <div style={{ position: 'relative', flex: 1 }}>
      <input 
        type="text" 
        className="engine-select" 
        style={{ width: '100%', padding: '8px 12px' }} 
        placeholder={placeholder}
        value={query}
        onChange={e => { setQuery(e.target.value); setIsOpen(true); }}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setIsOpen(false)}
      />
      {isOpen && (
        <div style={{ 
          position: 'absolute', top: '100%', left: 0, right: 0, maxHeight: '250px', 
          overflowY: 'auto', background: 'var(--bg-secondary)', border: '1px solid var(--bg-tertiary)', 
          borderRadius: '4px', zIndex: 100, boxShadow: '0 10px 20px rgba(0,0,0,0.5)' 
        }}>
          {filtered.slice(0, 50).map(t => (
            <div 
              key={t.id} 
              style={{ padding: '10px 12px', cursor: 'pointer', borderBottom: '1px solid var(--bg-tertiary)', fontSize: '13px' }}
              onClick={() => { onSelect(t.id); setQuery(''); setIsOpen(false); }}
              onMouseDown={(e) => e.preventDefault()} // [SEC] Evita la pérdida prematura del foco (onBlur)
            >
              <span style={{ fontWeight: 600 }}>{t.title}</span> 
              <span className="text-muted" style={{ marginLeft: '8px', fontSize: '11px' }}>({t.bpm.toFixed(0)} BPM)</span>
            </div>
          ))}
          {filtered.length === 0 && <div style={{ padding: '10px', fontSize: '13px' }} className="text-muted">No se encontraron tracks</div>}
        </div>
      )}
    </div>
  );
};

export default function LiveAssistant({ onTrackClick }: Props) {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [deckA, setDeckA] = useState<Track | null>(null);
  const [deckB, setDeckB] = useState<Track | null>(null);
  const [eqAdvice, setEqAdvice] = useState<{ alerts: EQAlertData[] } | null>(null);
  const [transition, setTransition] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [crossfader, setCrossfader] = useState(0.5);
  const [midiStatus, setMidiStatus] = useState('Offline');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getTracks().then(d => setTracks(d.tracks)).catch(err => {
      setError(`Error cargando librería: ${err.message || 'Error de conexión'}`);
    });
    
    const ws = api.connectLiveState((data) => {
      setDeckA(data.deck_a);
      setDeckB(data.deck_b);
      setCrossfader(data.crossfader);
      setMidiStatus(data.midi_status || 'Offline');
      if (data.eq_advice) setEqAdvice(data.eq_advice);
      if (data.transition) setTransition(data.transition);
    });

    return () => ws.close();
  }, []);

  // [SEC] Corrección de Flujo Lógico: Las recomendaciones se calculan en base al Deck A (saliente),
  // para predecir matemáticamente el mejor Deck B (entrante).
  useEffect(() => {
    if (deckA) {
      api.getRecommendations(deckA.id).then(d => setRecommendations(d.recommendations || [])).catch(err => {
        setError(`Error en recomendaciones: ${err.message}`);
      });
    } else {
      setRecommendations([]);
    }
  }, [deckA]);

  const handleLoadDeck = async (trackId: number, deck: 'a' | 'b') => {
    try {
      setError(null);
      await api.loadDeck(trackId, deck);
    } catch (err: any) {
      setError(`Fallo al cargar deck ${deck.toUpperCase()}: ${err.message || 'Error de API'}`);
    }
  };

  const surfToTrack = async (newTrackId: number) => {
    if (!deckB) {
      handleLoadDeck(newTrackId, 'b');
      return;
    }
    try {
      setError(null);
      // Move current B to A
      await api.loadDeck(deckB.id, 'a');
      // Load new to B
      await api.loadDeck(newTrackId, 'b');
    } catch (err: any) {
      setError(`Error en ciclo de surfeo: ${err.message}`);
    }
  };

  return (
    <div className="animate-in">
      <div className="view-header flex justify-between items-center">
        <div>
          <h2>🎧 Live Assistant</h2>
          <p>Asistente de mezcla en tiempo real con análisis de hardware</p>
        </div>
        <div className="flex items-center gap-16">
          {error && (
            <div style={{ background: 'rgba(239,68,68,0.1)', color: 'rgb(239,68,68)', padding: '8px 16px', borderRadius: '8px', fontSize: '12px', border: '1px solid rgba(239,68,68,0.2)' }}>
              ⚠️ {error}
            </div>
          )}
          <div className="flex items-center gap-8 card" style={{ padding: '8px 16px', background: 'rgba(255,255,255,0.03)' }}>
            <span className={`status-dot ${midiStatus === 'Online' ? 'status-online' : 'status-offline'}`}></span>
            <span style={{ fontSize: '12px', fontWeight: 700 }}>MIDI: {midiStatus.toUpperCase()}</span>
          </div>
        </div>
      </div>

      <div className="card mb-16" style={{ padding: '12px 24px' }}>
        <div style={{ height: '6px', background: 'var(--bg-tertiary)', borderRadius: '3px', position: 'relative' }}>
          <div style={{ 
            position: 'absolute', top: '-6px', width: '18px', height: '18px', 
            background: 'var(--accent-purple)', borderRadius: '50%', boxShadow: '0 0 15px var(--accent-purple)',
            left: `calc(${crossfader * 100}% - 9px)`, transition: 'left 0.1s linear', border: '3px solid var(--bg-secondary)'
          }}></div>
        </div>
      </div>

      <div className="flex gap-16" style={{ alignItems: 'stretch' }}>
        {/* Decks */}
        <div className="flex gap-16" style={{ flex: 2 }}>
          {deckA ? <DeckCard track={deckA} title="Deck A — Saliente" color="var(--accent-pink)" /> : (
            <div className="card" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: 'var(--text-muted)' }}>
              Carga un track en Deck A
            </div>
          )}
          {deckB ? <DeckCard track={deckB} title="Deck B — Entrante" color="var(--accent-purple)" /> : (
            <div className="card" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: 'var(--text-muted)' }}>
              Carga un track en Deck B
            </div>
          )}
        </div>

        {/* Dynamic Sidebar (Advice + Recommendations) */}
        <div style={{ flex: 1.2, display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* EQ & Transition Advice */}
          {deckA && deckB && (
            <div className="card" style={{ background: 'rgba(139,92,246,0.05)', border: '1px solid rgba(139,92,246,0.2)' }}>
              <h3 style={{ fontSize: '11px', fontWeight: 800, marginBottom: '12px', color: 'var(--accent-cyan)' }}>CONSEJO DE MEZCLA</h3>
              {eqAdvice?.alerts.map((a, i) => (
                <div key={i} className={`eq-alert ${a.level}`} style={{ padding: '8px', marginBottom: '8px', fontSize: '12px' }}>
                  <b>{a.message}</b>
                  <div>→ {a.action}</div>
                </div>
              ))}
              {transition && (
                <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>TRANSICIÓN IDEAL</div>
                  <div style={{ fontSize: '14px', fontWeight: 800 }}>{transition.type?.replace(/_/g, ' ').toUpperCase()}</div>
                  <div style={{ fontSize: '11px' }}>Duración: {transition.mix_duration_bars} Compases</div>
                </div>
              )}
            </div>
          )}

          {/* Recommendations for Deck B */}
          <div className="card">
            <h3 style={{ fontSize: '11px', fontWeight: 800, marginBottom: '12px', color: 'var(--accent-purple)' }}>
              SIGUIENTES PARA DECK B
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {recommendations.slice(0, 4).map((rec, i) => (
                <div key={i} className="rec-card" onClick={() => surfToTrack(rec.track.id)} style={{ padding: '8px 10px' }}>
                  <div className="rec-info">
                    <div style={{ fontSize: '12px', fontWeight: 700 }}>{rec.track.title}</div>
                    <div style={{ fontSize: '10px' }} className="text-muted">{rec.track.bpm.toFixed(0)} · {rec.track.camelot_code}</div>
                  </div>
                  <span className={`rec-match match-${rec.harmonic_match}`} style={{ fontSize: '9px' }}>{rec.harmonic_match === 'perfect' ? '✨' : '✅'}</span>
                </div>
              ))}
              {deckA && recommendations.length === 0 && <div className="text-muted text-xs">Analizando afinidades...</div>}
              {!deckA && <div className="text-muted text-xs">Carga el Deck A para ver sugerencias</div>}
            </div>
          </div>
        </div>
      </div>

      {/* Manual Load Bar con Buscador Integrado (Zero Trust - No Dependencias) */}
      <div className="flex gap-16 mt-16">
        <TrackSearch 
          tracks={tracks} 
          placeholder="🔍 Buscar y cargar Deck A..." 
          onSelect={id => handleLoadDeck(id, 'a')} 
        />
        <TrackSearch 
          tracks={tracks} 
          placeholder="🔍 Buscar y cargar Deck B..." 
          onSelect={id => handleLoadDeck(id, 'b')} 
        />
      </div>
    </div>
  );
}
