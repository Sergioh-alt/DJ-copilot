"""
DJ Copilot AI — MIDI & Real-Time State Reader (V2.1)
Reads MIDI input in a background thread to update the live decks and crossfader.
"""
import asyncio
import threading
import mido
from typing import Callable

# Global state manager for Live Decks
class LiveStateManager:
    def __init__(self):
        self.deck_a_track_id = None
        self.deck_b_track_id = None
        self.crossfader = 0.5  # 0.0 is Deck A, 1.0 is Deck B
        self.active_port = None
        self.listeners = []

    def load_track(self, deck: str, track_id: int):
        if deck.lower() == 'a':
            self.deck_a_track_id = track_id
        elif deck.lower() == 'b':
            self.deck_b_track_id = track_id
        self._notify()

    def set_crossfader(self, value: float):
        self.crossfader = max(0.0, min(1.0, value))
        self._notify()

    def subscribe(self, callback: Callable):
        self.listeners.append(callback)

    def _notify(self):
        state = {
            "deck_a": self.deck_a_track_id,
            "deck_b": self.deck_b_track_id,
            "crossfader": self.crossfader,
            "port": self.active_port
        }
        for listener in self.listeners:
            try:
                # If listener is async, schedule it
                if asyncio.iscoroutinefunction(listener):
                    asyncio.create_task(listener(state))
                else:
                    listener(state)
            except Exception as e:
                print(f"[LIVE] Error notifying listener: {e}")

# Singleton instance
live_state = LiveStateManager()

def midi_worker():
    """Background thread to handle MIDI input without blocking FastAPI."""
    global live_state
    
    # Try to find any available input
    inputs = mido.get_input_names()
    if not inputs:
        print("[MIDI] No se detectaron controladores MIDI. El sistema está en modo manual.")
        return

    # Use the first available port (usually the DJ controller)
    port_name = inputs[0]
    live_state.active_port = port_name
    print(f"[MIDI] CONECTADO A: {port_name}")
    print("[MIDI] Escuchando movimientos de Crossfader (CC 0, 1, 7, 8, 10)...")

    try:
        with mido.open_input(port_name) as inport:
            for msg in inport:
                if msg.type == 'control_change':
                    # Common DJ Crossfader CCs: 0, 1, 7, 8, 10
                    if msg.control in [0, 1, 7, 8, 10]:
                        val = msg.value / 127.0
                        # Thread-safe update: the manager will notify listeners
                        live_state.set_crossfader(val)
                        print(f"[MIDI] {port_name} -> Crossfader: {val:.2f} (CC {msg.control})")
                    else:
                        # Log other CCs to help the user identify their controller mapping
                        print(f"[MIDI] Control detectado: CC {msg.control} -> Valor {msg.value}")
    except Exception as e:
        print(f"[MIDI] Error en la conexión con {port_name}: {e}")
        live_state.active_port = None

async def midi_listener_task():
    """Starts the MIDI worker in a daemon thread."""
    # We use a thread because mido's input loop is blocking and doesn't have an async version for all OS
    t = threading.Thread(target=midi_worker, daemon=True)
    t.start()
    while True:
        await asyncio.sleep(10) # Just keep the task alive
