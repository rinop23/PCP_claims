"""
Data Extractor - Extracts ACTUAL numbers from Milberg Monthly Report Excel
No AI needed - direct data extraction
"""

import pandas as pd
import re
from typing import Dict, Any, List


def clean_currency(value) -> float:
    """Convert currency string to float"""
    if pd.isna(value) or value == '' or value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    # Remove currency symbols, commas, spaces
    value_str = str(value).replace('£', '').replace('�', '').replace(',', '').replace(' ', '').strip()

    try:
        return float(value_str)
    except:
        return 0.0


def clean_percentage(value) -> float:
    """Convert percentage string to float"""
    if pd.isna(value) or value == '':
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    value_str = str(value).replace('%', '').strip()
    try:
        return float(value_str)
    except:
        return 0.0


def extract_monthly_report_data(file_path: str) -> Dict[str, Any]:
    """Extract all actual data from Milberg Monthly Report Excel"""

    # Read Excel file with no header
    df = pd.read_excel(file_path, sheet_name='Monthly Summary', header=None)

    # Initialize data structure
    data = {
        'reporting_period': 'Monthly Report',
        'portfolio_metrics': {},
        'lender_distribution': [],
        'financial_costs': {},
        'pipeline': {},
        'forecasting': {}
    }

    # Extract Portfolio Overview (rows 8-14)
    # Row 9: Unique Clients - Current Month (col 1), Cumulative (col 2)
    # Row 10: Unique Claims
    try:
        data['portfolio_metrics'] = {
            'unique_clients_current': int(df.iloc[9, 1]) if not pd.isna(df.iloc[9, 1]) else 0,
            'unique_clients_cumulative': int(df.iloc[9, 2]) if not pd.isna(df.iloc[9, 2]) else 0,
            'unique_claims_current': int(df.iloc[10, 1]) if not pd.isna(df.iloc[10, 1]) else 0,
            'unique_claims_cumulative': int(df.iloc[10, 2]) if not pd.isna(df.iloc[10, 2]) else 0,
            'claims_submitted': int(df.iloc[11, 2]) if not pd.isna(df.iloc[11, 2]) else 0,
            'claims_successful': int(df.iloc[12, 2]) if not pd.isna(df.iloc[12, 2]) else 0,
            'claims_rejected': int(df.iloc[13, 2]) if not pd.isna(df.iloc[13, 2]) else 0,
            'avg_claim_value': clean_currency(df.iloc[14, 2])
        }
    except Exception as e:
        print(f"Warning: Could not extract portfolio metrics: {e}")

    # Extract Pipeline Breakdown (rows 17-22)
    try:
        data['pipeline'] = {
            'awaiting_dsar': {
                'count': int(df.iloc[18, 1]) if not pd.isna(df.iloc[18, 1]) else 0,
                'value': clean_currency(df.iloc[18, 2])
            },
            'pending_submission': {
                'count': int(df.iloc[19, 1]) if not pd.isna(df.iloc[19, 1]) else 0,
                'value': clean_currency(df.iloc[19, 2])
            },
            'under_review': {
                'count': int(df.iloc[20, 1]) if not pd.isna(df.iloc[20, 1]) else 0,
                'value': clean_currency(df.iloc[20, 2])
            },
            'settlement_offered': {
                'count': int(df.iloc[21, 1]) if not pd.isna(df.iloc[21, 1]) else 0,
                'value': clean_currency(df.iloc[21, 2])
            },
            'paid': {
                'count': int(df.iloc[22, 1]) if not pd.isna(df.iloc[22, 1]) else 0,
                'value': clean_currency(df.iloc[22, 2])
            }
        }
    except Exception as e:
        print(f"Warning: Could not extract pipeline: {e}")

    # Extract Lender Distribution (rows 27-87)
    # Column 0: Lender name, Column 1: No. Claims, Column 2: % of Total, Column 3: Est. Value
    lenders = []

    for i in range(27, 88):  # Rows with lender data
        try:
            lender_name = df.iloc[i, 0]

            # Skip if it's "Grand Summary" or empty
            if pd.isna(lender_name) or 'Grand Summary' in str(lender_name):
                break

            num_claims = int(df.iloc[i, 1]) if not pd.isna(df.iloc[i, 1]) else 0
            pct_total = clean_percentage(df.iloc[i, 2])
            est_value = clean_currency(df.iloc[i, 3])

            if num_claims > 0:  # Only add if there are claims
                lenders.append({
                    'lender': str(lender_name).strip(),
                    'num_claims': num_claims,
                    'pct_of_total': pct_total,
                    'estimated_value': est_value,
                    'avg_claim_value': est_value / num_claims if num_claims > 0 else 0
                })
        except Exception as e:
            continue

    data['lender_distribution'] = lenders

    # Extract Grand Summary totals (row 87)
    try:
        total_claims = int(df.iloc[87, 1]) if not pd.isna(df.iloc[87, 1]) else 0
        total_value = clean_currency(df.iloc[87, 3])

        data['portfolio_totals'] = {
            'total_claims': total_claims,
            'total_estimated_value': total_value
        }
    except Exception as e:
        print(f"Warning: Could not extract totals: {e}")

    # Extract Financial Costs (rows 93-98)
    try:
        data['financial_costs'] = {
            'acquisition_cost_current': clean_currency(df.iloc[93, 1]),
            'acquisition_cost_cumulative': clean_currency(df.iloc[93, 2]),
            'submission_cost_current': clean_currency(df.iloc[94, 1]),
            'submission_cost_cumulative': clean_currency(df.iloc[94, 2]),
            'processing_cost': clean_currency(df.iloc[95, 2]),
            'legal_cost': clean_currency(df.iloc[96, 2]),
            'total_action_costs': clean_currency(df.iloc[97, 2]),
            'collection_balance': clean_currency(df.iloc[98, 2])
        }

        # Calculate total costs
        data['financial_costs']['total_costs'] = (
            data['financial_costs']['acquisition_cost_cumulative'] +
            data['financial_costs']['submission_cost_cumulative'] +
            data['financial_costs']['processing_cost'] +
            data['financial_costs']['legal_cost']
        )
    except Exception as e:
        print(f"Warning: Could not extract financial costs: {e}")

    # Extract Forecasting (rows 102-104)
    try:
        data['forecasting'] = {
            'expected_new_clients': int(df.iloc[102, 1]) if not pd.isna(df.iloc[102, 1]) else 0,
            'expected_submissions': int(df.iloc[103, 1]) if not pd.isna(df.iloc[103, 1]) else 0,
            'expected_redress': clean_currency(df.iloc[104, 1])
        }
    except Exception as e:
        print(f"Warning: Could not extract forecasting: {e}")

    return data


def read_priority_deed_rules() -> Dict[str, Any]:
    """Return hardcoded Priority Deed rules (extracted from document)"""
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
    dba_rate = priority_deed['dba_rate'] / 100
    dba_proceeds = total_settlement * dba_rate

    # Get total costs
    total_costs = costs.get('total_costs', 0)

    # Calculate net proceeds (DBA proceeds - costs)
    net_proceeds = dba_proceeds - total_costs

    # Calculate profit split
    funder_pct = priority_deed['funder_percentage'] / 100
    firm_pct = priority_deed['firm_percentage'] / 100

    funder_return = net_proceeds * funder_pct
    firm_return = net_proceeds * firm_pct

    # Calculate ROI (assuming some initial investment - use total costs as proxy)
    roi = (funder_return / total_costs * 100) if total_costs > 0 else 0
    moic = (funder_return / total_costs) if total_costs > 0 else 0

    return {
        'total_settlement_value': total_settlement,
        'dba_proceeds': dba_proceeds,
        'dba_rate': priority_deed['dba_rate'],
        'total_costs': total_costs,
        'net_proceeds': net_proceeds,
        'funder_return': funder_return,
        'firm_return': firm_return,
        'funder_percentage': priority_deed['funder_percentage'],
        'firm_percentage': priority_deed['firm_percentage'],
        'roi': roi,
        'moic': moic
    }


if __name__ == "__main__":
    # Test extraction
    data = extract_monthly_report_data("uploads/Milberg_MOnthly_Report.xlsx")

    print("="*80)
    print("EXTRACTED DATA")
    print("="*80)

    print("\nPortfolio Metrics:")
    print(data['portfolio_metrics'])

    print(f"\nLenders: {len(data['lender_distribution'])}")
    print("Top 5 lenders:")
    for lender in data['lender_distribution'][:5]:
        print(f"  - {lender['lender']}: {lender['num_claims']} claims, £{lender['estimated_value']:,.2f}")

    print("\nFinancial Costs:")
    print(data['financial_costs'])

    print("\nPortfolio Totals:")
    print(data['portfolio_totals'])

    # Test financial calculations
    priority_deed = read_priority_deed_rules()
    financials = calculate_financial_projections(
        data['portfolio_totals'],
        data['financial_costs'],
        priority_deed
    )

    print("\nFinancial Projections:")
    print(f"Total Settlement Value: £{financials['total_settlement_value']:,.2f}")
    print(f"DBA Proceeds (30%): £{financials['dba_proceeds']:,.2f}")
    print(f"Total Costs: £{financials['total_costs']:,.2f}")
    print(f"Net Proceeds: £{financials['net_proceeds']:,.2f}")
    print(f"Funder Return (80%): £{financials['funder_return']:,.2f}")
    print(f"Firm Return (20%): £{financials['firm_return']:,.2f}")
    print(f"ROI: {financials['roi']:.1f}%")
    print(f"MOIC: {financials['moic']:.2f}x")
