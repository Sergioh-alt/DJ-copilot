const API_BASE = 'http://localhost:8000/api';

export async function request(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers as Record<string, string> },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API Error');
  }
  return res.json();
}

// ── Setup ──
export const generateExamples = () => request('/setup/generate-examples', { method: 'POST' });
export const clearLibrary = () => request('/setup/clear-library', { method: 'POST' });

// ── Detection ──
export const detectRekordbox = () => request('/detect/rekordbox');
export const detectAudioDirs = () => request('/detect/audio-dirs');
export const pickFolder = () => request('/detect/pick-folder', { method: 'POST' });

// ── Rekordbox ──
export const importRekordboxXML = (xmlPath: string) =>
  request('/rekordbox/import', { method: 'POST', body: JSON.stringify({ xml_path: xmlPath }) });

// ── Analysis ──
export const analyzeAudio = (path: string) =>
  request('/analyze', { method: 'POST', body: JSON.stringify({ path }) });
export const getAnalyzeStatus = () => request('/analyze/status');

// ── Tracks ──
export const getTracks = () => request('/tracks');
export const getTrack = (id: number) => request(`/tracks/${id}`);
export const deleteTrack = (id: number) => request(`/tracks/${id}`, { method: 'DELETE' });
export const getRecommendations = (id: number) => request(`/tracks/${id}/recommendations`);

// ── Engine Override (RLHF) ──
export const overrideEngine = (trackId: number, engine: string) =>
  request(`/tracks/${trackId}/engine`, { method: 'PATCH', body: JSON.stringify({ engine }) });

// ── Affinity ──
export const rebuildAffinity = () => request('/affinity/rebuild', { method: 'POST' });

// ── Night Programmer (Set Planner) ──
export const getPlannerOptions = (currentId: number, targetId?: number) => {
  const params = new URLSearchParams();
  params.append('current_id', currentId.toString());
  if (targetId) params.append('target_id', targetId.toString());
  return request(`/planner/options?${params.toString()}`);
};

// ── Live ──
export const loadDeck = (trackId: number, deck: string) =>
  request('/live/load-deck', { method: 'POST', body: JSON.stringify({ track_id: trackId, deck }) });
export const getLiveState = () => request('/live/state');
export const getEQAdvice = () => request('/live/eq-advice');

// ── WebSockets ──
export const connectLiveState = (onMessage: (data: any) => void) => {
  const ws = new WebSocket(`ws://localhost:8000/ws/live`);
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'LIVE_STATE') {
        onMessage(data);
      }
    } catch (e) {
      console.error('WS parsing error:', e);
    }
  };
  return ws;
};

// ── Camelot ──
export const getCamelotInfo = (code: string) => request(`/camelot/${code}`);

// ── Health ──
export const getHealth = () => request('/health');

// ── Learning ──
export const getLearningStats = () => request('/learning/stats');
