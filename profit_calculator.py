"""
Profit Calculator Module
Calculates DBA proceeds, profit splits, and MOIC based on Priority Deed terms
"""

from typing import Dict, Any, List


class ProfitCalculator:
    """Calculate profits and returns based on Priority Deed waterfall"""

    # Constants from Priority Deed
    DBA_PERCENTAGE = 0.30  # DBA Proceeds are 30% of total claim amount
    FUNDER_SHARE = 0.80    # Funder gets 80% of Net Proceeds
    MILBERG_SHARE = 0.20   # Milberg gets 20% of Net Proceeds

    def __init__(self):
        pass

    def calculate_dba_proceeds(self, total_claim_amount: float) -> float:
        """
        Calculate DBA Proceeds
        DBA Proceeds = 30% of total successful claim amount
        """
        return total_claim_amount * self.DBA_PERCENTAGE

    def calculate_profit_split(self, dba_proceeds: float) -> Dict[str, float]:
        """
        Calculate profit split per Priority Deed

        Returns:
            Dict with funder_share and milberg_share
        """
        return {
            'dba_proceeds': dba_proceeds,
            'funder_share': dba_proceeds * self.FUNDER_SHARE,
            'milberg_share': dba_proceeds * self.MILBERG_SHARE,
            'funder_percentage': self.FUNDER_SHARE * 100,
            'milberg_percentage': self.MILBERG_SHARE * 100
        }

    def calculate_moic(self, total_returns: float, total_funded: float) -> float:
        """
        Calculate MOIC (Multiple on Invested Capital)
        MOIC = Total Returns / Total Funded

        Args:
            total_returns: Total amount returned (e.g., funder's share of DBA proceeds)
            total_funded: Total amount invested/funded

        Returns:
            MOIC as a multiplier (e.g., 2.5x means 2.5 times the investment)
        """
        if total_funded == 0:
            return 0.0

        return total_returns / total_funded

    def calculate_portfolio_metrics(self, claims_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate comprehensive portfolio metrics

        Args:
            claims_data: List of claim dictionaries with 'claim_amount' and 'funded_amount'

        Returns:
            Dict with all calculated metrics
        """
        # Calculate totals
        total_claims_value = sum(claim.get('claim_amount', 0) for claim in claims_data)
        total_funded = sum(claim.get('funded_amount', 0) for claim in claims_data)

        # Calculate DBA Proceeds (30% of successful claims)
        dba_proceeds = self.calculate_dba_proceeds(total_claims_value)

        # Calculate profit split
        profit_split = self.calculate_profit_split(dba_proceeds)

        # Calculate MOIC for funder
        funder_moic = self.calculate_moic(profit_split['funder_share'], total_funded)

        return {
            'total_claims_value': total_claims_value,
            'total_funded': total_funded,
            'dba_proceeds': dba_proceeds,
            'dba_percentage': self.DBA_PERCENTAGE * 100,
            'funder_collection': profit_split['funder_share'],
            'funder_percentage': profit_split['funder_percentage'],
            'milberg_collection': profit_split['milberg_share'],
            'milberg_percentage': profit_split['milberg_percentage'],
            'funder_moic': funder_moic,
            'profit_margin': ((profit_split['funder_share'] - total_funded) / total_funded * 100) if total_funded > 0 else 0
        }

    def format_metrics_for_display(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """
        Format metrics for dashboard display

        Returns:
            Dict with formatted strings for display
        """
        return {
            'Total Claims Value': f"£{metrics['total_claims_value']:,.2f}",
            'Total Funded': f"£{metrics['total_funded']:,.2f}",
            'DBA Proceeds (30%)': f"£{metrics['dba_proceeds']:,.2f}",
            'Funder Collection (80%)': f"£{metrics['funder_collection']:,.2f}",
            'Milberg Collection (20%)': f"£{metrics['milberg_collection']:,.2f}",
            'Funder MOIC': f"{metrics['funder_moic']:.2f}x",
            'Profit Margin': f"{metrics['profit_margin']:.1f}%"
        }


def get_priority_deed_summary() -> Dict[str, Any]:
    """
    Returns a summary of Priority Deed terms for display
    """
    return {
        'dba_calculation': {
            'description': 'DBA Proceeds Calculation',
            'formula': 'Total Successful Claims × 30%',
            'example': 'If claims total £1,000,000, DBA Proceeds = £300,000'
        },
        'profit_split': {
            'description': 'Profit Distribution (from DBA Proceeds)',
            'funder': {
                'percentage': 80,
                'description': 'Funder receives 80% of DBA Proceeds'
            },
            'milberg': {
                'percentage': 20,
                'description': 'Milberg receives 20% of DBA Proceeds'
            }
        },
        'moic_explanation': {
            'description': 'Multiple on Invested Capital',
            'formula': 'Funder Collection ÷ Total Funded',
            'interpretation': {
                '< 1.0x': 'Loss - Not recovering full investment',
                '1.0x': 'Break-even - Recovering exactly the investment',
                '> 1.0x': 'Profit - Making returns on investment',
                '2.0x': 'Example: Doubling the investment'
            }
        },
        'payment_notes': [
            'DBA Proceeds = 30% of successful claim value',
            'Remaining 70% goes to claimants',
            'Funder gets 80% of DBA Proceeds',
            'Milberg gets 20% of DBA Proceeds',
            'Payments made quarterly via Collection Account'
        ]
    }
