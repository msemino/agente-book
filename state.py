"""Estado compartido del grafo de agentes."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class BookingResult(BaseModel):
    """Resultado estructurado que el LLM debe devolver."""

    status: Literal["AVAILABLE", "OCCUPIED", "CAPTCHA", "ERROR"] = Field(
        description="Estado de disponibilidad del hotel"
    )
    price_text: str | None = Field(
        default=None, description="Texto del precio tal como aparece en pantalla"
    )
    currency: str = Field(default="ARS", description="Moneda del precio")


class GraphState(TypedDict, total=False):
    """Estado que fluye entre nodos del grafo.

    Extensible: agregar campos acá cuando se sumen nuevos agentes.
    """

    # --- Inputs ---
    check_in: str  # formato dd/mm/yyyy
    check_out: str  # formato dd/mm/yyyy
    guests: int
    hotel_url: str

    # --- Outputs del nodo booking_scraper ---
    booking_result: BookingResult | None
    screenshot_path: str | None
    error: str | None
