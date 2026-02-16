"""Configuracion centralizada del proyecto."""

from pathlib import Path

# --- Hotel target ---
ALBARELLOS_URL = "https://www.booking.com/hotel/ar/albarellos-delta.es.html"

# --- Browser ---
HEADLESS = False  # False para ver el browser, True para produccion

# --- Paths ---
PROJECT_DIR = Path(__file__).parent
EVIDENCIAS_DIR = PROJECT_DIR / "evidencias"
EVIDENCIAS_DIR.mkdir(exist_ok=True)
