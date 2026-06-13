# DJ Copilot AI — Real-Time Music Analysis & Recommendation Engine

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Sub-100ms latency music recommendation system** for DJs. Analyzes audio → 512-d embeddings → FAISS ANN search → affinity scoring → real-time mixing guidance with MIDI/WebSocket integration.

---

## 🎯 Key Features

| Feature | Spec |
|---------|------|
| **Audio Analysis** | librosa: BPM (onset strength), Key (Krumhansl chroma), Energy (STFT), Onsets, Spectral bands |
| **Embeddings** | 512-dim vectors per track |
| **Similarity Search** | FAISS IndexFlatIP (cosine) — batch search 200 tracks in **<50ms** |
| **Affinity Graph** | 5-weight composite: Harmonic 35%, Timbre 25%, Tempo 20%, Groove 10%, Energy 10% |
| **Real-Time MIDI** | WebSocket + mido thread → crossfader tracking → live EQ/transition advice |
| **RLHF Loop** | User corrections → classification reweighting → online updates |
| **Rekordbox Import** | XML, SQLite (native DB), M3U8, auto-detection |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + TS)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐  │
│  │ LibrarySync │ │LiveAssistant│ │TrackDetail  │ │Transition│  │
│  │ (import/    │ │ (MIDI, WS,  │ │ (view,      │ │Guide     │  │
│  │  analyze)   │ │  EQ advice) │ │  correct)   │ │(step-by- │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ │  step)   │  │
└─────────────────────────────────────────────────────────────────┘
                                │ HTTPS + WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ /analyze │ │ /tracks  │ │/affinity │ │ /live    │           │
│  │ (audio)  │ │ (CRUD)   │ │ (graph)  │ │ (WS)     │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│         │            │            │            │                 │
│         ▼            ▼            ▼            ▼                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              CORE MODULES (backend/)                      │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │   │
│  │  │ audio  │ │engines │ │intellig│ │learning│ │ live   │  │   │
│  │  │analyzer│ │router  │ │ence    │ │(RLHF)  │ │(MIDI)  │  │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    SQLITE (copilot_master.db)             │   │
│  │  tracks │ affinity_links │ corrections │ live_state      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Core Modules

| Module | Responsibility | Key Tech |
|--------|----------------|----------|
| `audio/analyzer.py` | Full audio pipeline: BPM, key, energy curve, spectral bands, vocal presence, groove density, drop detection | librosa, numpy, mutagen |
| `audio/feature_extractor.py` | 512-dim embedding extraction | Custom spectral features |
| `audio/camelot.py` | Key→Camelot conversion, harmonic compatibility scoring | Music theory algorithms |
| `engines/engine_router.py` | Genre classification → mixing engine (Techno, House, Reggaeton, Salsa, etc.) | Heuristic rules + RLHF override |
| `intelligence/affinity_graph.py` | FAISS batch indexing + 5-weight affinity scoring | FAISS, numpy |
| `intelligence/transition_advisor.py` | Mix type, entry point, duration, EQ actions per engine pair | Engine-specific logic |
| `intelligence/eq_advisor.py` | Spectral collision detection, EQ action suggestions | Spectral analysis |
| `learning/rlhf_manager.py` | Human-in-the-loop corrections → classification reweighting | SQLite logging |
| `live/midi_reader.py` | Background thread: mido → LiveStateManager → WebSocket broadcast | mido, asyncio, threading |
| `rekordbox/` | XML, SQLite (native), M3U8 import + auto-detection | sqlite3, xml.etree |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (frontend)
- FFmpeg (audio decoding)

### Backend
```bash
cd backend
pip install -r requirements.txt
# Optional: create .env with CORS_ORIGINS, SECRET_KEY
python main.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# WS:  ws://localhost:8000/ws/live
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

### Generate Test Data
```bash
# Via API
curl -X POST http://localhost:8000/api/setup/generate-examples
# Or UI: Library Sync → "Generar Ejemplos"
```

---

## 📊 Performance Benchmarks

| Operation | Latency | Conditions |
|-----------|---------|------------|
| Single track analysis | ~2-5s | 4-min track, librosa @ 22kHz |
| FAISS batch search (200 tracks) | **<50ms** | IndexFlatIP, 512-dim, CPU |
| Affinity graph rebuild (1K tracks) | ~30s | FAISS k=20, top-10 links |
| WebSocket MIDI → UI update | **<10ms** | Local network, mido thread |
| MIDI CC → crossfader state | **<5ms** | Thread → async callback |

---

## 🔒 Security Notes

- **CORS**: Configure `CORS_ORIGINS` in production (not `*`)
- **Authentication**: Add JWT/API Key for `/setup`, `/rekordbox`, `/affinity/rebuild`
- **Path Traversal**: `xml_path` validated against allowed directories
- **Secrets**: `.env` for API keys, never committed
- **WebSocket**: Add token auth for production deployment

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest -v --cov=backend --cov-fail-under=80

# Frontend tests
cd frontend
npm test -- --coverage
```

---

## 📦 Deployment (Production)

```
┌─────────────────────────────────────────────────────────────┐
│  Internet                                                   │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Nginx (SSL, rate limit, static files)                     │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Docker Compose                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ FastAPI     │ │ Celery      │ │ Redis       │           │
│  │ (web: 2-4   │ │ (worker:    │ │ (broker +   │           │
│  │  workers)   │ │  2-4)       │ │  cache)     │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐                           │
│  │ PostgreSQL  │ │ React       │                           │
│  │ (persist)   │ │ (static)    │                           │
│  └─────────────┘ └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

**Key changes for production:**
- Workers: Celery + Redis for audio analysis (non-blocking)
- DB: PostgreSQL (multi-user, concurrency)
- Auth: JWT + role-based access
- Monitoring: structlog → Loki, Prometheus + Grafana, OpenTelemetry
- Secrets: Docker secrets / Vault

---

## 📁 Project Structure

```
DJ/
├── backend/
│   ├── main.py                 # FastAPI app, routes, lifespan
│   ├── requirements.txt
│   ├── audio/                  # Analysis pipeline
│   ├── engines/                # Genre-specific mixing engines
│   ├── intelligence/           # Affinity, transitions, EQ
│   ├── learning/               # RLHF correction loop
│   ├── live/                   # MIDI + WebSocket state
│   ├── rekordbox/              # Import parsers
│   ├── database/               # SQLite models + manager
│   └── data/                   # SQLite DB (gitignored)
├── frontend/
│   ├── src/
│   │   ├── views/              # LibrarySync, LiveAssistant, TrackDetail, TransitionGuide
│   │   ├── api/client.ts       # Typed API client + WS
│   │   ├── App.tsx             # Routing + state
│   │   └── main.tsx            # Entry
│   ├── package.json
│   └── vite.config.ts
├── data/                       # Example audio + XML (gitignored)
└── test_integration.py
```

---

## 🤝 Contributing

1. Fork → feature branch → PR
2. Run tests: `pytest` / `npm test`
3. Lint: `ruff check .` / `npm run lint`
4. Type check: `mypy backend` / `tsc --noEmit`

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 👨‍💻 Author

**Sergio Andrés Serrano Monsalve**  
Backend Engineer | FastAPI + asyncio | Real-time Systems  
[LinkedIn](https://www.linkedin.com/in/sergio-serrano-ml/) | [GitHub](https://github.com/tuusuario)

---

**Version**: 1.0.0 (Laboratorio)  
**Status**: Active development — core features functional, production hardening in progress