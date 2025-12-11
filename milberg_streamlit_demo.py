
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pcp_funding_agent import PCPFundingAgent
from profit_calculator import ProfitCalculator, get_priority_deed_summary
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
    """Create summary metrics display with profit calculations"""

    ps = summary.get('portfolio_summary', {})

    # Calculate profit metrics
    calc = ProfitCalculator()

    # Check if we have individual claims data (old format)
    if agent.claims_data:
        claims_list = []
        for claim_id, claim_obj in agent.claims_data.items():
            claims_list.append({
                'claim_amount': claim_obj.claim_amount,
                'funded_amount': claim_obj.funded_amount
            })
        profit_metrics = calc.calculate_portfolio_metrics(claims_list)
    else:
        # Use portfolio_summary data from new Monthly Summary format
        total_claim_value = ps.get('total_claim_value', 0)
        total_funded = ps.get('total_funded', 0)

        # Calculate DBA proceeds and profit split
        dba_proceeds = calc.calculate_dba_proceeds(total_claim_value)
        profit_split = calc.calculate_profit_split(dba_proceeds)
        funder_moic = calc.calculate_moic(profit_split['funder_share'], total_funded)

        profit_metrics = {
            'total_claims_value': total_claim_value,
            'total_funded': total_funded,
            'dba_proceeds': dba_proceeds,
            'funder_collection': profit_split['funder_share'],
            'milberg_collection': profit_split['milberg_share'],
            'funder_moic': funder_moic,
            'profit_margin': ((profit_split['funder_share'] - total_funded) / total_funded * 100) if total_funded > 0 else 0
        }

    # Top row - Main KPIs
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Total Claims",
            f"{summary.get('total_found', 0)}",
            f"{summary.get('ingested', 0)} Processed"
        )

    with col2:
        total_funding = profit_metrics.get('total_funded', ps.get('total_funding_provided', 0))
        st.metric(
            "Total Funded",
            f"£{total_funding:,.0f}",
            "Investment"
        )

    with col3:
        dba_proceeds = profit_metrics.get('dba_proceeds', 0)
        st.metric(
            "DBA Proceeds (30%)",
            f"£{dba_proceeds:,.0f}",
            "30% of Claims"
        )

    with col4:
        funder_collection = profit_metrics.get('funder_collection', 0)
        st.metric(
            "Funder Collection (80%)",
            f"£{funder_collection:,.0f}",
            "80% of DBA"
        )

    with col5:
        moic = profit_metrics.get('funder_moic', 0)
        moic_color = "normal" if moic >= 1.0 else "inverse"
        st.metric(
            "Funder MOIC",
            f"{moic:.2f}x",
            f"{'Profit' if moic > 1.0 else 'Loss' if moic < 1.0 else 'Break-even'}",
            delta_color=moic_color
        )

    # Second row - Additional metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        milberg_collection = profit_metrics.get('milberg_collection', 0)
        st.metric(
            "Milberg Collection (20%)",
            f"£{milberg_collection:,.0f}",
            "20% of DBA"
        )

    with col2:
        total_claims_value = profit_metrics.get('total_claims_value', 0)
        st.metric(
            "Total Claims Value",
            f"£{total_claims_value:,.0f}",
            "Successful Claims"
        )

    with col3:
        # Calculate eligibility rate or use portfolio data
        eligibility = summary.get('claim_eligibility', {})
        if eligibility:
            eligible_count = sum(1 for v in eligibility.values() if v.get('eligible'))
            total_checked = len(eligibility)
            rate = (eligible_count / total_checked * 100) if total_checked > 0 else 0
            st.metric(
                "FCA Eligibility Rate",
                f"{rate:.0f}%",
                f"{eligible_count}/{total_checked} Eligible"
            )
        else:
            # Use success rate from portfolio summary
            claims_submitted = ps.get('total_claims_submitted', 0)
            claims_successful = ps.get('claims_successful', 0)
            success_rate = (claims_successful / claims_submitted * 100) if claims_submitted > 0 else 0
            st.metric(
                "Success Rate",
                f"{success_rate:.0f}%",
                f"{claims_successful}/{claims_submitted} Successful"
            )

    with col4:
        profit_margin = profit_metrics.get('profit_margin', 0)
        st.metric(
            "Profit Margin",
            f"{profit_margin:.1f}%",
            "ROI"
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
    financial_util = summary.get('financial_utilisation', {})
    forecasting = summary.get('forecasting', {})

    # Check if we have new Monthly Summary format data
    if financial_util:
        st.subheader("Financial Utilisation Overview")

        # Cost breakdown metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            acquisition_cost = financial_util.get('acquisition_cost', 0)
            st.metric("Acquisition Cost", f"£{acquisition_cost:,.0f}")

        with col2:
            submission_cost = financial_util.get('submission_cost', 0)
            st.metric("Submission Cost", f"£{submission_cost:,.0f}")

        with col3:
            processing_cost = financial_util.get('processing_cost', 0)
            st.metric("Processing Cost", f"£{processing_cost:,.0f}")

        with col4:
            legal_cost = financial_util.get('legal_cost', 0)
            st.metric("Legal Cost", f"£{legal_cost:,.0f}")

        # Total costs and balance
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            total_costs = financial_util.get('total_action_costs', 0)
            st.metric("Total Action Costs", f"£{total_costs:,.0f}", "Cumulative")

        with col2:
            balance = financial_util.get('collection_account_balance', 0)
            st.metric("Collection Account Balance", f"£{balance:,.0f}")

        # Cost breakdown chart
        if total_costs > 0:
            st.markdown("---")
            st.subheader("Cost Breakdown")
            cost_data = pd.DataFrame({
                'Category': ['Acquisition', 'Submission', 'Processing', 'Legal'],
                'Amount': [acquisition_cost, submission_cost, processing_cost, legal_cost]
            })

            fig_costs = px.bar(
                cost_data,
                x='Category',
                y='Amount',
                title='Costs by Category',
                color='Amount',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_costs, use_container_width=True)

        # Forecasting section
        if forecasting:
            st.markdown("---")
            st.subheader("Forecasting")

            col1, col2, col3 = st.columns(3)

            with col1:
                expected_clients = forecasting.get('expected_new_clients', 0)
                st.metric("Expected New Clients", expected_clients)

            with col2:
                expected_submissions = forecasting.get('expected_submissions', 0)
                st.metric("Expected Submissions", expected_submissions)

            with col3:
                expected_redress = forecasting.get('expected_redress', 0)
                st.metric("Expected Redress", f"£{expected_redress:,.0f}")

        return

    # Check if we have real financial data (old format)
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
    doc.add_paragraph("")

    # Calculate profit metrics
    calc = ProfitCalculator()
    claims_list = []
    for claim_id, claim_obj in agent.claims_data.items():
        claims_list.append({
            'claim_amount': claim_obj.claim_amount,
            'funded_amount': claim_obj.funded_amount
        })
    profit_metrics = calc.calculate_portfolio_metrics(claims_list) if claims_list else {}

    # Profit Distribution & Returns Analysis
    doc.add_heading('💰 Profit Distribution & Returns Analysis', level=1)

    doc.add_paragraph("Based on Priority Deed terms:")
    doc.add_paragraph("")

    # Key metrics
    doc.add_paragraph(f"Total Claims Value: £{profit_metrics.get('total_claims_value', 0):,.2f}")
    doc.add_paragraph(f"Total Funded by Funder: £{profit_metrics.get('total_funded', 0):,.2f}")
    doc.add_paragraph("")

    doc.add_paragraph(f"DBA Proceeds (30% of claims): £{profit_metrics.get('dba_proceeds', 0):,.2f}")
    doc.add_paragraph("")

    # Profit split table
    doc.add_heading('Profit Split from DBA Proceeds', level=2)
    split_table = doc.add_table(rows=1, cols=3)
    split_table.style = 'Light Grid Accent 1'
    hdr_cells = split_table.rows[0].cells
    hdr_cells[0].text = 'Recipient'
    hdr_cells[1].text = 'Percentage'
    hdr_cells[2].text = 'Amount (£)'

    # Funder row
    row_cells = split_table.add_row().cells
    row_cells[0].text = 'Funder Collection'
    row_cells[1].text = '80%'
    row_cells[2].text = f"£{profit_metrics.get('funder_collection', 0):,.2f}"

    # Milberg row
    row_cells = split_table.add_row().cells
    row_cells[0].text = 'Milberg Collection'
    row_cells[1].text = '20%'
    row_cells[2].text = f"£{profit_metrics.get('milberg_collection', 0):,.2f}"

    doc.add_paragraph("")

    # MOIC and Returns
    doc.add_heading('Investment Returns (MOIC)', level=2)
    moic = profit_metrics.get('funder_moic', 0)
    profit_margin = profit_metrics.get('profit_margin', 0)

    doc.add_paragraph(f"Funder MOIC (Multiple on Invested Capital): {moic:.2f}x")
    doc.add_paragraph(f"Profit Margin: {profit_margin:.1f}%")
    doc.add_paragraph("")

    if moic > 1.0:
        doc.add_paragraph(f"✓ PROFITABLE: Funder earning {(moic-1)*100:.1f}% return on investment")
    elif moic == 1.0:
        doc.add_paragraph("= BREAK-EVEN: Funder recovering exactly the investment")
    else:
        doc.add_paragraph(f"✗ LOSS: Funder not yet recovering full investment ({(1-moic)*100:.1f}% shortfall)")

    doc.add_paragraph("")

    # Priority Deed explanation
    doc.add_heading('Priority Deed Payment Structure', level=2)
    doc.add_paragraph("Payment Waterfall (in order of priority):")
    doc.add_paragraph("1. Outstanding Costs Sum → Paid to Funder", style='List Bullet')
    doc.add_paragraph("2. First Tier Funder Return → Paid to Funder", style='List Bullet')
    doc.add_paragraph("3. Distribution Costs Overrun → Paid to Firm (Milberg)", style='List Bullet')
    doc.add_paragraph("4. Net Proceeds Split → 80% Funder / 20% Milberg", style='List Bullet')
    doc.add_paragraph("")
    doc.add_paragraph("Note: DBA Proceeds represent 30% of successful claim amounts. The remaining 70% is distributed to claimants.")
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
                df_bundles_filtered = df_bundles[df_bundles['funding_drawn'].fillna(0) > 0]

                if len(df_bundles_filtered) > 0:
                    # Create matplotlib bar chart
                    fig, ax = plt.subplots(figsize=(10, 6))
                    bars = ax.bar(df_bundles_filtered['bundle_id'], df_bundles_filtered['funding_drawn'], color='#2ca02c')
                    ax.set_xlabel('Bundle ID')
                    ax.set_ylabel('Funding (£)')
                    ax.set_title('Funding Drawn by Bundle', fontsize=14, fontweight='bold')
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()

                    # Save to temp file
                    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    plt.savefig(temp_img.name, dpi=150, bbox_inches='tight')
                    plt.close()

                    # Add to document
                    doc.add_heading('Funding by Bundle', level=2)
                    doc.add_picture(temp_img.name, width=Inches(5.5))
                    doc.add_paragraph("")

                    # Clean up temp file
                    os.unlink(temp_img.name)
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


def create_lender_analysis(summary, agent):
    """Create lender/defendant distribution analysis"""
    st.subheader("Distribution by Lender/Defendant")

    # Check if we have lender_distribution from new Monthly Summary format
    lender_summary = summary.get('lender_distribution', [])

    if lender_summary:
        # Use lender distribution data from new format
        lender_df = pd.DataFrame([
            {
                'Lender/Defendant': lender['lender'],
                'Number of Claims': lender.get('num_claims', 0),
                'Total Claim Value': lender.get('estimated_value', 0),
                'Total Funded': lender.get('estimated_value', 0) * 0.7,  # Assume 70% funding
                'Avg Claim Value': (lender.get('estimated_value', 0) / lender.get('num_claims', 1)) if lender.get('num_claims', 0) > 0 else 0
            }
            for lender in lender_summary
        ]).sort_values('Total Claim Value', ascending=False)
    else:
        # Extract lender data from individual claims (old format)
        lender_data = {}
        for claim_id, claim_obj in agent.claims_data.items():
            lender = claim_obj.defendant if hasattr(claim_obj, 'defendant') else 'Unknown'
            if lender not in lender_data:
                lender_data[lender] = {
                    'count': 0,
                    'total_value': 0,
                    'funded': 0,
                    'claims': []
                }
            lender_data[lender]['count'] += 1
            lender_data[lender]['total_value'] += claim_obj.claim_amount
            lender_data[lender]['funded'] += claim_obj.funded_amount
            lender_data[lender]['claims'].append(claim_id)

        if not lender_data:
            st.info("No lender data available")
            return

        # Create DataFrame
        lender_df = pd.DataFrame([
            {
                'Lender/Defendant': lender,
                'Number of Claims': data['count'],
                'Total Claim Value': data['total_value'],
                'Total Funded': data['funded'],
                'Avg Claim Value': data['total_value'] / data['count'] if data['count'] > 0 else 0
            }
            for lender, data in lender_data.items()
        ]).sort_values('Total Claim Value', ascending=False)

    if lender_df.empty:
        st.info("No lender data available")
        return

    # Calculate percentages
    total_claims = lender_df['Number of Claims'].sum()
    total_value = lender_df['Total Claim Value'].sum()
    lender_df['% of Claims'] = (lender_df['Number of Claims'] / total_claims * 100).round(1)
    lender_df['% of Value'] = (lender_df['Total Claim Value'] / total_value * 100).round(1)

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        # Pie chart - Claims count
        fig_pie = px.pie(
            lender_df,
            values='Number of Claims',
            names='Lender/Defendant',
            title='Claims Distribution by Lender',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Bar chart - Claim values
        fig_bar = px.bar(
            lender_df,
            x='Lender/Defendant',
            y='Total Claim Value',
            title='Total Claim Value by Lender',
            color='Total Claim Value',
            color_continuous_scale='Viridis'
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # Detailed table
    st.subheader("Detailed Breakdown")
    display_df = lender_df.copy()
    display_df['Total Claim Value'] = display_df['Total Claim Value'].apply(lambda x: f"£{x:,.2f}")
    display_df['Total Funded'] = display_df['Total Funded'].apply(lambda x: f"£{x:,.2f}")
    display_df['Avg Claim Value'] = display_df['Avg Claim Value'].apply(lambda x: f"£{x:,.2f}")
    st.dataframe(display_df, use_container_width=True)

    # Top lenders highlight
    st.subheader("Key Insights")
    col1, col2, col3 = st.columns(3)

    with col1:
        top_lender = lender_df.iloc[0]
        st.metric(
            "Largest Lender",
            top_lender['Lender/Defendant'],
            f"{top_lender['Number of Claims']} claims"
        )

    with col2:
        st.metric(
            "Total Lenders",
            len(lender_df),
            f"{total_claims} total claims"
        )

    with col3:
        concentration = lender_df.iloc[0]['% of Value']
        st.metric(
            "Top Lender Concentration",
            f"{concentration:.1f}%",
            "of total value"
        )


def create_claims_statistics(summary, agent):
    """Create claims statistics and pipeline analysis"""

    # Check if we have portfolio_summary from new Monthly Summary format
    portfolio = summary.get('portfolio_summary', {})
    pipeline = summary.get('pipeline_breakdown', {})

    if portfolio:
        # Use data from new Monthly Summary format
        st.subheader("Portfolio Overview")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_claims = portfolio.get('total_claims', 0)
            st.metric("Total Claims", total_claims)

        with col2:
            claims_submitted = portfolio.get('total_claims_submitted', 0)
            st.metric("Claims Submitted", claims_submitted)

        with col3:
            claims_successful = portfolio.get('claims_successful', 0)
            success_rate = (claims_successful / claims_submitted * 100) if claims_submitted > 0 else 0
            st.metric("Successful Claims", claims_successful, f"{success_rate:.1f}%")

        with col4:
            avg_value = portfolio.get('avg_claim_value', 0)
            st.metric("Avg Claim Value", f"£{avg_value:,.0f}")

        # Claim Pipeline Breakdown
        if pipeline:
            st.markdown("---")
            st.subheader("Claim Pipeline Status")

            pipeline_data = []
            for stage_key, stage_data in pipeline.items():
                if isinstance(stage_data, dict):
                    stage_name = stage_key.replace('_', ' ').title()
                    pipeline_data.append({
                        'Stage': stage_name,
                        'Count': stage_data.get('count', 0),
                        'Estimated Value': stage_data.get('value', 0)
                    })

            if pipeline_data:
                # Pipeline bar chart
                pipeline_df = pd.DataFrame(pipeline_data)
                fig_pipeline = px.bar(
                    pipeline_df,
                    x='Stage',
                    y='Count',
                    title='Claims by Pipeline Stage',
                    color='Count',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_pipeline, use_container_width=True)

                # Pipeline table
                display_df = pipeline_df.copy()
                display_df['Estimated Value'] = display_df['Estimated Value'].apply(lambda x: f"£{x:,.0f}")
                st.dataframe(display_df, use_container_width=True)

        return

    # Fall back to old format with eligibility data
    eligibility = summary.get('claim_eligibility', {})

    if not eligibility:
        st.info("No claims data available")
        return

    # Statistics overview
    st.subheader("Claims Overview")
    col1, col2, col3, col4 = st.columns(4)

    total_claims = len(eligibility)
    eligible_claims = sum(1 for v in eligibility.values() if v.get('eligible'))
    not_eligible = total_claims - eligible_claims
    eligibility_rate = (eligible_claims / total_claims * 100) if total_claims > 0 else 0

    with col1:
        st.metric("Total Claims Processed", total_claims)

    with col2:
        st.metric("Eligible Claims", eligible_claims, f"{eligibility_rate:.1f}%")

    with col3:
        st.metric("Not Eligible", not_eligible, f"{100-eligibility_rate:.1f}%")

    with col4:
        # Calculate average claim value
        avg_value = sum(claim.claim_amount for claim in agent.claims_data.values()) / len(agent.claims_data) if agent.claims_data else 0
        st.metric("Avg Claim Value", f"£{avg_value:,.0f}")

    st.markdown("---")

    # FCA Eligibility Breakdown
    st.subheader("FCA Eligibility Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # Eligibility pie chart
        status_data = pd.DataFrame({
            'Status': ['Eligible', 'Not Eligible'],
            'Count': [eligible_claims, not_eligible]
        })

        fig_pie = px.pie(
            status_data,
            values='Count',
            names='Status',
            title='FCA Eligibility Status',
            color='Status',
            color_discrete_map={'Eligible': '#28a745', 'Not Eligible': '#dc3545'}
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Recommendation breakdown
        recommendations = [v.get('recommendation', 'Unknown').split('-')[0].strip() for v in eligibility.values()]
        rec_counts = pd.Series(recommendations).value_counts()

        fig_bar = px.bar(
            x=rec_counts.index,
            y=rec_counts.values,
            title='Recommendation Distribution',
            labels={'x': 'Recommendation', 'y': 'Count'},
            color=rec_counts.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Detailed Claims Table
    st.subheader("Detailed Claims Status")

    claims_data = []
    for claim_id, result in eligibility.items():
        claim_obj = agent.claims_data.get(claim_id)
        if claim_obj:
            claims_data.append({
                'Claim ID': claim_id,
                'Claimant': claim_obj.claimant_name,
                'Defendant': claim_obj.defendant,
                'Claim Value': f"£{claim_obj.claim_amount:,.2f}",
                'Funded': f"£{claim_obj.funded_amount:,.2f}",
                'Eligible': '✅ Yes' if result.get('eligible') else '❌ No',
                'Commission Met': '✅' if result.get('commission_threshold_met') else '❌',
                'Date Valid': '✅' if result.get('date_checks_passed') else '❌',
                'Recommendation': result.get('recommendation', '')[:40] + '...'
            })

    if claims_data:
        df = pd.DataFrame(claims_data)
        st.dataframe(df, use_container_width=True)

        # Download option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Claims Data (CSV)",
            data=csv,
            file_name="claims_analysis.csv",
            mime="text/csv"
        )

    # Warnings and Issues
    if not_eligible > 0:
        st.subheader("⚠️ Claims Requiring Attention")
        flagged_claims = [(cid, res) for cid, res in eligibility.items() if not res.get('eligible')]

        for claim_id, result in flagged_claims[:5]:  # Show first 5
            with st.expander(f"❌ Claim {claim_id}"):
                claim_obj = agent.claims_data.get(claim_id)
                if claim_obj:
                    st.write(f"**Claimant:** {claim_obj.claimant_name}")
                    st.write(f"**Defendant:** {claim_obj.defendant}")
                    st.write(f"**Value:** £{claim_obj.claim_amount:,.2f}")
                st.write(f"**Issue:** {result.get('recommendation', 'Unknown')}")

                if result.get('reasons'):
                    st.write("**Reasons:**")
                    for reason in result.get('reasons', []):
                        st.write(f"- {reason}")


# Main App
def main():
    st.markdown('<p class="main-header">📊 PCP Claims Analysis Dashboard</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("Upload Report")
        uploaded_file = st.file_uploader(
            "Upload Milberg Monthly Report",
            type=["xlsx"],
            help="Upload an Excel file containing the Milberg monthly report"
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

        # Process report
        with st.spinner("Processing report... This may take a moment."):
            agent = PCPFundingAgent()
            summary = agent.ingest_excel_report(temp_path)

        st.success(f"✅ Report processed successfully! {summary.get('ingested', 0)} claims analyzed.")

        # Debug: Show what's in summary
        with st.expander("🔍 Debug: Summary Data"):
            st.json({
                'report_type': summary.get('report_type'),
                'total_found': summary.get('total_found'),
                'ingested': summary.get('ingested'),
                'has_portfolio_summary': bool(summary.get('portfolio_summary')),
                'has_lender_distribution': bool(summary.get('lender_distribution')),
                'has_pipeline_breakdown': bool(summary.get('pipeline_breakdown')),
                'has_financial_utilisation': bool(summary.get('financial_utilisation')),
                'lender_count': len(summary.get('lender_distribution', [])),
                'extraction_method': summary.get('extraction_method', 'unknown')
            })

        # Summary metrics
        create_summary_metrics(summary, agent)

        st.markdown("---")

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏦 Lenders & Defendants",
            "📊 Claims Statistics",
            "💰 Financial Analysis",
            "📄 Export Report"
        ])

        with tab1:
            st.header("Lenders & Defendants Distribution")
            create_lender_analysis(summary, agent)

        with tab2:
            st.header("Claims Pipeline & Statistics")
            create_claims_statistics(summary, agent)

        with tab3:
            st.header("Financial Overview & Performance")
            create_financial_overview(summary)

        with tab4:
            st.header("Export Reports")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📥 Download DOCX Report")
                st.write("Comprehensive report with all details")

                if st.button("Generate DOCX Report", type="primary"):
                    with st.spinner("Generating report..."):
                        docx_path = f"uploads/{os.path.splitext(uploaded_file.name)[0]}_analysis_report.docx"
                        create_docx_report(summary, agent, docx_path)

                        with open(docx_path, "rb") as f:
                            st.download_button(
                                "📥 Download Report",
                                f,
                                file_name=os.path.basename(docx_path),
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                    st.success("Report generated!")

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
