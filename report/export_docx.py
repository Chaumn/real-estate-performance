r"""
Export Markdown academic monograph to professional Microsoft Word (.docx).
Compliant with strict academic formatting standards:
- Native Word Heading 1-4 styles for dynamic Table of Contents
- Embedded native Word Table of Contents field (TOC \o "1-3" \h \z \u)
- Real image insertion with centered captions placed below images
- Standard academic tables with captions above, cantSplit, tblHeader, and zebra striping
- Header and footer with centered page numbering (PAGE / NUMPAGES), excluding cover page
- Full font XML definition (Times New Roman ascii/hAnsi/cs/eastAsia) for all text runs
- Explicit xml:space="preserve" to prevent space loss around formatted runs
- Preserved token whitespace (no stripping in clean_math_syntax)
- Sequential list numbering restarted per list (no cross-chapter accumulation)
- LaTeX math symbol translation and HTML/Markdown cleanup
- Times New Roman, A4 margins (1 inch)
"""
import os
import re
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

ROOT_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = Path(__file__).resolve().parent


def set_cell_background(cell, fill_hex):
    """Set background color of a table cell."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    """Set inner margins (padding) of a table cell in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_border(cell, **kwargs):
    """
    Set cell borders.
    kwargs: top, bottom, left, right
    values: dict(sz=12, val='single', color='CCCCCC')
    """
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = 'w:{}'.format(edge)
            element = OxmlElement(tag)
            element.set(qn('w:val'), edge_data.get('val', 'single'))
            element.set(qn('w:sz'), str(edge_data.get('sz', 4)))
            element.set(qn('w:space'), '0')
            element.set(qn('w:color'), edge_data.get('color', 'CCCCCC'))
            tcBorders.append(element)
    tcPr.append(tcBorders)


def make_row_cant_split(row):
    """Prevent table row from splitting across page breaks."""
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement('w:cantSplit'))


def make_row_header(row):
    """Mark table row as a repeating header row."""
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement('w:tblHeader'))


def clean_math_syntax(text: str) -> str:
    """Translate LaTeX math expressions into clean readable Unicode math text without stripping whitespace."""
    replacements = [
        (r'\\le', '≤'),
        (r'\\ge', '≥'),
        (r'\\times', '×'),
        (r'\\rho', 'ρ'),
        (r'\\approx', '≈'),
        (r'\\in', '∈'),
        (r'\\subset', '⊂'),
        (r'\\sum', '∑'),
        (r'\\Delta', 'Δ'),
        (r'\\mathcal\{D\}', 'D'),
        (r'\\odot', '⊙'),
        (r'\\cdot', '·'),
        (r'\\lceil', '⌈'),
        (r'\\rceil', '⌉'),
        (r'\\gg', '≫'),
        (r'\\ll', '≪'),
        (r'\\neq', '≠'),
        (r'\\pm', '±'),
        (r'\\rightarrow', '→'),
        (r'\\to', '→'),
        (r'\\mu', 'μ'),
        (r'\\sigma', 'σ'),
        (r'\\alpha', 'α'),
        (r'\\beta', 'β'),
        (r'\\log', 'log'),
        (r'\\text\{([^}]*)\}', r'\1'),
        (r'\\mathrm\{([^}]*)\}', r'\1'),
        (r'\\mathbf\{([^}]*)\}', r'\1'),
        (r'\\quad', '  '),
        (r'\\,', ' '),
        (r'\\_', '_'),
    ]
    for pat, rep in replacements:
        text = re.sub(pat, rep, text)

    # Clean any residual LaTeX braces (e.g. N_{page_seq} -> N_page_seq)
    text = re.sub(r'\{([^}]+)\}', r'\1', text)

    # Super/subscripts
    text = text.replace('^2', '²').replace('^3', '³').replace('_1', '₁').replace('_2', '₂').replace('_3', '₃')
    text = text.replace('m^2', 'm²').replace('m2', 'm²')

    # Remove outer dollar signs without stripping boundary whitespace
    def _strip_double_dollars(m):
        return m.group(1)

    def _strip_single_dollars(m):
        return m.group(1)

    text = re.sub(r'\$\$([^\$]+)\$\$', _strip_double_dollars, text)
    text = re.sub(r'\$([^\$]+)\$', _strip_single_dollars, text)

    return text


def clean_markdown_links(text: str) -> str:
    """Replace [Label](URL) with just Label and strip file:/// paths."""
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'file:///[^\s)]+', '', text)
    text = re.sub(r'<\/?br\s*\/?>', ' ', text, flags=re.IGNORECASE)
    return text


def format_run(run, font_name='Times New Roman', font_size_pt=12, bold=False, italic=False, color_rgb=None):
    """Set font properties and enforce full OpenXML font declarations and space preservation."""
    run.font.name = font_name
    run.font.size = Pt(font_size_pt)
    run.bold = bold
    run.italic = italic
    if color_rgb:
        run.font.color.rgb = color_rgb

    # Enforce rFonts for Latin, High ANSI, and Complex Scripts (Vietnamese Unicode)
    # Never set eastAsia on Latin text to prevent Word's CJK line-breaking engine from splitting words!
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rFonts.set(qn('w:cs'), font_name)
    if qn('w:eastAsia') in rFonts.attrib:
        del rFonts.attrib[qn('w:eastAsia')]

    # Set proofing language to Vietnamese
    lang = rPr.find(qn('w:lang'))
    if lang is None:
        lang = OxmlElement('w:lang')
        rPr.append(lang)
    lang.set(qn('w:val'), 'vi-VN')

    # Ensure xml:space="preserve" is set so leading/trailing spaces are never stripped
    t = run._r.find(qn('w:t'))
    if t is not None:
        t.set(qn('xml:space'), 'preserve')


def add_formatted_text(paragraph, text, base_font_size=12, italic_all=False, bold_all=False, default_color=None):
    """Add run tokens with bold, italic, code styling, and clean math."""
    text = clean_markdown_links(text)

    # Split by bold, italic, code: **...**, *...*, `...`
    token_pattern = r'(\*\*.*?\*\*|\*.*?\*|`.*?`)'
    tokens = re.split(token_pattern, text)

    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**') and len(token) >= 4:
            inner = clean_math_syntax(token[2:-2])
            run = paragraph.add_run(inner)
            format_run(run, 'Times New Roman', base_font_size, bold=True, italic=italic_all, color_rgb=default_color)
        elif token.startswith('*') and token.endswith('*') and len(token) >= 2:
            inner = clean_math_syntax(token[1:-1])
            run = paragraph.add_run(inner)
            format_run(run, 'Times New Roman', base_font_size, bold=bold_all, italic=True, color_rgb=default_color)
        elif token.startswith('`') and token.endswith('`') and len(token) >= 2:
            inner = token[1:-1]
            run = paragraph.add_run(inner)
            format_run(run, 'Consolas', base_font_size - 1.5, bold=bold_all, italic=italic_all, color_rgb=RGBColor(160, 40, 40))
        else:
            cleaned = clean_math_syntax(token)
            run = paragraph.add_run(cleaned)
            format_run(run, 'Times New Roman', base_font_size, bold=bold_all, italic=italic_all, color_rgb=default_color)


def add_toc_field(doc):
    """Insert a native Word Table of Contents field that updates automatically."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(12)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = p.add_run("[ Nhấn F9 hoặc chuột phải chọn 'Update Field' để cập nhật Mục lục tự động ]\n")
    format_run(run, 'Times New Roman', 10, italic=True, color_rgb=RGBColor(100, 100, 100))

    fld_p = doc.add_paragraph()
    fld_p.paragraph_format.space_after = Pt(12)

    # Word XML TOC field: TOC \o "1-3" \h \z \u
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), r'TOC \o "1-3" \h \z \u')
    fld_p._p.append(fldSimple)


def setup_header_footer(doc):
    """Set up header text and footer page numbering, excluding cover page."""
    for section in doc.sections:
        section.different_first_page_header_footer = True

        # Header (Pages 2+)
        header = section.header
        header.is_linked_to_previous = False
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("Tiểu luận: Tối ưu hiệu năng Hệ quản trị cơ sở dữ liệu lớn — PTIT 2026")
        format_run(hrun, 'Times New Roman', 8.5, italic=True, color_rgb=RGBColor(140, 140, 140))

        # Footer (Pages 2+)
        footer = section.footer
        footer.is_linked_to_previous = False
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER

        f_run1 = fp.add_run("Trang ")
        format_run(f_run1, 'Times New Roman', 9.5, color_rgb=RGBColor(100, 100, 100))

        fld_page = OxmlElement('w:fldSimple')
        fld_page.set(qn('w:instr'), 'PAGE')
        fp._p.append(fld_page)

        f_run2 = fp.add_run(" / ")
        format_run(f_run2, 'Times New Roman', 9.5, color_rgb=RGBColor(100, 100, 100))

        fld_numpages = OxmlElement('w:fldSimple')
        fld_numpages.set(qn('w:instr'), 'NUMPAGES')
        fp._p.append(fld_numpages)


def resolve_image_path(raw_path: str) -> Path | None:
    """Resolve image path from markdown link or file URL."""
    cleaned = raw_path.strip().replace('file:///', '').replace('file://', '')
    p = Path(cleaned)
    if p.is_file():
        return p

    p_rel = ROOT_DIR / cleaned
    if p_rel.is_file():
        return p_rel

    filename = p.name
    for match in ROOT_DIR.glob(f"results/**/{filename}"):
        if match.is_file():
            return match

    return None


def assemble_full_markdown() -> Path:
    """Concatenate 00 through 08 markdown chapter files into tieu_luan_toi_uu_csdl.md."""
    chapter_files = sorted(REPORT_DIR.glob("0[0-8]_*.md"))
    consolidated_path = REPORT_DIR / "tieu_luan_toi_uu_csdl.md"

    parts = []
    for f in chapter_files:
        content = f.read_text(encoding="utf-8").strip()
        parts.append(content)

    full_text = "\n\n---\n\n".join(parts) + "\n"
    consolidated_path.write_text(full_text, encoding="utf-8")
    print(f"[+] Da gop {len(chapter_files)} chuong vao: {consolidated_path} ({len(full_text):,} ky tu)")
    return consolidated_path


def markdown_to_docx(md_path: Path, docx_path: Path):
    """Convert consolidated markdown to a polished Word document."""
    doc = docx.Document()

    # Configure page margins to standard A4 (1 inch = 2.54 cm)
    for section in doc.sections:
        section.page_width = Inches(8.27)   # A4 Width
        section.page_height = Inches(11.69) # A4 Height
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    setup_header_footer(doc)

    # Configure Normal Style Font
    normal_style = doc.styles['Normal']
    normal_font = normal_style.font
    normal_font.name = 'Times New Roman'
    normal_font.size = Pt(12)
    normal_font.color.rgb = RGBColor(30, 30, 30)

    # Configure Heading Styles
    heading_configs = {
        'Heading 1': {'size': 16.0, 'color': RGBColor(20, 45, 90), 'bold': True},
        'Heading 2': {'size': 13.5, 'color': RGBColor(30, 60, 115), 'bold': True},
        'Heading 3': {'size': 12.0, 'color': RGBColor(40, 75, 135), 'bold': True},
        'Heading 4': {'size': 11.0, 'color': RGBColor(50, 85, 150), 'bold': True, 'italic': True},
    }
    for hname, cfg in heading_configs.items():
        if hname in doc.styles:
            hstyle = doc.styles[hname]
            hfont = hstyle.font
            hfont.name = 'Times New Roman'
            hfont.size = Pt(cfg['size'])
            hfont.bold = cfg['bold']
            hfont.color.rgb = cfg['color']
            if cfg.get('italic'):
                hfont.italic = True

    lines = md_path.read_text(encoding='utf-8').splitlines()

    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []
    pending_table_title = None

    def flush_table(t_lines, title=None):
        if not t_lines:
            return
        rows_data = []
        for l in t_lines:
            if re.match(r'^\s*\|?\s*[-:]+[-| :]*\|?\s*$', l):
                continue
            cells = [c.strip() for c in l.strip().strip('|').split('|')]
            if any(cells):
                rows_data.append(cells)
        if not rows_data:
            return

        # Add table caption ABOVE table
        if title:
            p_title = doc.add_paragraph()
            p_title.paragraph_format.space_before = Pt(10)
            p_title.paragraph_format.space_after = Pt(3)
            p_title.paragraph_format.keep_with_next = True
            add_formatted_text(p_title, title, base_font_size=10.5, bold_all=True)

        max_cols = max(len(r) for r in rows_data)
        table = doc.add_table(rows=len(rows_data), cols=max_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True

        for r_idx, row in enumerate(rows_data):
            tr = table.rows[r_idx]
            make_row_cant_split(tr)
            if r_idx == 0:
                make_row_header(tr)

            for c_idx in range(max_cols):
                cell_text = row[c_idx] if c_idx < len(row) else ""
                cell = table.cell(r_idx, c_idx)
                cell.text = ""
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                p = cell.paragraphs[0]
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.space_before = Pt(2)

                # Set cell padding and subtle borders
                set_cell_margins(cell, top=70, bottom=70, left=100, right=100)
                set_cell_border(cell,
                                top={'sz': 4, 'val': 'single', 'color': 'D0D7DE'},
                                bottom={'sz': 4, 'val': 'single', 'color': 'D0D7DE'},
                                left={'sz': 4, 'val': 'single', 'color': 'D0D7DE'},
                                right={'sz': 4, 'val': 'single', 'color': 'D0D7DE'})

                if r_idx == 0:
                    # Header styling: Dark Navy background, bold white text
                    set_cell_background(cell, "2B4C7E")
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    add_formatted_text(p, cell_text, base_font_size=9.5, bold_all=True, default_color=RGBColor(255, 255, 255))
                    for r in p.runs:
                        r.font.color.rgb = RGBColor(255, 255, 255)
                else:
                    # Data row styling with alternating zebra
                    if r_idx % 2 == 1:
                        set_cell_background(cell, "F8FAFD")
                    else:
                        set_cell_background(cell, "FFFFFF")

                    # Centering for numeric, code, or short tag cells
                    if re.match(r'^\s*(\d+[\d\.,]*%?|[-—]|[\d\.]+\s*(ms|blk|MB|x)|(Q\d.*))\s*$', cell_text, flags=re.IGNORECASE):
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    add_formatted_text(p, cell_text, base_font_size=9.5)

        # Space after table
        p_after = doc.add_paragraph()
        p_after.paragraph_format.space_after = Pt(6)

    idx = 0
    total_lines = len(lines)
    is_cover_page = True
    seen_ha_noi = False
    page_break_pending = False
    skip_markdown_toc = False

    while idx < total_lines:
        line = lines[idx]
        stripped = line.strip()

        # Handle Cover Page until horizontal rule (---) AFTER "Hà Nội"
        if is_cover_page:
            clean_l = clean_markdown_links(stripped).replace('<br>', '').replace('<br/>', '').strip()

            if "HÀ NỘI" in clean_l.upper():
                seen_ha_noi = True

            if stripped in ("---", "***"):
                if seen_ha_noi:
                    is_cover_page = False
                    doc.add_page_break()
                    page_break_pending = True
                    idx += 1
                    continue
                else:
                    # Decorative line under KHOA CÔNG NGHỆ THÔNG TIN
                    p_div = doc.add_paragraph()
                    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_div.paragraph_format.space_before = Pt(2)
                    p_div.paragraph_format.space_after = Pt(16)
                    run_div = p_div.add_run("______________________________")
                    format_run(run_div, 'Times New Roman', 9, bold=True, color_rgb=RGBColor(40, 75, 135))
                    idx += 1
                    continue

            if not clean_l:
                idx += 1
                continue

            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            clean_text = clean_l.lstrip('#').strip()
            upper_c = clean_text.upper()

            if "BỘ GIÁO DỤC" in upper_c or "HỌC VIỆN" in upper_c:
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(2)
                add_formatted_text(p, clean_text, base_font_size=13.0, bold_all=True)
            elif "KHOA CÔNG NGHỆ" in upper_c:
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(4)
                add_formatted_text(p, clean_text, base_font_size=12.5, bold_all=True)
            elif "TIỂU LUẬN" in upper_c:
                p.paragraph_format.space_before = Pt(20)
                p.paragraph_format.space_after = Pt(3)
                add_formatted_text(p, clean_text, base_font_size=15.0, bold_all=True, default_color=RGBColor(20, 45, 90))
            elif "NHẬP MÔN" in upper_c:
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(22)
                add_formatted_text(p, clean_text, base_font_size=12.5, bold_all=True, default_color=RGBColor(30, 60, 115))
            elif "ĐỀ TÀI" in upper_c:
                p.paragraph_format.space_before = Pt(10)
                p.paragraph_format.space_after = Pt(3)
                add_formatted_text(p, clean_text, base_font_size=14.0, bold_all=True)
            elif "XÂY DỰNG BỘ DỮ LIỆU" in upper_c:
                p.paragraph_format.space_before = Pt(3)
                p.paragraph_format.space_after = Pt(30)
                add_formatted_text(p, clean_text, base_font_size=14.5, bold_all=True, default_color=RGBColor(20, 45, 90))
            elif any(k in clean_text for k in ("Sinh viên thực hiện", "Mã sinh viên", "Chuyên ngành", "Giảng viên hướng dẫn")):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.left_indent = Inches(1.3)
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                add_formatted_text(p, clean_text, base_font_size=11.5)
            elif "HÀ NỘI" in upper_c:
                p.paragraph_format.space_before = Pt(35)
                p.paragraph_format.space_after = Pt(4)
                add_formatted_text(p, clean_text, base_font_size=12.0, bold_all=True)
            else:
                add_formatted_text(p, clean_text, base_font_size=12.0)

            idx += 1
            continue

        # Skip markdown bullet TOC lines if native Word TOC field is already inserted
        if skip_markdown_toc:
            if stripped.startswith("## ") or stripped.startswith("# "):
                skip_markdown_toc = False
            else:
                idx += 1
                continue

        # Handle Code block
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                if code_lines:
                    for cl_idx, c_line in enumerate(code_lines):
                        p = doc.add_paragraph()
                        p.paragraph_format.left_indent = Inches(0.3)
                        p.paragraph_format.right_indent = Inches(0.3)
                        p.paragraph_format.space_before = Pt(4 if cl_idx == 0 else 0)
                        p.paragraph_format.space_after = Pt(6 if cl_idx == len(code_lines) - 1 else 0)
                        p.paragraph_format.line_spacing = 1.05
                        run = p.add_run(c_line if c_line else " ")
                        format_run(run, 'Consolas', 8.5, color_rgb=RGBColor(40, 40, 40))
                code_lines = []
            else:
                in_code_block = True
                code_lines = []
            idx += 1
            continue

        if in_code_block:
            code_lines.append(line)
            idx += 1
            continue

        # Check Table Caption line (e.g. **Bảng 3.1: ...**)
        if re.match(r'^\*\*Bảng\s+\d+\.\d+[:\s]', stripped):
            pending_table_title = stripped
            idx += 1
            continue

        # Check Table row
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_lines.append(stripped)
            idx += 1
            continue
        else:
            if in_table:
                in_table = False
                flush_table(table_lines, pending_table_title)
                table_lines = []
                pending_table_title = None
                page_break_pending = False

        # Check Image syntax: ![caption](url)
        img_match = re.match(r'^!\[(.*?)\]\((.*?)\)$', stripped)
        if img_match:
            img_caption = img_match.group(1).strip()
            raw_url = img_match.group(2).strip()
            resolved = resolve_image_path(raw_url)

            if resolved and resolved.is_file():
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(10)
                p_img.paragraph_format.space_after = Pt(4)
                p_img.paragraph_format.keep_with_next = True
                p_img.add_run().add_picture(str(resolved), width=Inches(5.8))

                next_caption = None
                if idx + 1 < total_lines:
                    next_stripped = lines[idx + 1].strip()
                    if re.match(r'^\*Hình\s+\d+\.\d+[:\s]', next_stripped):
                        next_caption = next_stripped
                        idx += 1

                final_caption = next_caption if next_caption else f"*Hình: {img_caption}*"

                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_before = Pt(2)
                p_cap.paragraph_format.space_after = Pt(10)
                add_formatted_text(p_cap, final_caption, base_font_size=9.5, italic_all=True, default_color=RGBColor(80, 80, 80))
            else:
                p_missing = doc.add_paragraph()
                p_missing.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_formatted_text(p_missing, f"[Biểu đồ: {img_caption}]", base_font_size=10, italic_all=True)

            page_break_pending = False
            idx += 1
            continue

        # Handle Headings
        if stripped.startswith("# "):
            heading_text = stripped[2:].strip()
            upper_h = heading_text.upper()

            # Chapter break: add page break before each Chapter / References / Appendix
            if any(k in upper_h for k in ("CHƯƠNG", "TÀI LIỆU THAM KHẢO", "PHỤ LỤC")):
                if not page_break_pending:
                    doc.add_page_break()
                    page_break_pending = True

            h = doc.add_heading(level=1)
            h.paragraph_format.space_before = Pt(16)
            h.paragraph_format.space_after = Pt(8)
            h.paragraph_format.keep_with_next = True
            add_formatted_text(h, heading_text, base_font_size=16.0, bold_all=True)
            page_break_pending = False
            idx += 1
            continue

        elif stripped.startswith("## "):
            heading_text = stripped[3:].strip()
            upper_h = heading_text.upper()

            # Front-matter sections (Abstract, Acknowledgements, TOC, Abbr, Tables, Figures)
            is_front_matter = any(k in upper_h for k in ("TÓM TẮT", "LỜI CẢM ƠN", "MỤC LỤC", "DANH MỤC"))
            if is_front_matter or "CHƯƠNG" in upper_h:
                if not page_break_pending:
                    doc.add_page_break()
                    page_break_pending = True

            # If this is the TOC heading itself, do not make it Heading 1 (so TOC doesn't list itself)
            if "MỤC LỤC" in upper_h:
                h_p = doc.add_paragraph()
                h_p.paragraph_format.space_before = Pt(16)
                h_p.paragraph_format.space_after = Pt(6)
                h_p.paragraph_format.keep_with_next = True
                add_formatted_text(h_p, heading_text, base_font_size=16.0, bold_all=True, default_color=RGBColor(20, 45, 90))
                add_toc_field(doc)
                skip_markdown_toc = True
                page_break_pending = False
                idx += 1
                continue

            lvl = 1 if is_front_matter else 2
            fsize = 15.0 if is_front_matter else 13.5
            h = doc.add_heading(level=lvl)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(5)
            h.paragraph_format.keep_with_next = True
            add_formatted_text(h, heading_text, base_font_size=fsize, bold_all=True)
            page_break_pending = False
            idx += 1
            continue

        elif stripped.startswith("### "):
            heading_text = stripped[4:].strip()
            h = doc.add_heading(level=3)
            h.paragraph_format.space_before = Pt(9)
            h.paragraph_format.space_after = Pt(4)
            h.paragraph_format.keep_with_next = True
            add_formatted_text(h, heading_text, base_font_size=12.0, bold_all=True)
            page_break_pending = False
            idx += 1
            continue

        elif stripped.startswith("#### "):
            heading_text = stripped[5:].strip()
            h = doc.add_heading(level=4)
            h.paragraph_format.space_before = Pt(6)
            h.paragraph_format.space_after = Pt(2)
            h.paragraph_format.keep_with_next = True
            add_formatted_text(h, heading_text, base_font_size=11.0, bold_all=True, italic_all=True)
            page_break_pending = False
            idx += 1
            continue

        # Handle Blockquote (> ...)
        elif stripped.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.35)
            p.paragraph_format.right_indent = Inches(0.35)
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            clean_text = stripped[2:].replace("[!NOTE]", "LƯU Ý:").replace("[!IMPORTANT]", "QUAN TRỌNG:").strip()
            add_formatted_text(p, clean_text, base_font_size=10.5, italic_all=True, default_color=RGBColor(60, 60, 60))
            page_break_pending = False
            idx += 1
            continue

        # Handle Bullet List
        elif stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = stripped[2:].strip()
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_text(p, bullet_text, base_font_size=11.5)
            page_break_pending = False
            idx += 1
            continue

        # Handle Numbered List with explicit bold number run
        elif re.match(r'^\d+\.\s', stripped):
            num_match = re.match(r'^\d+\.\s', stripped)
            prefix = num_match.group(0)
            num_text = stripped[len(prefix):].strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            run_prefix = p.add_run(prefix)
            format_run(run_prefix, 'Times New Roman', 11.5, bold=True)
            add_formatted_text(p, num_text, base_font_size=11.5)
            page_break_pending = False
            idx += 1
            continue

        # Handle Display Math ($$ ... $$)
        elif stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) >= 4:
            math_content = clean_math_syntax(stripped[2:-2].strip())
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(math_content)
            format_run(run, 'Cambria Math', 11.5, bold=True, italic=True, color_rgb=RGBColor(20, 50, 100))
            page_break_pending = False
            idx += 1
            continue

        # Handle Horizontal Rule
        elif stripped in ("---", "***"):
            next_is_break_heading = False
            for peek_idx in range(idx + 1, min(idx + 5, total_lines)):
                peek_line = lines[peek_idx].strip()
                if not peek_line:
                    continue
                if peek_line.startswith("# ") or peek_line.startswith("## "):
                    peek_upper = peek_line.upper()
                    if any(k in peek_upper for k in ("CHƯƠNG", "TÀI LIỆU THAM KHẢO", "PHỤ LỤC", "TÓM TẮT", "LỜI CẢM ƠN", "MỤC LỤC", "DANH MỤC")):
                        next_is_break_heading = True
                break

            if not next_is_break_heading:
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(4)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run("____________________________________________________________")
                format_run(run, 'Times New Roman', 8, color_rgb=RGBColor(210, 215, 220))
            idx += 1
            continue

        # Normal text paragraph
        elif stripped:
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.25
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_formatted_text(p, stripped, base_font_size=12)
            page_break_pending = False
            idx += 1
            continue

        idx += 1

    if in_table:
        flush_table(table_lines, pending_table_title)

    docx_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(docx_path))
    print(f"[+] Da xuat thanh cong bao cao Word: {docx_path} ({os.path.getsize(docx_path):,} bytes)")


if __name__ == "__main__":
    consolidated_md = assemble_full_markdown()
    dst_docx = REPORT_DIR / "tieu_luan_toi_uu_csdl.docx"
    markdown_to_docx(consolidated_md, dst_docx)
