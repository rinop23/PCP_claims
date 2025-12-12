"""
Milberg PCP Claims Dashboard - Data Visualization Focused
Shows ACTUAL numbers and graphs, not AI summaries
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import hashlib
from data_extractor import extract_monthly_report_data, read_priority_deed_rules, calculate_financial_projections
from datetime import datetime

# NEW: OpenAI agent-based investor report generation
try:
    from intelligent_agents import generate_full_investor_report
except Exception:
    generate_full_investor_report = None

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

        if st.button("📊 Load Data", type="primary"):
            with st.spinner("Loading data from Excel..."):
                import sys
                from io import StringIO

                # Capture print output for debugging
                old_stdout = sys.stdout
                sys.stdout = captured_output = StringIO()

                try:
                    st.session_state.data = extract_monthly_report_data(temp_path)

                    # Get captured debug output
                    debug_output = captured_output.getvalue()
                    sys.stdout = old_stdout

                    # Store debug output in session state
                    st.session_state.debug_output = debug_output

                    st.success("Data loaded successfully!")

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

        # Get Priority Deed rules and calculate financials
        priority_deed = read_priority_deed_rules()
        financials = calculate_financial_projections(totals, costs, priority_deed)

        st.markdown("---")

        # NEW: Monthly Investor Report (OpenAI Agent)
        st.subheader("📄 Monthly Investor Report")

        col_r1, col_r2, col_r3 = st.columns([1, 1, 2])

        with col_r1:
            generate_clicked = st.button("🧠 Generate Investor Report", type="primary")

        with col_r2:
            if st.session_state.investor_report_md:
                st.download_button(
                    label="⬇️ Download Report (Markdown)",
                    data=st.session_state.investor_report_md.encode("utf-8"),
                    file_name=os.path.basename(st.session_state.investor_report_path or "monthly_investor_report.md"),
                    mime="text/markdown",
                    use_container_width=True,
                )
            else:
                st.caption("Generate the report to enable download")

        with col_r3:
            st.caption(
                "Uses the bundled OpenAI multi-agent system (`intelligent_agents.generate_full_investor_report`). "
                "Requires `OPENAI_API_KEY` env var or Streamlit secret."
            )

        if generate_clicked:
            if generate_full_investor_report is None:
                st.error("Investor report agent system is not available (failed to import `intelligent_agents`).")
            elif not st.session_state.last_uploaded_excel_path or not os.path.exists(st.session_state.last_uploaded_excel_path):
                st.error("No uploaded Excel detected. Please upload and load a Monthly Report first.")
            else:
                try:
                    with st.spinner("Generating investor report with OpenAI agents..."):
                        result = generate_full_investor_report(st.session_state.last_uploaded_excel_path)
                        md = result.get("markdown_report")
                        if not md:
                            raise ValueError("Agent did not return markdown_report")

                        # Persist in session
                        st.session_state.investor_report_md = md

                        # Write to disk for retention
                        os.makedirs("reports", exist_ok=True)
                        period = (
                            (result.get("monthly_data") or {}).get("reporting_period")
                            or datetime.now().strftime("%Y-%m")
                        )
                        safe_period = str(period).replace("/", "-").replace("\\", "-").replace(":", "-")
                        out_path = os.path.join("reports", f"Investor_Report_{safe_period}.md")
                        with open(out_path, "w", encoding="utf-8") as f:
                            f.write(md)
                        st.session_state.investor_report_path = out_path

                    st.success("Investor report generated.")

                    with st.expander("Preview report"):
                        st.markdown(st.session_state.investor_report_md)

                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate investor report: {e}")
                    st.info(
                        "If this is an API key issue, set `OPENAI_API_KEY` as an environment variable or in Streamlit secrets."
                    )

        st.markdown("---")

        # KPI Dashboard
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Claims", f"{totals['total_claims']:,}")

        with col2:
            st.metric("Total Clients", f"{portfolio['unique_clients_cumulative']:,}")

        with col3:
            st.metric("Lenders", f"{len(lenders)}")

        with col4:
            st.metric("Portfolio Value", f"£{totals['total_estimated_value']/1000:.0f}K")

        with col5:
            st.metric("Funder Return", f"£{financials['funder_return']/1000:.1f}K")

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
                st.metric("Total Settlement Value", f"£{financials['total_settlement_value']:,.2f}")
                st.caption("Estimated portfolio value")

            with col2:
                st.metric("DBA Proceeds (30%)", f"£{financials['dba_proceeds']:,.2f}")
                st.caption("Revenue from settlements")

            with col3:
                st.metric("Total Costs", f"£{financials['total_costs']:,.2f}")
                st.caption("All operational costs")

            st.markdown("---")

            # Waterfall Chart
            st.subheader("Financial Waterfall Analysis")

            fig_waterfall = go.Figure(go.Waterfall(
                name="Cash Flow",
                orientation="v",
                measure=["absolute", "relative", "relative", "total"],
                x=["Settlement Value", f"DBA Fee ({priority_deed['dba_rate']}%)", "Less: Costs", "Net Proceeds"],
                y=[
                    financials['total_settlement_value'],
                    financials['dba_proceeds'] - financials['total_settlement_value'],
                    -financials['total_costs'],
                    financials['net_proceeds']
                ],
                text=[
                    f"£{financials['total_settlement_value']:,.0f}",
                    f"£{financials['dba_proceeds']:,.0f}",
                    f"-£{financials['total_costs']:,.0f}",
                    f"£{financials['net_proceeds']:,.0f}"
                ],
                textposition="outside",
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                increasing={"marker": {"color": "#2ecc71"}},
                decreasing={"marker": {"color": "#e74c3c"}},
                totals={"marker": {"color": "#3498db"}}
            ))

            fig_waterfall.update_layout(
                title="From Settlement to Net Proceeds",
                height=500,
                showlegend=False
            )

            st.plotly_chart(fig_waterfall, use_container_width=True)

            st.markdown("---")

            # Profit Distribution
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("Profit Distribution (Priority Deed)")

                # Profit split pie chart
                fig_split = go.Figure(data=[go.Pie(
                    labels=[
                        f'Funder ({priority_deed["funder_percentage"]}%)',
                        f'Law Firm ({priority_deed["firm_percentage"]}%)'
                    ],
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
                        text=f'Net Proceeds<br>£{financials["net_proceeds"]:,.0f}',
                        x=0.5, y=0.5,
                        font_size=14,
                        showarrow=False
                    )]
                )

                st.plotly_chart(fig_split, use_container_width=True)

                st.info(f"""
                **Priority Deed Terms:**
                - DBA Rate: {priority_deed['dba_rate']}% of settlements
                - Split: {priority_deed['funder_percentage']}/{priority_deed['firm_percentage']} after costs
                - Cost recovery: First priority
                """)

            with col2:
                st.subheader("Performance Metrics")

                # ROI and MOIC
                metrics_df = pd.DataFrame({
                    'Metric': ['Funder Return', 'Firm Return', 'ROI', 'MOIC'],
                    'Value': [
                        f"£{financials['funder_return']:,.2f}",
                        f"£{financials['firm_return']:,.2f}",
                        f"{financials['roi']:.1f}%",
                        f"{financials['moic']:.2f}x"
                    ],
                    'Description': [
                        '80% of net proceeds',
                        '20% of net proceeds',
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

            pipeline_data = pd.DataFrame([
                {'Stage': 'Awaiting DSAR', 'Count': pipeline['awaiting_dsar']['count'], 'Value': pipeline['awaiting_dsar']['value']},
                {'Stage': 'Pending Submission', 'Count': pipeline['pending_submission']['count'], 'Value': pipeline['pending_submission']['value']},
                {'Stage': 'Under Review', 'Count': pipeline['under_review']['count'], 'Value': pipeline['under_review']['value']},
                {'Stage': 'Settlement Offered', 'Count': pipeline['settlement_offered']['count'], 'Value': pipeline['settlement_offered']['value']},
                {'Stage': 'Paid', 'Count': pipeline['paid']['count'], 'Value': pipeline['paid']['value']}
            ])

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
            pipeline_display['Value'] = pipeline_display['Value'].apply(lambda x: f"£{x:,.2f}")

            st.dataframe(pipeline_display, use_container_width=True, hide_index=True)

            st.markdown("---")

            # Portfolio Growth
            st.subheader("Portfolio Growth Metrics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Current Month Claims", portfolio['unique_claims_current'])

            with col2:
                st.metric("Current Month Clients", portfolio['unique_clients_current'])

            with col3:
                st.metric("Cumulative Claims", portfolio['unique_claims_cumulative'])

            with col4:
                st.metric("Cumulative Clients", portfolio['unique_clients_cumulative'])

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
