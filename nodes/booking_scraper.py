"""Nodo del grafo: scraper de precios en Booking.com usando browser-use."""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path

from browser_use import Agent, BrowserProfile, BrowserSession, ChatOllama

from config import EVIDENCIAS_DIR, HEADLESS, MAX_STEPS, OLLAMA_HOST, OLLAMA_MODEL
from state import BookingResult, GraphState


async def booking_scraper_node(state: GraphState) -> GraphState:
    """Nodo LangGraph: abre Booking, busca precio del hotel, devuelve resultado."""

    check_in = state["check_in"]
    check_out = state["check_out"]
    guests = state.get("guests", 2)
    hotel_url = state["hotel_url"]

    # Formatear fechas para la URL de Booking
    cin = datetime.strptime(check_in, "%d/%m/%Y").strftime("%Y-%m-%d")
    cout = datetime.strptime(check_out, "%d/%m/%Y").strftime("%Y-%m-%d")
    target_url = (
        f"{hotel_url}?checkin={cin}&checkout={cout}"
        f"&group_adults={guests}&no_rooms=1"
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # LLM local con Ollama en tu RTX 3090
    llm = ChatOllama(model=OLLAMA_MODEL, host=OLLAMA_HOST)

    # Browser con perfil limpio
    profile = BrowserProfile(headless=HEADLESS)
    browser = BrowserSession(browser_profile=profile)

    task = (
        f"Navegá a esta URL exacta: {target_url}\n"
        f"Esperá a que cargue la página del hotel.\n"
        f"Buscá el precio por noche para las fechas seleccionadas.\n"
        f"Si ves un precio, reportá status AVAILABLE y el precio.\n"
        f"Si dice que no hay disponibilidad, reportá status OCCUPIED.\n"
        f"Si aparece un CAPTCHA, reportá status CAPTCHA.\n"
        f"Si hay cualquier otro error, reportá status ERROR."
    )

    agent = Agent(
        task=task,
        llm=llm,
        browser_session=browser,
        use_vision=True,
        output_model_schema=BookingResult,
    )

    screenshot_path: str | None = None
    result: BookingResult | None = None
    error: str | None = None

    try:
        history = await agent.run(max_steps=MAX_STEPS)

        # Extraer resultado estructurado
        result = history.get_structured_output(BookingResult)
        if result is None:
            # Intentar desde final_result como fallback
            final = history.final_result()
            if final:
                try:
                    result = BookingResult.model_validate_json(final)
                except Exception:
                    result = BookingResult(status="ERROR")
                    error = f"No se pudo parsear respuesta: {final[:200]}"
            else:
                result = BookingResult(status="ERROR")
                error = "El agente no devolvió resultado"

        # Guardar último screenshot como evidencia
        shots = history.screenshots()
        if shots:
            last_shot = [s for s in shots if s is not None]
            if last_shot:
                img_path = EVIDENCIAS_DIR / f"audit_{ts}.png"
                img_path.write_bytes(base64.b64decode(last_shot[-1]))
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
