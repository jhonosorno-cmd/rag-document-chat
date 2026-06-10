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


def load_demo_questions_from_path(path: Path) -> list:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_demo_questions(vertical: str) -> list:
    return load_demo_questions_from_path(Path(f"demo/{vertical}/preguntas.txt"))


def load_demo_docs(engine, vertical: str) -> int:
    demo_dir = Path(f"demo/{vertical}")
    files = [
        f for f in list(demo_dir.glob("*.pdf")) + list(demo_dir.glob("*.txt"))
        if f.name not in ("preguntas.txt", "README.txt")
    ]
    total = 0
    for f in files:
        total += engine.ingest_document(str(f))
    return total


def handle_demo(engine, vertical: str) -> list:
    vertical = vertical.strip().lower()
    if vertical not in ("legal", "industrial"):
        console.print(f"  [err]Demo no disponible:[/err] {vertical}  (opciones: legal, industrial)")
        console.print()
        return []

    demo_dir = Path(f"demo/{vertical}")
    if not demo_dir.exists():
        console.print(f"  [err]Carpeta no encontrada:[/err] demo/{vertical}/")
        console.print()
        return []

    with Live(
        Spinner("dots", text=Text(f" Cargando demo {vertical}...", style="muted")),
        console=console,
        transient=True,
    ):
        count = load_demo_docs(engine, vertical)

    questions = load_demo_questions(vertical)
    console.print(f"  [ok]✓[/ok]  Demo [bold]{vertical}[/bold] cargada — {count} chunks")

    if questions:
        console.print()
        console.print("  [muted]Preguntas sugeridas:[/muted]")
        for i, q in enumerate(questions, 1):
            console.print(f"    [bold cyan]{i}.[/bold cyan] {q}")
    console.print()
    return questions


def handle_query(engine, question: str):
    with Live(
        Spinner("dots2", text=Text(" Pensando...", style="muted")),
        console=console,
        transient=True,
    ):
        result = engine.query(question)

    console.print()
    console.print(Panel(
        Text(result["answer"], style="white"),
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    if result["sources"]:
        joined = "  ".join(f"[source]{s}[/source]" for s in result["sources"])
        console.print(f"  [muted]fuentes[/muted]  {joined}")
    console.print()


def chat_loop(engine, questions: list):
    while True:
        try:
            user_input = console.input("[prompt] you ›[/prompt] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print()
            console.print("  [muted]Hasta luego.[/muted]")
            console.print()
            break

        if not user_input:
            continue

        # Number shortcut: typing "1"-"9" sends the corresponding demo question
        if questions and user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(questions):
                user_input = questions[idx]
                console.print(f"  [muted]→ {user_input}[/muted]")

        if user_input.startswith("/"):
            parts = user_input[1:].split(" ", 1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ("quit", "exit", "q"):
                console.print()
                console.print("  [muted]Hasta luego.[/muted]")
                console.print()
                break
            elif cmd == "help":
                console.print(Panel(HELP_TEXT, border_style="dim", box=box.ROUNDED, padding=(0, 1)))
                console.print()
            elif cmd == "clear":
                console.clear()
                print_logo()
            elif cmd == "upload":
                handle_upload(engine, arg)
            elif cmd == "list":
                handle_list(engine)
            elif cmd == "delete":
                handle_delete(engine, arg)
            elif cmd == "demo":
                questions = handle_demo(engine, arg)
            else:
                console.print(f"  [err]Comando desconocido:[/err] /{cmd}  (escribe /help)")
                console.print()
        else:
            if not engine.list_documents():
                console.print("  [muted]No hay documentos. Usá /upload <ruta> para subir uno.[/muted]")
                console.print()
            else:
                handle_query(engine, user_input)


def handle_upload(engine, path_str: str):
    import shutil
    if not path_str.strip():
        console.print("  [err]Uso: /upload <ruta>[/err]")
        console.print()
        return

    src = Path(path_str.strip())
    if not src.exists():
        console.print(f"  [err]Archivo no encontrado:[/err] {src}")
        console.print()
        return

    if src.suffix.lower() not in (".pdf", ".txt"):
        console.print("  [err]Solo se aceptan archivos .pdf y .txt[/err]")
        console.print()
        return

    dest = DOCS_DIR / src.name
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with Live(
        Spinner("dots", text=Text(f" Ingiriendo {src.name}...", style="muted")),
        console=console,
        transient=True,
    ):
        shutil.copy2(src, dest)
        chunks = engine.ingest_document(str(dest))

    console.print(f"  [ok]✓[/ok]  [bold]{src.name}[/bold] — {chunks} chunks creados")
    console.print()


def handle_list(engine):
    docs = engine.list_documents()
    if not docs:
        console.print("  [muted]No hay documentos indexados.[/muted]")
        console.print()
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="dim", padding=(0, 1))
    table.add_column("#", style="dim", width=4)
    table.add_column("Documento", style="white")
    for i, doc in enumerate(sorted(docs), 1):
        table.add_row(str(i), doc)

    console.print(table)
    console.print()


def handle_delete(engine, name: str):
    if not name.strip():
        console.print("  [err]Uso: /delete <nombre-documento>[/err]")
        console.print()
        return

    name = Path(name.strip()).name
    with Live(
        Spinner("dots", text=Text(f" Eliminando {name}...", style="muted")),
        console=console,
        transient=True,
    ):
        deleted = engine.delete_document(name)
        if deleted:
            file_path = DOCS_DIR / name
            if file_path.exists():
                file_path.unlink()

    if deleted:
        console.print(f"  [ok]✓[/ok]  Eliminado [bold]{name}[/bold]")
    else:
        console.print(f"  [err]No encontrado:[/err] {name}")
    console.print()


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

    questions = []
    if args.demo:
        questions = handle_demo(engine, args.demo)

    chat_loop(engine, questions)


if __name__ == "__main__":
    main()
