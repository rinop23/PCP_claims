import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pcp_funding_agent import PCPFundingAgent
from docx import Document
import os
from datetime import datetime
import hashlib
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import tempfile
from docx.shared import Inches

# Page configuration
st.set_page_config(
    page_title="PCP Claims Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== AUTHENTICATION ====================
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# User credentials (username: hashed_password)
USERS = {
    "admin": hash_password("Admin123!"),
    "walter": hash_password("Walter123!"),
    "dirk": hash_password("Dirk123!"),
    "eda": hash_password("Eda123!")
}

def check_authentication():
    """Handle user authentication"""

    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None

    # If already authenticated, return True
    if st.session_state.authenticated:
        return True

    # Show login form
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🔐 PCP Claims Analysis</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Please log in to continue</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if username in USERS and USERS[username] == hash_password(password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success(f"Welcome, {username.capitalize()}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("ℹ️ Default Credentials"):
            st.markdown("""
            **For initial setup, use these credentials:**
            - Admin: `admin` / `Admin123!`
            - Walter: `walter` / `Walter123!`
            - Dirk: `dirk` / `Dirk123!`
            - Eda: `eda` / `Eda123!`

            *Please change passwords after first login in production.*
            """)

    return False

# Check authentication before showing app
if not check_authentication():
    st.stop()

# Add logout button in sidebar
with st.sidebar:
    st.markdown(f"**Logged in as:** {st.session_state.username.capitalize()}")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()
    st.markdown("---")

# ==================== END AUTHENTICATION ===================="

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 5px 5px 0px 0px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def create_summary_metrics(summary, agent):
    """Create summary metrics display"""
    col1, col2, col3, col4 = st.columns(4)

    ps = summary.get('portfolio_summary', {})

    with col1:
        st.metric(
            "Total Claims",
            f"{summary.get('total_found', 0)}",
            f"{summary.get('ingested', 0)} Processed"
        )

    with col2:
        total_funding = ps.get('total_funding_provided', 0)
        st.metric(
            "Total Funding",
            f"£{total_funding:,.0f}",
            f"£{ps.get('outstanding_funding', 0):,.0f} Outstanding"
        )

    with col3:
        dba_proceeds = ps.get('total_dba_proceeds', 0)
        st.metric(
            "DBA Proceeds",
            f"£{dba_proceeds:,.0f}",
            f"£{ps.get('funder_total_share', 0):,.0f} Funder Share"
        )

    with col4:
        # Calculate eligibility rate
        eligibility = summary.get('claim_eligibility', {})
        eligible_count = sum(1 for v in eligibility.values() if v.get('eligible'))
        total_checked = len(eligibility)
        rate = (eligible_count / total_checked * 100) if total_checked > 0 else 0
        st.metric(
            "FCA Eligibility Rate",
            f"{rate:.0f}%",
            f"{eligible_count}/{total_checked} Eligible"
        )


def create_eligibility_charts(summary):
    """Create eligibility analysis charts"""
    eligibility = summary.get('claim_eligibility', {})

    if not eligibility:
        st.info("No eligibility data available")
        return

    # Prepare data
    statuses = []
    recommendations = []

    for claim_id, result in eligibility.items():
        status = "Eligible" if result.get('eligible') else "Not Eligible"
        statuses.append(status)
        recommendations.append(result.get('recommendation', '').split('-')[0].strip())

    col1, col2 = st.columns(2)

    with col1:
        # Eligibility pie chart
        status_counts = pd.Series(statuses).value_counts()
        fig_pie = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="FCA Eligibility Status Distribution",
            color_discrete_sequence=['#28a745', '#dc3545']
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Recommendation bar chart
        rec_counts = pd.Series(recommendations).value_counts()
        fig_bar = px.bar(
            x=rec_counts.index,
            y=rec_counts.values,
            title="Recommendation Distribution",
            labels={'x': 'Recommendation', 'y': 'Count'},
            color=rec_counts.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_bar, use_container_width=True)


def create_bundle_analysis(summary):
    """Create bundle tracker analysis"""
    bundles = summary.get('bundle_tracker', [])

    if not bundles:
        st.info("No bundle data available")
        return

    # Convert to DataFrame
    df = pd.DataFrame(bundles)

    col1, col2 = st.columns(2)

    with col1:
        # Funding by bundle
        fig_funding = px.bar(
            df,
            x='bundle_id',
            y='funding_drawn',
            title="Funding Drawn by Bundle",
            labels={'funding_drawn': 'Funding (£)', 'bundle_id': 'Bundle ID'},
            color='funding_drawn',
            color_continuous_scale='Viridis'
        )
        fig_funding.update_layout(showlegend=False)
        st.plotly_chart(fig_funding, use_container_width=True)

    with col2:
        # DBA Proceeds by bundle
        fig_proceeds = px.bar(
            df,
            x='bundle_id',
            y='dba_proceeds_received',
            title="DBA Proceeds by Bundle",
            labels={'dba_proceeds_received': 'DBA Proceeds (£)', 'bundle_id': 'Bundle ID'},
            color='dba_proceeds_received',
            color_continuous_scale='Plasma'
        )
        fig_proceeds.update_layout(showlegend=False)
        st.plotly_chart(fig_proceeds, use_container_width=True)

    # Detailed bundle table
    st.subheader("Bundle Details")
    display_df = df[['bundle_id', 'claimants_in_bundle', 'funding_drawn',
                     'dba_proceeds_received', 'funder_share', 'current_status']]
    display_df.columns = ['Bundle ID', 'Claimants', 'Funding Drawn (£)',
                          'DBA Proceeds (£)', 'Funder Share (£)', 'Status']
    st.dataframe(display_df, use_container_width=True)


def create_claims_detail_view(summary, agent):
    """Create detailed claims view with filters"""
    eligibility = summary.get('claim_eligibility', {})

    if not eligibility:
        st.info("No claims data available")
        return

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Filter by Eligibility",
            ["All", "Eligible", "Not Eligible", "Requires Review"]
        )

    with col2:
        # Get unique claim IDs
        claim_ids = list(eligibility.keys())
        selected_claim = st.selectbox(
            "Select Claim",
            ["All Claims"] + claim_ids
        )

    # Display claims
    if selected_claim == "All Claims":
        # Show summary table
        claims_data = []
        for claim_id, result in eligibility.items():
            claim = agent.claims_data.get(claim_id)
            if claim:
                claims_data.append({
                    'Claim ID': claim_id,
                    'Claimant': claim.claimant_name,
                    'Defendant': claim.defendant,
                    'Claim Amount': f"£{claim.claim_amount:,.2f}",
                    'Funded Amount': f"£{claim.funded_amount:,.2f}",
                    'Status': 'Eligible' if result.get('eligible') else 'Not Eligible',
                    'Recommendation': result.get('recommendation', '')[:30] + '...'
                })

        if claims_data:
            df = pd.DataFrame(claims_data)

            # Apply filter
            if status_filter != "All":
                if status_filter == "Eligible":
                    df = df[df['Status'] == 'Eligible']
                elif status_filter == "Not Eligible":
                    df = df[df['Status'] == 'Not Eligible']

            st.dataframe(df, use_container_width=True, height=400)
    else:
        # Show detailed claim view
        result = eligibility[selected_claim]
        claim = agent.claims_data.get(selected_claim)

        if claim:
            st.subheader(f"Claim Details: {selected_claim}")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Basic Information")
                st.write(f"**Claimant:** {claim.claimant_name}")
                st.write(f"**Defendant:** {claim.defendant}")
                st.write(f"**Law Firm:** {claim.law_firm}")
                st.write(f"**Status:** {claim.status}")

                st.markdown("### Financial Details")
                st.write(f"**Claim Amount:** £{claim.claim_amount:,.2f}")
                st.write(f"**Funded Amount:** £{claim.funded_amount:,.2f}")
                potential_return = claim.claim_amount - claim.funded_amount
                st.write(f"**Potential Return:** £{potential_return:,.2f}")

            with col2:
                st.markdown("### FCA Eligibility Assessment")

                # Status badge
                if result.get('eligible'):
                    st.success(f"✅ **ELIGIBLE**")
                else:
                    st.error(f"❌ **NOT ELIGIBLE**")

                st.write(f"**Recommendation:** {result.get('recommendation')}")

                # Checks
                st.markdown("#### Compliance Checks")
                checks = {
                    "Date Eligibility": result.get('date_checks_passed', False),
                    "Product Type": result.get('product_type_eligible', False),
                    "Commission Threshold": result.get('commission_threshold_met', False),
                    "Limitation Period": result.get('limitation_period_valid', False)
                }

                for check_name, passed in checks.items():
                    icon = "✅" if passed else "❌"
                    st.write(f"{icon} {check_name}")

                # Reasons and warnings
                if result.get('reasons'):
                    with st.expander("Detailed Reasons"):
                        for reason in result.get('reasons', []):
                            st.write(f"• {reason}")

                if result.get('warnings'):
                    with st.expander("⚠️ Warnings", expanded=True):
                        for warning in result.get('warnings', []):
                            st.warning(warning)


def create_financial_overview(summary):
    """Create financial overview with charts"""
    ps = summary.get('portfolio_summary', {})
    bundles = summary.get('bundle_tracker', [])

    # Check if we have real financial data
    total_funding = ps.get('total_funding_provided', 0)
    total_dba = ps.get('total_dba_proceeds', 0)
    has_financial_data = total_funding > 0 or total_dba > 0

    if not has_financial_data:
        st.warning("⚠️ No financial data available in Portfolio Summary sheet. This appears to be a template file.")
        st.info("The Portfolio Summary sheet contains zero values. Please ensure the Excel file has been populated with actual data.")

        # Show portfolio summary remarks if available
        remarks = ps.get('remarks', '')
        if remarks:
            st.markdown(f"**Note:** {remarks}")
    else:
        # Create waterfall chart for funds flow
        fig_waterfall = go.Figure(go.Waterfall(
            name="Funds Flow",
            orientation="v",
            measure=["relative", "relative", "relative", "total"],
            x=["Total Funding", "Outstanding", "DBA Proceeds", "Net Position"],
            y=[
                total_funding,
                -ps.get('outstanding_funding', 0),
                total_dba,
                0
            ],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))

        fig_waterfall.update_layout(
            title="Portfolio Funds Flow (£)",
            showlegend=False
        )

        st.plotly_chart(fig_waterfall, use_container_width=True)

        # Share distribution
        col1, col2 = st.columns(2)

        with col1:
            # Funder vs Milberg share
            funder_share = ps.get('funder_total_share', 0)
            milberg_share = ps.get('milberg_total_share', 0)

            if funder_share > 0 or milberg_share > 0:
                shares = {
                    'Funder': funder_share,
                    'Milberg': milberg_share
                }
                fig_shares = px.pie(
                    values=list(shares.values()),
                    names=list(shares.keys()),
                    title="DBA Proceeds Distribution",
                    color_discrete_sequence=['#1f77b4', '#ff7f0e']
                )
                st.plotly_chart(fig_shares, use_container_width=True)
            else:
                st.info("No DBA proceeds distribution data available")

        with col2:
            # Key metrics table
            st.markdown("### Key Financial Metrics")
            metrics_df = pd.DataFrame({
                'Metric': [
                    'Total Funding Provided',
                    'Outstanding Funding',
                    'Total DBA Proceeds',
                    'Funder Total Share',
                    'Milberg Total Share',
                    'Average Redress',
                    'Total Claimants'
                ],
                'Value': [
                    f"£{total_funding:,.2f}",
                    f"£{ps.get('outstanding_funding', 0):,.2f}",
                    f"£{total_dba:,.2f}",
                    f"£{funder_share:,.2f}",
                    f"£{milberg_share:,.2f}",
                    f"£{ps.get('average_redress', 0):,.2f}",
                    f"{ps.get('total_claimants', 0):,}"
                ]
            })
            st.table(metrics_df)

        # Show DBA proceeds split details if available
        if 'dba_distribution_details' in ps:
            st.markdown('### DBA Proceeds Split (Priorities Deed Waterfall)')
            dba_split = ps['dba_distribution_details']
            split_df = pd.DataFrame({
                'Recipient': [
                    'Funder (Outstanding Costs Sum)',
                    'Funder (First Tier Funder Return)',
                    'Firm (Distribution Costs Overrun)',
                    'Funder (80% of Net Proceeds)',
                    'Milberg (20% of Net Proceeds)',
                    'Claims Processor (50% of Milberg Share)'
                ],
                'Amount (£)': [
                    dba_split['outstanding_costs_sum'],
                    dba_split['first_tier_funder_return'],
                    dba_split['distribution_costs_overrun'],
                    dba_split['net_proceeds'] * 0.8,
                    dba_split['net_proceeds'] * 0.2 - dba_split['claims_processor_share'],
                    dba_split['claims_processor_share']
                ]
            })
            st.table(split_df)
            st.caption('Calculated as per Priorities Deed: Outstanding Costs, Funder Return, Distribution Overrun, then 80/20 split of Net Proceeds (with half of Milberg share to Claims Processor).')


def create_docx_report(summary, agent, docx_path):
    """Create comprehensive DOCX report with embedded charts using matplotlib"""
    doc = Document()

    # Title
    doc.add_heading('PCP Claims Analysis Report', 0)
    doc.add_heading('Milberg Monthly Report - Compliance & Financial Analysis', level=1)

    # Executive Summary
    doc.add_heading('Executive Summary', level=1)
    ps = summary.get('portfolio_summary', {})
    eligibility = summary.get('claim_eligibility', {})
    eligible_count = sum(1 for v in eligibility.values() if v.get('eligible'))

    doc.add_paragraph(f"Report Date: {ps.get('report_date', 'N/A')}")
    doc.add_paragraph(f"Total Claims Processed: {summary.get('ingested', 0)}")
    doc.add_paragraph(f"Eligible Claims: {eligible_count} ({(eligible_count/len(eligibility)*100):.1f}%)" if eligibility else "N/A")
    doc.add_paragraph(f"Total Funding Provided: £{ps.get('total_funding_provided', 0):,.2f}")
    doc.add_paragraph(f"Total DBA Proceeds: £{ps.get('total_dba_proceeds', 0):,.2f}")
    doc.add_paragraph(f"Funder Total Share: £{ps.get('funder_total_share', 0):,.2f}")
    doc.add_paragraph("")

    # Portfolio Summary
    doc.add_heading('Portfolio Summary', level=1)

    # Create a table for portfolio metrics
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Light Grid Accent 1'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Metric'
    hdr_cells[1].text = 'Value'

    for k, v in ps.items():
        row_cells = table.add_row().cells
        row_cells[0].text = k.replace('_', ' ').title()
        row_cells[1].text = str(v)

    doc.add_paragraph("")

    # FCA Eligibility Analysis with Charts
    doc.add_heading('FCA Eligibility Analysis', level=1)

    if eligibility:
        # Summary stats
        doc.add_paragraph(f"Total Claims Assessed: {len(eligibility)}")
        doc.add_paragraph(f"Eligible Claims: {eligible_count}")
        doc.add_paragraph(f"Not Eligible: {len(eligibility) - eligible_count}")
        doc.add_paragraph(f"Eligibility Rate: {(eligible_count/len(eligibility)*100):.1f}%")
        doc.add_paragraph("")

        # Generate and embed eligibility pie chart using matplotlib
        try:
            statuses = ["Eligible" if v.get('eligible') else "Not Eligible" for v in eligibility.values()]
            status_counts = pd.Series(statuses).value_counts()

            # Create matplotlib pie chart
            fig, ax = plt.subplots(figsize=(8, 6))
            colors = ['#28a745', '#dc3545']
            ax.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%',
                   colors=colors, startangle=90)
            ax.set_title('FCA Eligibility Status Distribution', fontsize=14, fontweight='bold')
            plt.axis('equal')

            # Save to temp file
            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            plt.savefig(temp_img.name, dpi=150, bbox_inches='tight')
            plt.close()

            # Add to document
            doc.add_heading('Eligibility Distribution', level=2)
            doc.add_picture(temp_img.name, width=Inches(5))
            doc.add_paragraph("")

            # Clean up temp file
            os.unlink(temp_img.name)
        except Exception as e:
            doc.add_paragraph(f"[Chart generation skipped: {str(e)}]")
            doc.add_paragraph("")

        # Generate and embed recommendations bar chart using matplotlib
        try:
            recommendations = [v.get('recommendation', '').split('-')[0].strip() for v in eligibility.values()]
            rec_counts = pd.Series(recommendations).value_counts()

            # Create matplotlib bar chart
            fig, ax = plt.subplots(figsize=(8, 6))
            bars = ax.bar(range(len(rec_counts)), rec_counts.values, color='#1f77b4')
            ax.set_xticks(range(len(rec_counts)))
            ax.set_xticklabels(rec_counts.index, rotation=45, ha='right')
            ax.set_xlabel('Recommendation')
            ax.set_ylabel('Count')
            ax.set_title('Recommendation Distribution', fontsize=14, fontweight='bold')
            plt.tight_layout()

            # Save to temp file
            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            plt.savefig(temp_img.name, dpi=150, bbox_inches='tight')
            plt.close()

            # Add to document
            doc.add_heading('Recommendation Summary', level=2)
            doc.add_picture(temp_img.name, width=Inches(5))
            doc.add_paragraph("")

            # Clean up temp file
            os.unlink(temp_img.name)
        except Exception as e:
            doc.add_paragraph(f"[Chart generation skipped: {str(e)}]")
            doc.add_paragraph("")

    # Bundle Performance with Charts
    doc.add_heading('Bundle Performance Analysis', level=1)
    bundles = summary.get('bundle_tracker', [])

    if bundles and len(bundles) > 0:
        doc.add_paragraph(f"Total Bundles: {len(bundles)}")
        doc.add_paragraph("")

        # Generate funding chart using matplotlib
        try:
            df_bundles = pd.DataFrame(bundles)

            # Check if required columns exist and have data
            if 'bundle_id' in df_bundles.columns and 'funding_drawn' in df_bundles.columns:
                # Filter out bundles with zero or null funding
                else:
                    doc.add_paragraph("No bundle funding data available to chart.")
                    doc.add_paragraph("")
            else:
                doc.add_paragraph("Bundle data structure incomplete - chart not generated.")
                doc.add_paragraph("")
        except Exception as e:
            doc.add_paragraph(f"[Chart generation skipped: {str(e)}]")
            doc.add_paragraph("")
        # Bundle details table (only if we have bundles)
        if bundles and len(bundles) > 0:
            doc.add_heading('Bundle Details', level=2)
            table = doc.add_table(rows=1, cols=5)
            table.style = 'Light Grid Accent 1'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'Bundle ID'
            hdr_cells[1].text = 'Claimants'
            hdr_cells[2].text = 'Funding Drawn'
            hdr_cells[3].text = 'DBA Proceeds'
            hdr_cells[4].text = 'Status'

            for bundle in bundles:
                row_cells = table.add_row().cells
                row_cells[0].text = str(bundle.get('bundle_id', 'N/A'))
                row_cells[1].text = str(bundle.get('claimants_in_bundle', 0))
                row_cells[2].text = f"£{bundle.get('funding_drawn', 0):,.2f}"
                row_cells[3].text = f"£{bundle.get('dba_proceeds_received', 0):,.2f}"
                row_cells[4].text = str(bundle.get('current_status', 'Unknown'))

            doc.add_paragraph("")
    else:
        doc.add_paragraph("No bundle data available in this report.")
        doc.add_paragraph("")

    # Flagged Claims (NOT Eligible) - Only show claims that need attention
    doc.add_heading('⚠️ Flagged Claims - Requires Review', level=1)

    # Filter for non-eligible claims only
    flagged_claims = {cid: result for cid, result in eligibility.items() if not result.get('eligible')}

    if flagged_claims:
        doc.add_paragraph(f"Total Flagged Claims: {len(flagged_claims)}")
        doc.add_paragraph("The following claims DO NOT meet FCA eligibility criteria and should be reviewed:")
        doc.add_paragraph("")

        # Create summary table for flagged claims
        table = doc.add_table(rows=1, cols=6)
        table.style = 'Light Grid Accent 1'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Claim ID'
        hdr_cells[1].text = 'Claimant'
        hdr_cells[2].text = 'Defendant'
        hdr_cells[3].text = 'Claim Amount'
        hdr_cells[4].text = 'Status'
        hdr_cells[5].text = 'Issue'

        for claim_id, result in flagged_claims.items():
            claim = agent.claims_data.get(claim_id)
            if claim:
                row_cells = table.add_row().cells
                row_cells[0].text = claim_id
                row_cells[1].text = claim.claimant_name
                row_cells[2].text = claim.defendant
                row_cells[3].text = f"£{claim.claim_amount:,.2f}"
                row_cells[4].text = 'NOT ELIGIBLE'
                # Get main reason from recommendation
                row_cells[5].text = result.get('recommendation', 'Review required')[:50]

        doc.add_paragraph("")

        # Detailed flagged claim information
        doc.add_heading('Detailed Issue Analysis', level=2)
        for claim_id, result in flagged_claims.items():
            doc.add_heading(f"❌ Claim ID: {claim_id}", level=3)
            claim = agent.claims_data.get(claim_id)
            if claim:
                doc.add_paragraph(f"Claimant: {claim.claimant_name}")
                doc.add_paragraph(f"Defendant: {claim.defendant}")
                doc.add_paragraph(f"Claim Amount: £{claim.claim_amount:,.2f}")

            doc.add_paragraph(f"Recommendation: {result.get('recommendation')}")

            doc.add_paragraph("Reasons for Flagging:")
            for reason in result.get('reasons', []):
                doc.add_paragraph(f"  • {reason}", style='List Bullet')

            if result.get('warnings'):
                doc.add_paragraph("Additional Warnings:")
                for warning in result.get('warnings', []):
                    doc.add_paragraph(f"  ⚠ {warning}", style='List Bullet')

            doc.add_paragraph("")
    else:
        doc.add_paragraph("✅ No flagged claims - All claims meet FCA eligibility criteria")
        doc.add_paragraph("")

    # Footer
    doc.add_paragraph("")
    doc.add_paragraph("─" * 50)
    doc.add_paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc.add_paragraph("Generated by PCP Claims Analysis System")

    doc.save(docx_path)


# Main App
def main():
    st.markdown('<p class="main-header">📊 PCP Claims Analysis Dashboard</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("Upload Report")
        uploaded_file = st.file_uploader(
            "Upload Milberg Monthly Report",
            type=["xlsx", "xls", "docx"],
            help="Upload an Excel (.xlsx, .xls) or Word (.docx) file containing the Milberg monthly report"
        )

        st.markdown("---")
        st.markdown("### About")
        st.info("""
        This dashboard analyzes PCP claims for:
        - FCA eligibility validation
        - Portfolio performance tracking
        - Bundle-level analysis
        - Financial reporting
        """)

    if uploaded_file:
        # Save uploaded file
        os.makedirs("uploads", exist_ok=True)
        temp_path = f"uploads/{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Determine file type
        file_extension = uploaded_file.name.lower().split('.')[-1]
        file_type_label = {
            'xlsx': 'Excel',
            'xls': 'Excel',
            'docx': 'Word'
        }.get(file_extension, 'Unknown')

        # Process report
        with st.spinner(f"Processing {file_type_label} report... This may take a moment."):
            agent = PCPFundingAgent()
            summary = agent.ingest_report(temp_path)

        st.success(f"✅ {file_type_label} report processed successfully! {summary.get('ingested', 0)} claims analyzed.")

        # Summary metrics
        create_summary_metrics(summary, agent)

        st.markdown("---")

        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview",
            "✅ Eligibility Analysis",
            "📦 Bundle Tracker",
            "📋 Claims Detail",
            "📄 Export Report"
        ])

        with tab1:
            st.header("Financial Overview")
            create_financial_overview(summary)

            # Display Pipeline Breakdown (if available from new Excel format)
            if 'pipeline_breakdown' in summary:
                st.markdown("---")
                st.subheader("📋 Claim Pipeline Breakdown")
                pipeline = summary['pipeline_breakdown']

                # Create DataFrame for pipeline
                pipeline_data = []
                for stage_name, stage_key in [
                    ('Awaiting DSAR', 'awaiting_dsar'),
                    ('Pending Submission', 'pending_submission'),
                    ('Under Review', 'under_review'),
                    ('Settlement Offered', 'settlement_offered'),
                    ('Paid', 'paid')
                ]:
                    stage_info = pipeline.get(stage_key, {})
                    pipeline_data.append({
                        'Stage': stage_name,
                        'Count': int(stage_info.get('count', 0)),
                        'Estimated Value': f"£{stage_info.get('value', 0):,.2f}"
                    })

                pipeline_df = pd.DataFrame(pipeline_data)
                st.dataframe(pipeline_df, use_container_width=True, hide_index=True)

                # Pipeline visualization
                fig_pipeline = px.funnel(
                    pipeline_df,
                    x='Count',
                    y='Stage',
                    title='Claims Pipeline Funnel'
                )
                st.plotly_chart(fig_pipeline, use_container_width=True)

            # Display Financial Utilisation (if available from new Excel format)
            if 'financial_utilisation' in summary:
                st.markdown("---")
                st.subheader("💰 Financial Utilisation Overview")
                financial = summary['financial_utilisation']

                col1, col2 = st.columns(2)

                with col1:
                    # Cost breakdown
                    st.markdown("#### Cost Breakdown")
                    costs_df = pd.DataFrame({
                        'Category': [
                            'Client Acquisition',
                            'Claim Submission',
                            'Claim Processing',
                            'Legal Costs'
                        ],
                        'Amount (£)': [
                            financial.get('acquisition_cost', 0),
                            financial.get('submission_cost', 0),
                            financial.get('processing_cost', 0),
                            financial.get('legal_cost', 0)
                        ]
                    })
                    st.dataframe(costs_df, use_container_width=True, hide_index=True)

                with col2:
                    # Summary metrics
                    st.markdown("#### Summary")
                    st.metric("Total Action Costs", f"£{financial.get('total_action_costs', 0):,.2f}")
                    st.metric("Collection Account Balance", f"£{financial.get('collection_account_balance', 0):,.2f}")

                    # Cost distribution pie chart
                    if financial.get('total_action_costs', 0) > 0:
                        fig_costs = px.pie(
                            costs_df,
                            values='Amount (£)',
                            names='Category',
                            title='Cost Distribution'
                        )
                        st.plotly_chart(fig_costs, use_container_width=True)

        with tab2:
            st.header("FCA Eligibility Analysis")
            create_eligibility_charts(summary)

            # Eligibility summary table
            st.subheader("Eligibility Summary by Claim")
            eligibility = summary.get('claim_eligibility', {})
            if eligibility:
                summary_data = []
                for claim_id, result in eligibility.items():
                    summary_data.append({
                        'Claim ID': claim_id,
                        'Eligible': '✅' if result.get('eligible') else '❌',
                        'Recommendation': result.get('recommendation', '')[:50] + '...',
                        'Commission Check': '✅' if result.get('commission_threshold_met') else '❌',
                        'Date Check': '✅' if result.get('date_checks_passed') else '❌'
                    })
                st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

        with tab3:
            st.header("Bundle Performance Analysis")
            create_bundle_analysis(summary)

        with tab4:
            st.header("Detailed Claims View")
            create_claims_detail_view(summary, agent)

        with tab5:
            st.header("Export Reports")

            # Check if comprehensive report was auto-generated
            if 'comprehensive_report_path' in summary and os.path.exists(summary['comprehensive_report_path']):
                st.success("✅ Comprehensive Analysis Report automatically generated!")
                st.info(f"📄 Report saved to: {os.path.basename(summary['comprehensive_report_path'])}")

                with open(summary['comprehensive_report_path'], "rb") as f:
                    st.download_button(
                        "📥 Download Comprehensive Analysis Report",
                        f,
                        file_name=os.path.basename(summary['comprehensive_report_path']),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary"
                    )

                st.markdown("---")
                st.markdown("**The Comprehensive Analysis Report includes:**")
                st.markdown("""
                - Executive Summary with key highlights
                - Portfolio Overview with metrics table
                - Claims Distribution by Lender (table & chart)
                - Detailed Claims Information
                - Visual Analysis with charts:
                  - Top 10 Lenders by Claims Volume (bar chart)
                  - Claims Status Distribution (pie chart)
                - FCA Compliance Analysis
                - Financial Analysis
                - Recommendations & Next Steps
                """)

                st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📥 Custom DOCX Report")
                st.write("Alternative report format")

                if st.button("Generate Custom DOCX", type="secondary"):
                    with st.spinner("Generating report..."):
                        docx_path = f"uploads/{os.path.splitext(uploaded_file.name)[0]}_analysis_report.docx"
                        create_docx_report(summary, agent, docx_path)

                        with open(docx_path, "rb") as f:
                            st.download_button(
                                "📥 Download Custom Report",
                                f,
                                file_name=os.path.basename(docx_path),
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                    st.success("Custom report generated!")

            with col2:
                st.subheader("📊 Download Raw Data")
                st.write("JSON format with all analysis data")

                json_data = json.dumps(summary, indent=2, default=str)
                st.download_button(
                    "📥 Download JSON",
                    json_data,
                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_analysis.json",
                    mime="application/json"
                )

    else:
        # Landing page
        st.info("👆 Please upload a Milberg monthly report Excel file to begin analysis")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            ### 📊 Portfolio Overview
            - Real-time funding metrics
            - DBA proceeds tracking
            - Funder share analysis
            """)

        with col2:
            st.markdown("""
            ### ✅ FCA Compliance
            - Automated eligibility checks
            - Plevin threshold validation
            - Commission disclosure review
            """)

        with col3:
            st.markdown("""
            ### 📈 Analytics
            - Bundle performance tracking
            - Claim-level insights
            - Exportable reports
            """)


if __name__ == "__main__":
    main()
