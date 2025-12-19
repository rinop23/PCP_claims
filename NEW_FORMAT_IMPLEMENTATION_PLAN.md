# Implementation Plan: New Excel Format + Priority Deed Integration

## Summary

The system needs to be updated to:
1. **Parse the new Excel format** (Milberg Monthly Report)
2. **Extract Priority Deed profit split** information
3. **Display both in dashboard and DOCX reports**

---

## ✅ Completed

1. **New Excel Parser Created** (`new_excel_parser.py`)
   - Extracts: Portfolio Overview, Claim Pipeline, Lender Distribution, Financial Utilisation, Forecasting, Risks & Compliance
   - Tested and working

2. **Priority Deed Waterfall Extracted**
   - 80% to Funder (after costs)
   - 20% to Firm (after costs)
   - 10% to Claims Processor (50% of Firm share)
   - 4-tier priority waterfall documented

---

## 🔄 Next Steps

### Step 1: Update Dashboard to Support Both Formats

The system should:
- Detect which format is being used (old vs new)
- Parse accordingly
- Display data appropriate to the format

### Step 2: Add New Tabs/Sections to Dashboard

**New sections needed:**
1. **Portfolio Metrics** - Current month vs cumulative
2. **Claim Pipeline Status** - Visual breakdown of stages
3. **Lender Distribution** - Who are the defendants
4. **Cost Analysis** - Acquisition, submission, processing, legal costs
5. **Forecasting** - Expected new clients, submissions, redress
6. **Compliance Dashboard** - Risks and KPIs

### Step 3: Add Priority Deed Profit Split Display

**In Dashboard:**
- New tab or sidebar section showing:
  - Waterfall diagram/flowchart
  - Percentage breakdowns
  - Payment priorities
  - Distribution frequency

**In DOCX Report:**
- New section: "Profit Distribution Structure"
  - Table showing waterfall priorities
  - Pie chart showing percentage splits
  - Notes on payment terms

---

## 📊 New Excel Format Structure

```
Section 1: Executive Summary
├── Reporting Period

Section 2: Portfolio Overview
├── Unique Clients (Current/Cumulative)
├── Unique Claims (Current/Cumulative)
├── Claims Submitted (Current/Cumulative)
├── Claims Successful (Current/Cumulative)
├── Claims Rejected (Current/Cumulative)
└── Average Claim Value (Current/Cumulative)

Section 3: Claim Pipeline Breakdown
├── Awaiting DSAR
├── Pending Submission
├── Under Review
├── Settlement Offered
└── Paid

Section 4: Lender Distribution Summary
└── [Dynamic list of lenders with claims count and value]

Section 5: Financial Utilisation Overview
├── Acquisition Cost (Current/Cumulative)
├── Submission Cost (Current/Cumulative)
├── Processing Cost (Current/Cumulative)
├── Legal Cost (Current/Cumulative)
├── Total Action Costs (Current/Cumulative)
└── Collection Account Balance (Current/Cumulative)

Section 6: Forecasting
├── Expected New Clients
├── Expected Submissions
└── Expected Redress

Section 7: Risks, Issues & Compliance
├── Infringement Events
├── Material Adverse Effects
└── Claims Processor KPI Status
```

---

## 💰 Priority Deed Profit Split

### Payment Waterfall (in order):

**Priority 1:** Outstanding Costs Sum → Funder
**Priority 2:** First Tier Funder Return → Funder
**Priority 3:** Distribution Costs Overrun → Firm (Milberg)
**Priority 4:** Net Proceeds Split:
- **80% → Funder**
- **20% → Firm (Milberg)**
  - Of this 20%, half (10% of total) → Claims Processor

### Visual Breakdown:

```
Net DBA Proceeds (100%)
    ↓
Pay Costs & Returns (Priority 1-3)
    ↓
Net Proceeds
    ├─ 80% → Funder
    └─ 20% → Firm
         ├─ 10% → Claims Processor
         └─ 10% → Firm (Milberg)
```

---

## 🔧 Implementation Code Structure

### Files to Update:

1. **`milberg_streamlit_demo.py`**
   - Add import for `new_excel_parser`
   - Add format detection logic
   - Create new dashboard sections
   - Add Priority Deed display
   - Update DOCX report generation

2. **`pcp_funding_agent.py`**
   - Add method to handle new format
   - Integrate Priority Deed information

3. **`new_excel_parser.py`** (Already created)
   - Contains parsing logic
   - Contains Priority Deed waterfall data

---

## 📱 Dashboard UI Mockup

```
┌─────────────────────────────────────────────────┐
│  PCP Claims Analysis Dashboard                  │
│  Logged in as: [Username]    [Logout]          │
├─────────────────────────────────────────────────┤
│                                                  │
│  📤 Upload Excel Report                         │
│  [Choose File] [Upload]                         │
│                                                  │
├─────────────────────────────────────────────────┤
│  📊 Overview | 📈 Portfolio | 📦 Pipeline |     │
│  💰 Financial | 📊 Lenders | 🔮 Forecast |      │
│  ⚠️ Compliance | 💸 Profit Split | 📄 Export   │
├─────────────────────────────────────────────────┤
│                                                  │
│  [PRIORITY DEED PROFIT DISTRIBUTION]            │
│                                                  │
│  Net Proceeds After Costs:                      │
│  ┌────────────────────────────────────┐        │
│  │ Funder:  80%  ████████████████████ │        │
│  │ Firm:    10%  ████████              │        │
│  │ Processor:10% ████████              │        │
│  └────────────────────────────────────┘        │
│                                                  │
│  Payment Priority:                              │
│  1️⃣  Outstanding Costs → Funder                │
│  2️⃣  First Tier Return → Funder                │
│  3️⃣  Cost Overrun → Firm                        │
│  4️⃣  Net Proceeds → 80/20 split                │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 🎯 User Experience Flow

### Old Format (Current):
1. User uploads Excel with claim details
2. System validates FCA eligibility
3. Dashboard shows eligibility analysis
4. DOCX report generated

### New Format (Enhanced):
1. User uploads new Monthly Report Excel
2. System detects format automatically
3. Extracts all 7 sections
4. Dashboard shows:
   - Portfolio metrics
   - Claim pipeline
   - Lender breakdown
   - Financial utilisation
   - Forecasting
   - Compliance status
   - **Profit split visualization**
5. DOCX report includes all above + Priority Deed waterfall

---

## 📝 Sample Dashboard Text

### Profit Distribution Section:

```
💰 Profit Distribution Structure (per Priority Deed)

Distribution Frequency: Quarterly
Payment Method: Via Collection Account

Payment Waterfall:
┌──────────────────────────────────────────┐
│ Priority 1: Outstanding Costs Sum        │
│ Recipient: Funder                        │
│ Description: All outstanding costs paid  │
│              first                       │
└──────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────┐
│ Priority 2: First Tier Funder Return     │
│ Recipient: Funder                        │
│ Description: Agreed return to funder     │
└──────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────┐
│ Priority 3: Distribution Cost Overrun    │
│ Recipient: Firm (Milberg)                │
│ Description: Additional distribution     │
│              costs if applicable         │
└──────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────┐
│ Priority 4: Net Proceeds Distribution    │
│                                           │
│ Funder:           80% of Net Proceeds    │
│ Firm (Milberg):   20% of Net Proceeds    │
│   ├─ Milberg:     10% of Net Proceeds    │
│   └─ Processor:   10% of Net Proceeds    │
└──────────────────────────────────────────┘
```

---

## 🧪 Testing Checklist

- [ ] Test with template Excel (all empty)
- [ ] Test with populated Excel
- [ ] Verify all 7 sections parse correctly
- [ ] Dashboard displays all new sections
- [ ] Priority Deed waterfall displays correctly
- [ ] DOCX report includes new sections
- [ ] DOCX report includes Priority Deed info
- [ ] Charts render properly
- [ ] Export functionality works
- [ ] Authentication still works
- [ ] Deploy to Streamlit Cloud
- [ ] Verify production deployment

---

## ⚡ Quick Start Implementation

**Minimal viable update (fastest path):**

1. Add Priority Deed display to existing dashboard sidebar
2. Add Priority Deed section to DOCX report
3. Keep existing Excel parsing as-is for backward compatibility
4. Add new format parser as optional enhancement

This allows you to show profit split info immediately without breaking existing functionality.

---

**Document created:** December 11, 2024
**Status:** Ready for implementation
**Priority:** High - New format is already in use
