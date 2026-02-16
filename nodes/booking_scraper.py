"""Nodo del grafo: scraper de precios en Booking.com con Playwright directo.

Sin LLM. Navega, espera, parsea HTML con selectores CSS, extrae precios
filtrando por capacidad de huéspedes.
~10 segundos por consulta.
"""

from __future__ import annotations

import re
from datetime import datetime

from playwright.async_api import async_playwright

from config import EVIDENCIAS_DIR, HEADLESS
from state import BookingResult, GraphState, RoomOption

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


async def booking_scraper_node(state: GraphState) -> GraphState:
    """Nodo LangGraph: abre Booking, extrae precios filtrados por capacidad."""

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

            # --- Extraer precios por fila con capacidad ---
            else:
                rows = await page.query_selector_all(
                    "#hprt-table tr.js-rt-block-row, #hprt-table tr[data-block-id]"
                )

                all_options: list[RoomOption] = []

                for row in rows:
                    # Capacidad: contar iconos de persona en la celda de ocupación
                    person_icons = await row.query_selector_all(
                        ".hprt-occupancy-occupancy-info svg, "
                        ".hprt-occupancy-occupancy-info i"
                    )
                    guests_max = len(person_icons) if person_icons else 0

                    # Si no hay iconos, intentar parsear texto "Máximo de personas: N"
                    if guests_max == 0:
                        occ_cell = await row.query_selector("td.hprt-table-cell-occupancy")
                        if occ_cell:
                            occ_text = await occ_cell.text_content() or ""
                            m = re.search(r"(\d+)", occ_text)
                            if m:
                                guests_max = int(m.group(1))

                    # Precio
                    price_span = await row.query_selector("span.prco-valign-middle-helper")
                    if not price_span:
                        continue
                    price_text = (await price_span.text_content() or "").strip()
                    if not price_text:
                        continue

                    price_value = _parse_price(price_text)

                    all_options.append(RoomOption(
                        guests_max=guests_max,
                        price_text=price_text,
                        price_value=price_value,
                    ))

                if all_options:
                    # Filtrar opciones que cumplen la capacidad solicitada
                    matched = [o for o in all_options if o.guests_max >= guests]

                    # Detectar moneda
                    first = all_options[0].price_text
                    currency = "USD" if ("USD" in first or "US$" in first) else "ARS"

                    if matched:
                        best = min(matched, key=lambda o: o.price_value)
                        result = BookingResult(
                            status="AVAILABLE",
                            best_price=best.price_text,
                            currency=currency,
                            all_options=all_options,
                            matched_options=matched,
                        )
                    else:
                        # Hay opciones pero ninguna para esa cantidad de personas
                        best_any = min(all_options, key=lambda o: o.price_value)
                        result = BookingResult(
                            status="AVAILABLE",
                            best_price=best_any.price_text,
                            currency=currency,
                            all_options=all_options,
                            matched_options=[],
                        )
                        error = (
                            f"No hay opciones para {guests} personas. "
                            f"Máximo disponible: {max(o.guests_max for o in all_options)}. "
                            f"Mostrando mejor precio general."
                        )
                else:
                    result = BookingResult(status="ERROR")
                    error = "Tabla de precios no encontrada o vacía"

            # Screenshot como evidencia (sin scroll para capturar precio visible)
            img_path = EVIDENCIAS_DIR / f"audit_{ts}.png"
            await page.screenshot(path=str(img_path), full_page=True)
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


def _parse_price(text: str) -> int:
    """Extrae el valor numérico de un string de precio como '$ 142.318'."""
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0
