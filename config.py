"""Configuración centralizada del proyecto."""

from pathlib import Path

# --- Hotel target ---
ALBARELLOS_URL = "https://www.booking.com/hotel/ar/albarellos-delta.es.html"

# --- LLM ---
OLLAMA_MODEL = "gemma3:12b"  # Multimodal (visión), cabe en 24GB VRAM con contexto
OLLAMA_HOST = "http://localhost:11434"

# --- Browser ---
HEADLESS = False  # False para ver qué hace, True para producción
MAX_STEPS = 20  # Pasos máximos del agente browser-use

# --- Paths ---
PROJECT_DIR = Path(__file__).parent
EVIDENCIAS_DIR = PROJECT_DIR / "evidencias"
EVIDENCIAS_DIR.mkdir(exist_ok=True)
