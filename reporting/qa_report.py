"""Valida e renderiza todas as páginas do PDF final para inspeção visual."""

from __future__ import annotations

import argparse
from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageDraw


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_PDF = BASE_DIR / "reports" / "final" / "lab02_relatorio_final.pdf"


def render_and_validate(pdf_path: Path, render_dir: Path) -> tuple[int, int]:
    render_dir.mkdir(parents=True, exist_ok=True)
    document = fitz.open(pdf_path)
    if document.page_count == 0:
        raise RuntimeError("O PDF não contém páginas")

    full_text: list[str] = []
    page_paths: list[Path] = []
    blank_pages: list[int] = []
    for index, page in enumerate(document):
        text = page.get_text().strip()
        full_text.append(text)
        if len(text) < 10 and not page.get_images(full=True):
            blank_pages.append(index + 1)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
        page_path = render_dir / f"pagina-{index + 1:02d}.png"
        pixmap.save(page_path)
        page_paths.append(page_path)

    if blank_pages:
        raise RuntimeError(f"Páginas vazias detectadas: {blank_pages}")

    joined = "\n".join(full_text)
    required = (
        "PUC Minas",
        "Assistentes de IA vs. Codificação Manual",
        "RQ1 — Tempo até green",
        "RQ2 — Resultado dos testes de aceitação",
        "RQ3 — Estrutura do código",
        "Inovação — Evolução por ciclos",
        "Referências",
    )
    missing = [item for item in required if item not in joined]
    if missing:
        raise RuntimeError(f"Conteúdo obrigatório ausente do PDF: {missing}")

    sheets = 0
    for start in range(0, len(page_paths), 4):
        group = page_paths[start:start + 4]
        thumbnails: list[Image.Image] = []
        for path in group:
            image = Image.open(path).convert("RGB")
            image.thumbnail((480, 680), Image.Resampling.LANCZOS)
            thumbnails.append(image.copy())
            image.close()

        sheet = Image.new("RGB", (1000, 1440), "#E8EDF2")
        draw = ImageDraw.Draw(sheet)
        for offset, thumbnail in enumerate(thumbnails):
            x = 15 + (offset % 2) * 495
            y = 35 + (offset // 2) * 700
            sheet.paste(thumbnail, (x, y))
            draw.text((x, 12 + (offset // 2) * 700), f"Página {start + offset + 1}", fill="#17365D")
        sheets += 1
        sheet.save(render_dir / f"contato-{sheets:02d}.png", quality=95)

    document.close()
    return len(page_paths), sheets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--render-dir", type=Path, required=True)
    args = parser.parse_args()
    pages, sheets = render_and_validate(args.pdf.resolve(), args.render_dir.resolve())
    print(f"PDF validado: {args.pdf.resolve()}")
    print(f"Páginas renderizadas: {pages}; folhas de contato: {sheets}; páginas vazias: 0")


if __name__ == "__main__":
    main()
