"""
New PCP Claims Analysis Dashboard
Uses intelligent agents to analyze Excel reports
"""

import streamlit as st
import os
import hashlib
from intelligent_agents import analyze_monthly_report
import json

# Page config
st.set_page_config(
    page_title="PCP Claims Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# Authentication
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

USERS = {
    "admin": hash_password("Admin123!"),
    "walter": hash_password("Walter123!"),
    "dirk": hash_password("Dirk123!"),
    "eda": hash_password("Eda123!")
}

def check_login(username: str, password: str) -> bool:
    if username in USERS:
        return USERS[username] == hash_password(password)
    return False

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# Login page
if not st.session_state.logged_in:
    st.title("🔐 PCP Claims Analysis Dashboard")
    st.subheader("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if check_login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password")

# Main dashboard
else:
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 PCP Claims Analysis Dashboard")
        st.markdown("**AI-Powered Analysis with Intelligent Agents**")
    with col2:
        st.write(f"👤 Logged in as: **{st.session_state.username}**")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.analysis_result = None
            st.rerun()

    st.markdown("---")

    # File upload
    st.subheader("📤 Upload Monthly Report")
    uploaded_file = st.file_uploader(
        "Upload Milberg Monthly Report (Excel)",
        type=['xlsx', 'xls'],
        help="Upload the Monthly Summary Excel file"
    )

    if uploaded_file:
        # Save uploaded file
        os.makedirs("uploads", exist_ok=True)
        temp_path = os.path.join("uploads", uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Analyze button
        if st.button("🤖 Analyze with AI Agents", type="primary"):
            with st.spinner("🤖 AI Agents are analyzing the report... This may take 30-60 seconds..."):
                try:
                    result = analyze_monthly_report(temp_path)
                    st.session_state.analysis_result = result
                    st.success("✅ Analysis complete!")
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
                    st.exception(e)

    # Display results
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        excel_data = result['excel_data']

        st.markdown("---")

        # Key Metrics
        st.subheader("📊 Key Metrics")

        portfolio = excel_data.get('portfolio_metrics', {})
        lenders = excel_data.get('lender_distribution', [])

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Total Claims",
                f"{portfolio.get('unique_claims', 0)}",
                "Cumulative"
            )

        with col2:
            st.metric(
                "Total Clients",
                f"{portfolio.get('unique_clients', 0)}",
                "Cumulative"
            )

        with col3:
            st.metric(
                "Lenders",
                f"{len(lenders)}",
                "Active"
            )

        with col4:
            st.metric(
                "Success Rate",
                f"{(portfolio.get('claims_successful', 0) / max(1, portfolio.get('claims_submitted', 1)) * 100):.0f}%",
                f"{portfolio.get('claims_successful', 0)}/{portfolio.get('claims_submitted', 0)}"
            )

        with col5:
            st.metric(
                "Avg Claim Value",
                f"£{portfolio.get('avg_claim_value', 0):,.0f}",
                "Per claim"
            )

        st.markdown("---")

        # Tabs for different analyses
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Executive Report",
            "💰 Economic Analysis",
            "⚖️ Compliance Analysis",
            "📊 Portfolio Analysis",
            "📁 Raw Data"
        ])

        with tab1:
            st.header("Executive Report")
            st.markdown(result['comprehensive_report'])

            # Download report
            st.download_button(
                label="📥 Download Executive Report (Markdown)",
                data=result['comprehensive_report'],
                file_name="executive_report.md",
                mime="text/markdown"
            )

        with tab2:
            st.header("Economic Analysis")
            st.markdown(result['economic_analysis'])

        with tab3:
            st.header("FCA Compliance Analysis")
            st.markdown(result['compliance_analysis'])

        with tab4:
            st.header("Portfolio Composition Analysis")
            st.markdown(result['portfolio_analysis'])

        with tab5:
            st.header("Raw Extracted Data")

            st.subheader("Portfolio Metrics")
            st.json(portfolio)

            st.subheader("Financial Costs")
            st.json(excel_data.get('financial_costs', {}))

            st.subheader("Pipeline Status")
            st.json(excel_data.get('pipeline', {}))

            st.subheader("Lender Distribution")
            st.dataframe(lenders)

            st.subheader("Forecasting")
            st.json(excel_data.get('forecasting', {}))

    else:
        st.info("👆 Upload an Excel file and click 'Analyze with AI Agents' to start")

    # Footer
    st.markdown("---")
    st.markdown("*Powered by OpenAI GPT-4o • Intelligent Multi-Agent Analysis*")
