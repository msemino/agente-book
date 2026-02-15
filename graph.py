"""Grafo LangGraph del sistema de agentes.

Estructura actual:
    START -> booking_scraper -> END

Extensible: para agregar más agentes, crear un nodo nuevo en nodes/
y conectarlo acá con add_node / add_edge.
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from state import GraphState
from nodes import booking_scraper_node


def build_graph() -> StateGraph:
    """Construye y compila el grafo de agentes."""

    builder = StateGraph(GraphState)

    # --- Nodos ---
    builder.add_node("booking_scraper", booking_scraper_node)

    # --- Edges ---
    # Flujo lineal por ahora. Cuando agregues más agentes:
    #   builder.add_node("price_comparator", comparator_node)
    #   builder.add_edge("booking_scraper", "price_comparator")
    #   O usar add_conditional_edges para routing inteligente.
    builder.add_edge(START, "booking_scraper")
    builder.add_edge("booking_scraper", END)

    return builder.compile()


def get_graph_image(output_path: str = "graph.png") -> str:
    """Genera imagen PNG del grafo para visualización.

    Requiere: pip install pygraphviz  (o graphviz + grandalf como fallback)
    """
    graph = build_graph()
    try:
        png_data = graph.get_graph().draw_mermaid_png()
        with open(output_path, "wb") as f:
            f.write(png_data)
        return output_path
    except Exception as exc:
        # Fallback: devolver representación Mermaid en texto
        mermaid = graph.get_graph().draw_mermaid()
        md_path = output_path.replace(".png", ".md")
        with open(md_path, "w") as f:
            f.write(f"```mermaid\n{mermaid}\n```\n")
        print(f"No se pudo generar PNG ({exc}). Mermaid guardado en {md_path}")
        return md_path
