from fpdf import FPDF
from datetime import datetime
from pathlib import Path
import json

class ForensicReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'SME Forensic Intelligence Report', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_session_report(output_path, osint_data, news_data, research_data):
    """Generate a clean PDF report from session data."""
    pdf = ForensicReport()
    pdf.add_page()
    
    # 1. Summary Section
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Executive Summary', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 10, f"This report summarizes the findings from the current SME intelligence gathering session. "
                          f"A total of {len(osint_data)} aliases were tracked, with {len(news_data)} forensic news articles "
                          f"ingested and {len(research_data)} academic deep-dives analyzed.")
    pdf.ln(5)

    # 2. Key Aliases & Platforms
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Discovered Identity Matrix', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    if osint_data:
        for scan in osint_data:
            user = scan.get('username', 'Unknown')
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 10, f"Alias: {user}", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            platforms = []
            for p in scan.get('platforms', []):
                if p.get('status') == 'found':
                    platforms.append(f"{p['name']} ({p.get('url')})")
            
            if platforms:
                pdf.multi_cell(0, 7, "Platforms Detected: " + ", ".join(platforms))
            else:
                pdf.cell(0, 7, "No platforms detected in standard OSINT footprint.", 0, 1)
            pdf.ln(2)
    else:
        pdf.cell(0, 10, "No identity data collected in this session.", 0, 1)

    # 3. Research Context
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '3. Academic Context & Signals', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    if research_data:
        for paper in research_data[:5]: # Top 5
            pdf.set_font('Arial', 'B', 10)
            pdf.multi_cell(0, 7, f"Paper: {paper.get('title')}")
            pdf.set_font('Arial', '', 9)
            pdf.multi_cell(0, 7, f"Abstract Snippet: {paper.get('abstract')[:200]}...")
            pdf.ln(2)
    else:
        pdf.cell(0, 10, "No research data available.", 0, 1)

    pdf.output(output_path)
    return output_path

def generate_case_report(output_path, osint_data, sentiment_data=None):
    """Generate a specialized case report focusing on identity hits and sentiment."""
    pdf = ForensicReport()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Target Case Analysis: Confirmed Footprints', 0, 1)
    pdf.ln(5)

    if not osint_data:
        pdf.set_font('Arial', 'I', 11)
        pdf.cell(0, 10, "No identity hits found in current session.", 0, 1)
        pdf.output(output_path)
        return output_path

    for scan in osint_data:
        user = scan.get('username', 'Unknown')
        pdf.set_font('Arial', 'B', 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, f"Subject: {user}", 0, 1, 'L', fill=True)
        pdf.set_font('Arial', '', 11)
        
        found_platforms = [p for p in scan.get('platforms', []) if p.get('status') == 'found']
        
        if found_platforms:
            pdf.cell(0, 10, "Confirmed Digital Footprints:", 0, 1)
            pdf.set_font('Arial', '', 10)
            for p in found_platforms:
                pdf.cell(10) # indentation
                pdf.cell(0, 7, f"- {p['name']}: {p.get('url')}", 0, 1)
        else:
            pdf.cell(0, 10, "No active digital footprints confirmed.", 0, 1)
        
        pdf.ln(5)

    # 3. Manual Pivots (Investigation Logic)
    pivot_log = Path("data/raw/pivot_log.json")
    if pivot_log.exists():
        try:
            with open(pivot_log, 'r') as f:
                logs = json.load(f)
            if logs:
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, '3. Investigative Pivot Logs (Deep Trace)', 0, 1)
                pdf.set_font('Arial', '', 10)
                for entry in logs[-5:]: # Show last 5
                    pdf.cell(0, 7, f"[{entry['timestamp'][:16]}] Target: {entry['target']} ({entry['action']})", 0, 1)
                pdf.ln(5)
        except:
            pass

    # Sentiment Section (if provided)
    if sentiment_data is not None and not sentiment_data.empty:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Forensic Sentiment Analysis', 0, 1)
        pdf.set_font('Arial', '', 11)
        avg_pol = sentiment_data['polarity'].mean()
        pdf.multi_cell(0, 10, f"Average session sentiment polarity: {avg_pol:.2f}. "
                              f"(Scale: -1 Hostile, 0 Neutral, +1 Positive)")
        pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, "Top News Signals analyzed:", 0, 1)
        pdf.set_font('Arial', '', 9)
        for _, row in sentiment_data.head(5).iterrows():
            pdf.multi_cell(0, 6, f"[{row['polarity']:.2f}] {row['title']}")
            pdf.ln(2)

    pdf.output(output_path)
    return output_path

if __name__ == "__main__":
    # Test generation
    try:
        data_path = Path("data/raw")
        osint = []
        if (data_path / "osint_results.json").exists():
            with open(data_path / "osint_results.json", 'r', encoding='utf-8') as f:
                osint = json.load(f)
        
        generate_session_report("reports/test_forensic_report.pdf", osint, [], [])
        print("Test report generated successfully.")
    except Exception as e:
        print(f"Error: {e}")
