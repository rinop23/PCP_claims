# PCP Claims Analysis - AI Multi-Agent System

## 🎯 Overview

Intelligent multi-agent system for analyzing PCP (Personal Contract Purchase) claims portfolios and generating comprehensive monthly investor reports using OpenAI GPT-4o.

## 🤖 The 4 Intelligent Agents

### 1️⃣ Priority Deed Agent
**Purpose:** Reads profit distribution agreements

**What it does:**
- Reads Priority Deed Word document
- Extracts profit split rules (Funder/Law Firm percentages)
- Extracts DBA rate (typically 30% of settlements)
- Identifies cost recovery waterfall
- Calculates profit distributions

**Input:** `DOCS/Priorities Deed (EV 9 October 2025).docx`

### 2️⃣ FCA Compliance Agent
**Purpose:** Validates claims against FCA Redress Scheme

**What it does:**
- Reads FCA Redress Scheme PDF (3.6MB, 20 pages extracted)
- Extracts commission thresholds
- Identifies eligible products
- Validates claim compliance
- Flags non-compliant claims

**Input:** `FCA redress scheme/Redress Scheme.pdf`

### 3️⃣ Monthly Report Agent
**Purpose:** Extracts data from monthly Excel reports

**What it does:**
- Reads Excel monthly reports
- Extracts portfolio metrics (claims, clients, success rates)
- Extracts ALL lenders (50-70 lenders with accurate counts)
- Extracts pipeline breakdown by stage
- Extracts financial costs and forecasting

**Input:** Monthly Summary Excel file

### 4️⃣ Investor Report Agent
**Purpose:** Master agent that generates comprehensive reports

**What it does:**
- Combines insights from all 3 specialist agents
- Calculates financial returns using Priority Deed rules
- Assesses FCA compliance using Redress Scheme rules
- Generates executive summary with portfolio health score
- Creates detailed financial analysis with ROI/MOIC
- Provides risk assessment and action items
- Outputs both JSON and formatted Markdown

**Output:** Complete investor report

---

## 📊 Dashboard Features

### Interactive Visualizations

1. **Portfolio Overview**
   - Claims by status (bar chart)
   - Success rate metrics
   - Portfolio value tracking

2. **Financial Waterfall**
   - Settlement → DBA Proceeds → Costs → Net Proceeds
   - Visual profit distribution flow

3. **Profit Split Chart**
   - Funder vs Firm distribution (pie chart)
   - Actual monetary values

4. **Lender Analytics**
   - Top 10 lenders (pie chart)
   - Top 15 by value (horizontal bar)
   - Concentration risk analysis

5. **Pipeline Funnel**
   - Claims progression through stages
   - Conversion rates visualization

6. **Cost Breakdown**
   - Acquisition, submission, processing, legal costs
   - Cost efficiency metrics

### Dashboard Tabs

**📋 Executive Report**
- Complete investor report in markdown
- Download as Markdown or Word document
- Includes all sections with specific metrics

**💰 Financial Analysis**
- Revenue breakdown
- Profit distribution calculations
- ROI and MOIC projections
- Interactive financial charts

**⚖️ Compliance**
- FCA compliance status (🟢🟡🔴)
- Commission analysis vs thresholds
- Claims at risk
- Required compliance actions

**📊 Portfolio Analytics**
- Lender concentration analysis
- Diversification score
- Top lenders by volume and value
- Portfolio composition charts

**📈 Visualizations**
- Pipeline funnel
- All lender value charts
- Complete lender data table
- Interactive filters

**📁 Raw Data**
- All extracted JSON data
- Portfolio metrics
- Financial data
- Pipeline status
- Profit distribution rules

---

## 🚀 System Workflow

```
1. Upload Monthly Excel Report
         ↓
2. Priority Deed Agent reads profit rules
         ↓
3. FCA Compliance Agent reads redress scheme
         ↓
4. Monthly Report Agent extracts Excel data
         ↓
5. Investor Report Agent generates comprehensive report
         ↓
6. Dashboard displays results with visualizations
```

**Processing Time:** 60-90 seconds

---

## 📁 File Structure

```
pcp_AGI_system/
├── intelligent_agents.py          # 4 AI agents (698 lines)
├── milberg_streamlit_demo.py      # Dashboard with visualizations (758 lines)
├── requirements.txt                # Dependencies
├── README.md                       # This file
├── DOCS/
│   └── Priorities Deed (EV 9 October 2025).docx
├── FCA redress scheme/
│   └── Redress Scheme.pdf
└── uploads/                        # Excel file uploads
```

**Total:** 2 Python files, 1,456 lines of code

---

## 🔧 Installation & Deployment

### Requirements

```txt
streamlit>=1.28.0       # Web framework
pandas>=2.0.0           # Data processing
openpyxl>=3.1.0         # Excel reading
openai>=1.0.0           # AI agents
plotly>=5.17.0          # Interactive charts
matplotlib>=3.5.0       # Additional charts
python-docx>=1.0.0      # Word document generation
PyPDF2>=3.0.0           # PDF reading
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-key-here"

# Run dashboard
streamlit run milberg_streamlit_demo.py
```

### Streamlit Cloud Deployment

1. Push to GitHub
2. Connect to Streamlit Cloud
3. Add secrets in Streamlit dashboard:
   ```toml
   OPENAI_API_KEY = "your-key-here"
   ```
4. Deploy

---

## 🔐 Authentication

**Built-in user accounts:**
- `admin` / `Admin123!`
- `walter` / `Walter123!`
- `dirk` / `Dirk123!`
- `eda` / `Eda123!`

Passwords are hashed with SHA-256.

---

## 📊 Sample Output

### Executive Summary
```
Portfolio Health Score: 85/100

Key Metrics:
- Total Claims: 180 across 61 lenders
- Success Rate: 45.5% (50/110 submitted)
- Portfolio Value: £2.4M
- Expected Funder Return: £384K (80%)
- Expected Firm Return: £96K (20%)
```

### Financial Analysis
```
Total Settlement Value: £2,400,000
DBA Proceeds (30%):     £720,000
Less: Total Costs:      £240,000
Net Proceeds:           £480,000

Funder Share (80%):     £384,000
Firm Share (20%):       £96,000

ROI Projection:         60%
MOIC Projection:        1.6x
```

### Compliance Assessment
```
Status: 🟢 COMPLIANT

Commission Analysis:
- Average commission: 12.5%
- FCA threshold: 50%
- Claims at risk: 0
```

---

## 💡 Key Features

### ✅ Intelligent Data Extraction
- AI reads entire Excel sheets intelligently
- Extracts ALL lenders (not just first few)
- Zero synthetic data - uses actual numbers
- Handles currency conversion automatically

### ✅ Document Understanding
- Reads Word documents (Priority Deed)
- Reads PDF documents (FCA Redress Scheme)
- Extracts structured rules and thresholds
- Applies rules to validate claims

### ✅ Factual Analysis
- No opinions - only data-driven observations
- Specific numbers for every metric
- Shows calculations and reasoning
- Objective risk assessment

### ✅ Professional Reporting
- Executive-level investor reports
- Interactive visualizations
- Export to Markdown or Word
- Downloadable reports

---

## 🔬 Technology Stack

**AI Model:** OpenAI GPT-4o
- JSON mode for structured extraction
- 16K token context for comprehensive analysis
- Temperature 0.1-0.2 for factual outputs

**Frontend:** Streamlit
- Interactive dashboard
- Real-time visualizations
- Session state management
- File uploads

**Visualization:** Plotly
- Interactive charts
- Waterfall diagrams
- Funnel charts
- Pie and bar charts

**Document Processing:**
- python-docx for Word reading/writing
- PyPDF2 for PDF extraction
- pandas for Excel analysis

---

## 📈 Performance Metrics

**Analysis Speed:** 60-90 seconds per report
**Cost per Report:** ~$0.10-0.15 (OpenAI API)
**Accuracy:** Uses actual data from documents
**Scalability:** Handles 50-70 lenders per report

---

## 🎯 Use Cases

1. **Monthly Investor Reporting**
   - Upload Excel, get comprehensive report
   - Financial analysis with profit calculations
   - Compliance assessment
   - Risk analysis

2. **Portfolio Monitoring**
   - Real-time portfolio health tracking
   - Lender concentration analysis
   - Pipeline progression monitoring

3. **Compliance Auditing**
   - Automated FCA compliance checks
   - Commission threshold validation
   - Risk identification

4. **Strategic Planning**
   - Forecasting and projections
   - ROI/MOIC tracking
   - Action item identification

---

## 🔄 System Advantages

### vs Manual Analysis
- ⚡ 60-90 seconds vs 2-3 hours
- 📊 Consistent format every time
- 🎯 No human error in calculations
- 📈 Interactive visualizations included

### vs Simple Data Display
- 🧠 Understands legal documents
- 💡 Applies rules intelligently
- 🔍 Validates compliance automatically
- 📝 Generates insights, not just data

### vs Traditional Reporting
- 📄 Reads source documents (Priority Deed, FCA Scheme)
- 🤖 4 specialized agents working together
- 💰 Calculates profit splits accurately
- ⚖️ Validates claims against regulations

---

## 🛠️ Maintenance

**Documents to keep updated:**
- Priority Deed (when terms change)
- FCA Redress Scheme (when regulations update)
- User credentials (in code or environment)

**Monitoring:**
- OpenAI API usage and costs
- Dashboard performance
- Agent output quality

---

## 📞 Support

**System Info:**
- Model: GPT-4o
- Analysis Time: ~60-90 seconds
- Version: 3.0 (Complete Multi-Agent Rebuild)

---

## 📜 License

Proprietary - Internal use only

---

## 🎉 Summary

A production-ready intelligent multi-agent system that:
1. 📄 Reads legal documents to extract profit rules
2. ⚖️ Validates claims against FCA regulations
3. 📊 Extracts comprehensive data from Excel reports
4. 📝 Generates professional investor reports
5. 📈 Provides interactive visualizations
6. 💾 Exports reports to Markdown/Word

**Result:** Complete investor report in 60-90 seconds with factual analysis, compliance validation, and beautiful visualizations!
