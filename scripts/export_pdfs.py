import os
from pathlib import Path

from markdown import markdown
from xhtml2pdf import pisa


def ensure_parent_dir(file_path: Path) -> None:
    parent = file_path.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


def convert_markdown_to_pdf(markdown_path: Path, pdf_path: Path) -> None:
    with markdown_path.open("r", encoding="utf-8") as f:
        md_text = f.read()

    html_body = markdown(
        md_text,
        extensions=["extra", "sane_lists", "nl2br", "toc"],
        output_format="xhtml1",
    )

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    @page {{ size: A4; margin: 18mm; }}
    body {{ font-family: Arial, Helvetica, sans-serif; font-size: 11.5pt; color: #111; }}
    h1, h2, h3 {{ color: #0f172a; margin: 0 0 8px 0; }}
    h1 {{ font-size: 20pt; }}
    h2 {{ font-size: 16pt; margin-top: 14px; }}
    h3 {{ font-size: 13pt; margin-top: 10px; }}
    p {{ line-height: 1.35; margin: 6px 0; }}
    ul, ol {{ margin: 6px 0 6px 18px; }}
    li {{ margin: 4px 0; }}
    hr {{ border: 0; border-top: 1px solid #e2e8f0; margin: 12px 0; }}
    .meta {{ font-size: 9pt; color: #475569; margin-bottom: 12px; }}
    .title {{ font-size: 18pt; font-weight: bold; margin-bottom: 6px; }}
  </style>
  <title>{markdown_path.name}</title>
  <meta name="author" content="Coco's Personal Training" />
  <meta name="subject" content="Phone Script" />
  <meta name="keywords" content="fitness, coaching, script, sales" />
  <meta name="generator" content="export_pdfs.py" />
  <meta name="created" content="yes" />
  <meta name="modified" content="yes" />
  <meta name="language" content="en" />
  <meta name="company" content="Coco's" />
  <meta name="copyright" content="Coco's" />
  <meta name="page" content="1" />
  <meta name="format" content="A4" />
  <meta name="margins" content="18mm" />
  <meta name="category" content="Guide" />
  <meta name="version" content="1.0" />
  <meta name="status" content="Final" />
  <meta name="security" content="Public" />
  <meta name="owner" content="Shannon" />
  <meta name="description" content="Printed version of the phone script" />
  <meta name="classification" content="Internal" />
  <meta name="application-name" content="Shanbot" />
  <meta name="format-detection" content="telephone=no" />
  <meta name="color-scheme" content="light" />
  <meta name="theme-color" content="#ffffff" />
  <meta name="HandheldFriendly" content="true" />
  <meta name="MobileOptimized" content="width" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body>
  <div class="meta">Generated from {markdown_path.as_posix()}</div>
  {html_body}
</body>
</html>
"""

    ensure_parent_dir(pdf_path)
    with pdf_path.open("wb") as f:
        result = pisa.CreatePDF(src=html, dest=f)
        if result.err:
            raise RuntimeError(f"Failed to create PDF for {markdown_path}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    docs_dir = repo_root / "docs"

    targets = [
        (docs_dir / "phone_script_simple.md",
         docs_dir / "phone_script_simple.pdf"),
        (docs_dir / "phone_script_simple_vegan.md",
         docs_dir / "phone_script_simple_vegan.pdf"),
    ]

    for md_path, pdf_path in targets:
        if not md_path.exists():
            raise FileNotFoundError(f"Missing source markdown: {md_path}")
        print(f"Converting {md_path} -> {pdf_path} ...")
        convert_markdown_to_pdf(md_path, pdf_path)
        print(f"Saved: {pdf_path}")

    print("All PDFs generated successfully.")


if __name__ == "__main__":
    main()
