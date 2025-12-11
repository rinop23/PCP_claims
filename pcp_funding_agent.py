"""
PCP Claim Funding Management Agentic System

This system processes claim reports, validates compliance with LFA terms,
generates investor and IC reports, and provides legal strategy assistance.
"""



import json
import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# OpenAI API integration
import openai

# PDF extraction
import PyPDF2

# Set your OpenAI API key here or via environment variable OPENAI_API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")

# Set stdout encoding to UTF-8 for Windows compatibility
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


class ClaimStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SETTLED = "settled"
    REJECTED = "rejected"
    LITIGATION = "litigation"


class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"


@dataclass
class ClaimData:
    """Structured data for PCP claims"""
    claim_id: str
    claimant_name: str
    defendant: str
    claim_amount: float
    funded_amount: float
    claim_date: str
    status: str
    law_firm: str
    case_reference: str
    documentation_received: List[str]
    last_update: str


@dataclass
class LFATerms:
    """Litigation Funding Agreement terms"""
    agreement_id: str
    funding_cap: float
    success_fee_percentage: float
    minimum_return_multiple: float
    permitted_expenses: List[str]
    reporting_frequency: str
    termination_conditions: List[str]
    jurisdiction: str = "UK"
    adverse_costs_insurance_required: bool = True


@dataclass
class ComplianceCheck:
    """Compliance check result"""
    check_name: str
    status: ComplianceStatus
    details: str
    recommendation: Optional[str] = None


def calculate_dba_distribution(
    net_dba_proceeds: float,
    outstanding_costs_sum: float,
    first_tier_funder_return: float,
    distribution_costs_overrun: float = 0.0
) -> dict:
    """
    Calculate the distribution of Net DBA Proceeds according to Priorities Deed waterfall:
    1. Pay Outstanding Costs Sum to Funder
    2. Pay First Tier Funder Return to Funder
    3. Pay Distribution Costs Overrun to Firm
    4. Split remaining Net Proceeds: 80% Funder, 20% Firm (half of Firm's share to Claims Processor)
    Returns a dict with breakdown.
    """
    # Step 1: Pay Outstanding Costs Sum
    step1 = min(net_dba_proceeds, outstanding_costs_sum)
    remaining = net_dba_proceeds - step1
    # Step 2: Pay First Tier Funder Return
    step2 = min(remaining, first_tier_funder_return)
    remaining -= step2
    # Step 3: Pay Distribution Costs Overrun
    step3 = min(remaining, distribution_costs_overrun)
    remaining -= step3
    # Step 4: Split remaining Net Proceeds
    net_proceeds = max(remaining, 0)
    funder_share = step1 + step2 + (net_proceeds * 0.8)
    firm_share = step3 + (net_proceeds * 0.2)
    claims_processor_share = firm_share * 0.5
    firm_final_share = firm_share - claims_processor_share
    return {
        "funder_share": funder_share,
        "firm_share": firm_final_share,
        "claims_processor_share": claims_processor_share,
        "outstanding_costs_sum": step1,
        "first_tier_funder_return": step2,
        "distribution_costs_overrun": step3,
        "net_proceeds": net_proceeds
    }


class PCPFundingAgent:
    """Main agent for managing PCP claim funding"""
    
    def __init__(self):
        self.claims_data: Dict[str, ClaimData] = {}
        self.lfa_terms: Optional[LFATerms] = None
        self.compliance_history: List[Dict] = []
        self.knowledge_cache: Dict[str, str] = {}
        self.fca_docs_paths = [
            os.path.join("FCA redress scheme", "Redress Scheme.pdf"),
            os.path.join("DOCS", "Motor Finance Redress Funding Agreement (EXECUTED).pdf"),
            os.path.join("DOCS", "Collection Acount Charge (EXECUTED).pdf"),
            os.path.join("DOCS", "Priorities Deed (EXECUTED).pdf")
        ]

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

    def get_fca_and_docs_knowledge(self) -> str:
        """Aggregate text from all FCA and DOCS PDFs for compliance/contextual analysis."""
        # Try to get from database first (for production)
        try:
            import streamlit as st
            if hasattr(st, 'connection'):
                conn = st.connection('legal_docs_db', type='sql')
                df = conn.query('SELECT document_name, content FROM legal_documents')
                if not df.empty:
                    print(f"[Info] Loaded {len(df)} documents from database")
                    return "\n\n".join(df['content'].tolist())
        except Exception as e:
            print(f"[Info] Database not available, using local files: {e}")

        # Fallback to local files (for development)
        all_text = []
        for path in self.fca_docs_paths:
            if os.path.exists(path):
                all_text.append(self.extract_pdf_text(path))
            else:
                print(f"[Warning] FCA/DOCS file not found: {path}")
        return "\n\n".join(all_text)
    
    def call_openai_llm(self, prompt: str, model: str = "gpt-4-1106-preview", max_tokens: int = 512, temperature: float = 0.2) -> str:
        """
        Call OpenAI ChatCompletion API with a prompt and return the response text.
        Compatible with openai>=1.0.0
        """
        try:
            from openai import OpenAI
            client = OpenAI()  # Uses OPENAI_API_KEY from environment
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[OpenAI API Error] {e}")
            return "[OpenAI API Error: Unable to get response]"
        
    def load_lfa(self, lfa_data: Dict[str, Any]) -> None:
        """Load and parse Litigation Funding Agreement"""
        self.lfa_terms = LFATerms(**lfa_data)
        print(f"✓ LFA loaded: {self.lfa_terms.agreement_id}")
        
    def ingest_claim_report(self, report_data: Dict[str, Any]) -> ClaimData:
        """
        Ingest claim report from law firm
        Extracts key information and structures it
        """
        claim = ClaimData(**report_data)
        self.claims_data[claim.claim_id] = claim
        print(f"✓ Claim report ingested: {claim.claim_id} - {claim.claimant_name}")
        return claim

    def ingest_report(self, file_path: str) -> Dict[str, Any]:
        """
        Process and ingest report from law firm (Excel or Word format)
        Supports .xlsx, .xls, and .docx files (e.g., Milberg monthly report)
        Uses FCA redress knowledge for eligibility/compliance and DOCS for profit analysis.
        """
        from document_processor import DocumentProcessor
        from fca_redress_validator import FCARedressValidator

        processor = DocumentProcessor()
        extracted_data = processor.process_law_firm_report(file_path)

        # Load FCA redress knowledge for compliance/eligibility
        fca_validator = FCARedressValidator()
        fca_knowledge = fca_validator.get_fca_redress_knowledge()

        # Load DOCS knowledge (esp. Priority Deed) for profit analysis
        docs_knowledge = self.extract_pdf_text(os.path.join("DOCS", "Priorities Deed (EXECUTED).pdf"))

        # Helper for date normalization
        def normalize_date(date_str):
            from datetime import datetime
            formats = [
                "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y",
                "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d-%m-%Y %H:%M:%S"
            ]
            if not date_str:
                return ''
            for fmt in formats:
                try:
                    dt = datetime.strptime(str(date_str), fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            # Try to extract just the date part if time is present
            if isinstance(date_str, str) and " " in date_str:
                date_only = date_str.split(" ")[0]
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                    try:
                        dt = datetime.strptime(date_only, fmt)
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            return str(date_str)

        ingested_count = 0
        skipped_count = 0
        claim_eligibility = {}
        claim_profits = {}

        # Check if this is a Milberg report with multiple claims
        if extracted_data.get('report_type') == 'Milberg Monthly Report':
            claims = extracted_data.get('claims', [])
            for claim_data in claims:
                # Only ingest claims with valid data
                if claim_data.get('claim_id') and claim_data.get('claim_amount', 0) > 0:
                    try:
                        # Normalize key fields before eligibility check
                        claim_data['agreement_date'] = normalize_date(claim_data.get('agreement_date', ''))
                        claim_data['submission_date'] = normalize_date(claim_data.get('submission_date', ''))
                        try:
                            claim_data['commission_pct_of_cost'] = float(claim_data.get('commission_pct_of_cost', 0))
                        except Exception:
                            claim_data['commission_pct_of_cost'] = 0.0

                        # FCA eligibility/compliance check
                        eligibility = fca_validator.check_eligibility(claim_data)
                        claim_eligibility[claim_data['claim_id']] = eligibility

                        # Map Milberg fields to our standard format
                        standardized_claim = {
                            'claim_id': claim_data['claim_id'],
                            'claimant_name': claim_data.get('claimant_id', 'Unknown'),
                            'defendant': claim_data.get('defendant', 'Unknown'),
                            'claim_amount': claim_data.get('claim_amount', 0),
                            'funded_amount': claim_data.get('funder_share', 0),
                            'status': claim_data.get('status', 'in_progress'),
                            'law_firm': claim_data.get('law_firm', 'Milberg'),
                            'case_reference': claim_data.get('claim_id'),
                            'documentation_received': claim_data.get('documentation_received', []),
                            'claim_date': claim_data.get('agreement_date', ''),
                            'last_update': claim_data.get('last_update', '')
                        }
                        self.ingest_claim_report(standardized_claim)
                        ingested_count += 1

                        # Calculate profit for investor using Priority Deed (LLM-powered)
                        profit_prompt = (
                            f"You are a legal-financial analyst. Using the following Priority Deed (between funder and investor):\n\n"
                            f"{docs_knowledge[:4000]}\n\n"
                            f"And this claim data:\n{json.dumps(standardized_claim, indent=2)}\n\n"
                            "Calculate the expected profit for the investor from this claim, considering the waterfall and priorities. "
                            "Give a concise explanation and the profit amount in GBP.\n\nProfit analysis:"
                        )
                        profit_result = self.call_openai_llm(profit_prompt, max_tokens=256)
                        claim_profits[claim_data['claim_id']] = profit_result
                    except Exception as e:
                        print(f"Warning: Could not ingest claim {claim_data.get('claim_id')}: {str(e)}")
                        skipped_count += 1
                else:
                    skipped_count += 1

        else:
            # Handle generic Excel format or single claim
            claims = extracted_data.get('claims', [])
            if claims:
                for claim_data in claims:
                    if claim_data.get('claim_id'):
                        try:
                            self.ingest_claim_report(claim_data)
                            ingested_count += 1
                        except Exception as e:
                            print(f"Warning: Could not ingest claim: {str(e)}")
                            skipped_count += 1

        # Calculate DBA proceeds split using Priorities Deed waterfall
        # Extract required values from portfolio_summary
        ps = extracted_data.get('portfolio_summary', {})
        net_dba_proceeds = ps.get('total_dba_proceeds', 0)
        outstanding_costs_sum = ps.get('outstanding_costs_sum', 0)
        first_tier_funder_return = ps.get('first_tier_funder_return', 0)
        distribution_costs_overrun = ps.get('distribution_costs_overrun', 0)
        dba_split = calculate_dba_distribution(
            net_dba_proceeds,
            outstanding_costs_sum,
            first_tier_funder_return,
            distribution_costs_overrun
        )
        ps['funder_total_share'] = dba_split['funder_share']
        ps['milberg_total_share'] = dba_split['firm_share']
        ps['claims_processor_share'] = dba_split['claims_processor_share']
        ps['dba_distribution_details'] = dba_split

        summary = {
            'file_path': file_path,
            'report_type': extracted_data.get('report_type', 'Unknown'),
            'total_found': len(extracted_data.get('claims', [])),
            'ingested': ingested_count,
            'skipped': skipped_count,
            'portfolio_summary': extracted_data.get('portfolio_summary', {}),
            'bundle_tracker': extracted_data.get('bundle_tracker', []),
            'claim_eligibility': {cid: eligibility.__dict__ for cid, eligibility in claim_eligibility.items()},
            'claim_profits': claim_profits
        }

        file_type = file_path.lower().split('.')[-1]
        print(f"✓ {file_type.upper()} report processed: {ingested_count} claims ingested, {skipped_count} skipped")

        # Generate comprehensive analysis report for all document types
        if file_type in ['docx', 'xlsx', 'xls']:
            try:
                from comprehensive_report_generator import ComprehensiveReportGenerator
                generator = ComprehensiveReportGenerator()

                # Create output filename
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_path = os.path.join(os.path.dirname(file_path), f"{base_name}_COMPREHENSIVE_ANALYSIS.docx")

                print(f"[Info] Generating comprehensive analysis report...")
                generator.generate_full_report(summary, output_path)
                summary['comprehensive_report_path'] = output_path
                print(f"✓ Comprehensive report generated: {output_path}")

            except Exception as e:
                print(f"[Warning] Could not generate comprehensive report: {e}")
                import traceback
                traceback.print_exc()

        return summary

    def ingest_excel_report(self, file_path: str) -> Dict[str, Any]:
        """
        Process and ingest Excel report (backwards compatibility alias)
        Use ingest_report() instead - supports both Excel and Word formats.
        """
        return self.ingest_report(file_path)
    
    def check_lfa_compliance(self, claim_id: str) -> List[ComplianceCheck]:
        """
        Check if claim is compliant with LFA terms
        """
        if not self.lfa_terms:
            raise ValueError("LFA terms not loaded")
            
        claim = self.claims_data.get(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")
        
        compliance_checks = []
        
        # Check 1: Funding cap compliance
        if claim.funded_amount <= self.lfa_terms.funding_cap:
            compliance_checks.append(ComplianceCheck(
                check_name="Funding Cap",
                status=ComplianceStatus.COMPLIANT,
                details=f"Funded amount £{claim.funded_amount:,.2f} is within cap of £{self.lfa_terms.funding_cap:,.2f}"
            ))
        else:
            compliance_checks.append(ComplianceCheck(
                check_name="Funding Cap",
                status=ComplianceStatus.NON_COMPLIANT,
                details=f"Funded amount £{claim.funded_amount:,.2f} exceeds cap of £{self.lfa_terms.funding_cap:,.2f}",
                recommendation="Seek IC approval for excess funding or restructure funding arrangement"
            ))
        
        # Check 2: Jurisdiction compliance
        if self.lfa_terms.jurisdiction == "UK":
            compliance_checks.append(ComplianceCheck(
                check_name="Jurisdiction",
                status=ComplianceStatus.COMPLIANT,
                details="Claim is within permitted UK jurisdiction"
            ))
        
        # Check 3: Documentation completeness
        required_docs = ["claim_form", "lfa_signed", "insurance_policy"]
        missing_docs = [doc for doc in required_docs if doc not in claim.documentation_received]
        
        if not missing_docs:
            compliance_checks.append(ComplianceCheck(
                check_name="Documentation",
                status=ComplianceStatus.COMPLIANT,
                details="All required documentation received"
            ))
        else:
            compliance_checks.append(ComplianceCheck(
                check_name="Documentation",
                status=ComplianceStatus.REQUIRES_REVIEW,
                details=f"Missing documentation: {', '.join(missing_docs)}",
                recommendation="Request outstanding documentation from law firm"
            ))
        
        # Check 4: Adverse costs insurance
        if self.lfa_terms.adverse_costs_insurance_required:
            if "insurance_policy" in claim.documentation_received:
                compliance_checks.append(ComplianceCheck(
                    check_name="Adverse Costs Insurance",
                    status=ComplianceStatus.COMPLIANT,
                    details="Insurance policy documentation received"
                ))
            else:
                compliance_checks.append(ComplianceCheck(
                    check_name="Adverse Costs Insurance",
                    status=ComplianceStatus.NON_COMPLIANT,
                    details="Adverse costs insurance required but not documented",
                    recommendation="Obtain ATE insurance policy immediately"
                ))
        
        # Store compliance check
        self.compliance_history.append({
            "claim_id": claim_id,
            "timestamp": datetime.now().isoformat(),
            "checks": [asdict(check) for check in compliance_checks]
        })
        
        return compliance_checks
    
    def generate_investor_report(self, claim_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate investor report with portfolio overview and returns analysis
        """
        if claim_ids is None:
            claim_ids = list(self.claims_data.keys())
        
        claims = [self.claims_data[cid] for cid in claim_ids if cid in self.claims_data]
        
        total_funded = sum(c.funded_amount for c in claims)
        total_claim_value = sum(c.claim_amount for c in claims)
        
        status_breakdown = {}
        for claim in claims:
            status_breakdown[claim.status] = status_breakdown.get(claim.status, 0) + 1
        
        report = {
            "report_type": "Investor Report",
            "generated_at": datetime.now().isoformat(),
            "reporting_period": "Current",
            "portfolio_summary": {
                "total_claims": len(claims),
                "total_funded": total_funded,
                "total_claim_value": total_claim_value,
                "potential_return_multiple": round(total_claim_value / total_funded, 2) if total_funded > 0 else 0,
                "status_breakdown": status_breakdown
            },
            "claims_detail": [
                {
                    "claim_id": c.claim_id,
                    "claimant": c.claimant_name,
                    "defendant": c.defendant,
                    "funded_amount": c.funded_amount,
                    "claim_amount": c.claim_amount,
                    "status": c.status,
                    "law_firm": c.law_firm,
                    "last_update": c.last_update
                }
                for c in claims
            ],
            "risk_metrics": {
                "average_claim_size": round(total_claim_value / len(claims), 2) if claims else 0,
                "largest_exposure": max((c.funded_amount for c in claims), default=0),
                "concentration_risk": "Low" if len(claims) > 10 else "Medium" if len(claims) > 5 else "High"
            }
        }
        
        if self.lfa_terms:
            report["lfa_compliance"] = {
                "funding_cap": self.lfa_terms.funding_cap,
                "current_utilization": total_funded,
                "utilization_percentage": round((total_funded / self.lfa_terms.funding_cap) * 100, 2),
                "success_fee_rate": f"{self.lfa_terms.success_fee_percentage}%"
            }
        
        return report
    
    def generate_ic_report(self, claim_id: str) -> Dict[str, Any]:
        """
        Generate Investment Committee report for specific claim
        """
        claim = self.claims_data.get(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")
        
        compliance_checks = self.check_lfa_compliance(claim_id)
        
        # Calculate risk score (simplified)
        risk_factors = []
        risk_score = 0
        
        if claim.funded_amount > 50000:
            risk_factors.append("High funding amount")
            risk_score += 2
        
        non_compliant_checks = [c for c in compliance_checks if c.status == ComplianceStatus.NON_COMPLIANT]
        if non_compliant_checks:
            risk_factors.append(f"{len(non_compliant_checks)} compliance issues")
            risk_score += len(non_compliant_checks) * 3
        
        if claim.status == ClaimStatus.LITIGATION.value:
            risk_factors.append("Case in litigation")
            risk_score += 2
        
        risk_rating = "High" if risk_score >= 5 else "Medium" if risk_score >= 2 else "Low"
        
        report = {
            "report_type": "Investment Committee Report",
            "generated_at": datetime.now().isoformat(),
            "claim_details": {
                "claim_id": claim.claim_id,
                "claimant_name": claim.claimant_name,
                "defendant": claim.defendant,
                "case_reference": claim.case_reference,
                "law_firm": claim.law_firm,
                "status": claim.status
            },
            "financial_analysis": {
                "funded_amount": claim.funded_amount,
                "claim_amount": claim.claim_amount,
                "potential_return": claim.claim_amount - claim.funded_amount,
                "return_multiple": round(claim.claim_amount / claim.funded_amount, 2) if claim.funded_amount > 0 else 0,
                "meets_minimum_return": self.lfa_terms and (claim.claim_amount / claim.funded_amount) >= self.lfa_terms.minimum_return_multiple
            },
            "compliance_status": {
                "overall_status": "Compliant" if all(c.status == ComplianceStatus.COMPLIANT for c in compliance_checks) else "Non-Compliant",
                "checks_performed": len(compliance_checks),
                "issues_identified": len([c for c in compliance_checks if c.status != ComplianceStatus.COMPLIANT]),
                "detailed_checks": [
                    {
                        "check": c.check_name,
                        "status": c.status.value,
                        "details": c.details,
                        "recommendation": c.recommendation
                    }
                    for c in compliance_checks
                ]
            },
            "risk_assessment": {
                "risk_rating": risk_rating,
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "mitigation_required": risk_score >= 5
            },
            "recommendation": self._generate_ic_recommendation(claim, compliance_checks, risk_rating)
        }
        
        return report
    
    def _generate_ic_recommendation(self, claim: ClaimData, compliance_checks: List[ComplianceCheck], 
                                   risk_rating: str) -> str:
        """Generate IC recommendation based on analysis"""
        if any(c.status == ComplianceStatus.NON_COMPLIANT for c in compliance_checks):
            return "HOLD - Address compliance issues before proceeding"
        
        if risk_rating == "High":
            return "REVIEW - High risk claim requires additional due diligence"
        
        return_multiple = claim.claim_amount / claim.funded_amount if claim.funded_amount > 0 else 0
        
        if self.lfa_terms and return_multiple >= self.lfa_terms.minimum_return_multiple:
            return "APPROVE - Claim meets investment criteria and compliance requirements"
        else:
            return "REVIEW - Return multiple below minimum threshold"
    
    def get_legal_strategy_insights(self, claim_id: str) -> Dict[str, Any]:
        """
        Provide legal strategy insights for UK PCP claims (optionally using OpenAI LLM)
        """
        claim = self.claims_data.get(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        # Example: Use OpenAI to generate legal strategy (uncomment to enable)
        # prompt = f"""
        # You are a legal strategy expert. Given the following claim data, provide a concise legal strategy for a UK PCP mis-selling claim, including key legal considerations, recommended actions, and compliance reminders.\n\nClaim Data: {json.dumps(asdict(claim), indent=2)}\n\nStrategy:"
        # llm_response = self.call_openai_llm(prompt)

        insights = {
            "claim_id": claim_id,
            "jurisdiction": "England & Wales",
            "strategic_considerations": [
                {
                    "area": "PCP Mis-selling Claims",
                    "key_points": [
                        "Commission disclosure requirements under FCA rules",
                        "Plevin v Paragon decision establishes duty to disclose commission",
                        "Time limits: 6 years from agreement or 3 years from knowledge",
                        "Consider Part 36 offers strategically"
                    ]
                },
                {
                    "area": "Litigation Strategy",
                    "key_points": [
                        "Pre-action protocol compliance essential",
                        "Consider Alternative Dispute Resolution (ADR) before court",
                        "Financial Ombudsman Service may have jurisdiction for claims under £375,000",
                        "County Court for smaller claims, High Court for larger amounts"
                    ]
                },
                {
                    "area": "Cost Management",
                    "key_points": [
                        "Ensure ATE insurance is in place for adverse costs protection",
                        "Monitor disbursements against LFA budget",
                        "Consider Qualified One-Way Cost Shifting (QOCS) if applicable",
                        "Track barrister and expert witness fees"
                    ]
                }
            ],
            "current_status_actions": self._get_status_specific_actions(claim.status),
            "compliance_reminders": [
                "Ensure regular updates to funders as per LFA terms",
                "Maintain detailed records of all communications",
                "Document decision-making process for audit trail",
                "Review LFA termination conditions regularly"
            ]
            # "llm_strategy": llm_response  # Uncomment to include LLM-generated strategy
        }

        return insights
    
    def _get_status_specific_actions(self, status: str) -> List[str]:
        """Get actions specific to claim status"""
        actions_map = {
            ClaimStatus.PENDING.value: [
                "Complete initial due diligence",
                "Verify insurance coverage",
                "Obtain signed LFA",
                "Request detailed case assessment from solicitors"
            ],
            ClaimStatus.IN_PROGRESS.value: [
                "Monitor case progression milestones",
                "Review monthly progress reports",
                "Ensure pre-action protocol compliance",
                "Track costs against budget"
            ],
            ClaimStatus.LITIGATION.value: [
                "Monitor court deadlines and listing",
                "Review counsel opinions regularly",
                "Assess settlement opportunities",
                "Consider Part 36 offer strategy"
            ],
            ClaimStatus.SETTLED.value: [
                "Calculate final returns and success fees",
                "Prepare final investor report",
                "Archive case documentation",
                "Process fund distribution"
            ]
        }
        return actions_map.get(status, ["Review case status with law firm"])
    
    def export_report(self, report: Dict[str, Any], output_path: str) -> None:
        """Export report to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"✓ Report exported to {output_path}")


def main():
    """Example usage of the PCP Funding Agent"""
    agent = PCPFundingAgent()
    
    # Load LFA terms
    lfa_data = {
        "agreement_id": "LFA-2024-001",
        "funding_cap": 500000.0,
        "success_fee_percentage": 25.0,
        "minimum_return_multiple": 2.0,
        "permitted_expenses": ["legal_fees", "court_fees", "expert_witnesses", "insurance"],
        "reporting_frequency": "monthly",
        "termination_conditions": ["breach_of_terms", "insolvency", "material_misrepresentation"],
        "jurisdiction": "UK",
        "adverse_costs_insurance_required": True
    }
    agent.load_lfa(lfa_data)
    
    # Ingest claim report
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
        "documentation_received": ["claim_form", "lfa_signed", "insurance_policy", "initial_assessment"],
        "last_update": "2024-12-01"
    }
    agent.ingest_claim_report(claim_report)
    
    # Check compliance
    print("\n" + "="*60)
    print("COMPLIANCE CHECK")
    print("="*60)
    compliance = agent.check_lfa_compliance("PCP-2024-1234")
    for check in compliance:
        print(f"\n{check.check_name}: {check.status.value}")
        print(f"  {check.details}")
        if check.recommendation:
            print(f"  → {check.recommendation}")
    
    # Generate IC Report
    print("\n" + "="*60)
    print("INVESTMENT COMMITTEE REPORT")
    print("="*60)
    ic_report = agent.generate_ic_report("PCP-2024-1234")
    print(json.dumps(ic_report, indent=2, default=str))
    
    # Generate Investor Report
    print("\n" + "="*60)
    print("INVESTOR REPORT")
    print("="*60)
    investor_report = agent.generate_investor_report()
    print(json.dumps(investor_report, indent=2, default=str))
    
    # Get Legal Strategy
    print("\n" + "="*60)
    print("LEGAL STRATEGY INSIGHTS")
    print("="*60)
    strategy = agent.get_legal_strategy_insights("PCP-2024-1234")
    print(json.dumps(strategy, indent=2, default=str))


if __name__ == "__main__":
    main()
