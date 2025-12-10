# PCP Claims Analysis Dashboard - User Guide

## 🚀 Quick Start

### Launching the Dashboard

**Option 1: Using the batch file (Windows)**
```bash
run_dashboard.bat
```

**Option 2: Using command line**
```bash
streamlit run milberg_streamlit_demo.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`

---

## 📊 Dashboard Features

### 1. **Overview Tab** - Financial Summary
- **Waterfall Chart**: Visual representation of fund flows
  - Total funding provided
  - Outstanding funding
  - DBA proceeds received
  - Net position
- **Funder vs Milberg Share**: Pie chart showing profit distribution
- **Key Financial Metrics Table**: All important financial figures at a glance

### 2. **Eligibility Analysis Tab** - FCA Compliance
- **Eligibility Status Pie Chart**: Visual breakdown of eligible vs non-eligible claims
- **Recommendation Distribution**: Bar chart showing approval/review/reject recommendations
- **Eligibility Summary Table**: Quick view of all claims with:
  - Claim ID
  - Eligibility status (✅/❌)
  - Recommendation
  - Commission threshold check
  - Date eligibility check

### 3. **Bundle Tracker Tab** - Bundle Performance
- **Funding by Bundle**: Bar chart showing funding drawn per bundle
- **DBA Proceeds by Bundle**: Bar chart showing proceeds received per bundle
- **Bundle Details Table**: Comprehensive table with:
  - Bundle ID
  - Number of claimants
  - Funding drawn
  - DBA proceeds
  - Funder share
  - Current status

### 4. **Claims Detail Tab** - Individual Claim Analysis

#### View Mode: All Claims
- Filterable table showing all claims
- Filter by eligibility status
- Columns include:
  - Claim ID
  - Claimant name
  - Defendant
  - Claim amount
  - Funded amount
  - Eligibility status
  - Recommendation

#### View Mode: Single Claim
Select any claim to see:
- **Basic Information**:
  - Claimant details
  - Defendant information
  - Law firm
  - Current status

- **Financial Details**:
  - Claim amount
  - Funded amount
  - Potential return

- **FCA Eligibility Assessment**:
  - Overall eligibility status (✅ ELIGIBLE / ❌ NOT ELIGIBLE)
  - Recommendation
  - Detailed compliance checks:
    - ✅ Date eligibility
    - ✅ Product type
    - ✅ Commission threshold (Plevin test)
    - ✅ Limitation period
  - Detailed reasons (expandable)
  - Warnings (if any)

### 5. **Export Report Tab** - Download Analysis

#### DOCX Report
- Comprehensive Word document including:
  - Executive summary
  - Portfolio summary
  - FCA eligibility summary
  - Detailed claim analysis
  - Bundle tracker summary
- Click "Generate DOCX Report" button
- Download directly from browser

#### JSON Export
- Raw data export for further analysis
- Contains all analysis data including:
  - Claim eligibility results
  - Portfolio summary
  - Bundle tracker data
  - Profit calculations (if available)

---

## 📈 Key Metrics Explained

### Top-Level Metrics (Always Visible)

1. **Total Claims**: Number of claims found and processed
2. **Total Funding**: Total amount funded with outstanding balance
3. **DBA Proceeds**: Total DBA proceeds received and funder's share
4. **FCA Eligibility Rate**: Percentage of claims meeting FCA eligibility criteria

### FCA Eligibility Criteria

The system automatically checks each claim against:

1. **Date Eligibility**: Agreement date between 2007-04-06 and 2021-01-28
2. **Product Type**: Must be PCP, HP, CS, or PCH
3. **Commission Threshold (Plevin Test)**: Commission ≥ 50% of cost of credit
4. **Limitation Period**: Claim submitted within limitation period (6 years)

**Recommendations**:
- ✅ **APPROVE**: All checks passed, eligible for redress
- ⚠️ **REVIEW**: Some concerns, requires manual review
- ❌ **REJECT**: Does not meet eligibility criteria

---

## 🎨 Visual Elements

### Color Coding

- **Green** (✅): Eligible, approved, passed checks
- **Red** (❌): Not eligible, failed checks
- **Blue**: Neutral information, financial metrics
- **Orange/Yellow** (⚠️): Warnings, requires review

### Charts

All charts are interactive:
- **Hover** for detailed information
- **Click and drag** to zoom
- **Double-click** to reset zoom
- **Click legend items** to show/hide data series

---

## 💡 Tips for Best Results

1. **Upload the Latest Report**: Always use the most recent Milberg monthly report
2. **Check Eligibility Tab First**: Review FCA compliance before detailed analysis
3. **Use Filters**: In Claims Detail tab, filter by eligibility status to focus on specific claims
4. **Export Regularly**: Download DOCX reports for record-keeping and stakeholder sharing
5. **Review Warnings**: Pay attention to warnings in individual claim details

---

## 🔧 Troubleshooting

### Dashboard won't start
- Ensure all dependencies are installed: `pip install streamlit pandas plotly openpyxl python-docx`
- Check if port 8501 is available

### Charts not displaying
- Refresh the browser
- Check browser console for errors
- Ensure plotly is installed: `pip install plotly`

### File upload fails
- Ensure file is in correct Excel format (.xlsx)
- Check that file contains required sheets: "Portfolio Summary", "Bundle Tracker"
- Verify bundle sheets are named "Bundle_XXX" format

### Eligibility showing "Not Eligible" unexpectedly
- Check if commission percentage is properly populated in Excel
- Verify agreement date is in correct format (YYYY-MM-DD or DD/MM/YYYY)
- Ensure product type is one of: PCP, HP, CS, PCH

---

## 📞 Support

For issues or questions:
1. Check the console output for error messages
2. Review the Excel file format requirements
3. Ensure all required columns are present in the Excel file

---

## 🔄 Updates and Improvements

Recent enhancements:
- ✅ Fixed commission percentage reading (decimal to percentage conversion)
- ✅ Added comprehensive FCA eligibility validation
- ✅ Enhanced visual dashboard with multiple tabs
- ✅ Interactive charts with Plotly
- ✅ Detailed claim-level views with filters
- ✅ Improved DOCX report generation

---

*Last updated: December 2024*
