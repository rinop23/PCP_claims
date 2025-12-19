"""
Parser for new Milberg Monthly Report format
Extracts data from the restructured Excel format
"""

import pandas as pd
import openpyxl
from typing import Dict, Any, List
from datetime import datetime


class NewExcelParser:
    """Parse the new Milberg Monthly Report format"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.workbook = openpyxl.load_workbook(file_path, data_only=True)
        self.sheet = self.workbook['Monthly Summary']

    def extract_all_data(self) -> Dict[str, Any]:
        """Extract all sections from the new format"""
        return {
            'reporting_period': self._extract_reporting_period(),
            'portfolio_overview': self._extract_portfolio_overview(),
            'claim_pipeline': self._extract_claim_pipeline(),
            'lender_distribution': self._extract_lender_distribution(),
            'financial_utilisation': self._extract_financial_utilisation(),
            'forecasting': self._extract_forecasting(),
            'risks_and_compliance': self._extract_risks_compliance()
        }

    def _get_cell_value(self, row: int, col: int):
        """Safely get cell value"""
        try:
            value = self.sheet.cell(row=row, column=col).value
            return value if value is not None else ''
        except:
            return ''

    def _extract_reporting_period(self) -> str:
        """Extract reporting period from row 3"""
        period = self._get_cell_value(3, 3)
        return str(period) if period else '[Month/Year]'

    def _extract_portfolio_overview(self) -> Dict[str, Any]:
        """Extract Portfolio Overview (rows 9-15)"""
        metrics = {}

        # Row 10: Unique Clients
        metrics['unique_clients_current'] = self._get_cell_value(10, 2)
        metrics['unique_clients_cumulative'] = self._get_cell_value(10, 3)

        # Row 11: Unique Claims
        metrics['unique_claims_current'] = self._get_cell_value(11, 2)
        metrics['unique_claims_cumulative'] = self._get_cell_value(11, 3)

        # Row 12: Claims Submitted
        metrics['claims_submitted_current'] = self._get_cell_value(12, 2)
        metrics['claims_submitted_cumulative'] = self._get_cell_value(12, 3)

        # Row 13: Claims Successful
        metrics['claims_successful_current'] = self._get_cell_value(13, 2)
        metrics['claims_successful_cumulative'] = self._get_cell_value(13, 3)

        # Row 14: Claims Rejected
        metrics['claims_rejected_current'] = self._get_cell_value(14, 2)
        metrics['claims_rejected_cumulative'] = self._get_cell_value(14, 3)

        # Row 15: Average Claim Value
        metrics['avg_claim_value_current'] = self._get_cell_value(15, 2)
        metrics['avg_claim_value_cumulative'] = self._get_cell_value(15, 3)

        return metrics

    def _extract_claim_pipeline(self) -> List[Dict[str, Any]]:
        """Extract Claim Pipeline Breakdown (rows 18-23)"""
        pipeline = []

        stages = [
            (19, 'Awaiting DSAR'),
            (20, 'Pending Submission'),
            (21, 'Under Review'),
            (22, 'Settlement Offered'),
            (23, 'Paid')
        ]

        for row, stage_name in stages:
            count = self._get_cell_value(row, 2)
            value = self._get_cell_value(row, 3)

            pipeline.append({
                'stage': stage_name,
                'count': count if count else 0,
                'estimated_value': value if value else 0
            })

        return pipeline

    def _extract_lender_distribution(self) -> List[Dict[str, Any]]:
        """Extract Lender Distribution Summary (starting row 27)"""
        lenders = []

        # Start from row 28 (after header row 27)
        row = 28
        while row < 100:  # Safety limit
            lender_name = self._get_cell_value(row, 1)

            # Stop if we hit an empty row or next section
            if not lender_name or str(lender_name).startswith('5.'):
                break

            claims_count = self._get_cell_value(row, 2)
            percentage = self._get_cell_value(row, 3)
            est_value = self._get_cell_value(row, 4)

            lenders.append({
                'lender': str(lender_name),
                'claims_count': claims_count if claims_count else 0,
                'percentage': percentage if percentage else 0,
                'estimated_value': est_value if est_value else 0
            })

            row += 1

        return lenders

    def _extract_financial_utilisation(self) -> Dict[str, Any]:
        """Extract Financial Utilisation Overview (rows 32-38)"""
        financial = {}

        # Row 33: Acquisition Cost
        financial['acquisition_cost_current'] = self._get_cell_value(33, 2)
        financial['acquisition_cost_cumulative'] = self._get_cell_value(33, 3)

        # Row 34: Submission Cost
        financial['submission_cost_current'] = self._get_cell_value(34, 2)
        financial['submission_cost_cumulative'] = self._get_cell_value(34, 3)

        # Row 35: Processing Cost
        financial['processing_cost_current'] = self._get_cell_value(35, 2)
        financial['processing_cost_cumulative'] = self._get_cell_value(35, 3)

        # Row 36: Legal Cost
        financial['legal_cost_current'] = self._get_cell_value(36, 2)
        financial['legal_cost_cumulative'] = self._get_cell_value(36, 3)

        # Row 37: Total Action Costs
        financial['total_action_costs_current'] = self._get_cell_value(37, 2)
        financial['total_action_costs_cumulative'] = self._get_cell_value(37, 3)

        # Row 38: Collection Account Balance
        financial['collection_account_balance_current'] = self._get_cell_value(38, 2)
        financial['collection_account_balance_cumulative'] = self._get_cell_value(38, 3)

        return financial

    def _extract_forecasting(self) -> Dict[str, Any]:
        """Extract Forecasting section (rows 42-44)"""
        forecast = {}

        # Row 42: Expected New Clients
        forecast['expected_new_clients'] = self._get_cell_value(42, 2)

        # Row 43: Expected Submissions
        forecast['expected_submissions'] = self._get_cell_value(43, 2)

        # Row 44: Expected Redress
        forecast['expected_redress'] = self._get_cell_value(44, 2)

        return forecast

    def _extract_risks_compliance(self) -> Dict[str, Any]:
        """Extract Risks, Issues & Compliance Notes (rows 48-50)"""
        risks = {}

        # Row 48: Infringement Events
        risks['infringement_events'] = self._get_cell_value(48, 2)

        # Row 49: Material Adverse Effects
        risks['material_adverse_effects'] = self._get_cell_value(49, 2)

        # Row 50: Claims Processor KPI Status
        risks['claims_processor_kpi'] = self._get_cell_value(50, 2)

        return risks


def get_priority_deed_waterfall() -> Dict[str, Any]:
    """
    Returns the profit distribution waterfall from the Priority Deed
    """
    return {
        'waterfall_order': [
            {
                'priority': 1,
                'description': 'Outstanding Costs Sum',
                'recipient': 'Funder',
                'percentage': None,
                'notes': 'First priority payment'
            },
            {
                'priority': 2,
                'description': 'First Tier Funder Return',
                'recipient': 'Funder',
                'percentage': None,
                'notes': 'Second priority payment'
            },
            {
                'priority': 3,
                'description': 'Distribution Costs Overrun',
                'recipient': 'Firm (Milberg)',
                'percentage': None,
                'notes': 'Third priority payment (subject to clause 10.3)'
            },
            {
                'priority': 4,
                'description': 'Net Proceeds Distribution',
                'recipient': 'Split between Funder and Firm',
                'percentage': None,
                'notes': 'After all above payments',
                'split': {
                    'funder': {
                        'percentage': 80,
                        'description': 'Funder receives 80% of Net Proceeds'
                    },
                    'firm': {
                        'percentage': 20,
                        'description': 'Firm receives 20% of Net Proceeds',
                        'notes': 'Half of Firm\'s share (10% of total) goes to Claims Processor per Services Agreement'
                    }
                }
            }
        ],
        'summary': {
            'funder_share': '80% of Net Proceeds (after costs)',
            'firm_share': '20% of Net Proceeds (after costs)',
            'claims_processor_share': '10% of Net Proceeds (50% of Firm share)',
            'distribution_frequency': 'Quarterly Distribution Dates',
            'payment_method': 'Via Collection Account'
        }
    }
