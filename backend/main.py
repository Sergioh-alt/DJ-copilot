"""
DJ Copilot AI — FastAPI Server (V1)
Main API server that connects all modules: analysis, engines, affinity, EQ, and RLHF.
"""
import os
import sys
import json
import asyncio
import threading
import tkinter as tk
from tkinter import filedialog
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure backend is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import db_manager
from database.models import EngineType, TrackResponse
from audio.analyzer import analyze_track
from audio.feature_extractor import extract_embedding
from audio.camelot import key_to_camelot, get_compatible_keys, calculate_harmonic_score
from audio.synth_examples import generate_all_examples
from rekordbox.xml_parser import parse_rekordbox_xml, extract_playlists
from rekordbox.auto_detector import find_rekordbox_xml, find_audio_directories, scan_directory_for_audio
from rekordbox.example_xml import generate_example_xml
from rekordbox.sqlite_reader import find_native_rekordbox_db, parse_native_db
from rekordbox.m3u_parser import parse_m3u8
from engines.engine_router import classify_track, get_effective_engine
from intelligence.affinity_graph import rebuild_affinity_graph
from intelligence.eq_advisor import analyze_eq_collision
from intelligence.transition_advisor import suggest_transition
from learning.rlhf_manager import record_correction, get_correction_stats
from live.midi_reader import live_state, midi_listener_task

# ── App Setup ──
app = FastAPI(title="DJ Copilot AI", version="1.0.0",
              description="Intelligent DJ Assistant — V1 El Laboratorio")

# CORS: configurable via env, default to localhost for dev
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.planner_router import router as planner_router
app.include_router(planner_router, prefix="/api/planner", tags=["planner"])

# Initialize database and background tasks on startup
@app.on_event("startup")
async def startup():
    db_manager.init_database()
    asyncio.create_task(midi_listener_task())


# ══════════════════════════════════════════════════════════
# SETUP & EXAMPLES
# ══════════════════════════════════════════════════════════

@app.post("/api/setup/generate-examples")
async def generate_examples():
    """Generate synthetic audio examples and Rekordbox XML for testing."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "examples")
    xml_path = os.path.join(data_dir, "example_rekordbox.xml")

    audio_files = generate_all_examples(data_dir)
    generate_example_xml(xml_path)

    return {
        "status": "examples_generated",
        "audio_files": audio_files,
        "xml_path": xml_path,
    }


@app.post("/api/setup/clear-library")
async def clear_library():
    """Wipe the database to start fresh."""
    db_manager.clear_all_data()
    return {"status": "library_cleared"}


# ══════════════════════════════════════════════════════════
# AUTO-DETECTION
# ══════════════════════════════════════════════════════════

@app.get("/api/detect/rekordbox")
async def detect_rekordbox():
    """Scan the system for Rekordbox XML files."""
    found = find_rekordbox_xml()
    return {"found": found, "count": len(found)}


@app.get("/api/detect/audio-dirs")
async def detect_audio_dirs():
    """Scan the system for directories containing audio files."""
    dirs = find_audio_directories(max_depth=2)
    return {"directories": dirs, "count": len(dirs)}


@app.post("/api/detect/pick-folder")
async def pick_folder():
    """Open a native OS folder picker and return the selected path(s)."""
    path_results = []
    
    def _open_picker():
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        # Loop to allow multiple folder selections
        while True:
            selected_path = filedialog.askdirectory(title="Selecciona una carpeta (Cancela para terminar)")
            if not selected_path:
                break
            path_results.append(selected_path)
            
        root.destroy()

    # Run in a separate thread to avoid blocking the event loop
    thread = threading.Thread(target=_open_picker)
    thread.start()
    
    # Wait for the user to finish (with timeout)
    timeout = 120
    start_time = asyncio.get_event_loop().time()
    while thread.is_alive() and (asyncio.get_event_loop().time() - start_time) < timeout:
        await asyncio.sleep(0.5)
            
    if path_results:
        return {"paths": path_results}
    return {"paths": []}


# ══════════════════════════════════════════════════════════
# REKORDBOX IMPORT
# ══════════════════════════════════════════════════════════

class ImportXMLRequest(BaseModel):
    xml_path: str


@app.post("/api/rekordbox/import")
async def import_rekordbox_xml(request: ImportXMLRequest):
    """Import tracks from Rekordbox native DB or XML."""
    tracks = []
    playlists = {}
    
    # Check if native DB exists
    native_db = find_native_rekordbox_db()
    if native_db:
        print("Using Native Rekordbox SQLite DB")
        tracks = parse_native_db(native_db)
        
    # Fallback to XML or M3U8
    if not tracks:
        if not request.xml_path or not os.path.exists(request.xml_path):
            raise HTTPException(404, "No se encontraron tracks y el archivo no existe.")
        
        ext = os.path.splitext(request.xml_path)[1].lower()
        if ext in ['.m3u', '.m3u8']:
            print(f"Using Rekordbox M3U8 Fallback: {request.xml_path}")
            tracks = parse_m3u8(request.xml_path)
            playlists = {"M3U8 Import": [t.title for t in tracks]}
        else:
            print(f"Using Rekordbox XML Fallback: {request.xml_path}")
            tracks = parse_rekordbox_xml(request.xml_path)
            playlists = extract_playlists(request.xml_path)

    imported = 0
    for track in tracks:
        db_manager.insert_track(track)
        imported += 1

    return {
        "status": "imported",
        "tracks_imported": imported,
        "playlists_found": list(playlists.keys()),
    }


# ══════════════════════════════════════════════════════════
# AUDIO ANALYSIS
# ══════════════════════════════════════════════════════════

# [SEC] Estado Global Aislado: Mitiga ataques de agotamiento de recursos limitando concurrencia
analysis_state = {
    "is_processing": False,
    "total": 0,
    "analyzed": 0,
    "errors": 0,
    "message": ""
}

def _background_analysis_worker(files: list):
    """
    [SEC] Trabajador de Segundo Plano (Arquitectura Zero Trust)
    Desacopla la inferencia pesada del ciclo de vida HTTP. 
    Previene Timeouts (L7) permitiendo el análisis de bibliotecas masivas.
    """
    global analysis_state
    analysis_state["is_processing"] = True
    analysis_state["total"] = len(files)
    analysis_state["analyzed"] = 0
    analysis_state["errors"] = 0
    analysis_state["message"] = "Iniciando análisis de pistas..."

    for i, file_path in enumerate(files):
        try:
            print(f"[IA-WORKER] ({i+1}/{len(files)}) Analizando: {file_path}")
            features = analyze_track(file_path)
            features.embedding = extract_embedding(features)
            features.camelot_code = key_to_camelot(features.key)

            engine_type = classify_track(features)

            title = os.path.splitext(os.path.basename(file_path))[0]
            from database.models import TrackModel
            track = TrackModel(
                title=title,
                artist="Unknown",
                file_path=file_path,
                features=features,
                assigned_engine=engine_type,
                analyzed=True,
            )
            db_manager.insert_track(track)
            
            analysis_state["analyzed"] += 1
            analysis_state["message"] = f"Procesando: {title}"
        except Exception as e:
            # [SEC] Opacidad: Log interno exhaustivo, sin filtrar Stack Trace al cliente
            print(f"[IA-WORKER] [ERROR FATAL] {file_path}: {str(e)}")
            analysis_state["errors"] += 1

    analysis_state["is_processing"] = False
    analysis_state["message"] = "Análisis completado."

class AnalyzeRequest(BaseModel):
    path: str  # Archivo o directorio (sanitizado internamente)

@app.post("/api/analyze")
async def analyze_audio(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Endpoint refactorizado para análisis masivo. Retorna HTTP 202 Inmediato.
    [SEC] Previene sobrecargas al rechazar peticiones simultáneas.
    """
    global analysis_state
    if analysis_state["is_processing"]:
        # [SEC] 429 Too Many Requests o 409 Conflict es más adecuado
        raise HTTPException(409, "Ya existe un análisis en progreso. Por favor, espere.")

    path = request.path.strip()
    files = []

    if not path or path == "LIBRARY":
        tracks = db_manager.get_all_tracks()
        files = [t["file_path"] for t in tracks if not t.get("analyzed")]
        if not files:
            return {"status": "nothing_to_analyze", "queued": 0}
    elif os.path.isfile(path):
        if path.lower().endswith(".xml"):
            raise HTTPException(400, "Entrada inválida. Se esperaba directorio o archivo de audio.")
        files = [path]
    elif os.path.isdir(path):
        files = scan_directory_for_audio(path)
    else:
        raise HTTPException(404, "Ruta no encontrada o acceso denegado.")

    # Encola el trabajo en el event-loop seguro
    background_tasks.add_task(_background_analysis_worker, files)
    
    return {"status": "accepted", "queued": len(files)}

@app.get("/api/analyze/status")
async def get_analyze_status():
    """
    [SEC] Polling endpoint seguro.
    No expone rutas absolutas ni objetos sensibles, solo progreso estadístico.
    """
    return analysis_state


# ══════════════════════════════════════════════════════════
# TRACKS
# ══════════════════════════════════════════════════════════

from audio.camelot import format_musical_key

def _track_to_response(t: dict) -> dict:
    return {
        "id": t["id"],
        "title": t["title"],
        "artist": t["artist"],
        "bpm": t.get("bpm", 0),
        "key": format_musical_key(t.get("key_name", "Unknown")),
        "camelot_code": t.get("camelot_code", "1A"),
        "energy": t.get("energy", 0),
        "bass_intensity": t.get("bass_intensity", 0),
        "mid_intensity": t.get("mid_intensity", 0),
        "high_intensity": t.get("high_intensity", 0),
        "vocal_presence": t.get("vocal_presence", 0),
        "groove_density": t.get("groove_density", 0),
        "assigned_engine": t.get("assigned_engine", "unknown"),
        "user_corrected_engine": t.get("user_corrected_engine"),
        "duration": t.get("duration", 0),
        "analyzed": bool(t.get("analyzed", 0)),
        "energy_curve": json.loads(t.get("energy_curve", "[]")),
        "drop_positions": json.loads(t.get("drop_positions", "[]")),
        "breakdown_positions": json.loads(t.get("breakdown_positions", "[]")),
    }


@app.get("/api/tracks")
async def get_tracks():
    """Get all tracks in the library."""
    tracks = db_manager.get_all_tracks()
    return {"tracks": [_track_to_response(t) for t in tracks], "count": len(tracks)}


@app.get("/api/tracks/{track_id}")
async def get_track(track_id: int):
    """Get detailed info for a specific track."""
    track = db_manager.get_track_by_id(track_id)
    if not track:
        raise HTTPException(404, "Track not found")
    return _track_to_response(track)


@app.delete("/api/tracks/{track_id}")
async def delete_track(track_id: int):
    """Remove a track from the database."""
    db_manager.delete_track(track_id)
    return {"status": "deleted", "id": track_id}

from fastapi.responses import FileResponse

@app.get("/api/tracks/{track_id}/audio")
async def get_track_audio(track_id: int):
    """Serve the actual audio file for streaming/playback."""
    track = db_manager.get_track_by_id(track_id)
    if not track or not track.get("file_path"):
        raise HTTPException(404, "Track or file path not found")
    
    file_path = track["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(404, f"File missing on disk: {file_path}")
        
    return FileResponse(file_path)


# ══════════════════════════════════════════════════════════
# ENGINE OVERRIDE (Human-in-the-Loop)
# ══════════════════════════════════════════════════════════

class EngineOverride(BaseModel):
    engine: str


@app.patch("/api/tracks/{track_id}/engine")
async def override_engine(track_id: int, override: EngineOverride):
    """Human-in-the-Loop: override the engine classification for a track."""
    track = db_manager.get_track_by_id(track_id)
    if not track:
        raise HTTPException(404, "Track not found")

    original = track.get("user_corrected_engine") or track.get("assigned_engine", "unknown")
    result = record_correction(track_id, original, override.engine)
    return result


@app.get("/api/learning/stats")
async def learning_stats():
    """Get RLHF correction statistics."""
    return get_correction_stats()


# ══════════════════════════════════════════════════════════
# AFFINITY GRAPH & RECOMMENDATIONS
# ══════════════════════════════════════════════════════════

@app.post("/api/affinity/rebuild")
async def rebuild_graph():
    """Rebuild the entire affinity graph."""
    result = rebuild_affinity_graph()
    return result


@app.get("/api/tracks/{track_id}/recommendations")
async def get_recommendations(track_id: int, limit: int = Query(5, ge=1, le=20)):
    """Get top N recommended tracks for mixing after this track."""
    track = db_manager.get_track_by_id(track_id)
    if not track:
        raise HTTPException(404, "Track not found")

    affinities = db_manager.get_top_affinities(track_id, limit)

    recommendations = []
    for aff in affinities:
        track_b = db_manager.get_track_by_id(aff["track_b_id"])
        if not track_b:
            continue

        # Get harmonic match type
        _, match_type = calculate_harmonic_score(
            track.get("camelot_code", "1A"),
            track_b.get("camelot_code", "1A")
        )

        # Get transition suggestion
        trans = suggest_transition(track, track_b)

        recommendations.append({
            "track": _track_to_response(track_b),
            "affinity_score": aff["total_score"],
            "harmonic_match": match_type,
            "harmonic_score": aff["harmonic_score"],
            "bpm_score": aff["bpm_score"],
            "texture_score": aff["texture_score"],
            "transition": {
                "type": trans.transition_type.value,
                "entry_point_seconds": trans.entry_point_seconds,
                "entry_point_bars": trans.entry_point_bars,
                "mix_duration_bars": trans.mix_duration_bars,
                "eq_actions": trans.eq_actions,
                "engine_used": trans.engine_used.value,
            }
        })

    return {"track": _track_to_response(track), "recommendations": recommendations}


# ══════════════════════════════════════════════════════════
# LIVE ASSISTANT (V2 WebSockets & MIDI)
# ══════════════════════════════════════════════════════════

# WebSocket clients
ws_clients = []

async def broadcast_live_state(state):
    """Callback fired when live_state changes (from MIDI or API)"""
    deck_a_obj = db_manager.get_track_by_id(state["deck_a"]) if state["deck_a"] else None
    deck_b_obj = db_manager.get_track_by_id(state["deck_b"]) if state["deck_b"] else None
    
    advice = None
    trans = None
    if deck_a_obj and deck_b_obj:
        advice = analyze_eq_collision(deck_a_obj, deck_b_obj)
        trans = suggest_transition(deck_a_obj, deck_b_obj)

    payload = {
        "type": "LIVE_STATE",
        "deck_a": _track_to_response(deck_a_obj) if deck_a_obj else None,
        "deck_b": _track_to_response(deck_b_obj) if deck_b_obj else None,
        "crossfader": state["crossfader"],
        "midi_status": "Online" if state.get("port") else "Offline",
        "midi_port": state.get("port"),
        "eq_advice": advice.model_dump() if advice else None,
        "transition": {
            "type": trans.transition_type.value,
            "entry_point_seconds": trans.entry_point_seconds,
            "entry_point_bars": trans.entry_point_bars,
            "mix_duration_bars": trans.mix_duration_bars,
            "eq_actions": trans.eq_actions,
            "engine_used": trans.engine_used.value,
        } if trans else None
    }
    
    for client in ws_clients:
        try:
            await client.send_json(payload)
        except:
            pass

# Register the callback
live_state.subscribe(broadcast_live_state)

@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_clients.append(websocket)
    try:
        # Send initial state
        await broadcast_live_state({
            "deck_a": live_state.deck_a_track_id,
            "deck_b": live_state.deck_b_track_id,
            "crossfader": live_state.crossfader
        })
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_clients.remove(websocket)


class LoadDeckRequest(BaseModel):
    track_id: int
    deck: str  # "a" or "b"


@app.post("/api/live/load-deck")
async def load_deck(request: LoadDeckRequest):
    """Load a track into a deck (from UI)."""
    track = db_manager.get_track_by_id(request.track_id)
    if not track:
        raise HTTPException(404, "Track not found")

    live_state.load_track(request.deck, request.track_id)
    return {"status": "loaded", "deck": request.deck, "track": _track_to_response(track)}


@app.get("/api/live/state")
async def get_live_state_rest():
    """REST fallback for live state."""
    deck_a_obj = db_manager.get_track_by_id(live_state.deck_a_track_id) if live_state.deck_a_track_id else None
    deck_b_obj = db_manager.get_track_by_id(live_state.deck_b_track_id) if live_state.deck_b_track_id else None
    
    return {
        "deck_a": _track_to_response(deck_a_obj) if deck_a_obj else None,
        "deck_b": _track_to_response(deck_b_obj) if deck_b_obj else None,
        "crossfader": live_state.crossfader
    }


@app.get("/api/live/eq-advice")
async def get_eq_advice_rest():
    """REST fallback for EQ advice."""
    deck_a_obj = db_manager.get_track_by_id(live_state.deck_a_track_id) if live_state.deck_a_track_id else None
    deck_b_obj = db_manager.get_track_by_id(live_state.deck_b_track_id) if live_state.deck_b_track_id else None
    
    if not deck_a_obj or not deck_b_obj:
        raise HTTPException(400, "Both decks must be loaded")

    advice = analyze_eq_collision(deck_a_obj, deck_b_obj)
    trans = suggest_transition(deck_a_obj, deck_b_obj)

    return {
        "eq_advice": advice.model_dump(),
        "transition": {
            "type": trans.transition_type.value,
            "entry_point_seconds": trans.entry_point_seconds,
            "entry_point_bars": trans.entry_point_bars,
            "mix_duration_bars": trans.mix_duration_bars,
            "eq_actions": trans.eq_actions,
            "engine_used": trans.engine_used.value,
            "confidence": trans.confidence,
        }
    }


# ══════════════════════════════════════════════════════════
# CAMELOT WHEEL
# ══════════════════════════════════════════════════════════

@app.get("/api/camelot/{code}")
async def get_camelot_info(code: str):
    """Get compatible keys for a Camelot code."""
    compatible = get_compatible_keys(code)
    return {"code": code, "compatible": compatible}


# ══════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    return {"status": "online", "version": "1.0.0", "name": "DJ Copilot AI"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
