"""Entry point del agente-book.

Uso:
    python main.py                           # Usa fechas por defecto (mañana, pasado)
    python main.py --checkin 20/03/2026 --checkout 22/03/2026 --guests 2
    python main.py --graph                   # Solo genera imagen del grafo
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta

from config import ALBARELLOS_URL
from graph import build_graph, get_graph_image


def default_dates() -> tuple[str, str]:
    """Genera check-in mañana, check-out pasado mañana."""
    tomorrow = datetime.now() + timedelta(days=1)
    day_after = tomorrow + timedelta(days=1)
    return tomorrow.strftime("%d/%m/%Y"), day_after.strftime("%d/%m/%Y")


async def run(check_in: str, check_out: str, guests: int) -> None:
    graph = build_graph()

    initial_state = {
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "hotel_url": ALBARELLOS_URL,
    }

    print(f"[*] Consultando Albarellos Delta...")
    print(f"    Check-in:  {check_in}")
    print(f"    Check-out: {check_out}")
    print(f"    Huéspedes: {guests}")
    print()

    result = await graph.ainvoke(initial_state)

    if result.get("error"):
        print(f"[!] Error: {result['error']}")

    if result.get("booking_result"):
        print("[+] Resultado:")
        print(json.dumps(result["booking_result"].model_dump(), indent=2, ensure_ascii=False))

    if result.get("screenshot_path"):
        print(f"[+] Screenshot: {result['screenshot_path']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agente-Book: consulta de precios en Booking")
    parser.add_argument("--checkin", type=str, help="Fecha check-in (dd/mm/yyyy)")
    parser.add_argument("--checkout", type=str, help="Fecha check-out (dd/mm/yyyy)")
    parser.add_argument("--guests", type=int, default=2, help="Cantidad de huéspedes")
    parser.add_argument("--graph", action="store_true", help="Solo generar imagen del grafo")
    args = parser.parse_args()

    if args.graph:
        path = get_graph_image("D:/tech-lab/agente-book/graph.png")
        print(f"[+] Grafo generado: {path}")
        return

    if args.checkin and args.checkout:
        check_in, check_out = args.checkin, args.checkout
    else:
        check_in, check_out = default_dates()

    asyncio.run(run(check_in, check_out, args.guests))


if __name__ == "__main__":
    main()
