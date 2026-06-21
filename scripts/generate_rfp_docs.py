import os
from fpdf import FPDF

# Ensure directory exists
output_dir = "data/rfp"
os.makedirs(output_dir, exist_ok=True)

class RFP_PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_fill_color(50, 50, 50)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "OFFICIAL REQUEST FOR PROPOSAL", 0, 1, "C", True)
        self.set_text_color(0, 0, 0)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()} - Confidential", 0, 0, "C")

    def section_title(self, title):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(220, 220, 220)
        self.cell(0, 8, title, 0, 1, "L", True)
        self.ln(4)

    def section_body(self, body):
        self.set_font("Arial", "", 10)
        self.multi_cell(0, 6, body)
        self.ln(4)

def generate_bordeaux_rfp():
    pdf = RFP_PDF()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Project: Bordeaux Municipal Sports Complex Renovation", 0, 1, "C")
    pdf.ln(5)
    
    pdf.section_title("1. Project Overview")
    pdf.section_body(
        "The City of Bordeaux is issuing this Request for Proposal (RFP) for the comprehensive energy "
        "retrofit of the Municipal Sports Complex. The objective is to modernize the facility to meet current "
        "environmental standards and significantly reduce operating expenses."
    )
    
    pdf.section_title("2. Technical Requirements")
    pdf.section_body(
        "The successful bidder must deliver the following key technical outcomes:\n"
        "- A minimum 40% reduction in overall energy consumption compared to the 2023 baseline.\n"
        "- Installation of a rooftop solar PV array to offset grid electricity usage.\n"
        "- Full integration of a smart GTB (Gestion Technique du Bâtiment) system for real-time HVAC "
        "and lighting optimization."
    )
    
    pdf.section_title("3. Mandatory Compliance Standards")
    pdf.section_body(
        "All energy audits and diagnostic procedures proposed in this bid MUST strictly adhere to the "
        "NF EN 16247 European standard. Bids lacking explicit confirmation of this methodological "
        "compliance will be automatically disqualified."
    )
    
    pdf.section_title("4. Evaluation Criteria")
    pdf.section_body(
        "- Technical Merit and Innovation (40%)\n"
        "- Cost Effectiveness and CAPEX/OPEX Projections (35%)\n"
        "- Methodological Rigor (NF EN 16247 compliance) (25%)"
    )
    
    pdf.output(os.path.join(output_dir, "RFP_Bordeaux_Sport_Complex.pdf"))

def generate_nuclear_rfp():
    pdf = RFP_PDF()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Project: Delta-9 Modular Nuclear Reactor Deployment", 0, 1, "C")
    pdf.ln(5)
    
    pdf.section_title("1. Project Overview")
    pdf.section_body(
        "Global Heavy Industries is seeking qualified primary contractors for the design, construction, and "
        "commissioning of a next-generation Modular Nuclear Reactor (MNR) at the coastal Delta-9 site. "
        "This is a high-stakes, Tier-1 critical infrastructure project requiring specialized nuclear engineering expertise."
    )
    
    pdf.section_title("2. Technical Requirements")
    pdf.section_body(
        "- Procurement and installation of a 300 MWt Pressurized Water Reactor core.\n"
        "- Construction of a Category-A reinforced concrete containment dome capable of withstanding "
        "direct seismic and ballistic impacts.\n"
        "- Deployment of primary loop coolant pumps and high-pressure steam generator assemblies."
    )
    
    pdf.section_title("3. Legal and Liability Clauses (CRITICAL)")
    pdf.section_body(
        "Due to the coastal location of the Delta-9 site, the selected contractor MUST agree to an "
        "unlimited liability clause covering all catastrophic flood, tsunami, and seawater ingress damages "
        "during the construction phase. By submitting a bid, the contractor waives all rights to invoke "
        "force majeure regarding coastal flooding."
    )
    
    pdf.section_title("4. Security Clearance")
    pdf.section_body(
        "All onsite personnel, engineering consultants, and subcontractors must possess active Level 3 "
        "Nuclear Security Clearances prior to site entry. Bidders must demonstrate a minimum of 15 years "
        "of continuous experience in primary nuclear containment construction."
    )
    
    pdf.output(os.path.join(output_dir, "RFP_Nuclear_Plant_Project.pdf"))

if __name__ == "__main__":
    print("Generating Test RFP PDFs...")
    generate_bordeaux_rfp()
    generate_nuclear_rfp()
    print("Successfully generated both RFPs in data/rfp/")
