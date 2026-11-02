"""
Automate Microsoft Word via COM to:
1. Open the document
2. Update all Fields (TOC, page numbers, cross-references)
3. Audit pages, tables, images
4. Export to PDF
5. Save updated docx
"""
import os
import sys
from pathlib import Path

def verify_word():
    import win32com.client
    docx_path = Path("report/tieu_luan_toi_uu_csdl.docx").resolve()
    pdf_path = Path("report/tieu_luan_toi_uu_csdl.pdf").resolve()

    if not docx_path.exists():
        print(f"Error: {docx_path} does not exist.")
        return 1

    print(f"Starting Microsoft Word COM automation for {docx_path.name}...")
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0

    try:
        doc = word.Documents.Open(str(docx_path))
        print("Document opened successfully in Microsoft Word.")

        # Update all fields in document
        print("Updating all Fields and Table of Contents...")
        for story in doc.StoryRanges:
            story.Fields.Update()
            while story.NextStoryRange:
                story = story.NextStoryRange
                story.Fields.Update()

        # Update all TOCs explicitly
        for toc in doc.TablesOfContents:
            toc.Update()

        page_count = doc.ComputeStatistics(2) # 2 = wdStatisticPages
        word_count = doc.ComputeStatistics(0) # 0 = wdStatisticWords
        table_count = doc.Tables.Count
        shape_count = doc.InlineShapes.Count

        print(f"=== Document Statistics ===")
        print(f"- Total Pages: {page_count}")
        print(f"- Total Words: {word_count}")
        print(f"- Total Tables: {table_count}")
        print(f"- Total Inline Images (Charts): {shape_count}")

        # Save docx with updated TOC and pagination
        doc.Save()
        print("Saved updated docx.")

        # Export to PDF (17 = wdExportFormatPDF)
        print(f"Exporting to PDF: {pdf_path.name}...")
        doc.ExportAsFixedFormat(
            OutputFileName=str(pdf_path),
            ExportFormat=17,
            OpenAfterExport=False,
            OptimizeFor=0, # wdExportOptimizeForPrint
            CreateBookmarks=1 # wdExportCreateHeadingBookmarks
        )
        print(f"PDF exported successfully ({pdf_path.stat().st_size:,} bytes).")

        doc.Close(False)
        return 0
    except Exception as e:
        print(f"Word COM Error: {e}")
        return 1
    finally:
        word.Quit()

if __name__ == "__main__":
    sys.exit(verify_word())

