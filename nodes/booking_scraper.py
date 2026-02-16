"""Nodo del grafo: scraper de precios en Booking.com con Playwright directo.

Sin LLM. Navega, espera, parsea HTML con selectores CSS, extrae precios.
~5 segundos por consulta.
"""

from __future__ import annotations

import re
from datetime import datetime

from playwright.async_api import async_playwright

from config import EVIDENCIAS_DIR, HEADLESS
from state import BookingResult, GraphState

# User-Agent realista para evitar bloqueos básicos
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


async def booking_scraper_node(state: GraphState) -> GraphState:
    """Nodo LangGraph: abre Booking, extrae precio con selectores CSS."""

    check_in = state["check_in"]
    check_out = state["check_out"]
    guests = state.get("guests", 2)
    hotel_url = state["hotel_url"]

    cin = datetime.strptime(check_in, "%d/%m/%Y").strftime("%Y-%m-%d")
    cout = datetime.strptime(check_out, "%d/%m/%Y").strftime("%Y-%m-%d")
    target_url = (
        f"{hotel_url}?checkin={cin}&checkout={cout}"
        f"&group_adults={guests}&no_rooms=1"
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path: str | None = None
    result: BookingResult | None = None
    error: str | None = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        ctx = await browser.new_context(
            user_agent=_UA,
            viewport={"width": 1366, "height": 768},
            locale="es-AR",
        )
        page = await ctx.new_page()

        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(6000)

            body_text = await page.text_content("body") or ""

            # --- Detectar CAPTCHA ---
            if "captcha" in body_text.lower() or await page.query_selector("[id*=captcha]"):
                result = BookingResult(status="CAPTCHA")

            # --- Detectar no disponibilidad ---
            elif "no tenemos disponibilidad" in body_text.lower():
                result = BookingResult(status="OCCUPIED")

            # --- Extraer precios de la tabla ---
            else:
                price_spans = await page.query_selector_all(
                    "#hprt-table span.prco-valign-middle-helper"
                )
                prices: list[str] = []
                for span in price_spans:
                    text = (await span.text_content() or "").strip()
                    if text:
                        prices.append(text)

                if prices:
                    # Detectar moneda del primer precio
                    first = prices[0]
                    if "ARS" in first or "$" in first:
                        currency = "ARS"
                    elif "USD" in first or "US$" in first:
                        currency = "USD"
                    else:
                        currency = "ARS"

                    # Precio más bajo
                    min_price = min(prices, key=_parse_price)
                    result = BookingResult(
                        status="AVAILABLE",
                        price_text=min_price,
                        currency=currency,
                    )
                else:
                    result = BookingResult(status="ERROR")
                    error = "Tabla de precios no encontrada o vacía"

            # Screenshot como evidencia
            img_path = EVIDENCIAS_DIR / f"audit_{ts}.png"
            # Scrollear a la tabla si existe para capturarla
            table = await page.query_selector("#hprt-table")
            if table:
                await table.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
            await page.screenshot(path=str(img_path))
            screenshot_path = str(img_path)

        except Exception as exc:
            result = BookingResult(status="ERROR")
            error = f"{type(exc).__name__}: {exc}"
        finally:
            await browser.close()

    return {
        "booking_result": result,
        "screenshot_path": screenshot_path,
        "error": error,
    }


def _parse_price(text: str) -> float:
    """Extrae el valor numérico de un string de precio como '$ 142.318'."""
    digits = re.sub(r"[^\d]", "", text)
    return float(digits) if digits else float("inf")
