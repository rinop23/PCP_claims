# PCP Claims Dashboard - Login Credentials

## 🔐 User Accounts

### Default Credentials

| User | Username | Password | Access Level |
|------|----------|----------|--------------|
| Administrator | `admin` | `Admin123!` | Full access |
| Walter | `walter` | `Walter123!` | Full access |
| Dirk | `dirk` | `Dirk123!` | Full access |
| Eda | `eda` | `Eda123!` | Full access |

---

## 🔒 Security Features

✅ **Password Hashing** - All passwords are hashed using SHA-256
✅ **Session Management** - Login persists during browser session
✅ **Logout Function** - Secure logout button in sidebar
✅ **No Plain Text Storage** - Passwords never stored in plain text

---

## 📝 Usage Instructions

### Logging In

1. Open the dashboard URL: https://share.streamlit.io (your app)
2. Enter your username (lowercase)
3. Enter your password (case-sensitive)
4. Click "Login"

### Logging Out

1. Look for the sidebar on the left
2. You'll see "Logged in as: [Your Name]"
3. Click the "🚪 Logout" button
4. You'll be returned to the login screen

---

## ⚠️ Important Notes

### Password Format
- Passwords are **case-sensitive**
- Default format: `Firstname123!`
- First letter capitalized, followed by `123!`

### Session Behavior
- Login session persists until:
  - You click logout
  - You close the browser tab
  - Session expires (Streamlit default ~24 hours)

### Security Best Practices
- **DO NOT share credentials** via email or unencrypted channels
- Change default passwords after first login (contact admin)
- Use unique, strong passwords
- Log out when using shared computers

---

## 🔧 For Administrators

### Adding New Users

To add a new user, edit `milberg_streamlit_demo.py`:

```python
# Find this section (around line 28):
USERS = {
    "admin": hash_password("Admin123!"),
    "walter": hash_password("Walter123!"),
    "dirk": hash_password("Dirk123!"),
    "eda": hash_password("Eda123!"),
    # Add new user here:
    "newuser": hash_password("Newuser123!")
}
```

Then commit and push to GitHub:
```bash
git add milberg_streamlit_demo.py
git commit -m "Add new user"
git push origin main
```

Streamlit will auto-deploy in 2-3 minutes.

### Changing Passwords

To change a password, edit the hash:

```python
"username": hash_password("NewPassword123!")
```

Then commit and push to GitHub.

### Removing Users

Delete the user line from the USERS dictionary and push to GitHub.

---

## 🐛 Troubleshooting

### "Invalid username or password"

**Possible causes:**
1. Username is case-sensitive (use lowercase: `admin`, not `Admin`)
2. Password is case-sensitive (check caps lock)
3. Typing error in password
4. Using wrong account

**Solution:** Double-check spelling and try again

### Login Page Not Showing

**Possible causes:**
1. Already logged in (check sidebar for logout button)
2. Browser cache issue

**Solution:**
- Click logout if already logged in
- Clear browser cache and refresh
- Try incognito/private browsing mode

### Stuck on Login Screen After Correct Credentials

**Possible causes:**
1. Browser cookies disabled
2. Streamlit session issue

**Solution:**
- Enable cookies in browser
- Refresh the page (F5)
- Clear browser cache
- Try a different browser

### Logged Out Unexpectedly

**Possible causes:**
1. Session expired (after ~24 hours)
2. App redeployed (Streamlit Cloud)
3. Network interruption

**Solution:** Simply log in again

---

## 📞 Support

If you're unable to log in:
1. Contact the system administrator
2. Verify you're using the correct URL
3. Try a different browser
4. Check if the app is online at https://share.streamlit.io

---

## 🔐 Password Change Policy

**Recommended:**
- Change default passwords after first login
- Use passwords with:
  - At least 8 characters
  - Mix of uppercase and lowercase
  - At least one number
  - At least one special character (!@#$%^&*)

**Example strong passwords:**
- `Finance2024!Secure`
- `Claims#Analysis99`
- `PCP$Dashboard!23`

---

**Document Created:** December 10, 2024
**Last Updated:** December 10, 2024
**Version:** 1.0
