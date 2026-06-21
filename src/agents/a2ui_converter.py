import re

def parse_markdown_bullets(text: str, heading_pattern: str) -> list:
    """
    Finds a section under a heading matching heading_pattern and extracts bullet points.
    """
    if not text:
        return []
        
    lines = text.split("\n")
    found_section = False
    bullets = []
    
    # Simple regex to match headers
    header_re = re.compile(r"^#+\s+(.*)$")
    bullet_re = re.compile(r"^[-*+]\s+(.*)$")
    
    for line in lines:
        stripped = line.strip()
        header_match = header_re.match(stripped)
        if header_match:
            title = header_match.group(1).lower()
            if re.search(heading_pattern.lower(), title):
                found_section = True
            elif found_section:
                # Started a new section, stop parsing
                break
            continue
            
        if found_section:
            bullet_match = bullet_re.match(stripped)
            if bullet_match:
                bullets.append(bullet_match.group(1).strip())
            elif stripped and not stripped.startswith(">") and not stripped.startswith("["):
                # If there's non-bullet text, let's keep it as an item too if it's substantial
                if len(stripped) > 5 and not header_re.match(stripped):
                    bullets.append(stripped)
                    
    # Fallback: if we didn't find the section, try extracting any bullets in the whole text
    if not bullets:
        for line in lines:
            bullet_match = bullet_re.match(line.strip())
            if bullet_match:
                bullets.append(bullet_match.group(1).strip())
                
    return bullets[:8]  # Limit to top 8 items to keep UI clean

def generate_a2ui_payload(analyst_output: str, legal_output: str) -> dict:
    """
    Converts raw analyst and legal markdown text into a flat A2UI v0.9 updateComponents payload.
    Uses the adjacency list model where layout containers reference children by ID.
    """
    # Extract structural sections
    specs = parse_markdown_bullets(analyst_output, r"specifications|deliverables|specs")
    reqs = parse_markdown_bullets(analyst_output, r"requirements|mandatory")
    criteria = parse_markdown_bullets(analyst_output, r"criteria|evaluation")
    
    risks = parse_markdown_bullets(legal_output, r"risks|compliance")
    penalties = parse_markdown_bullets(legal_output, r"penalties|financial")
    mitigations = parse_markdown_bullets(legal_output, r"mitigation|strategies")
    
    # Calculate a mock compliance score based on risk count
    risk_count = len(risks)
    compliance_score = max(30, 100 - (risk_count * 15))
    
    components = []
    
    # 1. Root Column Component
    components.append({
        "id": "root-layout",
        "component": "Column",
        "properties": {
            "children": ["header-section", "dashboard-grid"]
        }
    })
    
    # 2. Header Section
    components.append({
        "id": "header-section",
        "component": "Card",
        "properties": {
            "title": "TenderMind AI - RFP Analysis Report",
            "children": ["header-sub"]
        }
    })
    components.append({
        "id": "header-sub",
        "component": "Text",
        "properties": {
            "content": f"Automated compliance review. Dynamic compliance score: {compliance_score}%",
            "variant": "subtitle"
        }
    })
    
    # 3. Dashboard Grid (Row containing Analyst & Legal columns)
    components.append({
        "id": "dashboard-grid",
        "component": "Row",
        "properties": {
            "children": ["analyst-card", "legal-card"]
        }
    })
    
    # 4. Analyst Card & children
    analyst_children = ["analyst-title"]
    if specs:
        analyst_children.append("specs-header")
        analyst_children.append("specs-list")
    if reqs:
        analyst_children.append("reqs-header")
        analyst_children.append("reqs-list")
        
    components.append({
        "id": "analyst-card",
        "component": "Card",
        "properties": {
            "children": analyst_children
        }
    })
    components.append({
        "id": "analyst-title",
        "component": "Text",
        "properties": {
            "content": "RFP Analyst Findings",
            "variant": "h2"
        }
    })
    
    if specs:
        components.append({
            "id": "specs-header",
            "component": "Text",
            "properties": {
                "content": "Technical Specifications & Deliverables",
                "variant": "h3"
            }
        })
        components.append({
            "id": "specs-list",
            "component": "List",
            "properties": {
                "items": specs
            }
        })
        
    if reqs:
        components.append({
            "id": "reqs-header",
            "component": "Text",
            "properties": {
                "content": "Mandatory Requirements",
                "variant": "h3"
            }
        })
        components.append({
            "id": "reqs-list",
            "component": "List",
            "properties": {
                "items": reqs
            }
        })
        
    # 5. Legal Card & children
    legal_children = ["legal-title", "score-metric"]
    if risks:
        legal_children.append("risks-header")
        legal_children.append("risks-list")
    if mitigations:
        legal_children.append("mitigations-header")
        legal_children.append("mitigations-list")
        
    components.append({
        "id": "legal-card",
        "component": "Card",
        "properties": {
            "children": legal_children
        }
    })
    components.append({
        "id": "legal-title",
        "component": "Text",
        "properties": {
            "content": "Contractual Risk Assessment",
            "variant": "h2"
        }
    })
    components.append({
        "id": "score-metric",
        "component": "Metric",
        "properties": {
            "label": "Compliance Index",
            "value": f"{compliance_score}%",
            "color": "green" if compliance_score >= 80 else "yellow" if compliance_score >= 50 else "red"
        }
    })
    
    if risks:
        components.append({
            "id": "risks-header",
            "component": "Text",
            "properties": {
                "content": "Compliance Risks & Penalty Warnings",
                "variant": "h3"
            }
        })
        components.append({
            "id": "risks-list",
            "component": "List",
            "properties": {
                "items": risks
            }
        })
        
    if mitigations:
        components.append({
            "id": "mitigations-header",
            "component": "Text",
            "properties": {
                "content": "Suggested Mitigation Strategies",
                "variant": "h3"
            }
        })
        components.append({
            "id": "mitigations-list",
            "component": "List",
            "properties": {
                "items": mitigations
            }
        })
        
    # Return formatted payload
    return {
        "version": "v0.9",
        "updateComponents": {
            "surfaceId": "rfp-analysis-dashboard",
            "components": components
        }
    }
