import { useState } from 'react'
import LibrarySync from './views/LibrarySync'
import LiveAssistant from './views/LiveAssistant'
import TrackDetail from './views/TrackDetail'
import TransitionGuide from './views/TransitionGuide'
import SetPlanner from './views/SetPlanner'

type View = 'library' | 'live' | 'detail' | 'guide' | 'planner';

export default function App() {
  const [view, setView] = useState<View>('library');
  const [history, setHistory] = useState<number[]>([]);

  const openTrackDetail = (id: number) => {
    setHistory([id]);
    setView('detail');
  };

  const navigateToTrack = (id: number) => {
    // Keep last two tracks in history for side-by-side view
    setHistory(prev => {
      const current = prev[prev.length - 1];
      if (current === id) return prev;
      return [current, id];
    });
  };

  const goBack = () => {
    setHistory([]);
    setView('library');
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>DJ COPILOT AI</h1>
          <span>V1 — El Laboratorio</span>
        </div>
        <nav className="sidebar-nav">
          <button
            className={`nav-item ${view === 'library' ? 'active' : ''}`}
            onClick={() => setView('library')}
          >
            <span className="nav-icon">📚</span>
            Library Sync
          </button>
          <button
            className={`nav-item ${view === 'live' ? 'active' : ''}`}
            onClick={() => setView('live')}
          >
            <span className="nav-icon">🎧</span>
            Live Assistant
          </button>
          <button
            className={`nav-item ${view === 'guide' ? 'active' : ''}`}
            onClick={() => setView('guide')}
          >
            <span className="nav-icon">📖</span>
            Transition Guide
          </button>
          <button
            className={`nav-item ${view === 'planner' ? 'active' : ''}`}
            onClick={() => setView('planner')}
          >
            <span className="nav-icon">📅</span>
            Night Programmer
          </button>
          {history.length > 0 && (
            <button
              className={`nav-item ${view === 'detail' ? 'active' : ''}`}
              onClick={() => setView('detail')}
            >
              <span className="nav-icon">🔍</span>
              Track Detail
            </button>
          )}
        </nav>

        <div style={{ marginTop: 'auto', padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
          <div className="flex items-center gap-8">
            <span className="status-dot status-online"></span>
            <span className="text-sm text-muted">Sistema Online</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {view === 'library' && <LibrarySync onTrackClick={openTrackDetail} />}
        {view === 'live' && <LiveAssistant onTrackClick={openTrackDetail} />}
        {view === 'planner' && <SetPlanner />}
        {view === 'guide' && <TransitionGuide />}
        {view === 'detail' && history.length > 0 && (
          <TrackDetail 
            prevTrackId={history.length > 1 ? history[0] : undefined}
            trackId={history[history.length - 1]} 
            onBack={goBack} 
            onNavigate={navigateToTrack}
          />
        )}
      </main>
    </div>
  );
}
