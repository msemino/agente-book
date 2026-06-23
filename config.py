"""Configuracion centralizada del proyecto."""

from pathlib import Path

# --- Hotel target ---
# Set this to the Booking.com URL of the property you want to audit.
HOTEL_URL = "https://www.booking.com/hotel/ar/example-hotel.es.html"

# --- Browser ---
HEADLESS = False  # False para ver el browser, True para produccion

# --- Paths ---
PROJECT_DIR = Path(__file__).parent
EVIDENCIAS_DIR = PROJECT_DIR / "evidencias"
EVIDENCIAS_DIR.mkdir(exist_ok=True)
