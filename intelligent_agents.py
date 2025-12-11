"""
Intelligent Agents for PCP Claims Analysis
Uses OpenAI to analyze Excel reports, legal docs, and FCA compliance
"""

import os
import json
from typing import Dict, Any, List
from openai import OpenAI
import pandas as pd


class BaseAgent:
    """Base class for all intelligent agents"""

    def __init__(self, api_key: str = None):
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.environ.get("OPENAI_API_KEY")
            if not self.api_key:
                try:
                    import streamlit as st
                    self.api_key = st.secrets.get("OPENAI_API_KEY")
                except:
                    pass

        if not self.api_key:
            raise ValueError("OpenAI API key required")

        self.client = OpenAI(api_key=self.api_key)

    def call_openai(self, system_prompt: str, user_prompt: str, response_format: str = "json") -> Any:
        """Call OpenAI with prompts"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        if response_format == "json":
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.1,
                max_tokens=16000,
                response_format={"type": "json_object"}
            )
        else:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.3,
                max_tokens=8000
            )

        result = response.choices[0].message.content.strip()

        if response_format == "json":
            return json.loads(result)
        else:
            return result


class ExcelAnalysisAgent(BaseAgent):
    """Agent that analyzes Excel reports"""

    def analyze_excel(self, file_path: str) -> Dict[str, Any]:
        """Analyze Excel file and extract all data"""

        # Read Excel file
        xl = pd.ExcelFile(file_path)
        sheet_name = xl.sheet_names[0]
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        excel_text = df.to_string()

        # Truncate if too long
        if len(excel_text) > 20000:
            excel_text = excel_text[:20000] + "\n... [truncated]"

        system_prompt = """You are an expert financial analyst. Extract structured data from Excel reports.
You MUST return valid JSON with no additional text.

Required JSON structure:
{
  "reporting_period": "month/year string",
  "portfolio_metrics": {
    "unique_clients": number,
    "unique_claims": number,
    "claims_submitted": number,
    "claims_successful": number,
    "claims_rejected": number,
    "avg_claim_value": number
  },
  "lender_distribution": [
    {
      "lender": "string",
      "num_claims": number,
      "estimated_value": number
    }
  ],
  "pipeline": {
    "awaiting_dsar": {"count": number, "value": number},
    "pending_submission": {"count": number, "value": number},
    "under_review": {"count": number, "value": number},
    "settlement_offered": {"count": number, "value": number},
    "paid": {"count": number, "value": number}
  },
  "financial_costs": {
    "acquisition_cost": number,
    "submission_cost": number,
    "processing_cost": number,
    "legal_cost": number,
    "total_costs": number,
    "collection_balance": number
  },
  "forecasting": {
    "expected_clients": number,
    "expected_submissions": number,
    "expected_redress": number
  }
}"""

        user_prompt = f"""Analyze this Excel spreadsheet and extract ALL data:

{excel_text}

CRITICAL INSTRUCTIONS:
1. Extract reporting period from row 3
2. Portfolio metrics from rows 9-15 (use CUMULATIVE column)
3. Extract ALL lenders from the table (typically 50-70 lenders) - DO NOT skip any
4. Pipeline stages from rows 18-23
5. Financial costs from rows 32-38
6. Forecasting from rows 42-44

Convert all currency (£X,XXX) to numbers.
If a value is empty/NaN, use 0.
Return ONLY the JSON object."""

        return self.call_openai(system_prompt, user_prompt, "json")


class EconomicAnalysisAgent(BaseAgent):
    """Agent that analyzes economic performance"""

    def analyze_economics(self, excel_data: Dict[str, Any], priority_deed: str) -> str:
        """Analyze economic performance using Priority Deed"""

        system_prompt = """You are a financial analyst specializing in litigation funding economics.
Analyze portfolio performance and profitability."""

        user_prompt = f"""Analyze the economic performance of this PCP claims portfolio:

EXCEL DATA:
{json.dumps(excel_data, indent=2)}

PRIORITY DEED (Profit Distribution):
{priority_deed[:3000]}

Provide analysis covering:

1. **Revenue Analysis**
   - Total claim value and potential DBA proceeds (30% of successful claims)
   - Expected funder collection (80% of DBA proceeds)
   - Expected firm collection (20% of DBA proceeds)
   - MOIC (Multiple on Invested Capital) projection

2. **Cost Analysis**
   - Total costs incurred vs budget
   - Cost per claim acquisition
   - Cost per submission
   - Cost efficiency metrics

3. **Profitability**
   - Gross profit margins
   - Net profit after all costs
   - ROI for funder and firm
   - Break-even analysis

4. **Pipeline Value**
   - Value locked in each pipeline stage
   - Conversion rates between stages
   - Time to cash projections

5. **Key Insights & Recommendations**
   - Performance vs targets
   - Areas of concern
   - Optimization opportunities

Format as clear markdown with headers, bullet points, and specific numbers."""

        return self.call_openai(system_prompt, user_prompt, "text")


class ComplianceAnalysisAgent(BaseAgent):
    """Agent that analyzes FCA compliance"""

    def analyze_compliance(self, excel_data: Dict[str, Any], fca_guidelines: str) -> str:
        """Analyze compliance with FCA regulations"""

        system_prompt = """You are a legal compliance expert specializing in FCA regulations for PCP claims."""

        user_prompt = f"""Analyze FCA compliance for this PCP claims portfolio:

EXCEL DATA:
{json.dumps(excel_data, indent=2)}

FCA GUIDELINES:
{fca_guidelines[:4000]}

Provide compliance analysis covering:

1. **Commission Disclosure Compliance**
   - Are commission rates properly disclosed?
   - Commission percentages analysis
   - Unfair relationship thresholds

2. **Claims Processing Compliance**
   - Proper documentation requirements
   - DSAR (Data Subject Access Request) handling
   - Submission procedures

3. **Success/Rejection Ratios**
   - Claims successful: {excel_data.get('portfolio_metrics', {}).get('claims_successful', 0)}
   - Claims rejected: {excel_data.get('portfolio_metrics', {}).get('claims_rejected', 0)}
   - Compliance with FCA expectations

4. **Risk Assessment**
   - Compliance risks identified
   - Material adverse effects
   - Recommended mitigations

5. **Regulatory Reporting**
   - Adequacy of current reporting
   - Missing information
   - Recommendations for improvement

Format as clear markdown with specific compliance findings."""

        return self.call_openai(system_prompt, user_prompt, "text")


class PortfolioAnalysisAgent(BaseAgent):
    """Agent that analyzes portfolio composition and performance"""

    def analyze_portfolio(self, excel_data: Dict[str, Any]) -> str:
        """Analyze portfolio composition and performance"""

        system_prompt = """You are a portfolio analyst specializing in litigation funding portfolios."""

        lenders = excel_data.get('lender_distribution', [])
        portfolio = excel_data.get('portfolio_metrics', {})

        user_prompt = f"""Analyze this PCP claims portfolio composition:

PORTFOLIO METRICS:
{json.dumps(portfolio, indent=2)}

LENDER DISTRIBUTION ({len(lenders)} lenders):
{json.dumps(lenders[:20], indent=2)}
... and {max(0, len(lenders) - 20)} more lenders

Provide portfolio analysis covering:

1. **Portfolio Size & Growth**
   - Total clients: {portfolio.get('unique_clients', 0)}
   - Total claims: {portfolio.get('unique_claims', 0)}
   - Growth trajectory and velocity

2. **Lender Concentration**
   - Top 5 lenders by claim volume
   - Top 5 lenders by value
   - Concentration risk (% in top lender)
   - Diversification score

3. **Claim Quality**
   - Average claim value: £{portfolio.get('avg_claim_value', 0):,.0f}
   - Success rate: {portfolio.get('claims_successful', 0)}/{portfolio.get('claims_submitted', 0)} submitted
   - Quality indicators

4. **Pipeline Health**
   - Claims in each stage
   - Conversion rates
   - Bottlenecks identified

5. **Portfolio Recommendations**
   - Optimal lender targets
   - Risk mitigation strategies
   - Growth opportunities

Format as clear markdown with specific insights."""

        return self.call_openai(system_prompt, user_prompt, "text")


class ReportGenerationAgent(BaseAgent):
    """Agent that generates comprehensive analysis reports"""

    def generate_report(self,
                       excel_data: Dict[str, Any],
                       economic_analysis: str,
                       compliance_analysis: str,
                       portfolio_analysis: str) -> str:
        """Generate comprehensive report combining all analyses"""

        system_prompt = """You are a senior analyst creating executive reports for litigation funding stakeholders."""

        user_prompt = f"""Create a comprehensive executive report combining these analyses:

EXCEL DATA:
{json.dumps(excel_data, indent=2)}

ECONOMIC ANALYSIS:
{economic_analysis}

COMPLIANCE ANALYSIS:
{compliance_analysis}

PORTFOLIO ANALYSIS:
{portfolio_analysis}

Create a professional executive report with:

# Executive Summary
- Key highlights (3-5 bullet points)
- Overall portfolio health score (0-100)
- Critical issues requiring attention

# Financial Performance
- Include economic analysis insights
- Add specific numbers and calculations
- Charts descriptions (for later generation)

# Compliance Status
- Include compliance analysis insights
- Risk ratings (Low/Medium/High)
- Required actions

# Portfolio Composition
- Include portfolio analysis insights
- Diversification metrics
- Strategic recommendations

# Forecasting & Projections
- Expected performance next quarter
- Revenue projections
- Risk scenarios

# Action Items
- Prioritized list of recommendations
- Owner assignments (Funder/Firm/Processor)
- Urgency levels

Format with clear headers, bullet points, and specific metrics."""

        return self.call_openai(system_prompt, user_prompt, "text")


def analyze_monthly_report(excel_path: str) -> Dict[str, Any]:
    """
    Main function to analyze monthly report using all agents
    """
    print("🤖 Initializing intelligent agents...")

    # Read supporting documents
    priority_deed = ""
    fca_guidelines = ""

    try:
        with open("DOCS/Priorities Deed (EXECUTED).pdf", "r", encoding="utf-8", errors="ignore") as f:
            priority_deed = f.read()[:5000]
    except:
        priority_deed = "Priority Deed: 80% Funder, 20% Firm split after costs"

    try:
        with open("DOCS/FCA Redress Knowledge Base.pdf", "r", encoding="utf-8", errors="ignore") as f:
            fca_guidelines = f.read()[:5000]
    except:
        fca_guidelines = "FCA Guidelines for PCP claims redress"

    # Initialize agents
    excel_agent = ExcelAnalysisAgent()
    economic_agent = EconomicAnalysisAgent()
    compliance_agent = ComplianceAnalysisAgent()
    portfolio_agent = PortfolioAnalysisAgent()
    report_agent = ReportGenerationAgent()

    # Step 1: Extract data from Excel
    print("📊 Agent 1: Analyzing Excel data...")
    excel_data = excel_agent.analyze_excel(excel_path)

    # Step 2: Economic analysis
    print("💰 Agent 2: Performing economic analysis...")
    economic_analysis = economic_agent.analyze_economics(excel_data, priority_deed)

    # Step 3: Compliance analysis
    print("⚖️ Agent 3: Analyzing FCA compliance...")
    compliance_analysis = compliance_agent.analyze_compliance(excel_data, fca_guidelines)

    # Step 4: Portfolio analysis
    print("📈 Agent 4: Analyzing portfolio composition...")
    portfolio_analysis = portfolio_agent.analyze_portfolio(excel_data)

    # Step 5: Generate comprehensive report
    print("📝 Agent 5: Generating comprehensive report...")
    comprehensive_report = report_agent.generate_report(
        excel_data,
        economic_analysis,
        compliance_analysis,
        portfolio_analysis
    )

    print("✅ Analysis complete!")

    return {
        'excel_data': excel_data,
        'economic_analysis': economic_analysis,
        'compliance_analysis': compliance_analysis,
        'portfolio_analysis': portfolio_analysis,
        'comprehensive_report': comprehensive_report
    }


if __name__ == "__main__":
    result = analyze_monthly_report("uploads/Milberg_MOnthly_Report.xlsx")
    print("\n" + "="*80)
    print("COMPREHENSIVE REPORT")
    print("="*80)
    print(result['comprehensive_report'])
