"""
Forbin Document Chat — web interface
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

import gradio as gr

sys.path.insert(0, str(Path(__file__).parent))

def load_demo_questions(vertical: str) -> list:
    path = Path(f"demo/{vertical}/preguntas.txt")
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_demo_docs(engine, vertical: str):
    demo_dir = Path(f"demo/{vertical}")
    files = [
        f for f in list(demo_dir.glob("*.pdf")) + list(demo_dir.glob("*.txt"))
        if f.name not in ("preguntas.txt", "README.txt")
    ]
    for f in files:
        engine.ingest_document(str(f))


def build_app(demo_vertical=None):
    from app.rag_engine import RAGEngine
    from app.config import settings as cfg
    engine = RAGEngine()
    DOCS_DIR = Path(cfg.documents_dir)

    if demo_vertical:
        load_demo_docs(engine, demo_vertical)

    questions = load_demo_questions(demo_vertical) if demo_vertical else []

    def get_doc_list() -> str:
        docs = engine.list_documents()
        return "\n".join(f"• {d}" for d in sorted(docs)) if docs else "Sin documentos aún."

    def upload_file(file_path, history: list):
        if not file_path:
            return get_doc_list(), history
        src = Path(file_path)
        if src.suffix.lower() not in (".pdf", ".txt"):
            return get_doc_list(), list(history) + [
                {"role": "assistant", "content": f"⚠️ Tipo de archivo no permitido: '{src.suffix}'. Solo se aceptan PDF y TXT."}
            ]
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        dest = DOCS_DIR / src.name
        shutil.copy2(src, dest)
        engine.ingest_document(str(dest))
        return get_doc_list(), list(history) + [
            {"role": "assistant", "content": f"✅ Documento '{src.name}' cargado e indexado correctamente."}
        ]

    def respond(message: str, history: list) -> list:
        if not message.strip():
            return history
        if not engine.list_documents():
            return list(history) + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "⚠️ No hay documentos cargados. Subí un PDF o TXT primero."},
            ]
        result = engine.query(message)
        answer = result["answer"]
        if result["sources"]:
            answer += f"\n\n📎 *Fuente: {', '.join(result['sources'])}*"
        return list(history) + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": answer},
        ]

    with gr.Blocks(title="Forbin Document Chat", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🤖 Forbin Document Chat\n*Consultá tus documentos en lenguaje natural*")

        if demo_vertical and questions:
            gr.Markdown(f"**◆ Modo demo — Sector {demo_vertical.capitalize()}**")
            with gr.Row():
                example_btns = [gr.Button(q, size="sm") for q in questions[:5]]

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📎 Documentos")
                file_input = gr.File(label="Subir PDF o TXT", file_types=[".pdf", ".txt"])
                doc_list = gr.Textbox(
                    label="Indexados",
                    value=get_doc_list,
                    interactive=False,
                    lines=6,
                )

            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label="Chat", height=420, type="messages")

        with gr.Row():
            msg_box = gr.Textbox(
                placeholder="Escribí tu pregunta...",
                show_label=False,
                scale=4,
            )
            send_btn = gr.Button("Enviar", variant="primary", scale=1)

        if demo_vertical and questions:
            for btn in example_btns:
                btn.click(fn=lambda q=btn.value: q, outputs=msg_box)

        file_input.change(
            fn=upload_file,
            inputs=[file_input, chatbot],
            outputs=[doc_list, chatbot],
        )
        send_btn.click(
            fn=respond,
            inputs=[msg_box, chatbot],
            outputs=chatbot,
        ).then(fn=lambda: "", outputs=msg_box)
        msg_box.submit(
            fn=respond,
            inputs=[msg_box, chatbot],
            outputs=chatbot,
        ).then(fn=lambda: "", outputs=msg_box)

    return app


def main():
    parser = argparse.ArgumentParser(description="Forbin Document Chat — Web UI")
    parser.add_argument("--demo", choices=["legal", "industrial"],
                        help="Cargar demo por vertical al arrancar")
    parser.add_argument("--share", action="store_true",
                        help="Generar URL pública temporal (para demos remotas)")
    parser.add_argument("--port", type=int,
                        default=int(os.getenv("PORT", "7860")),
                        help="Puerto del servidor (default: 7860)")
    args = parser.parse_args()

    app = build_app(demo_vertical=args.demo)
    app.launch(server_port=args.port, share=args.share)


if __name__ == "__main__":
    main()
