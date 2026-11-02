"""Export Markdown academic monograph to Microsoft Word (.docx)."""
import re
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn


def set_cell_background(cell, fill_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def add_formatted_text(paragraph, text):
    # Regex to handle bold, italic, and code spans
    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`|\$.*?\$)', text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**') and len(token) >= 4:
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        elif token.startswith('*') and token.endswith('*') and len(token) >= 2:
            run = paragraph.add_run(token[1:-1])
            run.italic = True
        elif token.startswith('`') and token.endswith('`') and len(token) >= 2:
            run = paragraph.add_run(token[1:-1])
            run.font.name = 'Consolas'
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(160, 40, 40)
        elif token.startswith('$') and token.endswith('$') and len(token) >= 2:
            run = paragraph.add_run(token[1:-1])
            run.italic = True
            run.font.name = 'Cambria Math'
        else:
            paragraph.add_run(token)


def markdown_to_docx(md_path: Path, docx_path: Path):
    doc = docx.Document()

    # Set page margins to standard A4 (2.5cm each side)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Set default style font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    font.color.rgb = RGBColor(30, 30, 30)

    lines = md_path.read_text(encoding='utf-8').splitlines()
    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []

    def flush_table(t_lines):
        if not t_lines:
            return
        rows_data = []
        for l in t_lines:
            # ignore separator line | :--- | :---: |
            if re.match(r'^\s*\|?\s*[-:]+[-| :]*\|?\s*$', l):
                continue
            cells = [c.strip() for c in l.strip().strip('|').split('|')]
            if any(cells):
                rows_data.append(cells)
        if not rows_data:
            return

        max_cols = max(len(r) for r in rows_data)
        table = doc.add_table(rows=len(rows_data), cols=max_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True

        for r_idx, row in enumerate(rows_data):
            for c_idx in range(max_cols):
                cell_text = row[c_idx] if c_idx < len(row) else ""
                cell = table.cell(r_idx, c_idx)
                cell.text = ""
                p = cell.paragraphs[0]
                p.paragraph_format.line_spacing = 1.1
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.space_before = Pt(2)
                add_formatted_text(p, cell_text)
                set_cell_margins(cell, top=80, bottom=80, left=120, right=120)

                # Header formatting
                if r_idx == 0:
                    set_cell_background(cell, "2B4C7E")  # Dark Blue
                    for r in p.runs:
                        r.font.bold = True
                        r.font.color.rgb = RGBColor(255, 255, 255)
                        r.font.size = Pt(10)
                else:
                    if r_idx % 2 == 1:
                        set_cell_background(cell, "F7F9FC")  # Light gray-blue
                    for r in p.runs:
                        r.font.size = Pt(10)

        # Space after table
        p_after = doc.add_paragraph()
        p_after.paragraph_format.space_after = Pt(6)

    for line in lines:
        stripped = line.strip()

        # Handle Code block
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(4)
                run = p.add_run("\n".join(code_lines))
                run.font.name = 'Consolas'
                run.font.size = Pt(9.5)
                run.font.color.rgb = RGBColor(40, 40, 40)
                code_lines = []
            else:
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # Handle Table
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_lines.append(stripped)
            continue
        else:
            if in_table:
                in_table = False
                flush_table(table_lines)
                table_lines = []

        # Handle Headings
        if stripped.startswith("# "):
            doc.add_page_break() if len(doc.paragraphs) > 5 else None
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(18)
            h.paragraph_format.space_after = Pt(10)
            h.paragraph_format.keep_with_next = True
            run = h.add_run(stripped[2:])
            run.bold = True
            run.font.size = Pt(18)
            run.font.color.rgb = RGBColor(20, 45, 90)
        elif stripped.startswith("## "):
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(14)
            h.paragraph_format.space_after = Pt(6)
            h.paragraph_format.keep_with_next = True
            run = h.add_run(stripped[3:])
            run.bold = True
            run.font.size = Pt(14)
            run.font.color.rgb = RGBColor(30, 60, 115)
        elif stripped.startswith("### "):
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(4)
            h.paragraph_format.keep_with_next = True
            run = h.add_run(stripped[4:])
            run.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(40, 75, 135)
        elif stripped.startswith("#### "):
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(6)
            h.paragraph_format.space_after = Pt(2)
            h.paragraph_format.keep_with_next = True
            run = h.add_run(stripped[5:])
            run.bold = True
            run.font.size = Pt(11)
            run.font.italic = True
        elif stripped.startswith("> "):
            # Blockquote
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.4)
            p.paragraph_format.right_indent = Inches(0.4)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            clean_text = stripped[2:].replace("[!NOTE]", "").replace("[!IMPORTANT]", "").strip()
            add_formatted_text(p, clean_text)
            for r in p.runs:
                r.italic = True
                r.font.size = Pt(10.5)
                r.font.color.rgb = RGBColor(70, 70, 70)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            # Bullet list
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_text(p, stripped[2:])
        elif re.match(r'^\d+\.\s', stripped):
            # Numbered list
            prefix_len = len(re.match(r'^\d+\.\s', stripped).group(0))
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_text(p, stripped[prefix_len:])
        elif stripped == "---":
            # Horizontal rule
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run("____________________________________________________________")
            run.font.color.rgb = RGBColor(200, 200, 200)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif stripped:
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.25
            p.paragraph_format.space_after = Pt(4)
            add_formatted_text(p, stripped)

    if in_table:
        flush_table(table_lines)

    docx_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(docx_path))
    print(f"[+] Da xuat thanh cong bao cao Word: {docx_path}")


if __name__ == "__main__":
    src = Path(__file__).resolve().parent / "tieu_luan_toi_uu_csdl.md"
    dst = Path(__file__).resolve().parent / "tieu_luan_toi_uu_csdl.docx"
    markdown_to_docx(src, dst)
