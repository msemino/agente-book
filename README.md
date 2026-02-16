# Agente-Book — Booking Price Auditor

> **Scraper inteligente de precios y disponibilidad en Booking.com** con grafo extensible LangGraph, filtrado por capacidad de huespedes y evidencia visual via Playwright.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-1.58-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0-orange?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Output Examples](#output-examples)
- [Project Structure](#project-structure)
- [Extending the Graph](#extending-the-graph)
- [Agent-Lightning Integration](#agent-lightning-integration)
- [Evolution Log](#evolution-log)
- [Credits](#credits)

---

## Overview

Agente-Book es un modulo de consulta de precios para Booking.com, diseñado como nodo de un grafo LangGraph extensible. Consulta un hotel target, extrae todos los precios disponibles filtrados por capacidad de huespedes, detecta estados (disponible, ocupado, CAPTCHA) y guarda screenshots como evidencia.

**Target actual:** [Albarellos Delta, Tigre](https://www.booking.com/hotel/ar/albarellos-delta.es.html) (configurable en `config.py`).

**Tiempo de consulta:** ~10 segundos por ejecucion.

---

## How It Works

```
  Input (fecha, huespedes)
          |
          v
  ┌───────────────────────────┐
  │      LangGraph Engine     │
  │                           │
  │   START                   │
  │     |                     │
  │     v                     │
  │  ┌─────────────────────┐  │
  │  │  booking_scraper    │  │   Playwright: navega a Booking.com
  │  │                     │  │   CSS Selectors: extrae precios por fila
  │  │  1. Abrir URL       │  │   Filtra por capacidad >= guests
  │  │  2. Detectar estado │  │   Screenshot full-page como evidencia
  │  │  3. Parsear tabla   │  │
  │  │  4. Filtrar precios │  │
  │  └─────────────────────┘  │
  │     |                     │
  │     v                     │
  │    END                    │
  │                           │
  └───────────────────────────┘
          |
          v
  Output (BookingResult + screenshot)
```

**Flujo de deteccion:**

1. Navega a la URL del hotel con fechas y huespedes inyectados
2. Espera carga completa (6s)
3. Detecta CAPTCHA → status `CAPTCHA`
4. Detecta "No tenemos disponibilidad" → status `OCCUPIED`
5. Extrae tabla `#hprt-table`:
   - Por cada fila: cuenta iconos de persona (capacidad) + extrae precio
   - Filtra opciones donde capacidad >= huespedes solicitados
   - Selecciona el precio mas bajo del subset filtrado
6. Screenshot full-page + resultado estructurado Pydantic

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Filtrado por capacidad** | Extrae precio correcto segun cantidad de huespedes (no el minimo global) |
| **Deteccion de estados** | AVAILABLE, OCCUPIED, CAPTCHA, ERROR con logica determinista |
| **Evidencia visual** | Screenshot full-page guardado en `evidencias/` con timestamp |
| **Grafo extensible** | LangGraph StateGraph: agregar nuevos nodos sin tocar el existente |
| **Todas las opciones** | Devuelve `all_options` y `matched_options` con desglose completo |
| **Zero LLM** | Playwright directo con CSS selectors. Sin API keys, sin VRAM, sin costo |
| **~10 seg/consulta** | vs ~10 min con LLM agent (v1 usaba browser-use + ChatOllama) |

---

## Architecture

```
agente-book/
│
├── main.py                 Entry point + CLI
│     |
│     v
├── graph.py                LangGraph StateGraph (compile + visualize)
│     |
│     v
├── nodes/
│   └── booking_scraper.py  Playwright scraper node
│         |
│         v
├── state.py                GraphState (TypedDict) + BookingResult + RoomOption (Pydantic)
│
├── config.py               URLs, flags, paths
└── evidencias/             Screenshots con timestamp (gitignored)
```

**Flujo de datos:**

```
GraphState {                        BookingResult {
  check_in: "07/03/2026"              status: "AVAILABLE"
  check_out: "08/03/2026"   ──>       best_price: "$ 167.433"
  guests: 4                           currency: "ARS"
  hotel_url: "..."                     all_options: [8 RoomOption]
}                                      matched_options: [2 RoomOption]
                                    }
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Scraping** | Playwright 1.58 | Browser automation, navegacion, screenshots |
| **Orchestration** | LangGraph 1.0 | Grafo de estados, extensibilidad multi-agente |
| **Data Models** | Pydantic 2.x | Validacion y serializacion de resultados |
| **Parsing** | CSS Selectors + Regex | Extraccion de precios y capacidad del DOM |
| **Runtime** | Python 3.11+ | Async/await nativo |

---

## Getting Started

### Prerequisites

- **Python 3.11+** — [python.org](https://python.org) (3.14 testeado y funcional)
- **Playwright Chromium** — se instala automaticamente

### Installation

```bash
# Clonar el repositorio
git clone https://github.com/msemino/agente-book.git
cd agente-book

# Instalar dependencias
pip install -r requirements.txt

# Instalar browser de Playwright
python -m playwright install chromium
```

### Configuration

Editar `config.py` para cambiar el hotel target:

```python
# Hotel target
ALBARELLOS_URL = "https://www.booking.com/hotel/ar/albarellos-delta.es.html"

# Browser
HEADLESS = False   # False para ver el browser, True para produccion
```

No se necesitan API keys ni `.env` — todo corre local.

---

## Usage

### Consulta basica (fechas por defecto: mañana)

```bash
python main.py
```

### Consulta con fechas y huespedes especificos

```bash
python main.py --checkin 07/03/2026 --checkout 08/03/2026 --guests 4
```

### Solo generar imagen del grafo

```bash
python main.py --graph
```

### Parametros CLI

| Parametro | Default | Descripcion |
|-----------|---------|-------------|
| `--checkin` | mañana | Fecha check-in (dd/mm/yyyy) |
| `--checkout` | pasado mañana | Fecha check-out (dd/mm/yyyy) |
| `--guests` | 2 | Cantidad de huespedes |
| `--graph` | - | Solo genera imagen del grafo LangGraph |

---

## Output Examples

### Disponible — 4 personas

```
[*] Consultando Albarellos Delta...
    Check-in:  07/03/2026
    Check-out: 08/03/2026
    Huespedes: 4

[+] Status: AVAILABLE
[+] Mejor precio para 4 personas: $ 167.433 ARS
[+] Opciones para 4+ personas:
      4 pers. -> $ 167.433
      4 pers. -> $ 200.919
[*] Todas las opciones:
      4 pers. -> $ 167.433
      4 pers. -> $ 200.919
      3 pers. -> $ 159.061
      3 pers. -> $ 190.873
      2 pers. -> $ 150.690
      2 pers. -> $ 180.827
      1 pers. -> $ 142.318
      1 pers. -> $ 170.782
[+] Screenshot: D:\tech-lab\agente-book\evidencias\audit_20260216_090609.png
```

### Ocupado

```
[*] Consultando Albarellos Delta...
    Check-in:  16/02/2026
    Check-out: 17/02/2026
    Huespedes: 2

[+] Status: OCCUPIED
[+] Screenshot: D:\tech-lab\agente-book\evidencias\audit_20260215_214333.png
```

### Resultado JSON (BookingResult)

```json
{
  "status": "AVAILABLE",
  "best_price": "$ 167.433",
  "currency": "ARS",
  "all_options": [
    {"guests_max": 4, "price_text": "$ 167.433", "price_value": 167433},
    {"guests_max": 4, "price_text": "$ 200.919", "price_value": 200919},
    {"guests_max": 3, "price_text": "$ 159.061", "price_value": 159061},
    {"guests_max": 2, "price_text": "$ 150.690", "price_value": 150690},
    {"guests_max": 1, "price_text": "$ 142.318", "price_value": 142318}
  ],
  "matched_options": [
    {"guests_max": 4, "price_text": "$ 167.433", "price_value": 167433},
    {"guests_max": 4, "price_text": "$ 200.919", "price_value": 200919}
  ]
}
```

---

## Project Structure

```
agente-book/
├── main.py                 # Entry point, CLI args, output formatting
├── graph.py                # LangGraph StateGraph builder + Mermaid export
├── state.py                # GraphState, BookingResult, RoomOption (Pydantic)
├── config.py               # Hotel URL, headless flag, paths
├── nodes/
│   ├── __init__.py         # Re-export de nodos
│   └── booking_scraper.py  # Playwright scraper: navegar, parsear, filtrar
├── evidencias/             # Screenshots con timestamp (gitignored)
├── requirements.txt        # browser-use, langgraph, pydantic
├── .gitignore
└── .env.example
```

---

## Extending the Graph

El grafo actual es lineal (`START -> booking_scraper -> END`). Para agregar nodos:

### 1. Crear un nuevo nodo en `nodes/`

```python
# nodes/price_alert.py
from state import GraphState

async def price_alert_node(state: GraphState) -> GraphState:
    """Envia alerta si el precio baja de un umbral."""
    br = state.get("booking_result")
    if br and br.matched_options:
        best = min(br.matched_options, key=lambda o: o.price_value)
        if best.price_value < 150000:
            # Enviar notificacion...
            pass
    return state
```

### 2. Conectarlo en `graph.py`

```python
from nodes.price_alert import price_alert_node

builder.add_node("price_alert", price_alert_node)
builder.add_edge("booking_scraper", "price_alert")
builder.add_edge("price_alert", END)
```

### 3. Agregar campos al estado si es necesario en `state.py`

```python
class GraphState(TypedDict, total=False):
    # ... campos existentes ...
    alert_sent: bool  # nuevo campo
```

### Ideas de nodos futuros

| Nodo | Funcion |
|------|---------|
| `price_comparator` | Comparar precios entre multiples hoteles |
| `price_history` | Guardar historico en SQLite y detectar tendencias |
| `alert_telegram` | Notificar por Telegram cuando hay disponibilidad |
| `multi_date_scan` | Escanear un rango de fechas en paralelo |
| `captcha_handler` | Pausar y esperar intervencion manual en CAPTCHA |

---

## Agent-Lightning Integration

Este proyecto esta preparado para integrarse con [Microsoft Agent-Lightning](https://github.com/microsoft/agent-lightning) cuando se necesite optimizar agentes con RL o fine-tuning.

### Que es Agent-Lightning

Framework de entrenamiento de agentes AI usando:
- **APO** (Automatic Prompt Optimization) — optimiza prompts con gradientes textuales
- **VERL** (Reinforcement Learning) — entrena agentes con GRPO
- **SFT** (Supervised Fine-tuning) — fine-tuning con Azure OpenAI, Unsloth, etc.

### Por que es relevante

Agent-Lightning tiene **soporte nativo para LangGraph** (que es lo que usamos). Los examples relevantes:

| Example | Relevancia |
|---------|-----------|
| [`spider`](https://github.com/microsoft/agent-lightning/tree/main/examples/spider) | LangGraph + RL para agente de Text-to-SQL. Mismo patron de grafo que usamos |
| [`chartqa`](https://github.com/microsoft/agent-lightning/tree/main/examples/chartqa) | LangGraph + vision para razonamiento multi-paso sobre datos visuales |
| [`rag`](https://github.com/microsoft/agent-lightning/tree/main/examples/rag) | Pipeline de retrieval que se puede adaptar para historico de precios |
| [`apo`](https://github.com/microsoft/agent-lightning/tree/main/examples/apo) | Optimizacion automatica de prompts (util si se vuelve a usar LLM) |

### Cuando usarlo

Si en el futuro se reintroduce un LLM en el grafo (por ejemplo un nodo de analisis de tendencias o decision de compra), Agent-Lightning permitiria:

1. **Instrumentar el grafo** con su tracer (AgentOps o OpenTelemetry)
2. **Registrar ejecuciones** como traces de entrenamiento
3. **Optimizar prompts** del nodo LLM con APO
4. **Fine-tunear** el modelo local con RL usando las ejecuciones reales como datos

```python
# Ejemplo futuro de instrumentacion
from agentlightning import AgentOpsTracer

tracer = AgentOpsTracer()
# El grafo LangGraph se instrumenta automaticamente
result = await graph.ainvoke(state)
tracer.record_reward(result)  # feedback para RL
```

---

## Evolution Log

| Version | Cambio | Resultado |
|---------|--------|-----------|
| **v1.0** | browser-use + ChatOllama (gemma3:27b) | OOM en RTX 3090 (27b + vision = 24GB+) |
| **v1.1** | Switch a gemma3:12b | Funciono pero 10 min/consulta, se perdia en loops |
| **v2.0** | Playwright directo, sin LLM | 10 seg/consulta, 100% confiable, 0 VRAM |
| **v2.1** | Filtrado por capacidad de huespedes | Precio correcto por cantidad de personas |
| **v2.1** | Screenshot full-page sin scroll | Captura completa, precio visible |

---

## Credits

- **Playwright** — [playwright.dev](https://playwright.dev) — Browser automation
- **LangGraph** — [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) — State graph orchestration
- **Pydantic** — [pydantic.dev](https://docs.pydantic.dev) — Data validation
- **Agent-Lightning** — [microsoft/agent-lightning](https://github.com/microsoft/agent-lightning) — Future RL/APO training integration
- **Built with** Claude Code (Opus 4.6) + RTX 3090 Tech Lab
