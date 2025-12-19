"""
Data Extractor - INTELLIGENT extraction using OpenAI API
Reads Excel files dynamically - no hardcoded row numbers
"""

import pandas as pd
import json
import os
from typing import Dict, Any, List
from openai import OpenAI


def get_openai_client():
    """Get OpenAI client with API key from environment or Streamlit secrets"""
    api_key = os.environ.get('OPENAI_API_KEY')

    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get('OPENAI_API_KEY')
        except:
            pass

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment or Streamlit secrets")

    return OpenAI(api_key=api_key)


def extract_monthly_report_data(file_path: str) -> Dict[str, Any]:
    """
    INTELLIGENT extraction using OpenAI to read Excel data.
    No hardcoded rows - AI understands the structure dynamically.
    """
    print(f"DEBUG: Attempting to read file: {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read all sheets to find the right one
    try:
        # Try 'Monthly Summary' first
        df = pd.read_excel(file_path, sheet_name='Monthly Summary', header=None)
        sheet_name = 'Monthly Summary'
    except:
        # Get first sheet
        xl = pd.ExcelFile(file_path)
        sheet_name = xl.sheet_names[0]
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

    print(f"DEBUG: Reading sheet '{sheet_name}', DataFrame shape: {df.shape}")

    # Convert DataFrame to string for OpenAI analysis
    # Include enough rows to capture all data
    max_rows = min(150, len(df))
    excel_content = df.head(max_rows).to_string(index=True, header=False)

    # Truncate if too long (keep under token limits)
    if len(excel_content) > 30000:
        excel_content = excel_content[:30000]

    print(f"DEBUG: Excel content length: {len(excel_content)} chars")

    # Use OpenAI to intelligently extract data
    client = get_openai_client()

    extraction_prompt = f"""You are a data extraction expert. Analyze this Excel spreadsheet and extract ALL data accurately.

EXCEL CONTENT:
{excel_content}

EXTRACT THE FOLLOWING (use exact numbers from the cells, do not calculate or estimate):

1. PORTFOLIO METRICS (look in "Portfolio Overview" section):
   - "Unique Clients" row has Current Month and Cumulative columns - extract BOTH values
   - "Unique Claims" row has Current Month and Cumulative columns - extract BOTH values
   - "Claims Submitted", "Claims Successful", "Claims Rejected" - get Cumulative values
   - "Average Claim Value" - get the value (may be a large number like 151900 or 228900)

2. PIPELINE BREAKDOWN (look in "Claim Pipeline Breakdown" section):
   - "Awaiting DSAR Response" - extract Count and Estimated Value
   - "Pending Submission to Redress Scheme" - extract Count and Value
   - "Redress Scheme - Claims Under Review" - extract Count and Value
   - "Redress Scheme - Settlement Offered" - extract Count and Value
   - "Paid" - extract Count and Value

3. LENDER DISTRIBUTION (look for "Defendant" header):
   - This is a large table with columns: Defendant, Number of Claims, % of Total, Estimated Value
   - Extract ALL rows (there are typically 60-80 lenders)
   - Each row has: lender name, number of claims, percentage (like 0.009 means 0.9%), estimated value

4. FINANCIAL COSTS (look in "Financial Utilisation Overview" section):
   - "Client Acquisition Cost" - Current Month and Cumulative
   - "Claim Submission Cost" - Current Month and Cumulative
   - "Total Action Costs" - get cumulative value
   - "Collection Account Balance" - get value

5. FORECASTING (look in "Forecasting" section):
   - "Expected New Clients"
   - "Expected Submissions"
   - "Expected Redress"

6. TOTALS (look for "Grand Summary" row):
   - This row has the TOTAL claims count and TOTAL estimated value
   - The total claims should match the sum of all lender claims (typically 300+)
   - The total value should be a large number (like 228900)

CRITICAL: The "Grand Summary" row contains the portfolio totals:
- total_claims: the number in the "Number of Claims" column (e.g., 327)
- total_estimated_value: the number in the "Estimated Value" column (e.g., 228900)

Return ONLY valid JSON in this exact format:
{{
    "portfolio_metrics": {{
        "unique_clients_current": <number>,
        "unique_clients_cumulative": <number>,
        "unique_claims_current": <number>,
        "unique_claims_cumulative": <number>,
        "claims_submitted": <number>,
        "claims_successful": <number>,
        "claims_rejected": <number>,
        "avg_claim_value": <number>
    }},
    "pipeline": {{
        "awaiting_dsar": {{"count": <number>, "value": <number>}},
        "pending_submission": {{"count": <number>, "value": <number>}},
        "under_review": {{"count": <number>, "value": <number>}},
        "settlement_offered": {{"count": <number>, "value": <number>}},
        "paid": {{"count": <number>, "value": <number>}}
    }},
    "lender_distribution": [
        {{"lender": "<name>", "num_claims": <number>, "pct_of_total": <number>, "estimated_value": <number>}},
        ... (include ALL lenders)
    ],
    "financial_costs": {{
        "acquisition_cost_current": <number>,
        "acquisition_cost_cumulative": <number>,
        "submission_cost_current": <number>,
        "submission_cost_cumulative": <number>,
        "processing_cost": <number>,
        "legal_cost": <number>,
        "total_costs": <number>
    }},
    "forecasting": {{
        "expected_new_clients": <number>,
        "expected_submissions": <number>,
        "expected_redress": <number>
    }},
    "portfolio_totals": {{
        "total_claims": <number>,
        "total_estimated_value": <number>
    }}
}}

IMPORTANT:
- Use 0 for any values you cannot find
- Extract numbers EXACTLY as they appear (don't calculate)
- Include ALL lenders, not just top ones
- Currency values should be numbers only (no £ or commas)
- Return ONLY the JSON, no other text"""

    print("DEBUG: Calling OpenAI for intelligent extraction...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a precise data extraction assistant. Return only valid JSON."},
                {"role": "user", "content": extraction_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=16000,
            temperature=0
        )

        result_text = response.choices[0].message.content
        print(f"DEBUG: OpenAI response length: {len(result_text)} chars")

        # Parse JSON response
        data = json.loads(result_text)

        # Validate and add calculated fields
        data = validate_and_enhance_data(data)

        print(f"DEBUG: Extracted {len(data.get('lender_distribution', []))} lenders")
        print(f"DEBUG: Portfolio metrics: {data.get('portfolio_metrics', {})}")

        return data

    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse OpenAI response as JSON: {e}")
        print(f"Response was: {result_text[:500]}...")
        return get_empty_data_structure()
    except Exception as e:
        print(f"ERROR: OpenAI extraction failed: {e}")
        return get_empty_data_structure()


def validate_and_enhance_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate extracted data and add calculated fields"""

    # Ensure all required keys exist
    if 'portfolio_metrics' not in data:
        data['portfolio_metrics'] = {}
    if 'pipeline' not in data:
        data['pipeline'] = {}
    if 'lender_distribution' not in data:
        data['lender_distribution'] = []
    if 'financial_costs' not in data:
        data['financial_costs'] = {}
    if 'forecasting' not in data:
        data['forecasting'] = {}
    if 'portfolio_totals' not in data:
        data['portfolio_totals'] = {}

    # Ensure portfolio_metrics has all required keys with defaults
    pm = data['portfolio_metrics']
    pm.setdefault('unique_clients_current', 0)
    pm.setdefault('unique_clients_cumulative', 0)
    pm.setdefault('unique_claims_current', 0)
    pm.setdefault('unique_claims_cumulative', 0)
    pm.setdefault('claims_submitted', 0)
    pm.setdefault('claims_successful', 0)
    pm.setdefault('claims_rejected', 0)
    pm.setdefault('avg_claim_value', 0)

    # Ensure pipeline has all required stages with defaults
    pipeline_stages = ['awaiting_dsar', 'pending_submission', 'under_review', 'settlement_offered', 'paid']
    for stage in pipeline_stages:
        if stage not in data['pipeline']:
            data['pipeline'][stage] = {'count': 0, 'value': 0}
        else:
            data['pipeline'][stage].setdefault('count', 0)
            data['pipeline'][stage].setdefault('value', 0)

    # Add avg_claim_value to lenders if missing
    for lender in data['lender_distribution']:
        if 'avg_claim_value' not in lender and lender.get('num_claims', 0) > 0:
            lender['avg_claim_value'] = lender.get('estimated_value', 0) / lender['num_claims']
        elif 'avg_claim_value' not in lender:
            lender['avg_claim_value'] = 0

    # Calculate total costs if not present
    if 'total_costs' not in data['financial_costs'] or data['financial_costs']['total_costs'] == 0:
        data['financial_costs']['total_costs'] = (
            data['financial_costs'].get('acquisition_cost_cumulative', 0) +
            data['financial_costs'].get('submission_cost_cumulative', 0) +
            data['financial_costs'].get('processing_cost', 0) +
            data['financial_costs'].get('legal_cost', 0)
        )

    # Ensure portfolio_totals has required keys - calculate from lenders if not present
    pt = data['portfolio_totals']
    if pt.get('total_claims', 0) == 0 and data['lender_distribution']:
        pt['total_claims'] = sum(l.get('num_claims', 0) for l in data['lender_distribution'])
    if pt.get('total_estimated_value', 0) == 0 and data['lender_distribution']:
        pt['total_estimated_value'] = sum(l.get('estimated_value', 0) for l in data['lender_distribution'])

    # Cross-validate: total_claims should match unique_claims_cumulative
    if pt.get('total_claims', 0) == 0 and pm.get('unique_claims_cumulative', 0) > 0:
        pt['total_claims'] = pm['unique_claims_cumulative']

    pt.setdefault('total_claims', 0)
    pt.setdefault('total_estimated_value', 0)

    # Add reporting period
    data['reporting_period'] = 'Monthly Report'

    print(f"DEBUG validate_and_enhance: total_claims={pt.get('total_claims')}, total_value={pt.get('total_estimated_value')}")
    print(f"DEBUG validate_and_enhance: clients_cumulative={pm.get('unique_clients_cumulative')}, claims_cumulative={pm.get('unique_claims_cumulative')}")

    return data


def get_empty_data_structure() -> Dict[str, Any]:
    """Return empty data structure for error cases"""
    return {
        'reporting_period': 'Monthly Report',
        'portfolio_metrics': {
            'unique_clients_current': 0,
            'unique_clients_cumulative': 0,
            'unique_claims_current': 0,
            'unique_claims_cumulative': 0,
            'claims_submitted': 0,
            'claims_successful': 0,
            'claims_rejected': 0,
            'avg_claim_value': 0
        },
        'pipeline': {
            'awaiting_dsar': {'count': 0, 'value': 0},
            'pending_submission': {'count': 0, 'value': 0},
            'under_review': {'count': 0, 'value': 0},
            'settlement_offered': {'count': 0, 'value': 0},
            'paid': {'count': 0, 'value': 0}
        },
        'lender_distribution': [],
        'financial_costs': {
            'acquisition_cost_current': 0,
            'acquisition_cost_cumulative': 0,
            'submission_cost_current': 0,
            'submission_cost_cumulative': 0,
            'processing_cost': 0,
            'legal_cost': 0,
            'total_costs': 0
        },
        'forecasting': {
            'expected_new_clients': 0,
            'expected_submissions': 0,
            'expected_redress': 0
        },
        'portfolio_totals': {
            'total_claims': 0,
            'total_estimated_value': 0
        }
    }


def read_priority_deed_rules() -> Dict[str, Any]:
    """
    Read Priority Deed document using OpenAI to extract profit distribution rules.
    Falls back to known rules if document cannot be read.
    """
    docs_path = "DOCS"
    priority_deed_file = None

    # Look for Priority Deed document
    if os.path.exists(docs_path):
        for file in os.listdir(docs_path):
            if 'priorit' in file.lower() and file.endswith('.docx'):
                priority_deed_file = os.path.join(docs_path, file)
                break

    if priority_deed_file and os.path.exists(priority_deed_file):
        try:
            from docx import Document
            doc = Document(priority_deed_file)
            doc_text = "\n".join([para.text for para in doc.paragraphs])

            # Use OpenAI to extract rules
            client = get_openai_client()

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Extract financial terms from legal documents. Return JSON only."},
                    {"role": "user", "content": f"""Extract the profit distribution rules from this Priority Deed:

{doc_text[:8000]}

Return JSON with:
{{
    "dba_rate": <percentage of settlement that becomes DBA proceeds>,
    "funder_percentage": <funder's share of net proceeds>,
    "firm_percentage": <law firm's share of net proceeds>,
    "cost_recovery_first": <true if costs recovered before profit split>,
    "description": "<one sentence summary of the arrangement>"
}}"""}
                ],
                response_format={"type": "json_object"},
                max_tokens=500
            )

            rules = json.loads(response.choices[0].message.content)
            print(f"DEBUG: Extracted Priority Deed rules: {rules}")
            return rules

        except Exception as e:
            print(f"Warning: Could not read Priority Deed with OpenAI: {e}")

    # Fallback to known rules
    return {
        'dba_rate': 30,  # 30% of settlement goes to DBA proceeds
        'funder_percentage': 80,  # 80% of net proceeds to Funder
        'firm_percentage': 20,  # 20% of net proceeds to Law Firm
        'cost_recovery_first': True,  # Costs are recovered before profit split
        'description': '80/20 split after costs, from 30% DBA proceeds'
    }


def calculate_financial_projections(portfolio_data: Dict[str, Any], costs: Dict[str, Any], priority_deed: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate financial projections using actual data and Priority Deed rules"""

    # Get total estimated settlement value
    total_settlement = portfolio_data.get('total_estimated_value', 0)

    # Calculate DBA proceeds (30% of settlements)
    dba_rate = priority_deed.get('dba_rate', 30) / 100
    dba_proceeds = total_settlement * dba_rate

    # Get total costs
    total_costs = costs.get('total_costs', 0)

    # Calculate net proceeds (DBA proceeds - costs)
    net_proceeds = dba_proceeds - total_costs

    # Calculate profit split
    funder_pct = priority_deed.get('funder_percentage', 80) / 100
    firm_pct = priority_deed.get('firm_percentage', 20) / 100

    funder_return = net_proceeds * funder_pct if net_proceeds > 0 else 0
    firm_return = net_proceeds * firm_pct if net_proceeds > 0 else 0

    # Calculate ROI and MOIC
    roi = (funder_return / total_costs * 100) if total_costs > 0 else 0
    moic = (funder_return / total_costs) if total_costs > 0 else 0

    return {
        'total_settlement_value': total_settlement,
        'dba_proceeds': dba_proceeds,
        'dba_rate': priority_deed.get('dba_rate', 30),
        'total_costs': total_costs,
        'net_proceeds': net_proceeds,
        'funder_return': funder_return,
        'firm_return': firm_return,
        'funder_percentage': priority_deed.get('funder_percentage', 80),
        'firm_percentage': priority_deed.get('firm_percentage', 20),
        'roi': roi,
        'moic': moic
    }


if __name__ == "__main__":
    # Test extraction with new report
    test_files = [
        "reports/2025.12.18 Milberg Motor Finance - Monthly Report December 2025.xlsx",
        "uploads/Milberg_MOnthly_Report.xlsx"
    ]

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n{'='*80}")
            print(f"TESTING: {test_file}")
            print("="*80)

            data = extract_monthly_report_data(test_file)

            print("\nPortfolio Metrics:")
            for key, value in data['portfolio_metrics'].items():
                print(f"  {key}: {value}")

            print(f"\nLenders: {len(data['lender_distribution'])}")
            print("Top 5 lenders:")
            for lender in data['lender_distribution'][:5]:
                print(f"  - {lender['lender']}: {lender['num_claims']} claims, £{lender.get('estimated_value', 0):,.2f}")

            print("\nPipeline:")
            for stage, info in data['pipeline'].items():
                print(f"  {stage}: {info.get('count', 0)} claims, £{info.get('value', 0):,.2f}")

            print("\nFinancial Costs:")
            for key, value in data['financial_costs'].items():
                print(f"  {key}: £{value:,.2f}" if isinstance(value, (int, float)) else f"  {key}: {value}")

            print("\nPortfolio Totals:")
            print(f"  Total Claims: {data['portfolio_totals'].get('total_claims', 0)}")
            print(f"  Total Estimated Value: £{data['portfolio_totals'].get('total_estimated_value', 0):,.2f}")

            # Test financial calculations
            priority_deed = read_priority_deed_rules()
            financials = calculate_financial_projections(
                data['portfolio_totals'],
                data['financial_costs'],
                priority_deed
            )

            print("\nFinancial Projections:")
            print(f"  Total Settlement Value: £{financials['total_settlement_value']:,.2f}")
            print(f"  DBA Proceeds ({financials['dba_rate']}%): £{financials['dba_proceeds']:,.2f}")
            print(f"  Total Costs: £{financials['total_costs']:,.2f}")
            print(f"  Net Proceeds: £{financials['net_proceeds']:,.2f}")
            print(f"  Funder Return ({financials['funder_percentage']}%): £{financials['funder_return']:,.2f}")
            print(f"  Firm Return ({financials['firm_percentage']}%): £{financials['firm_return']:,.2f}")
            print(f"  ROI: {financials['roi']:.1f}%")
            print(f"  MOIC: {financials['moic']:.2f}x")

            break
    else:
        print("No test files found!")
