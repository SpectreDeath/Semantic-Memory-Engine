from fpdf import FPDF
import os

def test_fpdf():
    print("Testing FPDF2...")
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="SME Forensic Test", ln=1, align="C")
        pdf.output("data/reports/fpdf_test.pdf")
        if os.path.exists("data/reports/fpdf_test.pdf"):
            print("✅ FPDF2 is working correctly.")
        else:
            print("❌ FPDF2 failed to create file.")
    except Exception as e:
        print(f"❌ FPDF2 Error: {e}")

if __name__ == "__main__":
    test_fpdf()
