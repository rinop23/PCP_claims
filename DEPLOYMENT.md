# Deployment Guide - PCP Claims Analysis System

## 📋 Pre-Deployment Checklist

### Files to Include in GitHub ✅

#### Core Application Files
- `milberg_streamlit_demo.py` - Main Streamlit dashboard
- `pcp_funding_agent.py` - Core agent logic
- `document_processor.py` - Excel/document processing
- `fca_redress_validator.py` - FCA eligibility validation
- `api_server.py` - API server (if using)
- `cli_interface.py` - CLI interface (if using)
- `workflow_example.py` - Example workflows

#### Configuration Files
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules
- `run_dashboard.bat` - Windows launcher script

#### Documentation
- `README.md` - Main documentation
- `DASHBOARD_GUIDE.md` - Dashboard user guide
- `DEPLOYMENT.md` - This file
- `SYSTEM_OVERVIEW.md` - System architecture
- `QUICKSTART.md` - Quick start guide
- `MILBERG_EXCEL_INTEGRATION.md` - Excel integration guide

#### Test Files (Optional)
- `test_dashboard_fixes.py` - Dashboard tests
- `test_docx_charts.py` - DOCX generation tests
- `test_milberg_excel.py` - Excel processing tests

#### Directory Structure
- `uploads/.gitkeep` - Placeholder for uploads folder

---

### Files to EXCLUDE from GitHub ❌

#### Sensitive Data & Documents
- ❌ Any Excel files (`.xlsx`, `.xls`)
- ❌ Generated reports (`.docx`)
- ❌ PDF documents in legal folders
- ❌ `Priority Deed/` folder
- ❌ `Milberg Lawfirm Agreement/` folder
- ❌ `FCA redress scheme/` folder
- ❌ Any files in `uploads/` (except `.gitkeep`)

#### API Keys & Credentials
- ❌ `.env` files
- ❌ `config.json` with API keys
- ❌ `secrets.json`
- ❌ Any files with credentials

#### Generated/Temporary Files
- ❌ `__pycache__/` folders
- ❌ `.venv/` virtual environment
- ❌ `.claude/` Claude Code settings
- ❌ Log files (`.log`)
- ❌ Test output files

---

## 🚀 Deployment to Streamlit Cloud

### Step 1: Prepare Your Repository

1. **Create `.gitignore`** (already created)
   ```bash
   # Already in your project
   ```

2. **Create `requirements.txt`** (update if needed)
   ```bash
   pip freeze > requirements.txt
   ```

3. **Remove sensitive data**
   ```bash
   # Check no sensitive files are tracked
   git status
   ```

### Step 2: Update Configuration for Production

#### Create `config.py` for Environment Variables
Create a new file `config.py`:

```python
import os

# API Configuration (will use Streamlit secrets in production)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# File Upload Settings
MAX_UPLOAD_SIZE_MB = 10
ALLOWED_EXTENSIONS = ['.xlsx', '.xls']

# FCA Rules (can be configured per deployment)
FCA_AGREEMENT_DATE_MIN = "2007-04-06"
FCA_AGREEMENT_DATE_MAX = "2021-01-28"
FCA_PLEVIN_THRESHOLD = 50.0

# Application Settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

#### Update `milberg_streamlit_demo.py`
Add at the top:

```python
import config

# Use config values instead of hardcoded ones
```

### Step 3: Create Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 10
enableCORS = false
enableXsrfProtection = true

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[browser]
gatherUsageStats = false
```

### Step 4: GitHub Setup

```bash
# Initialize Git (if not already)
git init

# Add all files
git add .

# Check what will be committed
git status

# Commit
git commit -m "Initial commit - PCP Claims Analysis System"

# Create GitHub repository (via GitHub website)
# Then connect and push:
git remote add origin https://github.com/YOUR_USERNAME/pcp-claims-analysis.git
git branch -M main
git push -u origin main
```

### Step 5: Deploy to Streamlit Cloud

1. **Go to [share.streamlit.io](https://share.streamlit.io)**

2. **Sign in** with GitHub

3. **Click "New app"**

4. **Configure:**
   - Repository: `YOUR_USERNAME/pcp-claims-analysis`
   - Branch: `main`
   - Main file path: `milberg_streamlit_demo.py`

5. **Add Secrets** (if using OpenAI API):
   - Click "Advanced settings"
   - Add secrets in TOML format:
   ```toml
   OPENAI_API_KEY = "your-api-key-here"
   ```

6. **Deploy!**

---

## 🔐 Security Recommendations

### 1. API Keys Management

**For Streamlit Cloud:**
- Use Streamlit Secrets management
- Never commit API keys to Git
- Access via `st.secrets["OPENAI_API_KEY"]`

**Update code to use secrets:**
```python
import streamlit as st

# In pcp_funding_agent.py or wherever OpenAI is initialized
if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    openai.api_key = os.getenv("OPENAI_API_KEY", "")
```

### 2. File Upload Security

- Validate file extensions
- Check file sizes
- Scan uploaded files
- Automatically delete old uploads

### 3. Access Control

**For Organization-Wide Access:**

Option A: **Private Streamlit App**
- Deploy to Streamlit Cloud with email authentication
- Configure allowed email domains
- Users must authenticate with company email

Option B: **Password Protection**
Add authentication to your app:

```python
import streamlit as st

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password",
                     on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password",
                     on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if check_password():
    # Your main app code here
    main()
```

Option C: **Self-Hosted with SSO**
- Deploy on your own infrastructure
- Integrate with company SSO/SAML

### 4. Data Handling

- Don't log sensitive data
- Clear uploads after processing
- Use temporary files that auto-delete
- Encrypt data at rest if storing

---

## 📝 Environment Variables Needed

Create a `.env` file locally (NOT committed to Git):

```bash
# OpenAI API (optional - only if using LLM features)
OPENAI_API_KEY=your_key_here

# Application Settings
DEBUG=False
MAX_UPLOAD_SIZE_MB=10

# FCA Configuration (optional - can override defaults)
FCA_PLEVIN_THRESHOLD=50.0
```

For Streamlit Cloud, add these in the Secrets section.

---

## 🧪 Pre-Production Testing

### Local Testing
```bash
# Test with production settings
streamlit run milberg_streamlit_demo.py

# Test file uploads
# Test report generation
# Test all tabs and features
```

### Checklist
- [ ] All sensitive files excluded from Git
- [ ] `.gitignore` properly configured
- [ ] `requirements.txt` updated and tested
- [ ] API keys moved to environment variables
- [ ] Documentation updated
- [ ] Test upload and report generation
- [ ] Test with sample data only
- [ ] Verify no real client data in repo

---

## 🔄 Continuous Deployment

Once deployed, updates are automatic:

1. Make changes locally
2. Test thoroughly
3. Commit and push to GitHub
4. Streamlit Cloud auto-deploys

```bash
git add .
git commit -m "Description of changes"
git push origin main
```

---

## 🆘 Troubleshooting

### Common Issues

**1. Module not found**
- Check `requirements.txt` includes all packages
- Verify package names and versions

**2. File not found errors**
- Ensure `uploads/` directory exists
- Check file paths are relative, not absolute

**3. Charts not generating in DOCX**
- Verify `kaleido` is in requirements.txt
- Check sufficient memory available

**4. Slow performance**
- Consider caching with `@st.cache_data`
- Optimize file processing
- Use smaller file sizes for testing

---

## 📊 Monitoring

After deployment, monitor:

- Upload success/failure rates
- Processing times
- Error logs in Streamlit Cloud
- User feedback

---

## 📞 Support

For deployment issues:
- Streamlit Docs: https://docs.streamlit.io/
- Streamlit Community: https://discuss.streamlit.io/
- GitHub Issues: Your repository issues page

---

*Last updated: December 2024*
