import os
from fpdf import FPDF

# Ensure directory exists
output_dir = "data/corporate"
os.makedirs(output_dir, exist_ok=True)

class CorporatePDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, "EcoBuild Solutions", 0, 1, "C")
        self.set_font("Arial", "I", 10)
        self.cell(0, 10, "Advanced Energy Engineering & Consulting", 0, 1, "C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, "L", True)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font("Arial", "", 11)
        self.multi_cell(0, 6, body)
        self.ln()

def generate_company_profile():
    pdf = CorporatePDF()
    pdf.add_page()
    
    pdf.chapter_title("Company Profile & History")
    pdf.chapter_body(
        "Founded in 2012, EcoBuild Solutions has established itself as a premier energy engineering firm "
        "dedicated to transforming commercial and industrial infrastructures. Over the past decade, we have "
        "deployed over 500+ megawatt-scale energy efficiency projects across Europe."
    )
    
    pdf.chapter_title("Certifications")
    pdf.chapter_body(
        "- ISO 9001: Quality Management Systems\n"
        "- ISO 14001: Environmental Management Systems\n"
        "- RGE (Reconnu Garant de l'Environnement) Certified"
    )
    
    pdf.chapter_title("R&D Focus")
    pdf.chapter_body(
        "Our current R&D trajectory heavily focuses on AI-driven energy management systems. By integrating "
        "predictive machine learning models with real-time IoT sensor telemetry, we dynamically optimize HVAC "
        "and GTB (Gestion Technique du Bâtiment) parameters, routinely reducing baseline energy consumption by "
        "an additional 15-20% compared to static algorithmic controls."
    )
    
    pdf.output(os.path.join(output_dir, "Company_Profile.pdf"))

def generate_technical_methodology():
    pdf = CorporatePDF()
    pdf.add_page()
    
    pdf.chapter_title("The Eco-Audit Methodology")
    pdf.chapter_body(
        "EcoBuild Solutions employs a rigorous, 4-phase 'Eco-Audit' methodology strictly compliant with "
        "NF EN 16247 standards. Our approach leverages advanced BIM (Building Information Modeling) and "
        "thermal envelope analysis to ensure zero-loss diagnostics."
    )
    
    pdf.chapter_title("Methodology Phases")
    
    # Table Header
    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 10, "Phase", 1)
    pdf.cell(150, 10, "Description & Technical Execution", 1)
    pdf.ln()
    
    # Table Body
    pdf.set_font("Arial", "", 10)
    phases = [
        ("Phase 1: Discovery", "IoT sensor telemetry deployment, initial data acquisition (D+0 to D+14)."),
        ("Phase 2: Modeling", "BIM modeling creation, thermal envelope analysis, HVAC baseline extraction."),
        ("Phase 3: Simulation", "Digital twin scenario testing, ROI projection modeling."),
        ("Phase 4: Synthesis", "Delivery of the NF EN 16247 compliant action plan and CAPEX/OPEX breakdown.")
    ]
    
    for phase, desc in phases:
        pdf.cell(40, 10, phase, 1)
        pdf.cell(150, 10, desc, 1)
        pdf.ln()
        
    pdf.output(os.path.join(output_dir, "Technical_Methodology.pdf"))

def generate_pricing_guide():
    pdf = CorporatePDF()
    pdf.add_page()
    
    pdf.chapter_title("Standardized Pricing Guide (2026)")
    pdf.chapter_body("Below is our granular baseline pricing structure for engineering and implementation services.")
    
    # Table Header
    pdf.set_font("Arial", "B", 10)
    pdf.cell(120, 10, "Service / Component", 1)
    pdf.cell(70, 10, "Unit Price", 1)
    pdf.ln()
    
    # Table Body
    pdf.set_font("Arial", "", 10)
    prices = [
        ("Solar PV Installation (Turnkey)", "1200 EUR / kWc"),
        ("Comprehensive Building Diagnostic (NF EN 16247)", "2500 EUR / audit"),
        ("Smart-Grid Integration Module", "4500 EUR / node"),
        ("GTB System Annual Maintenance Fee", "1800 EUR / year"),
        ("Thermal Envelope Upgrades (Insulation)", "85 EUR / m2"),
        ("Project Management (AMO)", "15% of CAPEX")
    ]
    
    for service, price in prices:
        pdf.cell(120, 10, service, 1)
        pdf.cell(70, 10, price, 1)
        pdf.ln()
        
    pdf.ln(10)
    pdf.chapter_title("Disclaimer")
    pdf.chapter_body(
        "All prices listed above are strictly indicative and subject to material indexation clauses. "
        "Due to raw material market volatility (specifically silicon and copper), final CAPEX estimates "
        "will be indexed to the BT01 index at the time of contract signature."
    )
    
    pdf.output(os.path.join(output_dir, "Pricing_Guide.pdf"))

def generate_success_stories():
    pdf = CorporatePDF()
    pdf.add_page()
    
    pdf.chapter_title("Past Success Stories")
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "1. Lyon City Hall Renovation (2024)", 0, 1)
    pdf.chapter_body(
        "Project Scope: Complete thermal retrofit and GTB modernization of the historic City Hall.\n"
        "Budget: 150,000 EUR\n"
        "Outcome: Achieved a 45% efficiency gain in HVAC consumption while strictly adhering to heritage "
        "building constraints. Deployed 120 wireless IoT sensors for granular room-level control."
    )
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "2. Marseille Logistic Hub (2025)", 0, 1)
    pdf.chapter_body(
        "Project Scope: Renewable energy transition for a major shipping distribution center.\n"
        "Budget: 85,000 EUR\n"
        "Outcome: Installed 500m2 of high-efficiency solar PV arrays on the warehouse roofing. "
        "The facility now operates at 60% grid independence during peak operational hours."
    )
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "3. Bordeaux Industrial Plant (2026)", 0, 1)
    pdf.chapter_body(
        "Project Scope: Advanced energy orchestration for a manufacturing facility.\n"
        "Budget: 220,000 EUR\n"
        "Outcome: Full smart-grid integration featuring peak-shaving algorithms and battery energy "
        "storage systems (BESS). Successfully reduced peak tariff penalties by 80%."
    )
    
    pdf.output(os.path.join(output_dir, "Past_Success_Stories.pdf"))

def generate_compliance_safety():
    pdf = CorporatePDF()
    pdf.add_page()
    
    pdf.chapter_title("Compliance and Safety Framework")
    pdf.chapter_body(
        "EcoBuild Solutions operates under the strictest regulatory and safety frameworks in the European "
        "energy sector. Our engineering designs are fully guaranteed and insured."
    )
    
    pdf.chapter_title("Regulatory Compliance")
    pdf.chapter_body(
        "- Decree n° 2023-112: All our commercial retrofits comply with the 'Tertiary Decree', mandating "
        "a 40% reduction in energy consumption by 2030.\n"
        "- NF EN 16247: Our audits strictly follow the European standard for energy audits, ensuring "
        "methodological rigor and actionable outputs."
    )
    
    pdf.chapter_title("Liability and Guarantees")
    pdf.chapter_body(
        "We provide comprehensive protection for our clients through our 'Decennial Civil Liability' "
        "(Assurance Décennale) clauses. This legally binds us to a 10-year guarantee covering all structural "
        "and major functional defects arising from our installations, ensuring total peace of mind for long-term "
        "infrastructure investments."
    )
    
    pdf.output(os.path.join(output_dir, "Compliance_and_Safety.pdf"))

if __name__ == "__main__":
    print("Generating Corporate Memory PDFs...")
    generate_company_profile()
    generate_technical_methodology()
    generate_pricing_guide()
    generate_success_stories()
    generate_compliance_safety()
    print("Successfully generated all 5 PDFs in data/corporate/")
