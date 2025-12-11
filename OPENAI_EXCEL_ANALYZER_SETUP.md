# OpenAI Excel Analyzer Setup Guide

## Overview

The system now uses **OpenAI GPT-4o** to intelligently analyze Excel files and extract data. This ensures accurate extraction even when Excel formats change.

---

## How It Works

1. **Upload Excel File** → System detects "Monthly Summary" sheet
2. **AI Analysis** → OpenAI reads the entire sheet and understands structure
3. **Smart Extraction** → AI extracts:
   - Portfolio metrics (clients, claims, success rates)
   - Lender distribution with proper currency parsing
   - Claim pipeline stages
   - Financial costs and balance
   - Forecasting data
4. **Display** → Dashboard tabs populate with accurate data

---

## Setup Instructions

### For Streamlit Cloud Deployment

1. **Go to Streamlit Cloud Dashboard**
   - Navigate to: https://share.streamlit.io
   - Select your app: `PCP_claims`

2. **Add OpenAI API Key to Secrets**
   - Click **Settings** → **Secrets**
   - Add the following:

```toml
OPENAI_API_KEY = "sk-your-api-key-here"
```

3. **Save and Redeploy**
   - Click **Save**
   - App will automatically redeploy
   - OpenAI analysis will now work

### For Local Development

#### Windows

```cmd
setx OPENAI_API_KEY "sk-your-api-key-here"
```

Then restart your terminal.

#### Mac/Linux

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

Add to `~/.bashrc` or `~/.zshrc` to make permanent.

---

## Getting an OpenAI API Key

1. **Go to**: https://platform.openai.com/api-keys
2. **Sign in** or create an account
3. **Click**: "Create new secret key"
4. **Copy** the key (starts with `sk-`)
5. **Add** to Streamlit secrets or environment variable

### Pricing

The Excel analyzer uses **GPT-4o** which costs approximately:
- **$2.50 per 1M input tokens**
- **$10.00 per 1M output tokens**

For typical Monthly Summary Excel files:
- ~2,000 tokens input
- ~500 tokens output
- **Cost per analysis: ~$0.01** (1 cent)

Very affordable for monthly reports!

---

## Features

### Intelligent Data Extraction

The AI analyzer can:
- ✅ **Parse currency strings**: `£1,400` → `1400.00`
- ✅ **Handle percentages**: `2.86%` → `0.0286`
- ✅ **Understand table structures**: Even if rows/columns shift
- ✅ **Extract nested data**: Multi-level summaries
- ✅ **Handle missing values**: Smart defaults
- ✅ **Identify lender names**: Including special characters

### Fallback Mechanism

If OpenAI fails (no API key, network error, etc.):
- System automatically falls back to manual extraction
- Uses hardcoded row/column positions
- May be less accurate if Excel format changes

---

## Testing

To verify OpenAI integration is working:

1. **Upload** the Milberg Monthly Report Excel file
2. **Check logs** in Streamlit for:
   ```
   [Info] Using OpenAI to analyze Monthly Summary Excel
   ```
3. **Verify data** in dashboard tabs:
   - 🏦 Lenders & Defendants: Should show all 61 lenders
   - 📊 Claims Statistics: Portfolio overview with correct numbers
   - 💰 Financial Analysis: Cost breakdown

If you see:
```
[Warning] OpenAI extraction failed: ...
[Info] Falling back to manual extraction
```

→ Check that `OPENAI_API_KEY` is set in Streamlit secrets.

---

## Troubleshooting

### "OpenAI API key required" Error

**Cause**: API key not found in environment or secrets

**Solution**:
1. Add `OPENAI_API_KEY` to Streamlit Cloud secrets
2. Or set environment variable locally

### Numbers Still Wrong After Setup

**Possible causes**:
1. API key invalid (check on OpenAI platform)
2. API quota exceeded (check billing)
3. Network connectivity issue

**Debug**:
- Check Streamlit logs for `[Info] Using OpenAI...`
- If missing, AI analyzer didn't run
- Check for error messages

### Empty Dashboard Tabs

If tabs are still empty:
1. Ensure Excel file uploaded successfully
2. Check that file has "Monthly Summary" sheet
3. Look for extraction errors in logs
4. Verify `lender_distribution`, `portfolio_summary` populated in summary dict

---

## Code Reference

### Key Files

- **`intelligent_excel_analyzer.py`**: Main AI analyzer class
- **`document_processor.py`**: Integration point (calls AI analyzer)
- **`milberg_streamlit_demo.py`**: Dashboard display logic

### How Data Flows

```
Excel Upload
    ↓
document_processor.extract_from_excel_detailed()
    ↓
Detects "Monthly Summary" sheet
    ↓
intelligent_excel_analyzer.analyze_excel_with_ai()
    ↓
OpenAI GPT-4o reads entire sheet
    ↓
Returns JSON with structured data
    ↓
_transform_ai_extraction() formats for dashboard
    ↓
Dashboard tabs display data
```

---

## Alternative: Manual Extraction

If you prefer NOT to use OpenAI:

1. Comment out the OpenAI call in `document_processor.py`:

```python
# Lines 997-1009 in document_processor.py
if 'Monthly Summary' in xl.sheet_names and len(xl.sheet_names) == 1:
    # Disable OpenAI extraction
    # print("[Info] Using OpenAI to analyze Monthly Summary Excel")
    # try:
    #     from intelligent_excel_analyzer import IntelligentExcelAnalyzer
    #     analyzer = IntelligentExcelAnalyzer()
    #     ai_extracted = analyzer.analyze_excel_with_ai(file_path)
    #     return self._transform_ai_extraction(ai_extracted, file_path)
    # except Exception as e:
    #     print(f"[Warning] OpenAI extraction failed: {e}")

    # Use manual extraction instead
    print("[Info] Using manual extraction")
    return self.extract_from_excel_monthly_summary(file_path)
```

2. Push to GitHub

**Note**: Manual extraction may break if Excel format changes.

---

## Benefits of AI Extraction

1. **Resilient**: Works even if rows/columns move
2. **Accurate**: Understands context, not just positions
3. **Flexible**: Adapts to format variations
4. **Smart**: Parses currency, percentages automatically
5. **Future-proof**: No need to update code for format changes

---

**Created**: December 11, 2024
**Last Updated**: December 11, 2024
**Status**: Active - OpenAI integration deployed
