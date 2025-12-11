# PCP Claim Funding Management - Agentic System

A comprehensive agentic system for managing PCP (Personal Contract Purchase) claim funding, designed specifically for UK litigation funders and investors.

## 🎯 Features

### Core Capabilities
- **Document Processing**: Automatically extract structured data from law firm claim reports
- **LFA Compliance Checking**: Validate claims against Litigation Funding Agreement terms
- **Multi-Report Generation**: 
  - Investor Reports (portfolio-wide)
  - IC Reports (Investment Committee analysis)
  - Compliance Reports
- **Legal Strategy Insights**: UK-specific legal guidance for PCP claims
- **Portfolio Management**: Track multiple claims, funding utilization, and returns
- **REST API**: Web-based API for integration with other systems

### Compliance Checks
- Funding cap validation
- Jurisdiction verification
- Documentation completeness
- Adverse costs insurance requirements
- Return multiple analysis

### Reports Generated
1. **Investor Reports**: Portfolio overview, returns analysis, risk metrics
2. **IC Reports**: Detailed claim analysis, compliance status, risk assessment, recommendations
3. **Legal Strategy Reports**: Case-specific guidance, milestone tracking, cost management

## 📁 Project Structure

```
pcp-funding-system/
├── pcp_funding_agent.py      # Main agent system
├── document_processor.py      # Document extraction engine
├── api_server.py             # REST API interface
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── uploads/                  # Uploaded claim reports
└── reports/                  # Generated reports
```

## 🚀 Quick Start

### Installation

1. **Clone or download the system files**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the demo**:
```bash
# Test the core agent
python pcp_funding_agent.py

# Test document processing
python document_processor.py

# Start the API server
python api_server.py
```

## 📖 Usage Guide

### 1. Command Line Usage

#### Load LFA and Process Claims
```python
from pcp_funding_agent import PCPFundingAgent

# Initialize agent
agent = PCPFundingAgent()

# Load LFA terms
lfa_data = {
    "agreement_id": "LFA-2024-001",
    "funding_cap": 500000.0,
    "success_fee_percentage": 25.0,
    "minimum_return_multiple": 2.0,
    "permitted_expenses": ["legal_fees", "court_fees", "expert_witnesses", "insurance"],
    "reporting_frequency": "monthly",
    "termination_conditions": ["breach_of_terms", "insolvency"],
    "jurisdiction": "UK",
    "adverse_costs_insurance_required": True
}
agent.load_lfa(lfa_data)

# Ingest claim
claim_report = {
    "claim_id": "PCP-2024-1234",
    "claimant_name": "John Smith",
    "defendant": "Premium Auto Finance Ltd",
    "claim_amount": 85000.0,
    "funded_amount": 35000.0,
    "claim_date": "2024-03-15",
    "status": "in_progress",
    "law_firm": "Legal Partners LLP",
    "case_reference": "LP/PCP/2024/1234",
    "documentation_received": ["claim_form", "lfa_signed", "insurance_policy"],
    "last_update": "2024-12-01"
}
agent.ingest_claim_report(claim_report)

# Check compliance
compliance = agent.check_lfa_compliance("PCP-2024-1234")

# Generate reports
ic_report = agent.generate_ic_report("PCP-2024-1234")
investor_report = agent.generate_investor_report()
strategy = agent.get_legal_strategy_insights("PCP-2024-1234")
```

#### Process Law Firm Reports
```python
from document_processor import DocumentProcessor

processor = DocumentProcessor()

# Process uploaded document
extracted_data = processor.process_law_firm_report("report.txt")

# Validate extraction
validation = processor.validate_extracted_data(extracted_data)

# Extract specific information
milestones = processor.extract_case_milestones(text)
financials = processor.extract_financial_summary(text)
```

### 2. API Usage

Start the API server:
```bash
python api_server.py
```

The API will be available at `http://localhost:5000`

#### API Endpoints

**Load LFA Terms**
```bash
curl -X POST http://localhost:5000/api/lfa/load \
  -H "Content-Type: application/json" \
  -d '{
    "agreement_id": "LFA-2024-001",
    "funding_cap": 500000.0,
    "success_fee_percentage": 25.0,
    "minimum_return_multiple": 2.0,
    "permitted_expenses": ["legal_fees", "court_fees"],
    "reporting_frequency": "monthly",
    "termination_conditions": ["breach_of_terms"],
    "jurisdiction": "UK",
    "adverse_costs_insurance_required": true
  }'
```

**Upload Claim Report**
```bash
curl -X POST http://localhost:5000/api/claims/upload \
  -F "file=@claim_report.txt"
```

**Check Compliance**
```bash
curl http://localhost:5000/api/compliance/check/PCP-2024-1234
```

**Generate IC Report**
```bash
curl http://localhost:5000/api/reports/ic/PCP-2024-1234
```

**Generate Investor Report**
```bash
curl http://localhost:5000/api/reports/investor
```

**Get Dashboard Data**
```bash
curl http://localhost:5000/api/dashboard
```

**Get Legal Strategy**
```bash
curl http://localhost:5000/api/strategy/PCP-2024-1234
```

## 🔍 Sample Claim Report Format

The system can extract data from text reports in this format:

```
LEGAL PARTNERS LLP
Claim Progress Report

Claim Reference: PCP/2024/5678
Date: 15/11/2024

Claimant: Sarah Johnson
Defendant: Auto Finance Solutions Limited

FINANCIAL SUMMARY
Claim Amount: £95,500.00
Funded Amount: £42,000.00

Status: In Progress

COSTS BREAKDOWN
Solicitor Fees: £18,500.00
Court Fees: £2,500.00
Expert Witness Fees: £5,000.00
ATE Insurance Premium: £8,000.00

DOCUMENTATION
- Claim Form completed and filed
- Litigation Funding Agreement signed
- ATE Insurance policy in place
- Expert Report commissioned

CASE MILESTONES
Claim Filed: 10/09/2024
Defense Received: 25/09/2024
Disclosure deadline: 15/12/2024
Trial Date: 15/03/2025
```

## 📊 Report Types

### 1. Investor Report
- Portfolio summary (total claims, funded amount, claim values)
- Status breakdown of all claims
- Return multiples and potential returns
- Risk metrics (concentration, exposure)
- LFA utilization tracking

### 2. IC (Investment Committee) Report
- Detailed claim analysis
- Financial metrics (funded amount, claim value, return multiple)
- Full compliance status with specific checks
- Risk assessment (rating, factors, mitigation)
- Recommendation (Approve/Hold/Review)

### 3. Legal Strategy Report
- UK jurisdiction-specific guidance
- PCP mis-selling legal framework
- Litigation strategy recommendations
- Cost management advice
- Status-specific action items

## 🔐 Compliance Framework

The system checks:
1. **Funding Cap**: Ensures funded amount doesn't exceed LFA limits
2. **Jurisdiction**: Validates UK jurisdiction requirement
3. **Documentation**: Verifies required documents are received
4. **Insurance**: Confirms ATE insurance is in place
5. **Returns**: Validates minimum return multiples

## 🎓 UK PCP Legal Context

The system provides guidance on:
- **Commission Disclosure**: FCA requirements and Plevin v Paragon precedent
- **Time Limits**: 6-year limitation period or 3 years from knowledge
- **Litigation Strategy**: Pre-action protocols, ADR, court procedures
- **Financial Ombudsman**: Jurisdiction and processes
- **Cost Protection**: QOCS, ATE insurance, costs management

## 🛠️ Customization

### Adding New Compliance Checks

Edit `pcp_funding_agent.py`, `check_lfa_compliance()` method:

```python
# Add custom check
compliance_checks.append(ComplianceCheck(
    check_name="Your Check Name",
    status=ComplianceStatus.COMPLIANT,  # or NON_COMPLIANT or REQUIRES_REVIEW
    details="Description of check result",
    recommendation="Action if needed"
))
```

### Extending Document Processing

Edit `document_processor.py`, `_compile_patterns()` method:

```python
# Add new extraction pattern
"new_field": re.compile(r"YourPattern", re.IGNORECASE)
```

### Adding New Report Types

Create new method in `PCPFundingAgent` class:

```python
def generate_custom_report(self, claim_id: str) -> Dict[str, Any]:
    claim = self.claims_data.get(claim_id)
    # Your report logic
    return report_data
```

## 📈 Future Enhancements

Potential additions:
- [ ] PDF/DOCX direct parsing (PyPDF2, python-docx integration)
- [ ] Claude API integration for intelligent document understanding
- [ ] Automated email notifications for compliance issues
- [ ] Excel export for reports
- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] Advanced analytics and forecasting
- [ ] Multi-currency support
- [ ] Automated settlement calculation
- [ ] Calendar integration for deadline tracking

## 🐛 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt --upgrade
```

**API Port Already in Use**
```bash
# Change port in api_server.py
app.run(debug=True, host='0.0.0.0', port=5001)  # Use different port
```

**Document Processing Fails**
- Ensure text encoding is UTF-8 or Latin-1
- Check that required fields are present in the document
- Validate date formats (DD/MM/YYYY or YYYY-MM-DD)

## 📝 License

This system is provided for internal use in managing PCP claim funding. 

## 🤝 Support

For questions or issues:
1. Review this documentation
2. Check the code comments in each module
3. Examine the demo/example code at the bottom of each file

## 🔄 Version History

- **v1.0.0** (December 2024)
  - Initial release
  - Core agent functionality
  - Document processing
  - REST API
  - Multiple report types
  - UK legal strategy guidance

---

**Built for UK litigation funders to efficiently manage PCP claim portfolios with automated compliance and reporting.**
