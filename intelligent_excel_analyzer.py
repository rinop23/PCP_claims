"""
Intelligent Excel Analyzer using OpenAI
Analyzes Excel sheets and extracts structured data using LLM
"""

import pandas as pd
import openpyxl
from typing import Dict, Any, List
import json
import os
from openai import OpenAI


class IntelligentExcelAnalyzer:
    """Use OpenAI to intelligently analyze and extract data from Excel files"""

    def __init__(self, api_key: str = None):
        # Try to get API key from multiple sources
        if api_key:
            self.api_key = api_key
        else:
            # Try environment variable
            self.api_key = os.environ.get("OPENAI_API_KEY")

            # Try Streamlit secrets
            if not self.api_key:
                try:
                    import streamlit as st
                    self.api_key = st.secrets.get("OPENAI_API_KEY")
                except:
                    pass

        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable or Streamlit secret.")

        self.client = OpenAI(api_key=self.api_key)

    def analyze_excel_with_ai(self, file_path: str) -> Dict[str, Any]:
        """
        Use OpenAI to analyze Excel file and extract structured data
        """
        # Read Excel file
        xl = pd.ExcelFile(file_path)

        # Get all sheet names
        sheet_names = xl.sheet_names

        # Read all sheets as text representation
        sheets_data = {}
        for sheet_name in sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            # Convert to readable text format
            sheets_data[sheet_name] = df.to_string()

        # Prepare prompt for OpenAI
        prompt = self._create_analysis_prompt(sheets_data)

        # Call OpenAI
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert financial data analyst. Your task is to analyze Excel spreadsheets and extract structured data.
You must return ONLY valid JSON with no additional text or markdown formatting.

Expected JSON structure:
{
    "report_type": "Monthly Summary" or "Detailed Claims",
    "reporting_period": "Month/Year",
    "portfolio_overview": {
        "total_claims": number,
        "total_claimants": number,
        "total_claims_submitted": number,
        "claims_successful": number,
        "claims_rejected": number,
        "avg_claim_value": number,
        "total_claim_value": number,
        "total_funded": number
    },
    "lender_distribution": [
        {
            "lender": "string",
            "num_claims": number,
            "pct_total": number,
            "estimated_value": number
        }
    ],
    "pipeline_breakdown": {
        "awaiting_dsar": {"count": number, "value": number},
        "pending_submission": {"count": number, "value": number},
        "under_review": {"count": number, "value": number},
        "settlement_offered": {"count": number, "value": number},
        "paid": {"count": number, "value": number}
    },
    "financial_utilisation": {
        "acquisition_cost": number,
        "submission_cost": number,
        "processing_cost": number,
        "legal_cost": number,
        "total_action_costs": number,
        "collection_account_balance": number
    },
    "forecasting": {
        "expected_new_clients": number,
        "expected_submissions": number,
        "expected_redress": number
    }
}"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=8000
            )

            # Parse response
            result_text = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            extracted_data = json.loads(result_text)

            # Add metadata
            extracted_data['processed_at'] = pd.Timestamp.now().isoformat()
            extracted_data['source_file'] = file_path
            extracted_data['extraction_method'] = 'openai_analysis'

            return extracted_data

        except Exception as e:
            print(f"Error using OpenAI to analyze Excel: {str(e)}")
            raise

    def _create_analysis_prompt(self, sheets_data: Dict[str, str]) -> str:
        """Create prompt for OpenAI analysis"""

        prompt = "Analyze the following Excel spreadsheet data and extract structured information.\n\n"

        for sheet_name, sheet_content in sheets_data.items():
            # Truncate very long sheets but keep more for lender data
            if len(sheet_content) > 15000:
                sheet_content = sheet_content[:15000] + "\n... [truncated]"

            prompt += f"=== SHEET: {sheet_name} ===\n{sheet_content}\n\n"

        prompt += """
Extract the following information:

1. **Report Type**: Determine if this is a "Monthly Summary" or "Detailed Claims" report
2. **Reporting Period**: Extract the month/year this report covers
3. **Portfolio Overview**:
   - Total unique clients (cumulative)
   - Total unique claims (cumulative)
   - Claims submitted (cumulative)
   - Claims successful (cumulative)
   - Claims rejected (cumulative)
   - Average claim value
   - Calculate total_claim_value from lender distribution
   - Calculate total_funded (assume 70% of total_claim_value if not specified)

4. **Lender Distribution**: IMPORTANT - Extract ALL lenders from the table (there are typically 50-70 lenders):
   - Lender name (exactly as shown)
   - Number of claims (integer)
   - Percentage of total (as decimal, e.g., 1.1% → 0.011)
   - Estimated value (convert £X,XXX.XX to numeric value)
   - DO NOT skip any rows - include every lender in the table until you reach the next section

5. **Claim Pipeline**: Extract counts and values for each stage:
   - Awaiting DSAR
   - Pending Submission
   - Under Review
   - Settlement Offered
   - Paid

6. **Financial Utilisation**: Extract all cost data:
   - Acquisition cost
   - Submission cost
   - Processing cost
   - Legal cost
   - Total action costs
   - Collection account balance

7. **Forecasting**: Extract forecasts for:
   - Expected new clients
   - Expected submissions
   - Expected redress

IMPORTANT:
- Convert all currency strings (£X,XXX) to numbers
- Convert all percentage strings (XX%) to decimal numbers
- If a field is not found, use 0 for numbers, [] for arrays, {} for objects
- Return ONLY the JSON object, no additional text
"""

        return prompt


def test_analyzer():
    """Test the intelligent analyzer"""
    analyzer = IntelligentExcelAnalyzer()

    file_path = "uploads/Milberg_MOnthly_Report.xlsx"

    print(f"Analyzing {file_path} with OpenAI...")
    result = analyzer.analyze_excel_with_ai(file_path)

    print("\n=== EXTRACTED DATA ===")
    print(json.dumps(result, indent=2))

    print("\n=== SUMMARY ===")
    print(f"Report Type: {result.get('report_type')}")
    print(f"Reporting Period: {result.get('reporting_period')}")
    print(f"Total Claims: {result.get('portfolio_overview', {}).get('total_claims')}")
    print(f"Total Lenders: {len(result.get('lender_distribution', []))}")
    print(f"Total Claim Value: £{result.get('portfolio_overview', {}).get('total_claim_value', 0):,.2f}")


if __name__ == "__main__":
    test_analyzer()
