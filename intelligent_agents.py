"""
Intelligent Multi-Agent System for PCP Claims Analysis
4 Specialized Agents working together to generate investor reports
"""

import os
import json
from typing import Dict, Any, List, Tuple
from openai import OpenAI
import pandas as pd
from docx import Document
from docx.shared import Inches
import PyPDF2


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
        self.knowledge_base = {}

    def call_openai(self, system_prompt: str, user_prompt: str, response_format: str = "json", max_tokens: int = 16000) -> Any:
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
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
        else:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.2,
                max_tokens=max_tokens
            )

        result = response.choices[0].message.content.strip()

        if response_format == "json":
            return json.loads(result)
        else:
            return result


class PriorityDeedAgent(BaseAgent):
    """Agent that reads and understands the Priority Deed for profit distribution"""

    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.profit_rules = None

    def read_priority_deed(self, file_path: str = "DOCS/Priorities Deed (EV 9 October 2025).docx") -> Dict[str, Any]:
        """Read Priority Deed document and extract profit distribution rules"""

        print("📄 Priority Deed Agent: Reading profit distribution agreement...")

        try:
            # Read Word document
            doc = Document(file_path)
            text_content = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_content.append(para.text)

            full_text = "\n".join(text_content)

            # Truncate if too long
            if len(full_text) > 15000:
                full_text = full_text[:15000]

        except Exception as e:
            print(f"Warning: Could not read Priority Deed document: {e}")
            full_text = "Priority Deed not available"

        system_prompt = """You are a legal document analyst specializing in litigation funding agreements.
Extract the profit distribution rules from the Priority Deed document.
Return structured JSON with EXACT percentages and rules."""

        user_prompt = f"""Analyze this Priority Deed document and extract profit distribution rules:

{full_text}

Extract and return JSON with:
{{
  "profit_split": {{
    "funder_percentage": number (e.g., 80 for 80%),
    "law_firm_percentage": number (e.g., 20 for 20%),
    "split_basis": "string (e.g., 'after costs', 'of DBA proceeds')"
  }},
  "dba_rate": {{
    "percentage_of_settlement": number (e.g., 30 for 30%),
    "description": "string"
  }},
  "cost_recovery": {{
    "order": "string (e.g., 'costs recovered first, then split')",
    "included_costs": ["list of cost types"]
  }},
  "waterfall": [
    {{
      "priority": 1,
      "recipient": "string",
      "amount_type": "string",
      "description": "string"
    }}
  ],
  "key_terms": {{
    "collection_account": "string describing collection account rules",
    "payment_triggers": "string describing when payments are made",
    "reporting_requirements": "string"
  }}
}}

Be precise with percentages and rules."""

        self.profit_rules = self.call_openai(system_prompt, user_prompt, "json")
        self.knowledge_base = self.profit_rules

        print(f"✅ Extracted profit split: {self.profit_rules['profit_split']['funder_percentage']}% Funder / {self.profit_rules['profit_split']['law_firm_percentage']}% Law Firm")

        return self.profit_rules

    def calculate_distributions(self, total_settlement: float, total_costs: float) -> Dict[str, float]:
        """Calculate profit distributions based on Priority Deed rules"""

        if not self.profit_rules:
            raise ValueError("Priority Deed must be read first")

        # Calculate DBA proceeds (typically 30% of settlement)
        dba_rate = self.profit_rules['dba_rate']['percentage_of_settlement'] / 100
        dba_proceeds = total_settlement * dba_rate

        # Subtract costs first (based on waterfall)
        net_proceeds = dba_proceeds - total_costs

        # Split remaining proceeds
        funder_split = self.profit_rules['profit_split']['funder_percentage'] / 100
        firm_split = self.profit_rules['profit_split']['law_firm_percentage'] / 100

        return {
            "total_settlement": total_settlement,
            "dba_proceeds": dba_proceeds,
            "total_costs": total_costs,
            "net_proceeds": net_proceeds,
            "funder_share": net_proceeds * funder_split,
            "firm_share": net_proceeds * firm_split,
            "funder_percentage": self.profit_rules['profit_split']['funder_percentage'],
            "firm_percentage": self.profit_rules['profit_split']['law_firm_percentage']
        }


class FCAComplianceAgent(BaseAgent):
    """Agent that reads FCA Redress Scheme and validates claim compliance"""

    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.compliance_rules = None

    def read_fca_scheme(self, file_path: str = "FCA redress scheme/Redress Scheme.pdf") -> Dict[str, Any]:
        """Read FCA Redress Scheme PDF and extract compliance rules"""

        print("⚖️ FCA Compliance Agent: Reading FCA Redress Scheme...")

        try:
            # Read PDF
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = []

                # Read first 20 pages (usually contains key info)
                num_pages = min(20, len(pdf_reader.pages))
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())

                full_text = "\n".join(text_content)

                # Truncate if too long
                if len(full_text) > 15000:
                    full_text = full_text[:15000]

        except Exception as e:
            print(f"Warning: Could not read FCA Redress Scheme: {e}")
            full_text = "FCA Redress Scheme not available"

        system_prompt = """You are an FCA compliance expert specializing in motor finance redress schemes.
Extract the key compliance rules and validation criteria for PCP claims.
Return structured JSON."""

        user_prompt = f"""Analyze this FCA Redress Scheme document and extract compliance rules:

{full_text}

Extract and return JSON with:
{{
  "eligible_products": ["list of eligible product types"],
  "commission_thresholds": {{
    "likely_unfair_above": number (percentage),
    "review_required_above": number (percentage),
    "acceptable_below": number (percentage),
    "description": "string"
  }},
  "disclosure_requirements": {{
    "must_disclose": ["list of required disclosures"],
    "disclosure_timing": "string",
    "consequences_of_non_disclosure": "string"
  }},
  "claim_validation": {{
    "required_evidence": ["list of required evidence"],
    "invalid_if": ["list of invalidation criteria"],
    "success_criteria": ["list of success criteria"]
  }},
  "redress_calculation": {{
    "methodology": "string describing how redress is calculated",
    "components": ["list of components included"],
    "exclusions": ["list of exclusions"]
  }},
  "timeline_requirements": {{
    "claim_submission_deadline": "string",
    "expected_response_time": "string",
    "appeal_period": "string"
  }},
  "red_flags": ["list of red flags that indicate non-compliance"]
}}

Be specific with thresholds and criteria."""

        self.compliance_rules = self.call_openai(system_prompt, user_prompt, "json")
        self.knowledge_base = self.compliance_rules

        print(f"✅ Loaded FCA compliance rules for {len(self.compliance_rules.get('eligible_products', []))} product types")

        return self.compliance_rules

    def validate_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a claim against FCA compliance rules"""

        if not self.compliance_rules:
            raise ValueError("FCA Redress Scheme must be read first")

        commission_pct = claim_data.get('commission_pct_of_cost', 0)
        product_type = claim_data.get('product_type', 'Unknown')

        # Check commission threshold
        thresholds = self.compliance_rules.get('commission_thresholds', {})
        likely_unfair = thresholds.get('likely_unfair_above', 50)

        compliance_status = "compliant"
        issues = []

        if commission_pct > likely_unfair:
            compliance_status = "non_compliant"
            issues.append(f"Commission {commission_pct}% exceeds FCA threshold of {likely_unfair}%")

        if product_type not in self.compliance_rules.get('eligible_products', []):
            issues.append(f"Product type '{product_type}' may not be eligible")

        return {
            "claim_id": claim_data.get('claim_id'),
            "compliance_status": compliance_status,
            "commission_percentage": commission_pct,
            "issues": issues,
            "fca_threshold": likely_unfair,
            "is_valid": len(issues) == 0
        }


class MonthlyReportAgent(BaseAgent):
    """Agent that reads and extracts data from monthly Excel reports"""

    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.monthly_data = None

    def analyze_monthly_report(self, file_path: str) -> Dict[str, Any]:
        """Analyze monthly Excel report and extract all metrics"""

        print("📊 Monthly Report Agent: Analyzing Excel report...")

        # Read Excel file
        xl = pd.ExcelFile(file_path)
        sheet_name = xl.sheet_names[0]
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        excel_text = df.to_string()

        # Truncate if too long
        if len(excel_text) > 20000:
            excel_text = excel_text[:20000] + "\n... [truncated]"

        system_prompt = """You are a financial data analyst. Extract ALL data from monthly reports.
Return structured JSON with complete data - do NOT skip any lenders or data points."""

        user_prompt = f"""Analyze this monthly Excel report and extract ALL data:

{excel_text}

Extract and return JSON with:
{{
  "reporting_period": "month/year",
  "portfolio_metrics": {{
    "unique_clients": number,
    "unique_claims": number,
    "claims_submitted": number,
    "claims_successful": number,
    "claims_rejected": number,
    "claims_pending": number,
    "avg_claim_value": number,
    "total_settlement_value": number,
    "success_rate": number (percentage)
  }},
  "lender_distribution": [
    {{
      "lender": "string",
      "num_claims": number,
      "pct_of_total": number,
      "estimated_value": number,
      "avg_claim_value": number
    }}
  ],
  "pipeline": {{
    "awaiting_dsar": {{"count": number, "value": number}},
    "pending_submission": {{"count": number, "value": number}},
    "under_review": {{"count": number, "value": number}},
    "settlement_offered": {{"count": number, "value": number}},
    "paid": {{"count": number, "value": number}}
  }},
  "financial_metrics": {{
    "acquisition_cost": number,
    "submission_cost": number,
    "processing_cost": number,
    "legal_cost": number,
    "total_costs": number,
    "cost_per_claim": number,
    "collection_balance": number
  }},
  "forecasting": {{
    "expected_new_clients": number,
    "expected_submissions": number,
    "expected_settlement_value": number,
    "projected_timeline": "string"
  }},
  "key_changes": {{
    "new_claims_this_month": number,
    "claims_resolved_this_month": number,
    "major_settlements": ["list of notable events"]
  }}
}}

CRITICAL: Extract ALL lenders (typically 50-70), not just the first few. Convert all currency to numbers."""

        self.monthly_data = self.call_openai(system_prompt, user_prompt, "json", max_tokens=16000)
        self.knowledge_base = self.monthly_data

        print(f"✅ Extracted data for {self.monthly_data['portfolio_metrics']['unique_claims']} claims across {len(self.monthly_data['lender_distribution'])} lenders")

        return self.monthly_data


class InvestorReportAgent(BaseAgent):
    """Master agent that generates investor reports using insights from all other agents"""

    def __init__(self, api_key: str = None):
        super().__init__(api_key)

    def generate_investor_report(self,
                                monthly_data: Dict[str, Any],
                                profit_rules: Dict[str, Any],
                                compliance_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive investor report combining all agent insights"""

        print("📝 Investor Report Agent: Generating comprehensive report...")

        system_prompt = """You are a senior investment analyst creating monthly investor reports for litigation funding stakeholders.
Generate factual, data-driven analysis WITHOUT opinions. Focus on metrics, trends, and objective observations."""

        user_prompt = f"""Create a comprehensive monthly investor report using these inputs:

MONTHLY REPORT DATA:
{json.dumps(monthly_data, indent=2)}

PROFIT DISTRIBUTION RULES (from Priority Deed):
{json.dumps(profit_rules, indent=2)}

FCA COMPLIANCE RULES (from Redress Scheme):
{json.dumps(compliance_rules, indent=2)}

Generate a structured investor report in JSON format:
{{
  "executive_summary": {{
    "reporting_period": "string",
    "portfolio_health_score": number (0-100),
    "key_metrics_summary": ["3-5 key metrics with values"],
    "critical_updates": ["major changes or events"]
  }},
  "portfolio_performance": {{
    "total_claims": number,
    "total_clients": number,
    "claims_by_stage": {{}},
    "success_rate": number,
    "average_settlement": number,
    "total_portfolio_value": number,
    "month_over_month_growth": "string with numbers"
  }},
  "financial_analysis": {{
    "total_settlements": number,
    "dba_proceeds_expected": number,
    "total_costs_incurred": number,
    "net_proceeds_after_costs": number,
    "funder_expected_return": number,
    "firm_expected_return": number,
    "roi_projection": number,
    "moic_projection": number
  }},
  "compliance_assessment": {{
    "fca_compliance_status": "compliant/review_required/at_risk",
    "commission_analysis": "string describing commission levels vs FCA thresholds",
    "claims_at_risk": number,
    "compliance_actions_needed": ["list specific actions"]
  }},
  "lender_concentration": {{
    "total_lenders": number,
    "top_5_lenders": [{{"lender": "string", "claims": number, "percentage": number}}],
    "concentration_risk": "low/medium/high with explanation",
    "diversification_score": number (0-100)
  }},
  "pipeline_analysis": {{
    "pipeline_by_stage": {{}},
    "conversion_rates": "string with percentages",
    "estimated_time_to_settlement": "string",
    "pipeline_value": number,
    "bottlenecks": ["list any bottlenecks observed"]
  }},
  "cost_efficiency": {{
    "cost_per_claim": number,
    "cost_per_successful_claim": number,
    "cost_breakdown": {{}},
    "efficiency_trends": "string describing if costs are improving"
  }},
  "forecasting": {{
    "next_month_projections": {{}},
    "quarterly_outlook": "string",
    "expected_settlements_next_90_days": number,
    "projected_returns": {{}}
  }},
  "risk_assessment": {{
    "key_risks": ["list of specific risks with data"],
    "mitigation_status": ["what's being done about each risk"],
    "risk_level": "low/medium/high"
  }},
  "action_items": [
    {{
      "priority": "high/medium/low",
      "action": "string",
      "owner": "Funder/Milberg/Processor",
      "deadline": "string",
      "rationale": "data-driven reason"
    }}
  ]
}}

IMPORTANT:
- Use ONLY the data provided
- Include specific numbers for every metric
- Calculate profit distributions using the Priority Deed split rules
- Flag compliance issues based on FCA thresholds
- Be factual and objective - no opinions
- Show calculations and basis for projections"""

        report_data = self.call_openai(system_prompt, user_prompt, "json", max_tokens=16000)

        # Generate markdown version for display
        markdown_report = self._format_as_markdown(report_data)

        # Generate a short narrative (few lines) to accompany charts in the DOCX
        narrative = self._generate_short_narrative(report_data)

        print("✅ Investor report generated successfully")

        return {
            "report_data": report_data,
            "markdown_report": markdown_report,
            "narrative": narrative,
        }

    def _generate_short_narrative(self, report_data: Dict[str, Any]) -> str:
        """Generate brief narrative lines to explain the data (kept short and factual)."""
        exec_sum = report_data.get("executive_summary") or {}
        perf = report_data.get("portfolio_performance") or {}
        fin = report_data.get("financial_analysis") or {}

        period = exec_sum.get("reporting_period") or "the reporting period"
        claims = perf.get("total_claims")
        clients = perf.get("total_clients")
        value = perf.get("total_portfolio_value")
        roi = fin.get("roi_projection")

        parts = [
            f"This report summarizes portfolio activity for {period}.",
        ]
        if claims is not None and clients is not None:
            parts.append(f"The portfolio contains {claims} claims across {clients} clients.")
        if value is not None:
            parts.append(f"Estimated total portfolio value is £{value:,.0f}.")
        if roi is not None:
            parts.append(f"Projected ROI based on current inputs is {roi:.1f}%.")

        # Keep it short (few lines)
        return " ".join(parts[:4])


def _build_dashboard_figures(monthly_data: Dict[str, Any], report_data: Dict[str, Any]):
    """Create Plotly figures similar to the dashboard for embedding in the DOCX."""
    try:
        import plotly.express as px
        import plotly.graph_objects as go
    except Exception:
        return {}

    figs = {}

    # Lender Top 10 by claims
    lenders = (monthly_data or {}).get("lender_distribution") or []
    if lenders:
        df_l = pd.DataFrame(lenders).sort_values("num_claims", ascending=False)
        top10 = df_l.head(10)
        others_claims = df_l.iloc[10:]["num_claims"].sum() if len(df_l) > 10 else 0
        if others_claims > 0:
            pie_df = pd.concat(
                [top10[["lender", "num_claims"]], pd.DataFrame([{ "lender": "Others", "num_claims": others_claims }])]
            )
        else:
            pie_df = top10[["lender", "num_claims"]]

        fig_pie = px.pie(pie_df, values="num_claims", names="lender", hole=0.4)
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(title="Top 10 Lenders by Claims")
        figs["lenders_pie"] = fig_pie

        # Top 15 lenders by value (bar)
        if "estimated_value" in df_l.columns:
            top15_val = df_l.head(15).sort_values("estimated_value")
            fig_bar = px.bar(
                top15_val,
                x="estimated_value",
                y="lender",
                orientation="h",
                color="num_claims" if "num_claims" in top15_val.columns else None,
                title="Top 15 Lenders by Portfolio Value",
            )
            figs["lenders_value_bar"] = fig_bar

    # Pipeline funnel by count
    pipeline = (monthly_data or {}).get("pipeline") or {}
    stage_order = [
        ("Awaiting DSAR", "awaiting_dsar"),
        ("Pending Submission", "pending_submission"),
        ("Under Review", "under_review"),
        ("Settlement Offered", "settlement_offered"),
        ("Paid", "paid"),
    ]
    try:
        pipe_rows = []
        for label, key in stage_order:
            d = pipeline.get(key) or {}
            pipe_rows.append({"Stage": label, "Count": d.get("count", 0), "Value": d.get("value", 0)})
        df_p = pd.DataFrame(pipe_rows)
        fig_funnel = go.Figure(go.Funnel(y=df_p["Stage"], x=df_p["Count"], textinfo="value+percent initial"))
        fig_funnel.update_layout(title="Pipeline Funnel (by Count)")
        figs["pipeline_funnel"] = fig_funnel

        fig_pipe_val = px.bar(df_p, x="Stage", y="Value", title="Pipeline Value by Stage")
        figs["pipeline_value"] = fig_pipe_val
    except Exception:
        pass

    return figs


def _export_plotly_fig_to_png_bytes(fig) -> bytes:
    """Export a Plotly figure to PNG bytes (requires kaleido)."""
    try:
        import plotly.io as pio
        return pio.to_image(fig, format="png", width=1200, height=700, scale=2)
    except Exception:
        return b""


def build_investor_report_docx(
    *,
    out_path: str,
    narrative: str,
    monthly_data: Dict[str, Any],
    investor_report: Dict[str, Any],
) -> str:
    """Create a .docx investor report including brief narrative and dashboard charts."""

    doc = Document()
    doc.add_heading("Monthly Investor Report", level=0)

    period = ((investor_report or {}).get("executive_summary") or {}).get("reporting_period")
    if period:
        doc.add_paragraph(str(period))

    if narrative:
        doc.add_paragraph(narrative)

    doc.add_heading("Key Charts", level=1)

    figs = _build_dashboard_figures(monthly_data, investor_report)

    # Write images to temp files (python-docx needs file paths)
    tmp_dir = os.path.join(os.path.dirname(out_path), ".tmp_report_assets")
    os.makedirs(tmp_dir, exist_ok=True)

    added_any = False
    for key, fig in figs.items():
        png = _export_plotly_fig_to_png_bytes(fig)
        if not png:
            continue
        img_path = os.path.join(tmp_dir, f"{key}.png")
        with open(img_path, "wb") as f:
            f.write(png)
        doc.add_paragraph(key.replace("_", " ").title())
        doc.add_picture(img_path, width=Inches(6.5))
        added_any = True

    if not added_any:
        doc.add_paragraph("Charts could not be embedded (PNG export requires the 'kaleido' package).")

    # Also include the action items (brief)
    doc.add_heading("Action Items", level=1)
    for item in ((investor_report or {}).get("action_items") or []):
        item = item or {}
        doc.add_paragraph(
            f"[{(item.get('priority') or 'N/A').upper()}] {item.get('action') or 'N/A'}  "
            f"Owner: {item.get('owner') or 'N/A'}  Deadline: {item.get('deadline') or 'N/A'}",
            style=None,
        )

    doc.save(out_path)
    return out_path


def generate_full_investor_report(excel_path: str) -> Dict[str, Any]:
    """
    Main orchestration function - coordinates all agents to generate investor report
    """
    print("="*80)
    print("🤖 INTELLIGENT MULTI-AGENT SYSTEM")
    print("="*80)

    # Initialize all agents
    priority_deed_agent = PriorityDeedAgent()
    fca_agent = FCAComplianceAgent()
    monthly_agent = MonthlyReportAgent()
    investor_agent = InvestorReportAgent()

    # Step 1: Priority Deed Agent reads profit distribution rules
    profit_rules = priority_deed_agent.read_priority_deed()

    # Step 2: FCA Agent reads compliance requirements
    compliance_rules = fca_agent.read_fca_scheme()

    # Step 3: Monthly Report Agent extracts data from Excel
    monthly_data = monthly_agent.analyze_monthly_report(excel_path)

    # Step 4: Investor Report Agent generates comprehensive report
    report = investor_agent.generate_investor_report(
        monthly_data=monthly_data,
        profit_rules=profit_rules,
        compliance_rules=compliance_rules
    )

    # Build DOCX report on disk
    os.makedirs("reports", exist_ok=True)
    period = (monthly_data or {}).get("reporting_period") or "Report"
    safe_period = str(period).replace("/", "-").replace("\\", "-").replace(":", "-")
    docx_path = os.path.join("reports", f"Investor_Report_{safe_period}.docx")
    try:
        build_investor_report_docx(
            out_path=docx_path,
            narrative=report.get("narrative") or "",
            monthly_data=monthly_data,
            investor_report=report.get("report_data") or {},
        )
    except Exception as e:
        # Keep generation robust; downstream UI can show charts warning
        print(f"Warning: DOCX report generation failed: {e}")
        docx_path = None

    print("="*80)
    print("✅ REPORT GENERATION COMPLETE")
    print("="*80)

    return {
        "monthly_data": monthly_data,
        "profit_rules": profit_rules,
        "compliance_rules": compliance_rules,
        "investor_report": report["report_data"],
        "markdown_report": report["markdown_report"],
        "docx_report_path": docx_path,
    }


if __name__ == "__main__":
    result = generate_full_investor_report("uploads/Milberg_MOnthly_Report.xlsx")
    print("\n" + result['markdown_report'])
