Feature: RFP Analysis and Proposal Drafting Swarm
  As a business development team
  I want TenderMind AI's specialized agent swarm to analyze RFP documents and draft bid proposals
  So that we can rapidly construct legally compliant and technically accurate bid responses

  Scenario: Extracting technical requirements and performing compliance auditing
    Given a vectorized RFP document is available in the vector database
    When a user requests analysis with focus area "Bordeaux Sports Complex structure requirements"
    Then the Analyst Agent should invoke tool "search_rfp_database" with query containing "Bordeaux"
    And the Analyst Agent should return structured technical specs and mandatory requirements
    And the Legal Agent should review the analyst output and flag any performance penalty risks
    And the system should pause execution for Human-In-The-Loop review

  Scenario: Generating the final proposal bid draft
    Given the Analyst Agent findings and Legal Agent reviews have been completed
    And the human reviewer has approved the pre-review findings
    When the user triggers the post-review bid writer pipeline
    Then the Bid Writer Agent should invoke tool "search_corporate_memory" with query containing "proposals" or "methodology"
    And the Bid Writer Agent should produce a draft containing "Executive Summary", "Technical Response", and "Compliance Matrix"
