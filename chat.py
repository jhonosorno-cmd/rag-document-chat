"""
Forbin Document Chat — interactive console interface
"""
import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich import box
from rich.theme import Theme

sys.path.insert(0, str(Path(__file__).parent))

LOGO = """\
 ███████╗ ██████╗ ██████╗ ██████╗ ██╗███╗   ██╗
 ██╔════╝██╔═══██╗██╔══██╗██╔══██╗██║████╗  ██║
 █████╗  ██║   ██║██████╔╝██████╔╝██║██╔██╗ ██║
 ██╔══╝  ██║   ██║██╔══██╗██╔══██╗██║██║╚██╗██║
 ██║     ╚██████╔╝██║  ██║██████╔╝██║██║ ╚████║
 ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═══╝"""

_THEME = Theme({
    "prompt": "bold cyan",
    "source": "dim cyan",
    "cmd":    "bold yellow",
    "ok":     "bold green",
    "err":    "bold red",
    "muted":  "dim white",
})

console = Console(theme=_THEME)
DOCS_DIR = Path("data/documents")

HELP_TEXT = (
    "  [cmd]/upload[/cmd] [muted]<ruta>[/muted]              Subir un PDF o TXT\n"
    "  [cmd]/list[/cmd]                       Ver documentos indexados\n"
    "  [cmd]/delete[/cmd] [muted]<nombre>[/muted]             Eliminar un documento\n"
    "  [cmd]/demo[/cmd] [muted]legal|industrial[/muted]  Cargar demo por vertical\n"
    "  [cmd]/clear[/cmd]                      Limpiar pantalla\n"
    "  [cmd]/help[/cmd]                       Mostrar esta ayuda\n"
    "  [cmd]/quit[/cmd]                       Salir"
)


def print_logo():
    console.print()
    console.print(Text(LOGO, style="bold blue"))
    console.print()
    console.print("  Document Chat  ·  by Forbin  ·  v1.0", style="bold white")
    console.print()


def init_engine():
    with Live(
        Spinner("dots", text=Text(" Iniciando motor RAG...", style="muted")),
        console=console,
        transient=True,
    ):
        from app.rag_engine import RAGEngine
        return RAGEngine()


def main():
    parser = argparse.ArgumentParser(description="Forbin Document Chat")
    parser.add_argument("--demo", choices=["legal", "industrial"],
                        help="Cargar demo por vertical al arrancar")
    args = parser.parse_args()

    print_logo()

    try:
        engine = init_engine()
    except Exception as e:
        console.print(f"  [err]Error al iniciar:[/err] {e}")
        sys.exit(1)

    docs = engine.list_documents()
    count = len(docs)
    console.print(f"  [ok]✓[/ok]  [muted]{count} documento{'s' if count != 1 else ''} indexado{'s' if count != 1 else ''}[/muted]")
    console.print()
    console.print(Panel(HELP_TEXT, border_style="dim", box=box.ROUNDED, padding=(0, 1)))
    console.print()


if __name__ == "__main__":
    main()
