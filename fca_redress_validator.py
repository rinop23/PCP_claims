"""
FCA Motor Finance Redress Scheme Validator

Validates claims against FCA redress scheme rules for motor finance
discretionary commission arrangements (DCA).

Based on FCA guidance for motor finance redress schemes.
"""


import os
import sys
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json

# PDF extraction
import PyPDF2


class EligibilityStatus(Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    REQUIRES_REVIEW = "requires_review"


class RedressCalculationMethod(Enum):
    BASIC_RATE = "basic_rate"
    DIFFERENCE_IN_COST = "difference_in_cost"
    COMPOSITE_RATE = "composite_rate"
    FULL_REDRESS = "full_redress"


@dataclass
class FCASchemeRules:
    """FCA Redress Scheme Rules and Parameters"""

    # Eligibility criteria
    agreement_start_date_min: str = "2007-04-06"  # Post-CCA 1974 amendments
    agreement_start_date_max: str = "2021-01-28"  # FCA review announcement date

    # Commission thresholds
    commission_disclosure_threshold: float = 50.0  # % of finance charge
    plevin_threshold: float = 50.0  # % commission that triggers automatic redress

    # Time limits
    limitation_period_years: int = 6
    knowledge_period_years: int = 3  # From date of knowledge

    # Calculation parameters
    statutory_interest_rate: float = 8.0  # % per annum
    basic_rate_8_percent: bool = True

    # Product types covered
    eligible_product_types: List[str] = None

    # Maximum redress caps (if applicable)
    max_redress_amount: Optional[float] = None  # None = no cap

    def __post_init__(self):
        if self.eligible_product_types is None:
            self.eligible_product_types = [
                "PCP",  # Personal Contract Purchase
                "HP",   # Hire Purchase
                "CS",   # Conditional Sale
                "PCH"   # Personal Contract Hire
            ]


@dataclass
class ClaimEligibility:
    """Result of FCA eligibility check"""
    status: EligibilityStatus
    eligible: bool
    reasons: List[str]
    warnings: List[str]
    date_checks_passed: bool
    product_type_eligible: bool
    commission_threshold_met: bool
    limitation_period_valid: bool
    recommendation: str


@dataclass
class RedressCalculation:
    """FCA Redress Calculation Result"""
    calculation_method: RedressCalculationMethod
    base_redress_amount: float
    statutory_interest: float
    total_redress: float
    breakdown: Dict[str, float]
    distress_inconvenience: float
    consequential_losses: float
    calculation_notes: List[str]


class FCARedressValidator:
    """
    Validates claims against FCA motor finance redress scheme
    """

    def __init__(self, scheme_rules: Optional[FCASchemeRules] = None):
        self.rules = scheme_rules or FCASchemeRules()
        self.fca_pdf_paths = [
            os.path.join("FCA redress scheme", "Redress Scheme.pdf")
        ]
        self.knowledge_cache: Dict[str, str] = {}

    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract all text from a PDF file using PyPDF2."""
        if pdf_path in self.knowledge_cache:
            return self.knowledge_cache[pdf_path]
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                self.knowledge_cache[pdf_path] = text
                return text
        except Exception as e:
            print(f"[PDF Extraction Error] {pdf_path}: {e}")
            return ""

    def get_fca_redress_knowledge(self) -> str:
        """Aggregate text from all FCA redress PDFs for compliance/contextual analysis."""
        all_text = []
        for path in self.fca_pdf_paths:
            if os.path.exists(path):
                all_text.append(self.extract_pdf_text(path))
            else:
                print(f"[Warning] FCA file not found: {path}")
        return "\n\n".join(all_text)

    def check_eligibility(self, claim_data: Dict[str, Any]) -> ClaimEligibility:
        """
        Comprehensive eligibility check against FCA scheme rules
        """
        reasons = []
        warnings = []

        # Extract claim data
        agreement_date = claim_data.get('agreement_date', '')
        product_type = claim_data.get('product_type', '').upper()
        commission_pct = claim_data.get('commission_pct_of_cost', 0)
        loan_amount = claim_data.get('loan_amount', 0)
        commission_amount = claim_data.get('commission_amount', 0)
        disclosure_adequate = claim_data.get('disclosure_adequate', 'N')

        # Calculate commission percentage if not provided
        if commission_pct == 0 and commission_amount > 0:
            cost_of_credit = claim_data.get('total_cost_of_credit', 0)
            if cost_of_credit > 0:
                commission_pct = (commission_amount / cost_of_credit) * 100

        # Check 1: Date eligibility
        date_checks_passed = self._check_date_eligibility(
            agreement_date, reasons, warnings
        )

        # Check 2: Product type eligibility
        product_type_eligible = self._check_product_type(
            product_type, reasons, warnings
        )

        # Check 3: Commission threshold (Plevin test)
        commission_threshold_met = self._check_commission_threshold(
            commission_pct, disclosure_adequate, reasons, warnings
        )

        # Check 4: Limitation period
        limitation_period_valid = self._check_limitation_period(
            agreement_date, claim_data.get('submission_date', ''),
            reasons, warnings
        )

        # Check 5: Minimum claim value
        if loan_amount > 0 and loan_amount < 1000:
            warnings.append(f"Low loan amount (£{loan_amount:,.2f}) - verify claim is worthwhile")

        # Check 6: Commission disclosure
        if disclosure_adequate == 'Y':
            warnings.append("Claimant indicated disclosure was adequate - review evidence")

        # Determine overall eligibility
        critical_checks = [
            date_checks_passed,
            product_type_eligible,
            limitation_period_valid
        ]

        if all(critical_checks) and commission_threshold_met:
            status = EligibilityStatus.ELIGIBLE
            eligible = True
            recommendation = "APPROVE - Claim meets FCA eligibility criteria"
        elif all(critical_checks) and not commission_threshold_met:
            status = EligibilityStatus.REQUIRES_REVIEW
            eligible = False
            recommendation = "REVIEW - Commission below Plevin threshold but may have other grounds"
            warnings.append("Commission below 50% threshold - review for other unfairness grounds")
        else:
            status = EligibilityStatus.INELIGIBLE
            eligible = False
            recommendation = "REJECT - Claim does not meet FCA eligibility criteria"

        return ClaimEligibility(
            status=status,
            eligible=eligible,
            reasons=reasons,
            warnings=warnings,
            date_checks_passed=date_checks_passed,
            product_type_eligible=product_type_eligible,
            commission_threshold_met=commission_threshold_met,
            limitation_period_valid=limitation_period_valid,
            recommendation=recommendation
        )

    def _check_date_eligibility(self, agreement_date: str, reasons: List[str], warnings: List[str]) -> bool:
        """Check if agreement date falls within eligible period"""
        if not agreement_date:
            reasons.append("Agreement date not provided")
            return False

        try:
            # Parse date
            if isinstance(agreement_date, str):
                # Try multiple date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        agr_date = datetime.strptime(agreement_date, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    reasons.append(f"Invalid agreement date format: {agreement_date}")
                    return False
            else:
                agr_date = agreement_date

            min_date = datetime.strptime(self.rules.agreement_start_date_min, '%Y-%m-%d')
            max_date = datetime.strptime(self.rules.agreement_start_date_max, '%Y-%m-%d')

            if agr_date < min_date:
                reasons.append(f"Agreement date {agreement_date} is before eligible period (min: {self.rules.agreement_start_date_min})")
                return False

            if agr_date > max_date:
                reasons.append(f"Agreement date {agreement_date} is after eligible period (max: {self.rules.agreement_start_date_max})")
                return False

            # Check if agreement is very recent (edge case)
            if (datetime.now() - agr_date).days < 365:
                warnings.append("Recent agreement - verify all documentation")

            reasons.append(f"✓ Agreement date {agreement_date} within eligible period")
            return True

        except Exception as e:
            reasons.append(f"Error checking agreement date: {str(e)}")
            return False

    def _check_product_type(self, product_type: str, reasons: List[str], warnings: List[str]) -> bool:
        """Check if product type is eligible"""
        if not product_type:
            warnings.append("Product type not specified - assuming eligible")
            return True

        # Normalize product type
        product_type = product_type.upper().strip()

        # Check common abbreviations and variations
        product_mappings = {
            'PCP': 'PCP',
            'PERSONAL CONTRACT PURCHASE': 'PCP',
            'HP': 'HP',
            'HIRE PURCHASE': 'HP',
            'CS': 'CS',
            'CONDITIONAL SALE': 'CS',
            'PCH': 'PCH',
            'PERSONAL CONTRACT HIRE': 'PCH'
        }

        normalized_type = product_mappings.get(product_type, product_type)

        if normalized_type in self.rules.eligible_product_types:
            reasons.append(f"✓ Product type '{product_type}' is eligible under FCA scheme")
            return True
        else:
            reasons.append(f"Product type '{product_type}' not covered by FCA scheme")
            warnings.append(f"Eligible types: {', '.join(self.rules.eligible_product_types)}")
            return False

    def _check_commission_threshold(self, commission_pct: float, disclosure_adequate: str,
                                   reasons: List[str], warnings: List[str]) -> bool:
        """Check if commission meets Plevin threshold"""
        if commission_pct == 0:
            warnings.append("Commission percentage not available - cannot verify Plevin threshold")
            return False

        if commission_pct >= self.rules.plevin_threshold:
            reasons.append(f"✓ Commission {commission_pct:.1f}% exceeds Plevin threshold ({self.rules.plevin_threshold}%)")
            if disclosure_adequate != 'Y':
                reasons.append("✓ Commission not adequately disclosed")
            return True
        else:
            reasons.append(f"Commission {commission_pct:.1f}% below Plevin threshold ({self.rules.plevin_threshold}%)")
            warnings.append("May still be eligible under other unfairness grounds")
            return False

    def _check_limitation_period(self, agreement_date: str, submission_date: str,
                                reasons: List[str], warnings: List[str]) -> bool:
        """Check if claim is within limitation period"""
        if not agreement_date:
            warnings.append("Cannot verify limitation period without agreement date")
            return True  # Don't reject on this alone

        try:
            # Parse dates
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                try:
                    if isinstance(agreement_date, str):
                        agr_date = datetime.strptime(agreement_date, fmt)
                    else:
                        agr_date = agreement_date
                    break
                except ValueError:
                    continue

            if submission_date:
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        sub_date = datetime.strptime(submission_date, fmt)
                        break
                    except ValueError:
                        continue
            else:
                sub_date = datetime.now()

            # Calculate years between agreement and submission
            years_elapsed = (sub_date - agr_date).days / 365.25

            if years_elapsed > self.rules.limitation_period_years:
                # Check if within 3 years of knowledge (benefit of doubt)
                warnings.append(f"Agreement over {self.rules.limitation_period_years} years old - verify date of knowledge")
                reasons.append(f"⚠ Limitation: {years_elapsed:.1f} years since agreement (standard: {self.rules.limitation_period_years} years)")
                # Don't automatically reject - FCA scheme may have different rules
                return True
            else:
                reasons.append(f"✓ Within limitation period ({years_elapsed:.1f} years)")
                return True

        except Exception as e:
            warnings.append(f"Could not verify limitation period: {str(e)}")
            return True  # Don't reject on this alone

    def calculate_redress(self, claim_data: Dict[str, Any]) -> RedressCalculation:
        """
        Calculate FCA redress amount based on scheme methodology
        """
        loan_amount = claim_data.get('loan_amount', 0)
        commission_amount = claim_data.get('commission_amount', 0)
        total_cost_of_credit = claim_data.get('total_cost_of_credit', 0)
        agreement_date = claim_data.get('agreement_date', '')

        calculation_notes = []
        breakdown = {}

        # Method 1: Basic redress - return half the commission
        # (Common approach: customer and firm share equally)
        basic_redress = commission_amount * 0.5
        breakdown['commission_refund'] = basic_redress
        calculation_notes.append(f"Basic redress: 50% of commission (£{commission_amount:,.2f})")

        # Calculate statutory interest (8% per annum)
        if agreement_date:
            try:
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        agr_date = datetime.strptime(agreement_date, fmt)
                        break
                    except ValueError:
                        continue

                years_elapsed = (datetime.now() - agr_date).days / 365.25
                statutory_interest = basic_redress * (self.rules.statutory_interest_rate / 100) * years_elapsed
                breakdown['statutory_interest'] = statutory_interest
                calculation_notes.append(f"Statutory interest: {self.rules.statutory_interest_rate}% p.a. over {years_elapsed:.1f} years")
            except:
                statutory_interest = 0
                calculation_notes.append("Could not calculate statutory interest")
        else:
            statutory_interest = 0

        # Distress and inconvenience (typical: £50-£300)
        distress_inconvenience = 150.0  # Standard amount
        breakdown['distress_inconvenience'] = distress_inconvenience
        calculation_notes.append("Distress & inconvenience: £150 (standard award)")

        # Consequential losses (if applicable)
        consequential_losses = claim_data.get('consequential_losses', 0)
        if consequential_losses > 0:
            breakdown['consequential_losses'] = consequential_losses
            calculation_notes.append(f"Consequential losses: £{consequential_losses:,.2f}")

        # Total redress
        total_redress = basic_redress + statutory_interest + distress_inconvenience + consequential_losses

        # Check against maximum cap (if applicable)
        if self.rules.max_redress_amount and total_redress > self.rules.max_redress_amount:
            calculation_notes.append(f"⚠ Total capped at scheme maximum: £{self.rules.max_redress_amount:,.2f}")
            total_redress = self.rules.max_redress_amount

        calculation_notes.append(f"Total FCA redress: £{total_redress:,.2f}")

        return RedressCalculation(
            calculation_method=RedressCalculationMethod.BASIC_RATE,
            base_redress_amount=basic_redress,
            statutory_interest=statutory_interest,
            total_redress=total_redress,
            breakdown=breakdown,
            distress_inconvenience=distress_inconvenience,
            consequential_losses=consequential_losses,
            calculation_notes=calculation_notes
        )

    def validate_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete validation: eligibility + redress calculation
        """
        # Check eligibility
        eligibility = self.check_eligibility(claim_data)

        # Calculate redress (even if not eligible, for comparison)
        redress = self.calculate_redress(claim_data)

        # Compare with claimed amount
        claimed_amount = claim_data.get('claim_amount', 0) or claim_data.get('redress_calculated', 0)

        variance = claimed_amount - redress.total_redress if claimed_amount > 0 else 0
        variance_pct = (variance / redress.total_redress * 100) if redress.total_redress > 0 else 0

        validation_result = {
            'claim_id': claim_data.get('claim_id', 'Unknown'),
            'eligibility': {
                'status': eligibility.status.value,
                'eligible': eligibility.eligible,
                'reasons': eligibility.reasons,
                'warnings': eligibility.warnings,
                'recommendation': eligibility.recommendation
            },
            'fca_redress_calculation': {
                'method': redress.calculation_method.value,
                'base_redress': redress.base_redress_amount,
                'statutory_interest': redress.statutory_interest,
                'distress_inconvenience': redress.distress_inconvenience,
                'consequential_losses': redress.consequential_losses,
                'total_fca_redress': redress.total_redress,
                'breakdown': redress.breakdown,
                'notes': redress.calculation_notes
            },
            'amount_comparison': {
                'claimed_amount': claimed_amount,
                'fca_calculated_amount': redress.total_redress,
                'variance': variance,
                'variance_percentage': variance_pct,
                'assessment': self._assess_claim_amount(variance_pct)
            }
        }

        return validation_result

    def _assess_claim_amount(self, variance_pct: float) -> str:
        """Assess if claimed amount is reasonable"""
        if abs(variance_pct) < 10:
            return "✓ Claimed amount aligns with FCA calculation"
        elif variance_pct > 10:
            return f"⚠ Claimed amount {variance_pct:.1f}% higher than FCA calculation - review justification"
        else:
            return f"⚠ Claimed amount {abs(variance_pct):.1f}% lower than FCA calculation - may be under-claimed"


def demo_fca_validation():
    """Demonstrate FCA validation functionality"""

    print("=" * 70)
    print("FCA REDRESS SCHEME VALIDATOR - DEMO")
    print("=" * 70)
    print()

    # Initialize validator
    validator = FCARedressValidator()

    # Sample claim data
    sample_claims = [
        {
            'claim_id': 'TEST-001',
            'agreement_date': '2019-06-15',
            'product_type': 'PCP',
            'loan_amount': 25000.0,
            'total_cost_of_credit': 5000.0,
            'commission_amount': 3000.0,
            'commission_pct_of_cost': 60.0,
            'disclosure_adequate': 'N',
            'submission_date': '2024-11-01',
            'claim_amount': 4500.0
        },
        {
            'claim_id': 'TEST-002',
            'agreement_date': '2015-03-20',
            'product_type': 'HP',
            'loan_amount': 15000.0,
            'total_cost_of_credit': 3000.0,
            'commission_amount': 1200.0,
            'commission_pct_of_cost': 40.0,
            'disclosure_adequate': 'N',
            'submission_date': '2024-11-01',
            'claim_amount': 2000.0
        }
    ]

    for claim in sample_claims:
        print(f"Validating Claim: {claim['claim_id']}")
        print("-" * 70)

        result = validator.validate_claim(claim)

        print(json.dumps(result, indent=2))
        print()
        print("=" * 70)
        print()


if __name__ == "__main__":
    demo_fca_validation()
