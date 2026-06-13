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

const formatDuration = (sec: number) => {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
};

interface Props { 
  trackId: number; 
  prevTrackId?: number;
  onBack: () => void; 
  onNavigate: (id: number) => void; 
}

const FeatureBar = ({ label, value, color, compact = false }: { label: string; value: number; color: string; compact?: boolean }) => (
  <div style={{ marginBottom: compact ? '8px' : '12px' }}>
    <div className="flex justify-between" style={{ fontSize: compact ? '10px' : '12px', marginBottom: '4px' }}>
      <span className="text-muted">{label}</span>
      <span style={{ fontWeight: 600 }}>{(value * 100).toFixed(0)}%</span>
    </div>
    <div style={{ height: compact ? '4px' : '6px', background: 'var(--bg-tertiary)', borderRadius: '3px', overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${value * 100}%`, background: color, borderRadius: '3px',
        transition: 'width 0.5s ease' }}></div>
    </div>
  </div>
);

const TrackCard = ({ track, title, color }: { track: Track; title: string; color: string }) => {
  const effective = track.user_corrected_engine || track.assigned_engine;
  
  return (
    <div className="card" style={{ flex: 1, minWidth: '0' }}>
      <div className="flex justify-between items-center mb-16">
        <h3 style={{ fontSize: '13px', fontWeight: 800, textTransform: 'uppercase', color }}>
          {title}
        </h3>
        <span className="text-muted text-sm">{formatDuration(track.duration)}</span>
      </div>
      
      <div style={{ marginBottom: '16px' }}>
        <div style={{ fontSize: '16px', fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {track.title}
        </div>
        <div className="text-muted text-sm">{track.artist}</div>
      </div>

      <div className="flex gap-16 mb-16">
        <div>
          <div className="text-muted" style={{ fontSize: '10px' }}>BPM</div>
          <div style={{ fontSize: '20px', fontWeight: 800 }}>{track.bpm.toFixed(1)}</div>
        </div>
        <div>
          <div className="text-muted" style={{ fontSize: '10px' }}>KEY</div>
          <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--accent-cyan)' }}>
            {track.key}/{track.camelot_code}
          </div>
        </div>
        <div>
          <div className="text-muted" style={{ fontSize: '10px' }}>ENGINE</div>
          <div style={{ marginTop: '2px' }}>
            <span className={`engine-badge engine-${effective}`} style={{ padding: '2px 8px', fontSize: '10px' }}>
              {effective.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      <FeatureBar label="Energía" value={track.energy} color="var(--accent-purple)" compact />
      <FeatureBar label="Graves" value={track.bass_intensity} color="var(--accent-cyan)" compact />
      <FeatureBar label="Vocales" value={track.vocal_presence} color="var(--accent-green)" compact />

      {/* Compact Energy Curve */}
      {track.energy_curve?.length > 0 && (
        <div style={{ marginTop: '12px' }}>
          <div style={{ height: '40px', width: '100%', background: 'rgba(255,255,255,0.03)', borderRadius: '4px', padding: '2px' }}>
            <svg width="100%" height="100%" preserveAspectRatio="none" viewBox={`0 0 ${track.energy_curve.length} 1`}>
              <path
                d={`M 0 1 ${track.energy_curve.map((v, i) => `L ${i} ${1 - v}`).join(' ')} L ${track.energy_curve.length} 1 Z`}
                fill={color}
                fillOpacity="0.15"
                stroke={color}
                strokeWidth="0.05"
                vectorEffect="non-scaling-stroke"
              />
            </svg>
          </div>
        </div>
      )}

      {/* Drops/Breakdowns badges */}
      <div style={{ marginTop: '16px' }}>
        {track.drop_positions?.length > 0 && (
          <div className="flex items-center gap-8 mb-4" style={{ flexWrap: 'wrap' }}>
            <span className="text-muted" style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', minWidth: '60px' }}>Drops:</span>
            <div className="flex gap-4">
              {track.drop_positions.slice(0, 3).map((p, i) => (
                <span key={i} className="engine-badge engine-techno" style={{ fontSize: '11px', padding: '4px 10px' }}>🔥 {formatDuration(p)}</span>
              ))}
            </div>
          </div>
        )}
        {track.breakdown_positions?.length > 0 && (
          <div className="flex items-center gap-8" style={{ flexWrap: 'wrap' }}>
            <span className="text-muted" style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', minWidth: '60px' }}>Breaks:</span>
            <div className="flex gap-4">
              {track.breakdown_positions.slice(0, 2).map((p, i) => (
                <span key={i} className="engine-badge engine-reggaeton" style={{ fontSize: '11px', padding: '4px 10px' }}>💎 {formatDuration(p)}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default function TrackDetail({ trackId, prevTrackId, onBack, onNavigate }: Props) {
  const [track, setTrack] = useState<Track | null>(null);
  const [prevTrack, setPrevTrack] = useState<Track | null>(null);
  const [recommendations, setRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    window.scrollTo(0, 0);
    setLoading(true);
    
    const calls = [
      api.getTrack(trackId),
      api.getRecommendations(trackId).catch(() => ({ recommendations: [] })),
    ];
    
    if (prevTrackId) {
      calls.push(api.getTrack(prevTrackId));
    }

    Promise.all(calls).then(([t, r, pt]) => {
      setTrack(t);
      setRecs(r.recommendations || []);
      if (pt) setPrevTrack(pt);
      else setPrevTrack(null);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [trackId, prevTrackId]);

  if (loading) return <div className="loading"><span className="spinner"></span> Cargando...</div>;
  if (!track) return <div>Track no encontrado</div>;

  return (
    <div className="animate-in">
      <div className="view-header flex justify-between items-center">
        <div>
          <h2>🔍 Modo Mezcla Dual</h2>
          <p>Compara el track saliente con el entrante y planea tu transición</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={onBack}>
          ← Salir al Listado
        </button>
      </div>

      <div className="flex gap-16" style={{ alignItems: 'stretch' }}>
        {/* Deck A: Outgoing */}
        {prevTrack && (
          <TrackCard track={prevTrack} title="Deck A — Saliente" color="var(--accent-pink)" />
        )}

        {/* Deck B: Incoming (Current) */}
        <TrackCard track={track} title={prevTrack ? "Deck B — Entrante" : "Seleccionado"} color="var(--accent-purple)" />

        {/* Right: Recommendations for the incoming track */}
        <div style={{ flex: prevTrack ? 0.8 : 1.2, minWidth: '300px' }}>
          <div className="card" style={{ height: '100%' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 800, marginBottom: '16px', textTransform: 'uppercase', color: 'var(--accent-cyan)' }}>
              🕸️ Siguientes (Perfectas)
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {recommendations
                .filter(rec => rec.harmonic_match === 'perfect' || rec.affinity_score > 0.7)
                .map((rec, i) => (
                <div key={i} className="rec-card" onClick={() => onNavigate(rec.track.id)} style={{ padding: '10px 12px' }}>
                  <div className="rec-score" style={{ width: '32px', height: '32px', fontSize: '12px' }}>
                    {(rec.affinity_score * 100).toFixed(0)}
                  </div>
                  <div className="rec-info">
                    <div className="rec-title" style={{ fontSize: '13px' }}>{rec.track.title}</div>
                    <div className="rec-meta" style={{ fontSize: '10px' }}>
                      {rec.track.bpm.toFixed(0)} · {rec.track.key}/{rec.track.camelot_code} · {formatDuration(rec.track.duration)}
                    </div>
                  </div>
                  <span className={`rec-match match-${rec.harmonic_match}`} style={{ fontSize: '9px' }}>
                    {rec.harmonic_match === 'perfect' ? '✨' : '✅'}
                  </span>
                </div>
              ))}
              {recommendations.length === 0 && (
                <div className="text-muted text-sm" style={{ textAlign: 'center', padding: '20px' }}>
                  No hay más sugerencias perfectas para este track.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
