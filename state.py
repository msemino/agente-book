"""Estado compartido del grafo de agentes."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class RoomOption(BaseModel):
    """Una opción de habitación con su precio y capacidad."""

    guests_max: int = Field(description="Capacidad máxima de huéspedes")
    price_text: str = Field(description="Precio tal como aparece en pantalla")
    price_value: int = Field(description="Precio numérico sin decimales")


class BookingResult(BaseModel):
    """Resultado estructurado de la consulta a Booking."""

    status: Literal["AVAILABLE", "OCCUPIED", "CAPTCHA", "ERROR"] = Field(
        description="Estado de disponibilidad del hotel"
    )
    best_price: str | None = Field(
        default=None, description="Mejor precio para la cantidad de huéspedes solicitada"
    )
    currency: str = Field(default="ARS", description="Moneda del precio")
    all_options: list[RoomOption] = Field(
        default_factory=list, description="Todas las opciones disponibles"
    )
    matched_options: list[RoomOption] = Field(
        default_factory=list, description="Opciones que cumplen la capacidad solicitada"
    )


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
