# HTML Email Integration - Setup Guide

## 📁 Files Included

1. **admin_tool_with_html.py** - Your modified Python script with HTML email support
2. **email_template.html** - Professional HTML email template

## 🚀 Setup Instructions

### Step 1: Place Files in Same Directory

Make sure both files are in the same folder:
```
your_folder/
├── admin_tool_with_html.py
├── email_template.html
├── users.csv (will be created automatically)
└── users.txt (optional, for batch sending)
```

### Step 2: Configure Your Email Credentials

Open `admin_tool_with_html.py` and update these lines (around line 22-25):

```python
SENDER_EMAIL = "your-email@gmail.com"  # Replace with your Gmail
APP_PASSWORD = "your app password"      # Replace with your Gmail App Password
```

### Step 3: Get Gmail App Password

1. Go to https://myaccount.google.com/
2. Click on **Security**
3. Enable **2-Step Verification** (if not already enabled)
4. Search for **App Passwords**
5. Create a new app password for "Mail"
6. Copy the 16-character password (format: xxxx xxxx xxxx xxxx)
7. Paste it in the script (remove spaces)

### Step 4: Run the Script

```bash
python admin_tool_with_html.py
```

## 🎨 What Changed?

### HTML Email Features
- ✅ Professional gradient header with ADMIN branding
- ✅ Clean, modern layout with proper spacing
- ✅ Responsive design (works on mobile)
- ✅ Personalized greeting with username
- ✅ Call-to-action button
- ✅ Professional footer

### Script Improvements
1. **Automatic HTML template loading** - The script automatically loads `email_template.html`
2. **Multipart emails** - Sends both HTML and plain text versions (better compatibility)
3. **Fallback system** - If HTML template is missing, uses plain text
4. **All functions updated** - Options 5, 6, 7, and 8 now send HTML emails

## 📧 How It Works

The script now:
1. Loads the HTML template when starting
2. Replaces `{{username}}` placeholder with actual username
3. Creates a multipart email with both HTML and plain text
4. Sends beautiful HTML emails to your users

## 🔧 Customizing the Template

You can edit `email_template.html` to change:
- **Colors**: Change hex codes (e.g., `#dc2626` for red)
- **Text**: Update welcome message
- **Logo/Header**: Modify the ADMIN text
- **Button link**: Change `href="#"` to your actual dashboard URL
- **Footer**: Update company name and links

### Example Customizations:

**Change the color scheme:**
Replace `#dc2626` (red) with:
- `#667eea` (purple/blue)
- `#10b981` (green)
- `#f59e0b` (orange)

**Add your logo:**
Add this in the header section:
```html
<img src="https://your-site.com/logo.png" alt="Logo" style="height: 50px;">
```

## 📝 Template Placeholders

Current placeholder:
- `{{username}}` - Replaced with recipient's username

You can add more placeholders by:
1. Adding them in the HTML: `{{custom_field}}`
2. Updating the `build_welcome_message()` function to replace them

## ⚠️ Important Notes

- The HTML template file **must** be in the same directory as the script
- If template is missing, script automatically falls back to plain text
- Option 9 (custom messages) still uses plain text (as intended)
- All HTML emails include a plain text alternative for compatibility

## 🎯 Testing

To test the HTML email:
1. Add a test user (option 1)
2. Send email to ONE user (option 5)
3. Check your inbox for the beautiful HTML email!

## 💡 Tips

- Test with one email first before sending to 100 users
- Keep Gmail's sending limits in mind (500 emails/day)
- The script includes automatic delays to avoid spam flags
- HTML emails have better open rates than plain text

Enjoy your professional email system! 🚀
