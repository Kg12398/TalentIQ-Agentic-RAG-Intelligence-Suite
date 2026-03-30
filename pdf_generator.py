import markdown
from fpdf import FPDF
import datetime

class TalentIQ_PDF(FPDF):
    def header(self):
        # Professional Header
        self.set_font("helvetica", "B", 16)
        self.set_text_color(30, 41, 59) # Slate-800
        self.cell(0, 10, "TalentIQ Intelligence Report", border=False, align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("helvetica", "I", 10)
        self.set_text_color(100, 116, 139) # Slate-500
        date_str = datetime.datetime.now().strftime("%B %d, %Y - %H:%M")
        self.cell(0, 10, f"Generated on: {date_str}", border=False, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        # Professional Footer
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(148, 163, 184) # Slate-400
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Powered by TalentIQ Agentic RAG", align="C")

def create_pdf_from_md(md_text: str) -> bytes:
    """
    Converts a Markdown string containing LLM responses into a fully styled PDF byte string.
    """
    # 1. Convert Markdown to HTML
    # We use 'extra' for tables/lists and 'nl2br' for standard line breaks
    html_content = markdown.markdown(md_text, extensions=['extra', 'nl2br'])
    
    # 2. Build PDF
    pdf = TalentIQ_PDF()
    pdf.add_page("P", "A4")
    
    # 3. Apply standard styling
    pdf.set_font("helvetica", size=11)
    pdf.set_text_color(15, 23, 42) # Slate-900 (almost black)
    
    # 4. Inject HTML directly into fpdf2
    try:
        pdf.write_html(html_content)
    except Exception as e:
        # Fallback to plain text if HTML parsing fails on complex markdown
        pdf.set_font("helvetica", size=11)
        # Strip simple markdown or just write it raw
        clean_text = md_text.replace("**", "").replace("#", "")
        pdf.multi_cell(0, 6, clean_text)
        
    # 5. Export as raw bytes (ready for Streamlit download_button)
    return bytes(pdf.output())
