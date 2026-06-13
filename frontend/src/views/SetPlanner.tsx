import { useState, useEffect, useRef } from 'react';
import * as api from '../api/client';

interface Track {
  id: number; title: string; artist: string; bpm: number; key: string;
  camelot_code: string; energy: number; duration: number; assigned_engine: string;
  user_corrected_engine: string | null;
}

interface TimelineItem {
  id: string; // unique instance id
  track: Track;
  startTime: number; // in seconds on the timeline
  trimStart: number; // in seconds (offset into the audio file)
  trimEnd: number;   // in seconds (end time in the audio file)
  mixPoints?: { entry_seconds: number, mix_duration_bars: number, transition_type: string };
}

interface MacroBlock {
  id: string;
  engine: string;
  durationSeconds: number;
}

export default function SetPlanner() {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [options, setOptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('ALL');
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  // Macro-Planner State
  const [macroBlocks, setMacroBlocks] = useState<MacroBlock[]>([]);
  const [targetGap, setTargetGap] = useState<{ startSeconds: number, endSeconds: number, prevTrackId?: number, nextTrackId?: number } | null>(null);

  // History State
  const [history, setHistory] = useState<TimelineItem[][]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Tools
  const [toolMode, setToolMode] = useState<'select' | 'split'>('select');

  // Custom setTimeline wrapper to handle history
  const updateTimeline = (newTimeline: TimelineItem[] | ((prev: TimelineItem[]) => TimelineItem[])) => {
    setTimeline(prev => {
      const next = typeof newTimeline === 'function' ? newTimeline(prev) : newTimeline;
      
      // Save to history
      const newHistory = history.slice(0, historyIndex + 1);
      newHistory.push(next);
      // Limit history to 50 steps to save RAM
      if (newHistory.length > 50) newHistory.shift();
      
      setHistory(newHistory);
      setHistoryIndex(newHistory.length - 1);
      return next;
    });
  };

  const undo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1);
      setTimeline(history[historyIndex - 1]);
    }
  };

  const redo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1);
      setTimeline(history[historyIndex + 1]);
    }
  };

  // Keyboard Shortcuts for Undo/Redo/Split
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        if (e.shiftKey) redo(); else undo();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'y') redo();
      if (e.key === 'c' || e.key === 'C') setToolMode('split');
      if (e.key === 'v' || e.key === 'V') setToolMode('select');
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [historyIndex, history]);

  // NLE Audio State
  const [isPlaying, setIsPlaying] = useState(false);
  const [playheadTime, setPlayheadTime] = useState(0); // in seconds
  const playheadInterval = useRef<number | null>(null);
  const audioRefs = useRef<{ [id: string]: HTMLAudioElement }>({});
  const lastPlayhead = useRef<number>(0);

  const pixelsPerSecond = 5; // Zoom scale

  const handleTrackMouseDown = (e: React.MouseEvent, id: string, type: 'move' | 'trim-left' | 'trim-right') => {
    e.stopPropagation();
    const startX = e.clientX;
    const itemIndex = timeline.findIndex(t => t.id === id);
    if (itemIndex === -1) return;
    const initialItem = timeline[itemIndex];

    const onMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const deltaSeconds = deltaX / pixelsPerSecond;

      updateTimeline(prev => {
        const arr = [...prev];
        const item = { ...arr[itemIndex] };

        if (type === 'move') {
          item.startTime = Math.max(0, initialItem.startTime + deltaSeconds);
        } else if (type === 'trim-left') {
          // No puede ser negativo el trimStart
          const newTrim = Math.max(0, initialItem.trimStart + deltaSeconds);
          // Ajustar el startTime para compensar visualmente el borde izquierdo
          item.startTime = initialItem.startTime + (newTrim - initialItem.trimStart);
          item.trimStart = newTrim;
        } else if (type === 'trim-right') {
          item.trimEnd = Math.max(item.trimStart + 1, initialItem.trimEnd + deltaSeconds);
        }

        arr[itemIndex] = item;
        return arr;
      });
    };

    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const recalculateTimeline = (newTimeline: TimelineItem[]) => {
    let currentStart = 0;
    for (let i = 0; i < newTimeline.length; i++) {
      newTimeline[i].startTime = currentStart;
      currentStart += (newTimeline[i].track.duration * 0.8);
    }
    updateTimeline(newTimeline);
  };

  useEffect(() => {
    api.getTracks().then(d => setTracks(d.tracks)).catch(console.error);
    return () => stopAllAudio();
  }, []);

  const stopAllAudio = () => {
    Object.values(audioRefs.current).forEach(audio => {
      audio.pause();
    });
  };

  const syncAudio = (time: number) => {
    timeline.forEach(item => {
      const audio = audioRefs.current[item.id];
      if (!audio) return;

      const durationOnTimeline = item.trimEnd - item.trimStart;
      const isWithinBounds = time >= item.startTime && time <= (item.startTime + durationOnTimeline);

      if (isWithinBounds && isPlaying) {
        if (audio.paused) {
          const fileTime = (time - item.startTime) + item.trimStart;
          audio.currentTime = fileTime;
          audio.play().catch(e => console.warn("Audio play blocked", e));
        } else {
          // Check drift
          const expectedFileTime = (time - item.startTime) + item.trimStart;
          if (Math.abs(audio.currentTime - expectedFileTime) > 0.5) {
             audio.currentTime = expectedFileTime;
          }
        }
      } else {
        if (!audio.paused) audio.pause();
      }
    });
  };

  useEffect(() => {
    if (isPlaying) {
      playheadInterval.current = window.setInterval(() => {
        setPlayheadTime(prev => {
          const next = prev + 0.1; // 100ms
          syncAudio(next);
          return next;
        });
      }, 100);
    } else {
      if (playheadInterval.current) clearInterval(playheadInterval.current);
      stopAllAudio();
    }
    return () => {
      if (playheadInterval.current) clearInterval(playheadInterval.current);
    };
  }, [isPlaying, timeline]);

  const togglePlayback = () => setIsPlaying(!isPlaying);

  const addToTimeline = (track: Track) => {
    const lastItem = timeline[timeline.length - 1];
    let newStart = 0;
    if (lastItem) {
      newStart = lastItem.startTime + (lastItem.trimEnd - lastItem.trimStart) - 15; // 15 seconds overlap
    }
    addToTimelineAt(track, Math.max(0, newStart));
  };

  const addToTimelineAt = (track: Track, startTime: number) => {
    const newItem: TimelineItem = {
      id: Math.random().toString(36).substr(2, 9),
      track,
      startTime: startTime,
      trimStart: 0,
      trimEnd: track.duration > 0 ? track.duration : 300 // default 5 min if 0
    };

    // Pre-load audio element
    const audio = new Audio(`http://localhost:8000/api/tracks/${track.id}/audio`);
    audio.preload = 'auto';
    audioRefs.current[newItem.id] = audio;

    updateTimeline([...timeline, newItem]);
    setOptions([]); 
  };

  const handleTimelineClick = (e: React.MouseEvent) => {
    // Si el clic viene de una pista, no mover el cabezal, dejarlo propagar si es necesario
    if ((e.target as HTMLElement).closest('.timeline-item')) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left + e.currentTarget.scrollLeft;
    const newTime = Math.max(0, x / pixelsPerSecond);
    setPlayheadTime(newTime);
    syncAudio(newTime);
  };

  const handleDropOnTimeline = (e: React.DragEvent) => {
    e.preventDefault();
    const trackStr = e.dataTransfer.getData('track');
    if (!trackStr) return;
    
    const track = JSON.parse(trackStr);
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left + e.currentTarget.scrollLeft;
    const startTime = Math.max(0, x / pixelsPerSecond);
    
    addToTimelineAt(track, startTime);
  };

  const removeFromTimeline = (id: string) => {
    if (audioRefs.current[id]) {
       audioRefs.current[id].pause();
       delete audioRefs.current[id];
    }
    updateTimeline(timeline.filter(t => t.id !== id));
  };

  const splitTrack = (id: string, splitPointSeconds: number) => {
    const itemIndex = timeline.findIndex(t => t.id === id);
    if (itemIndex === -1) return;
    const item = timeline[itemIndex];
    
    // Check if split point is valid
    if (splitPointSeconds <= item.trimStart || splitPointSeconds >= item.trimEnd) return;
    
    const item1 = { ...item, id: Math.random().toString(36).substr(2, 9), trimEnd: splitPointSeconds };
    const item2 = { ...item, id: Math.random().toString(36).substr(2, 9), startTime: item.startTime + (splitPointSeconds - item.trimStart), trimStart: splitPointSeconds };
    
    // Preload audio for new items
    const audio1 = new Audio(`http://localhost:8000/api/tracks/${item1.track.id}/audio`);
    audioRefs.current[item1.id] = audio1;
    const audio2 = new Audio(`http://localhost:8000/api/tracks/${item2.track.id}/audio`);
    audioRefs.current[item2.id] = audio2;
    
    updateTimeline(prev => {
      const arr = [...prev];
      arr.splice(itemIndex, 1, item1, item2);
      return arr;
    });
  };

  // Synthetic Continuous Waveform
  const SyntheticWaveform = ({ energy, bpm, widthPx }: { energy: number, bpm: number, widthPx: number }) => {
    // Generate static peaks using simple hash
    const bars = Math.floor(widthPx / 4); // 4px per bar
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '1px', height: '100%', width: '100%', overflow: 'hidden' }}>
        {Array.from({ length: bars }).map((_, i) => {
           // Deterministic randomness
           const isKick = i % Math.max(2, Math.floor(150 / bpm)) === 0;
           const height = isKick ? (60 + (energy * 40)) : (20 + ((i*17)%30) + (energy * 20));
           return (
             <div key={i} style={{ 
               flex: '0 0 3px', 
               height: `${height}%`, 
               background: isKick ? '#f97316' : '#0ea5e9',
               opacity: 0.9,
               borderRadius: '1px'
             }}></div>
           );
        })}
      </div>
    );
  };

  const getAIOptions = async () => {
    if (timeline.length === 0) return;
    setLoading(true);
    const lastTrack = timeline[timeline.length - 1].track;
    try {
      const data = await api.getPlannerOptions(lastTrack.id);
      setOptions(data.options);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const formatDuration = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const totalTime = timeline.length > 0 
    ? Math.max(...timeline.map(t => t.startTime + (t.trimEnd - t.trimStart)))
    : 0;

  const uniqueEngines = ['ALL', ...Array.from(new Set(tracks.map(t => t.user_corrected_engine || t.assigned_engine).filter(Boolean)))].sort();
  const displayedTracks = tracks.filter(t => {
    if (filter !== 'ALL' && (t.user_corrected_engine || t.assigned_engine) !== filter) return false;
    if (search && !t.title.toLowerCase().includes(search.toLowerCase()) && !t.artist.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="animate-in" style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div className="view-header flex justify-between items-center" style={{ marginBottom: 0 }}>
        <div>
          <h2 style={{ fontSize: '18px', margin: 0 }}>📅 Night Programmer (DAW Mode)</h2>
        </div>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-pink)', fontFamily: 'monospace' }}>
            {formatDuration(playheadTime)}
          </div>
          <button className={`btn ${isPlaying ? 'btn-secondary' : 'btn-primary'}`} onClick={togglePlayback} style={{ width: '80px' }}>
            {isPlaying ? '⏸ Pause' : '▶ Play'}
          </button>
          <button className="btn" onClick={() => { setPlayheadTime(0); stopAllAudio(); }} style={{ background: 'rgba(255,255,255,0.1)' }}>⏹ Stop</button>
          <button className="btn btn-secondary" onClick={() => { setTimeline([]); stopAllAudio(); }} style={{ padding: '4px 12px', fontSize: '12px' }}>Vaciar Timeline</button>
        </div>
      </div>

      {/* TOP SECTION: NLE Timeline */}
      <div className="card" style={{ flex: '0 0 auto', height: '320px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)', margin: 0 }}>Timeline NLE ({formatDuration(totalTime)})</h3>
            {/* Toolbar */}
            <div style={{ background: '#111', borderRadius: '4px', padding: '2px', display: 'flex', gap: '2px', border: '1px solid var(--border)' }}>
               <button className="btn" onClick={() => setToolMode('select')} style={{ background: toolMode === 'select' ? 'rgba(255,255,255,0.2)' : 'transparent', padding: '4px 8px', fontSize: '12px' }} title="Puntero (V)">🖱️ Seleccionar</button>
               <button className="btn" onClick={() => setToolMode('split')} style={{ background: toolMode === 'split' ? 'rgba(255,255,255,0.2)' : 'transparent', padding: '4px 8px', fontSize: '12px' }} title="Tijera (C)">✂️ Cortar</button>
               <div style={{ width: '1px', background: 'var(--border)', margin: '0 4px' }}></div>
               <button className="btn" onClick={undo} disabled={historyIndex <= 0} style={{ padding: '4px 8px', fontSize: '12px' }} title="Deshacer (Ctrl+Z)">⏪</button>
               <button className="btn" onClick={redo} disabled={historyIndex >= history.length - 1} style={{ padding: '4px 8px', fontSize: '12px' }} title="Rehacer (Ctrl+Y)">⏩</button>
            </div>
            {/* Botón añadir Bloque Macro */}
            <button className="btn btn-secondary" onClick={() => {
              setMacroBlocks([...macroBlocks, { id: Math.random().toString(), engine: 'TECH_HOUSE', durationSeconds: 25 * 60 }]);
            }} style={{ padding: '4px 8px', fontSize: '12px' }}>+ Añadir Género</button>
          </div>
          {macroBlocks.length > 0 && (
             <button className="btn btn-primary" onClick={() => {}} style={{ padding: '4px 12px', fontSize: '12px', background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-purple))', border: 'none', color: '#fff', fontWeight: 'bold' }}>
               🤖 Auto-Generar Set Completo
             </button>
          )}
        </div>
        
        {/* NLE Scrollable Canvas */}
        <div style={{ flex: 1, background: '#0a0a0a', borderRadius: '4px', overflowX: 'auto', overflowY: 'hidden', position: 'relative', border: '1px solid var(--border)', cursor: toolMode === 'split' ? 'crosshair' : 'default' }}>
          <div 
            onClick={handleTimelineClick}
            onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; }}
            onDrop={handleDropOnTimeline}
            style={{ position: 'relative', width: `${Math.max(1000, totalTime * pixelsPerSecond + 500)}px`, height: '100%' }}
          >
            
            {/* Macro Tracks (Genre Blocks) */}
            <div style={{ height: '24px', background: '#1a1a1a', borderBottom: '1px solid var(--border)', position: 'sticky', top: 0, display: 'flex', zIndex: 2 }}>
               {macroBlocks.map((block, i) => {
                  let leftOffset = 0;
                  for (let j = 0; j < i; j++) leftOffset += macroBlocks[j].durationSeconds;
                  const widthPx = block.durationSeconds * pixelsPerSecond;
                  return (
                    <div key={block.id} style={{
                       position: 'absolute', left: `${leftOffset * pixelsPerSecond}px`, width: `${widthPx}px`, height: '100%',
                       background: 'rgba(255,255,255,0.05)', borderRight: '1px dashed var(--accent-pink)', padding: '2px 8px',
                       display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '10px', color: 'var(--accent-pink)'
                    }}>
                       <select value={block.engine} onChange={(e) => {
                          const arr = [...macroBlocks]; arr[i].engine = e.target.value; setMacroBlocks(arr);
                       }} style={{ background: 'transparent', border: 'none', color: 'inherit', outline: 'none', fontWeight: 'bold' }}>
                          <option value="TECHNO">Techno</option>
                          <option value="TECH_HOUSE">Tech House</option>
                          <option value="HOUSE">House</option>
                          <option value="MELODIC_TECHNO">Melodic Techno</option>
                          <option value="REGGAETON">Reggaeton</option>
                          <option value="SALSA">Salsa</option>
                       </select>
                       <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                         <span>{Math.floor(block.durationSeconds/60)} mins</span>
                         <button onClick={() => setMacroBlocks(macroBlocks.filter(b => b.id !== block.id))} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>×</button>
                       </div>
                    </div>
                  );
               })}
            </div>

            {/* Timeline Rules (Time markers) */}
            <div style={{ height: '20px', borderBottom: '1px solid var(--border)', position: 'sticky', top: '24px', background: 'rgba(0,0,0,0.5)', display: 'flex', zIndex: 2 }}>
               {Array.from({ length: Math.ceil(Math.max(1000, totalTime * pixelsPerSecond + 500) / (60 * pixelsPerSecond)) }).map((_, i) => (
                 <div key={i} style={{ width: `${60 * pixelsPerSecond}px`, borderLeft: '1px solid rgba(255,255,255,0.2)', paddingLeft: '4px', fontSize: '10px', color: 'var(--text-muted)' }}>
                   {i}:00
                 </div>
               ))}
            </div>

            {/* Playhead */}
            <div style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: `${playheadTime * pixelsPerSecond}px`,
              width: '2px',
              background: '#ef4444',
              zIndex: 10,
              boxShadow: '0 0 10px #ef4444',
              cursor: 'col-resize'
            }} />

            {timeline.length === 0 ? (
              <div style={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%, -50%)', color: 'var(--text-muted)', fontSize: '12px', pointerEvents: 'none' }}>
                Arrastra una pista aquí o haz clic abajo para empezar.
              </div>
            ) : (
              timeline.map((item, i) => {
                const width = (item.trimEnd - item.trimStart) * pixelsPerSecond;
                const left = item.startTime * pixelsPerSecond;
                const isHighEnergy = item.track.energy > 0.7;
                
                // Calculamos si hay un hueco con el SIGUIENTE track
                let gapButton = null;
                const nextItem = timeline.find(t => t.startTime > item.startTime);
                if (nextItem) {
                   const itemEnd = item.startTime + (item.trimEnd - item.trimStart);
                   const gapSeconds = nextItem.startTime - itemEnd;
                   if (gapSeconds > 5) {
                      const gapLeftPx = itemEnd * pixelsPerSecond;
                      const gapWidthPx = gapSeconds * pixelsPerSecond;
                      gapButton = (
                         <div style={{
                            position: 'absolute', left: `${gapLeftPx}px`, top: '100px', width: `${gapWidthPx}px`, height: '30px',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 5
                         }}>
                            <button className="btn" onClick={(e) => { e.stopPropagation(); setTargetGap({ startSeconds: itemEnd, endSeconds: nextItem.startTime, prevTrackId: item.track.id }); getAIOptions(); }}
                                    style={{ background: 'rgba(217,70,239,0.2)', border: '1px dashed var(--accent-pink)', color: 'var(--accent-pink)', fontSize: '10px', padding: '4px 8px', borderRadius: '15px' }}>
                               + ✨ Sugerir
                            </button>
                         </div>
                      );
                   }
                }

                return (
                  <React.Fragment key={item.id}>
                  <div className="timeline-item"
                    onMouseDown={(e) => {
                      if (toolMode === 'split') {
                         const rect = e.currentTarget.getBoundingClientRect();
                         const x = e.clientX - rect.left;
                         const clickTimeSeconds = item.trimStart + (x / pixelsPerSecond);
                         splitTrack(item.id, clickTimeSeconds);
                      } else {
                         handleTrackMouseDown(e, item.id, 'move');
                      }
                    }}
                    title={toolMode === 'split' ? 'Haz clic para cortar pista aquí' : 'Arrastra para mover horizontalmente'}
                    style={{ 
                    position: 'absolute',
                    top: `${(i % 3) * 60 + 30}px`, // Stagger vertically to show crossfades
                    left: `${left}px`,
                    width: `${width}px`,
                    height: '50px',
                    background: toolMode === 'split' ? '#2a0000' : '#1a1a1a', 
                    border: `1px solid ${isHighEnergy ? 'var(--accent-pink)' : 'var(--accent-cyan)'}`,
                    borderRadius: '4px',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column',
                    cursor: toolMode === 'split' ? 'copy' : 'grab',
                    opacity: toolMode === 'split' ? 0.8 : 1
                  }}>
                    {/* Header bar */}
                    <div style={{ background: isHighEnergy ? 'rgba(217,70,239,0.3)' : 'rgba(6,182,212,0.3)', padding: '2px 6px', fontSize: '10px', display: 'flex', justifyContent: 'space-between', color: '#fff' }}>
                       <span style={{ fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', pointerEvents: 'none' }}>{item.track.title}</span>
                       <button 
                         onMouseDown={e => e.stopPropagation()} 
                         onClick={() => removeFromTimeline(item.id)} 
                         title="Eliminar pista"
                         style={{ background: 'rgba(255,0,0,0.5)', border: 'none', color: '#fff', cursor: 'pointer', borderRadius: '2px', padding: '0 4px' }}>
                         Eliminar
                       </button>
                    </div>
                    {/* Waveform body */}
                    <div style={{ flex: 1, padding: '2px 0', pointerEvents: 'none' }}>
                      <SyntheticWaveform energy={item.track.energy} bpm={item.track.bpm} widthPx={width} />
                    </div>
                    
                    {/* Trimming Handles */}
                    <div onMouseDown={(e) => handleTrackMouseDown(e, item.id, 'trim-left')} 
                         title="Arrastra para recortar inicio"
                         style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '12px', background: 'rgba(255,255,255,0.1)', borderLeft: '3px solid rgba(255,255,255,0.7)', cursor: 'ew-resize', zIndex: 10 }} />
                    <div onMouseDown={(e) => handleTrackMouseDown(e, item.id, 'trim-right')} 
                         title="Arrastra para recortar final"
                         style={{ position: 'absolute', right: 0, top: 0, bottom: 0, width: '12px', background: 'rgba(255,255,255,0.1)', borderRight: '3px solid rgba(255,255,255,0.7)', cursor: 'ew-resize', zIndex: 10 }} />
                  </div>
                  {gapButton}
                  </React.Fragment>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* BOTTOM SECTION: Browser */}
      <div style={{ flex: 1, display: 'flex', gap: '16px', minHeight: 0 }}>
        
        {/* Left Sidebar: Collection / Folders */}
        <div className="card" style={{ flex: '0 0 200px', display: 'flex', flexDirection: 'column', overflowY: 'auto', padding: '12px' }}>
          <h4 style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '12px' }}>Colección</h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '13px' }}>
            {uniqueEngines.map(engine => (
               <li key={engine} 
                   style={{ 
                     padding: '8px', cursor: 'pointer', borderRadius: '4px', 
                     background: filter === engine ? 'rgba(255,255,255,0.1)' : 'transparent',
                     display: 'flex', alignItems: 'center', gap: '8px'
                   }}
                   onClick={() => setFilter(engine)}>
                 <span style={{ color: filter === engine ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>📁</span>
                 {engine === 'ALL' ? 'Todos los Tracks' : engine.toUpperCase().replace('_', ' ')}
               </li>
            ))}
          </ul>
        </div>

        {/* Right Area: Table */}
        <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 0 }}>
          
          <div style={{ padding: '12px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-secondary)' }}>
            <div style={{ fontSize: '13px', fontWeight: 600 }}>Colección ({displayedTracks.length} pistas)</div>
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: '8px', top: '5px', fontSize: '12px', color: 'var(--text-muted)' }}>🔍</span>
              <input type="text" placeholder="Buscar pista o artista..." value={search} onChange={e => setSearch(e.target.value)}
                style={{ background: '#111', border: '1px solid var(--border)', borderRadius: '4px', padding: '4px 8px 4px 24px', color: '#fff', fontSize: '12px', width: '200px' }} />
            </div>
          </div>

          {options.length > 0 && (
             <div style={{ padding: '8px 12px', background: 'rgba(217,70,239,0.1)', borderBottom: '1px solid rgba(217,70,239,0.3)', display: 'flex', gap: '8px', overflowX: 'auto' }}>
               <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--accent-pink)', display: 'flex', alignItems: 'center', marginRight: '8px' }}>
                 ✨ Opciones sugeridas:
               </div>
               {options.map((opt, i) => (
                 <button key={i} className="btn" style={{ padding: '4px 12px', fontSize: '11px', background: 'rgba(0,0,0,0.5)', border: '1px solid var(--accent-purple)' }}
                         onClick={() => {
                           if (targetGap) {
                              addToTimelineAt(opt.track, targetGap.startSeconds);
                              setTargetGap(null);
                           } else {
                              const newStart = timeline.length > 0 ? timeline[timeline.length - 1].startTime + (timeline[timeline.length - 1].trimEnd - timeline[timeline.length - 1].trimStart - opt.mixPoints.entry_seconds) : 0;
                              addToTimelineAt(opt.track, Math.max(0, newStart));
                           }
                           setOptions([]);
                         }}>
                   {opt.track.title} ({(opt.score * 100).toFixed(0)}%)
                 </button>
               ))}
               <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '11px', marginLeft: 'auto' }} onClick={() => setOptions([])}>X</button>
             </div>
          )}

          <div style={{ flex: 1, overflowY: 'auto', background: '#0a0a0a' }}>
            <table className="track-table" style={{ margin: 0 }}>
              <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-secondary)', zIndex: 1 }}>
                <tr>
                  <th style={{ width: '40px', textAlign: 'center' }}></th>
                  <th>Ilustración</th>
                  <th>Título de la pista</th>
                  <th>Artista</th>
                  <th>Género</th>
                  <th>BPM</th>
                  <th>Key</th>
                </tr>
              </thead>
              <tbody>
                {displayedTracks.map(t => (
                  <tr key={t.id} 
                      onClick={() => addToTimeline(t)} 
                      draggable 
                      onDragStart={(e) => {
                         e.dataTransfer.setData('track', JSON.stringify(t));
                         e.dataTransfer.effectAllowed = 'copy';
                      }}
                      style={{ cursor: 'pointer', borderBottom: '1px solid rgba(255,255,255,0.02)' }}
                      title="Haz clic para añadir al final, o arrastra hacia la línea de tiempo"
                  >
                    <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>+</td>
                    <td><div style={{ width: '30px', height: '15px', background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-purple))', borderRadius: '2px' }}></div></td>
                    <td style={{ fontWeight: 600, fontSize: '12px' }}>{t.title}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{t.artist || 'Desconocido'}</td>
                    <td style={{ fontSize: '12px' }}>{(t.user_corrected_engine || t.assigned_engine || '').toUpperCase()}</td>
                    <td style={{ fontSize: '12px', color: 'var(--accent-cyan)' }}>{t.bpm > 0 ? t.bpm.toFixed(2) : '—'}</td>
                    <td style={{ fontSize: '12px' }}>{t.camelot_code || t.key}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
