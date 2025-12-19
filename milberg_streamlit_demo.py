"""
Milberg PCP Claims Dashboard - Unified Intelligent Agent System
Uses OpenAI-powered agents for consistent data extraction and report generation
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import hashlib
from datetime import datetime

# Import the unified intelligent agent system
try:
    from intelligent_agents import (
        generate_full_investor_report,
        MonthlyReportAgent,
        PriorityDeedAgent
    )
    AGENTS_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not import intelligent_agents: {e}")
    AGENTS_AVAILABLE = False
    generate_full_investor_report = None
    MonthlyReportAgent = None
    PriorityDeedAgent = None

# Page config
st.set_page_config(
    page_title="Milberg PCP Claims Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)

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
    return username in USERS and USERS[username] == hash_password(password)

# Session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'data' not in st.session_state:
    st.session_state.data = None
if 'debug_output' not in st.session_state:
    st.session_state.debug_output = None
# NEW: investor report state
if 'investor_report_md' not in st.session_state:
    st.session_state.investor_report_md = None
if 'investor_report_path' not in st.session_state:
    st.session_state.investor_report_path = None
if 'investor_report_docx_bytes' not in st.session_state:
    st.session_state.investor_report_docx_bytes = None
if 'investor_report_docx_path' not in st.session_state:
    st.session_state.investor_report_docx_path = None
if 'investor_report_pptx_bytes' not in st.session_state:
    st.session_state.investor_report_pptx_bytes = None
if 'investor_report_pptx_path' not in st.session_state:
    st.session_state.investor_report_pptx_path = None
if 'last_uploaded_excel_path' not in st.session_state:
    st.session_state.last_uploaded_excel_path = None

# Login page
if not st.session_state.logged_in:
    st.markdown('<div class="main-header">🔐 Milberg PCP Claims Dashboard</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                if check_login(username, password):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
else:
    # Main Dashboard
    st.markdown('<div class="main-header">📊 Milberg PCP Claims Dashboard</div>', unsafe_allow_html=True)

    # File upload
    uploaded_file = st.file_uploader("Upload Monthly Report Excel", type=['xlsx', 'xls'])

    if uploaded_file:
        os.makedirs("uploads", exist_ok=True)
        temp_path = os.path.join("uploads", uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Track latest upload path for report generation
        st.session_state.last_uploaded_excel_path = temp_path

        if st.button("📊 Load Data with AI Agent", type="primary"):
            if not AGENTS_AVAILABLE:
                st.error("Intelligent agent system not available. Check that intelligent_agents.py is properly configured.")
            else:
                with st.spinner("🤖 AI Agent analyzing Excel report..."):
                    import sys
                    from io import StringIO

                    # Capture print output for debugging
                    old_stdout = sys.stdout
                    sys.stdout = captured_output = StringIO()

                    try:
                        # Use the MonthlyReportAgent for consistent extraction
                        agent = MonthlyReportAgent()
                        monthly_data = agent.analyze_monthly_report(temp_path)

                        # Convert agent output to dashboard format
                        pm = monthly_data.get('portfolio_metrics', {})
                        lenders = monthly_data.get('lender_distribution', [])
                        pipeline = monthly_data.get('pipeline', {})
                        fm = monthly_data.get('financial_metrics', {})

                        # Calculate totals from lenders if needed
                        total_claims = pm.get('unique_claims', 0)
                        total_value = pm.get('total_settlement_value', 0)
                        if total_value == 0 and lenders:
                            total_value = sum(l.get('estimated_value', 0) for l in lenders)
                        if total_claims == 0 and lenders:
                            total_claims = sum(l.get('num_claims', 0) for l in lenders)

                        # Structure data for dashboard
                        st.session_state.data = {
                            'portfolio_metrics': {
                                'unique_clients_cumulative': pm.get('unique_clients', 0),
                                'unique_claims_cumulative': pm.get('unique_claims', 0),
                                'claims_submitted': pm.get('claims_submitted', 0),
                                'claims_successful': pm.get('claims_successful', 0),
                                'claims_rejected': pm.get('claims_rejected', 0),
                                'avg_claim_value': pm.get('avg_claim_value', 0),
                                'success_rate': pm.get('success_rate', 0)
                            },
                            'lender_distribution': lenders,
                            'pipeline': pipeline,
                            'financial_costs': {
                                'total_costs': fm.get('total_costs', 0),
                                'acquisition_cost_cumulative': fm.get('acquisition_cost', 0),
                                'submission_cost_cumulative': fm.get('submission_cost', 0),
                                'cost_per_claim': fm.get('cost_per_claim', 0)
                            },
                            'portfolio_totals': {
                                'total_claims': total_claims,
                                'total_estimated_value': total_value
                            },
                            'reporting_period': monthly_data.get('reporting_period', 'Monthly Report'),
                            # Store raw agent data for report generation
                            '_agent_monthly_data': monthly_data
                        }

                        # Get captured debug output
                        debug_output = captured_output.getvalue()
                        sys.stdout = old_stdout

                        # Store debug output in session state
                        st.session_state.debug_output = debug_output

                        st.success(f"✅ AI Agent extracted data: {total_claims} claims, {len(lenders)} lenders, £{total_value:,.0f} portfolio value")

                        # Show debug info in expander
                        if debug_output:
                            with st.expander("🔍 Debug Information (for troubleshooting)"):
                                st.code(debug_output)

                        st.rerun()
                    except Exception as e:
                        sys.stdout = old_stdout
                        st.error(f"Error loading data: {e}")
                        st.exception(e)

    # Display data if loaded
    if st.session_state.data:
        data = st.session_state.data

        # Show debug output if available
        if 'debug_output' in st.session_state and st.session_state.debug_output:
            with st.expander("🔍 Debug Information (click to view)"):
                st.code(st.session_state.debug_output)

                # Check for common errors in debug output
                if "ERROR:" in st.session_state.debug_output:
                    st.error("⚠️ **File Format Error Detected**")
                    if "only" in st.session_state.debug_output and "rows" in st.session_state.debug_output:
                        st.warning("""
                        **The uploaded Excel file appears to be incomplete or in a different format.**

                        **Expected format:**
                        - File should have 100+ rows
                        - Sheet name: "Monthly Summary"
                        - Lender data starting at row 27
                        - Grand totals at row 87

                        **Please ensure you're uploading the complete Milberg Monthly Report Excel file.**
                        """)
                        st.info("💡 **Tip:** Check that you're uploading the file named 'Milberg_MOnthly_Report.xlsx' with the full dataset.")

        # Safely get data with defaults
        portfolio = data.get('portfolio_metrics', {})
        lenders = data.get('lender_distribution', [])
        costs = data.get('financial_costs', {})
        pipeline = data.get('pipeline', {})
        totals = data.get('portfolio_totals', {'total_claims': 0, 'total_estimated_value': 0})

        # Fallback calculations if totals are missing but lenders exist
        if totals.get('total_claims', 0) == 0 and lenders:
            totals['total_claims'] = sum(l.get('num_claims', 0) for l in lenders)
        if totals.get('total_estimated_value', 0) == 0 and lenders:
            totals['total_estimated_value'] = sum(l.get('estimated_value', 0) for l in lenders)

        # Debug info for troubleshooting
        print(f"DASHBOARD DEBUG: total_claims={totals.get('total_claims')}, total_value={totals.get('total_estimated_value')}")
        print(f"DASHBOARD DEBUG: clients_cum={portfolio.get('unique_clients_cumulative')}, lenders={len(lenders)}")

        # Calculate financials using 20-80 split (Milberg 20% / Funder 80%)
        # Split is on GROSS DBA proceeds, NOT net proceeds after costs
        total_settlement = totals.get('total_estimated_value', 0)
        total_costs = costs.get('total_costs', 0)
        dba_rate = 0.30  # 30% DBA rate
        funder_pct = 0.80  # Funder gets 80% of DBA proceeds
        firm_pct = 0.20  # Milberg gets 20% of DBA proceeds

        dba_proceeds = total_settlement * dba_rate
        # Funder and Milberg split the GROSS DBA proceeds (not net after costs)
        funder_return = dba_proceeds * funder_pct
        firm_return = dba_proceeds * firm_pct

        financials = {
            'total_settlement': total_settlement,
            'dba_proceeds': dba_proceeds,
            'total_costs': total_costs,
            'funder_return': funder_return,
            'firm_return': firm_return,
            # ROI = (Return - Investment) / Investment * 100
            # MOIC = Return / Investment
            'roi': ((funder_return - total_costs) / total_costs * 100) if total_costs > 0 else 0,
            'moic': (funder_return / total_costs) if total_costs > 0 else 0
        }

        st.markdown("---")

        # NEW: Monthly Investor Report (OpenAI Agent)
        st.subheader("📄 Monthly Investor Report")

        col_r1, col_r2, col_r3, col_r4 = st.columns([1, 1, 1, 1])

        with col_r1:
            generate_clicked = st.button("🧠 Generate Reports (Word + PowerPoint)", type="primary")

        with col_r2:
            if st.session_state.investor_report_docx_bytes:
                st.download_button(
                    label="📄 Download Word Report",
                    data=st.session_state.investor_report_docx_bytes,
                    file_name=os.path.basename(st.session_state.investor_report_docx_path or "monthly_investor_report.docx"),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            else:
                st.caption("Click Generate to create reports")

        with col_r3:
            if st.session_state.investor_report_pptx_bytes:
                st.download_button(
                    label="📊 Download PowerPoint",
                    data=st.session_state.investor_report_pptx_bytes,
                    file_name=os.path.basename(st.session_state.investor_report_pptx_path or "monthly_investor_report.pptx"),
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True,
                )
            elif st.session_state.investor_report_docx_bytes:
                # DOCX was generated but PPTX failed - show warning
                st.warning("⚠️ PowerPoint unavailable")
                with st.expander("Why?"):
                    st.caption("python-pptx library may not be installed. Check requirements.txt includes 'python-pptx'.")
            else:
                st.caption("Click Generate to create reports")

        with col_r4:
            import sys
            st.caption(
                "Uses the bundled OpenAI multi-agent system (`intelligent_agents.generate_full_investor_report`). "
                "Requires `OPENAI_API_KEY` env var or Streamlit secret."
            )
            with st.expander("Report generation environment"):
                import os as _os
                st.code(
                    "\n".join(
                        [
                            f"python: {sys.executable}",
                            f"platform: {sys.platform}",
                            f"cwd: {_os.getcwd()}",
                            f"OPENAI_API_KEY set: {bool(_os.environ.get('OPENAI_API_KEY'))}",
                        ]
                    )
                )
                try:
                    import kaleido as _k
                    st.success(f"kaleido available: {getattr(_k, '__version__', 'unknown')}")
                except Exception as e:
                    st.error(f"kaleido NOT available: {type(e).__name__}: {e}")
                try:
                    import plotly as _plotly
                    st.caption(f"plotly version: {getattr(_plotly, '__version__', 'unknown')}")
                except Exception as e:
                    st.caption(f"plotly version: unknown ({type(e).__name__}: {e})")

        if generate_clicked:
            if generate_full_investor_report is None:
                st.error("Investor report agent system is not available (failed to import `intelligent_agents`).")
            elif not st.session_state.last_uploaded_excel_path or not os.path.exists(st.session_state.last_uploaded_excel_path):
                st.error("No uploaded Excel detected. Please upload and load a Monthly Report first.")
            else:
                # Check API key early for clearer UX
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    try:
                        api_key = st.secrets.get("OPENAI_API_KEY")
                    except Exception:
                        api_key = None
                if not api_key:
                    st.error("OPENAI_API_KEY is not set. Add it as an environment variable or to Streamlit secrets.")
                else:
                    try:
                        with st.spinner("Generating investor report with OpenAI agents..."):
                            result = generate_full_investor_report(st.session_state.last_uploaded_excel_path)

                            # Keep markdown preview if returned
                            st.session_state.investor_report_md = result.get("markdown_report")

                            # Prefer DOCX report from agent system
                            docx_path = result.get("docx_report_path")
                            if not docx_path or not os.path.exists(docx_path):
                                raise ValueError("Agent did not produce a DOCX report (docx_report_path missing)")

                            with open(docx_path, "rb") as f:
                                st.session_state.investor_report_docx_bytes = f.read()
                            st.session_state.investor_report_docx_path = docx_path

                            # Persist path for compatibility
                            st.session_state.investor_report_path = docx_path

                            # Load PowerPoint report if available
                            pptx_path = result.get("pptx_report_path")
                            if pptx_path and os.path.exists(pptx_path):
                                with open(pptx_path, "rb") as f:
                                    st.session_state.investor_report_pptx_bytes = f.read()
                                st.session_state.investor_report_pptx_path = pptx_path

                        st.success("Investor report generated.")

                        if st.session_state.investor_report_md:
                            with st.expander("Preview report (markdown)"):
                                st.markdown(st.session_state.investor_report_md)

                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate investor report: {e}")
                        st.info(
                            "If charts are missing, install 'kaleido'. If this is an API key issue, set `OPENAI_API_KEY` as an environment variable or in Streamlit secrets."
                        )

        st.markdown("---")

        # KPI Dashboard - Split Funder Return into LP (80%) and GP (20%)
        # The DBA proceeds are split 80/20 between Funder (LP) and Milberg (GP)
        lp_return = financials['funder_return']  # 80% of DBA proceeds
        gp_return = financials['firm_return']    # 20% of DBA proceeds

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            st.metric("Total Claims", f"{totals.get('total_claims', 0):,}")

        with col2:
            st.metric("Total Clients", f"{portfolio.get('unique_clients_cumulative', 0):,}")

        with col3:
            st.metric("Lenders", f"{len(lenders)}")

        with col4:
            st.metric("Portfolio Value", f"£{totals.get('total_estimated_value', 0)/1000:.0f}K")

        with col5:
            st.metric("LP Return (80%)", f"£{lp_return/1000:.1f}K")

        with col6:
            st.metric("GP Return (20%)", f"£{gp_return/1000:.1f}K")

        st.markdown("---")

        # Main Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏦 Lenders",
            "💰 Economic Analysis",
            "⚖️ Compliance & Pipeline",
            "📊 Portfolio Analysis"
        ])

        # ==================== TAB 1: LENDERS ====================
        with tab1:
            st.header("Lender Distribution & Analysis")

            # Check if we have lender data
            if not lenders or len(lenders) == 0:
                st.warning("⚠️ No lender data found in the Excel file.")
                st.info("Please make sure the uploaded file contains lender information in the expected format.")
            else:
                # Sort lenders by number of claims
                df_lenders = pd.DataFrame(lenders).sort_values('num_claims', ascending=False)

                col1, col2 = st.columns([1, 1])
    
                with col1:
                    # Network graph (Instagram-style)
                    st.subheader("Lender Network Visualization")
    
                    # Create network graph
                    fig = go.Figure()
    
                    # Top 15 lenders for cleaner visualization
                    top_lenders = df_lenders.head(15)
    
                    # Calculate positions in a circle
                    import math
                    n = len(top_lenders)
                    angles = [2 * math.pi * i / n for i in range(n)]
    
                    # Add edges (lines from center to each lender)
                    for i, (idx, lender) in enumerate(top_lenders.iterrows()):
                        x_pos = math.cos(angles[i]) * (lender['num_claims'] / df_lenders['num_claims'].max())
                        y_pos = math.sin(angles[i]) * (lender['num_claims'] / df_lenders['num_claims'].max())
    
                        # Line from center to lender
                        fig.add_trace(go.Scatter(
                            x=[0, x_pos],
                            y=[0, y_pos],
                            mode='lines',
                            line=dict(color='lightgray', width=1),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
    
                        # Lender node
                        fig.add_trace(go.Scatter(
                            x=[x_pos],
                            y=[y_pos],
                            mode='markers+text',
                            marker=dict(
                                size=lender['num_claims'] * 3,
                                color=lender['num_claims'],
                                colorscale='Viridis',
                                showscale=False,
                                line=dict(width=2, color='white')
                            ),
                            text=[lender['lender'][:20]],
                            textposition='top center',
                            textfont=dict(size=8),
                            hovertemplate=f"<b>{lender['lender']}</b><br>" +
                                        f"Claims: {lender['num_claims']}<br>" +
                                        f"Value: £{lender['estimated_value']:,.0f}<br>" +
                                        f"Share: {lender['pct_of_total']:.1f}%<extra></extra>",
                            showlegend=False
                        ))
    
                    # Center node
                    fig.add_trace(go.Scatter(
                        x=[0],
                        y=[0],
                        mode='markers+text',
                        marker=dict(size=30, color='red', symbol='star'),
                        text=['Portfolio<br>180 Claims'],
                        textposition='middle center',
                        textfont=dict(size=10, color='white'),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
    
                    fig.update_layout(
                        title="Top 15 Lenders - Network View",
                        showlegend=False,
                        height=600,
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
    
                    st.plotly_chart(fig, use_container_width=True)
    
                with col2:
                    # Top 10 Pie Chart
                    st.subheader("Top 10 Lenders by Claims")
    
                    top10 = df_lenders.head(10)
                    others_claims = df_lenders.iloc[10:]['num_claims'].sum()
    
                    if others_claims > 0:
                        pie_data = pd.concat([
                            top10[['lender', 'num_claims']],
                            pd.DataFrame([{'lender': 'Others', 'num_claims': others_claims}])
                        ])
                    else:
                        pie_data = top10[['lender', 'num_claims']]
    
                    fig_pie = px.pie(
                        pie_data,
                        values='num_claims',
                        names='lender',
                        hole=0.4
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie.update_layout(height=600, showlegend=True)
    
                    st.plotly_chart(fig_pie, use_container_width=True)
    
                # Lender Data Table
                st.subheader("Complete Lender Data")
    
                # Format the dataframe
                df_display = df_lenders.copy()
                df_display['estimated_value'] = df_display['estimated_value'].apply(lambda x: f"£{x:,.2f}")
                df_display['avg_claim_value'] = df_display['avg_claim_value'].apply(lambda x: f"£{x:,.2f}")
                df_display['pct_of_total'] = df_display['pct_of_total'].apply(lambda x: f"{x:.1f}%")
    
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "lender": st.column_config.TextColumn("Lender", width="large"),
                        "num_claims": st.column_config.NumberColumn("Claims", width="small"),
                        "pct_of_total": st.column_config.TextColumn("% of Total", width="small"),
                        "estimated_value": st.column_config.TextColumn("Est. Value", width="medium"),
                        "avg_claim_value": st.column_config.TextColumn("Avg/Claim", width="medium")
                    }
                )
    
                # Top 15 Horizontal Bar Chart
                st.subheader("Top 15 Lenders by Portfolio Value")
    
                top15_value = df_lenders.head(15).sort_values('estimated_value')
    
                fig_bar = px.bar(
                    top15_value,
                    x='estimated_value',
                    y='lender',
                    orientation='h',
                    color='num_claims',
                    color_continuous_scale='Blues',
                    text=[f"£{v:,.0f}" for v in top15_value['estimated_value']]
                )
    
                fig_bar.update_traces(textposition='outside')
                fig_bar.update_layout(
                    height=600,
                    xaxis_title="Portfolio Value (£)",
                    yaxis_title="",
                    yaxis={'categoryorder':'total ascending'},
                    showlegend=False
                )
    
                st.plotly_chart(fig_bar, use_container_width=True)
    
        # ==================== TAB 2: ECONOMIC ANALYSIS ====================
        with tab2:
            st.header("Economic Analysis & Profit Distribution")

            # Financial Overview Cards
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Settlement Value", f"£{financials['total_settlement']:,.2f}")
                st.caption("Estimated portfolio value")

            with col2:
                st.metric("DBA Proceeds (30%)", f"£{financials['dba_proceeds']:,.2f}")
                st.caption("Revenue from settlements")

            with col3:
                st.metric("Total Costs", f"£{financials['total_costs']:,.2f}")
                st.caption("All operational costs")

            st.markdown("---")

            # NUMERIC DATA TABLE - Economic Summary
            st.subheader("📊 Financial Summary Table")
            financial_table = pd.DataFrame({
                'Metric': [
                    'Total Settlement Value',
                    'DBA Proceeds (30%)',
                    'Total Costs Incurred',
                    'LP Return (80% of DBA)',
                    'GP Return (20% of DBA)',
                    'ROI',
                    'MOIC'
                ],
                'Value': [
                    f"£{financials['total_settlement']:,.2f}",
                    f"£{financials['dba_proceeds']:,.2f}",
                    f"£{financials['total_costs']:,.2f}",
                    f"£{financials['funder_return']:,.2f}",
                    f"£{financials['firm_return']:,.2f}",
                    f"{financials['roi']:.1f}%",
                    f"{financials['moic']:.2f}x"
                ]
            })
            st.dataframe(financial_table, use_container_width=True, hide_index=True)

            st.markdown("---")

            # Waterfall Chart
            st.subheader("Financial Waterfall Analysis")

            fig_waterfall = go.Figure(go.Waterfall(
                name="Cash Flow",
                orientation="v",
                measure=["absolute", "relative", "relative", "total"],
                x=["Settlement Value", "DBA Fee (30%)", "Less: Costs", "LP Return"],
                y=[
                    financials['total_settlement'],
                    financials['dba_proceeds'] - financials['total_settlement'],
                    -financials['total_costs'],
                    financials['funder_return']
                ],
                text=[
                    f"£{financials['total_settlement']:,.0f}",
                    f"£{financials['dba_proceeds']:,.0f}",
                    f"-£{financials['total_costs']:,.0f}",
                    f"£{financials['funder_return']:,.0f}"
                ],
                textposition="outside",
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                increasing={"marker": {"color": "#2ecc71"}},
                decreasing={"marker": {"color": "#e74c3c"}},
                totals={"marker": {"color": "#3498db"}}
            ))

            fig_waterfall.update_layout(
                title="From Settlement to LP Return",
                height=500,
                showlegend=False
            )

            st.plotly_chart(fig_waterfall, use_container_width=True)

            st.markdown("---")

            # Profit Distribution
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("Profit Distribution (Priority Deed)")

                # Profit split pie chart - LP (Funder) and GP (Milberg)
                fig_split = go.Figure(data=[go.Pie(
                    labels=['LP (80%)', 'GP (20%)'],
                    values=[financials['funder_return'], financials['firm_return']],
                    hole=0.4,
                    marker_colors=['#3498db', '#2ecc71'],
                    text=[
                        f"£{financials['funder_return']:,.0f}",
                        f"£{financials['firm_return']:,.0f}"
                    ],
                    textinfo='label+text',
                    textposition='inside'
                )])

                fig_split.update_layout(
                    height=400,
                    annotations=[dict(
                        text=f'DBA Proceeds<br>£{financials["dba_proceeds"]:,.0f}',
                        x=0.5, y=0.5,
                        font_size=14,
                        showarrow=False
                    )]
                )

                st.plotly_chart(fig_split, use_container_width=True)

                st.info("""
                **Priority Deed Terms:**
                - DBA Rate: 30% of settlements
                - Split: 80/20 (LP/GP) on GROSS DBA proceeds
                - LP = Limited Partner (Funder), GP = General Partner (Milberg)
                - Costs paid separately by LP
                """)

            with col2:
                st.subheader("Performance Metrics")

                # ROI and MOIC with LP/GP terminology
                metrics_df = pd.DataFrame({
                    'Metric': ['LP Return', 'GP Return', 'ROI', 'MOIC'],
                    'Value': [
                        f"£{financials['funder_return']:,.2f}",
                        f"£{financials['firm_return']:,.2f}",
                        f"{financials['roi']:.1f}%",
                        f"{financials['moic']:.2f}x"
                    ],
                    'Description': [
                        '80% of GROSS DBA proceeds (Funder)',
                        '20% of GROSS DBA proceeds (Milberg)',
                        'Return on Investment',
                        'Multiple on Invested Capital'
                    ]
                })

                st.dataframe(metrics_df, use_container_width=True, hide_index=True)

                # Cost Breakdown
                st.subheader("Cost Breakdown")

                # Check if cost data is available
                if not costs or 'acquisition_cost_cumulative' not in costs:
                    st.warning("⚠️ Financial cost data not available in the Excel file.")
                    cost_data = pd.DataFrame({
                        'Category': ['Acquisition', 'Submission', 'Processing', 'Legal'],
                        'Amount': [0, 0, 0, 0]
                    })
                else:
                    cost_data = pd.DataFrame({
                        'Category': ['Acquisition', 'Submission', 'Processing', 'Legal'],
                        'Amount': [
                            costs.get('acquisition_cost_cumulative', 0),
                            costs.get('submission_cost_cumulative', 0),
                            costs.get('processing_cost', 0),
                            costs.get('legal_cost', 0)
                        ]
                    })

                fig_costs = px.bar(
                    cost_data,
                    x='Category',
                    y='Amount',
                    text=[f"£{v:,.2f}" for v in cost_data['Amount']],
                    color='Amount',
                    color_continuous_scale='Reds'
                )

                fig_costs.update_traces(textposition='outside')
                fig_costs.update_layout(height=350, showlegend=False)

                st.plotly_chart(fig_costs, use_container_width=True)

        # ==================== TAB 3: COMPLIANCE & PIPELINE ====================
        with tab3:
            st.header("Pipeline Status & Compliance")

            # Pipeline Overview
            st.subheader("Claims Pipeline by Stage")

            # Safe access to pipeline data with defaults
            def get_pipeline_stage(stage_name):
                stage = pipeline.get(stage_name, {})
                return {'count': stage.get('count', 0), 'value': stage.get('value', 0)}

            pipeline_data = pd.DataFrame([
                {'Stage': 'Awaiting DSAR', **get_pipeline_stage('awaiting_dsar')},
                {'Stage': 'Pending Submission', **get_pipeline_stage('pending_submission')},
                {'Stage': 'Under Review', **get_pipeline_stage('under_review')},
                {'Stage': 'Settlement Offered', **get_pipeline_stage('settlement_offered')},
                {'Stage': 'Paid', **get_pipeline_stage('paid')}
            ])
            pipeline_data = pipeline_data.rename(columns={'count': 'Count', 'value': 'Value'})

            col1, col2 = st.columns([1, 1])

            with col1:
                # Funnel chart
                fig_funnel = go.Figure(go.Funnel(
                    y=pipeline_data['Stage'],
                    x=pipeline_data['Count'],
                    textinfo="value+percent initial",
                    marker={"color": ["#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]}
                ))

                fig_funnel.update_layout(title="Pipeline Funnel (by Count)", height=500)

                st.plotly_chart(fig_funnel, use_container_width=True)

            with col2:
                # Stacked bar chart by value
                fig_pipeline_val = px.bar(
                    pipeline_data,
                    x='Stage',
                    y='Value',
                    text=[f"£{v:,.0f}" for v in pipeline_data['Value']],
                    color='Stage',
                    color_discrete_sequence=px.colors.qualitative.Set2
                )

                fig_pipeline_val.update_traces(textposition='outside')
                fig_pipeline_val.update_layout(
                    title="Pipeline Value by Stage",
                    height=500,
                    showlegend=False,
                    xaxis_title="",
                    yaxis_title="Value (£)"
                )

                st.plotly_chart(fig_pipeline_val, use_container_width=True)

            # Pipeline Data Table
            st.subheader("Pipeline Breakdown Data")

            pipeline_display = pipeline_data.copy()
            pipeline_display['Value'] = pipeline_display['Value'].apply(lambda x: f"£{x:.2f}")

            st.dataframe(pipeline_display, use_container_width=True, hide_index=True)

            st.markdown("---")

            # Portfolio Growth
            st.subheader("Portfolio Growth Metrics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Claims", totals.get('total_claims', 0))

            with col2:
                st.metric("Total Clients", portfolio.get('unique_clients_cumulative', 0))

            with col3:
                st.metric("Success Rate", f"{portfolio.get('success_rate', 0):.1f}%")

            with col4:
                st.metric("Total Lenders", len(lenders))

            # NUMERIC DATA TABLE - Portfolio Summary
            st.subheader("📊 Portfolio Summary Table")
            portfolio_table = pd.DataFrame({
                'Metric': [
                    'Total Claims',
                    'Total Clients',
                    'Total Lenders',
                    'Total Portfolio Value',
                    'Claims Submitted',
                    'Claims Successful',
                    'Claims Rejected',
                    'Average Claim Value',
                    'Success Rate'
                ],
                'Value': [
                    f"{totals.get('total_claims', 0):,}",
                    f"{portfolio.get('unique_clients_cumulative', 0):,}",
                    f"{len(lenders):,}",
                    f"£{totals.get('total_estimated_value', 0):,.2f}",
                    f"{portfolio.get('claims_submitted', 0):,}",
                    f"{portfolio.get('claims_successful', 0):,}",
                    f"{portfolio.get('claims_rejected', 0):,}",
                    f"£{portfolio.get('avg_claim_value', 0):,.2f}",
                    f"{portfolio.get('success_rate', 0):.1f}%"
                ]
            })
            st.dataframe(portfolio_table, use_container_width=True, hide_index=True)

        # ==================== TAB 4: PORTFOLIO ANALYSIS ====================
        with tab4:
            st.header("Comprehensive Portfolio Analysis")

            # Check if we have lender data
            if not lenders or len(lenders) == 0:
                st.warning("⚠️ No lender data available for portfolio analysis.")
            else:
                # Sort lenders if not already done
                if 'df_lenders' not in locals():
                    df_lenders = pd.DataFrame(lenders).sort_values('num_claims', ascending=False)

                # Concentration Analysis
                st.subheader("Lender Concentration Risk")

                # Calculate concentration
                top5_claims = df_lenders.head(5)['num_claims'].sum()
                top10_claims = df_lenders.head(10)['num_claims'].sum()
                concentration_top5 = (top5_claims / totals['total_claims']) * 100
                concentration_top10 = (top10_claims / totals['total_claims']) * 100

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Top 5 Concentration", f"{concentration_top5:.1f}%")
                    st.caption(f"{top5_claims} claims out of {totals['total_claims']}")

                with col2:
                    st.metric("Top 10 Concentration", f"{concentration_top10:.1f}%")
                    st.caption(f"{top10_claims} claims out of {totals['total_claims']}")

                with col3:
                    diversification_score = 100 - concentration_top5
                    st.metric("Diversification Score", f"{diversification_score:.1f}/100")
                    st.caption("Higher is better")

                # Concentration risk indicator
                if concentration_top5 > 50:
                    st.warning("⚠️ High Concentration Risk: Top 5 lenders represent >50% of portfolio")
                elif concentration_top5 > 30:
                    st.info("ℹ️ Moderate Concentration: Top 5 lenders represent 30-50% of portfolio")
                else:
                    st.success("✅ Low Concentration: Well-diversified portfolio")

                st.markdown("---")

                # Claims Distribution
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.subheader("Claims Distribution by Lender Size")

                    # Categorize lenders
                    df_lenders['Category'] = pd.cut(
                        df_lenders['num_claims'],
                        bins=[0, 2, 5, 10, 999],
                        labels=['Small (1-2)', 'Medium (3-5)', 'Large (6-10)', 'Very Large (10+)']
                    )

                    category_dist = df_lenders.groupby('Category', observed=False).agg({
                        'num_claims': 'sum',
                        'lender': 'count'
                    }).reset_index()
                    category_dist.columns = ['Category', 'Total Claims', 'Number of Lenders']

                    fig_cat = px.bar(
                        category_dist,
                        x='Category',
                        y='Total Claims',
                        text='Total Claims',
                        color='Number of Lenders',
                        color_continuous_scale='Viridis'
                    )

                    fig_cat.update_traces(textposition='outside')
                    fig_cat.update_layout(height=400)

                    st.plotly_chart(fig_cat, use_container_width=True)

                with col2:
                    st.subheader("Value Distribution")

                    # Value ranges
                    df_lenders['Value_Category'] = pd.cut(
                        df_lenders['estimated_value'],
                        bins=[0, 2000, 5000, 10000, 999999],
                        labels=['<£2K', '£2-5K', '£5-10K', '>£10K']
                    )

                    value_dist = df_lenders.groupby('Value_Category', observed=False).agg({
                        'estimated_value': 'sum',
                        'lender': 'count'
                    }).reset_index()
                    value_dist.columns = ['Value Range', 'Total Value', 'Count']

                    fig_val = px.pie(
                        value_dist,
                        values='Total Value',
                        names='Value Range',
                        hole=0.4
                    )

                    fig_val.update_layout(height=400)

                    st.plotly_chart(fig_val, use_container_width=True)

                st.markdown("---")

                # Summary Statistics
                st.subheader("Portfolio Statistics Summary")

                stats_df = pd.DataFrame({
                    'Metric': [
                        'Total Lenders',
                        'Total Claims',
                        'Total Portfolio Value',
                        'Average Claims per Lender',
                        'Average Value per Lender',
                        'Largest Lender (by claims)',
                        'Largest Lender (by value)',
                        'Smallest Active Lender'
                    ],
                    'Value': [
                        f"{len(lenders)}",
                        f"{totals['total_claims']}",
                        f"£{totals['total_estimated_value']:,.2f}",
                        f"{totals['total_claims'] / len(lenders):.1f}",
                        f"£{totals['total_estimated_value'] / len(lenders):,.2f}",
                        f"{df_lenders.iloc[0]['lender']} ({df_lenders.iloc[0]['num_claims']} claims)",
                        f"{df_lenders.sort_values('estimated_value', ascending=False).iloc[0]['lender']} (£{df_lenders.sort_values('estimated_value', ascending=False).iloc[0]['estimated_value']:,.2f})",
                        f"{df_lenders.iloc[-1]['lender']} ({df_lenders.iloc[-1]['num_claims']} claims)"
                    ]
                })

                st.dataframe(stats_df, use_container_width=True, hide_index=True)

    else:
        st.info("👆 Please upload a Milberg Monthly Report Excel file to view the dashboard")

        # Logout button
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("*Milberg PCP Claims Dashboard • Direct Data Extraction • No AI Summaries*")
