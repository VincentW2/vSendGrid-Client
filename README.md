# Sendgrid GUI

A simple, user-friendly tool for sending batch email campaigns using SendGrid. Supports both a modern GUI and command-line interface. Progress is tracked per CSV file, and email content is easy to edit for non-technical users.

---

## Features
- Send batch emails from a CSV list using SendGrid
- Modern, easy-to-use GUI (Windows 11 look)
- Per-CSV progress tracking (never email the same address twice)
- Edit email content in a single file (`email.txt` or `email.html`)
- Secure: API keys and sensitive data are never committed

---

## Setup
1. **Clone this repo**
2. **Install dependencies**
   ```sh
   pip install sendgrid tkinter
   ```
3. **Add your SendGrid API key and sender info**
   - Run the app once (`python mail_gui.py` or `python mail.py`) and follow the prompts. This will create a `settings.json` file.
4. **Prepare your email list**
   - The CSV must have a column with email addresses (auto-detected).
5. **Edit your email content**
   - Use `email.txt` for plain text, or `email.html` for HTML (takes priority if present).
   - The first line must be `SUBJECT: ...`, followed by the body.

---

## Usage
### GUI (Recommended)
```sh
python mail_gui.py
```
- Use the buttons to run batches, send test emails, change CSV, and more.
- All logs and progress are shown in the GUI.

### Command Line
```sh
python mail.py
```
- Follow the menu prompts in your terminal.

---

## Editing Email Content
- **Plain text:**
  - Edit `email.txt`:
    ```
    SUBJECT: Your subject here
    Your plain text email body here.
    ```
- **HTML:**
  - Edit `email.html` (takes priority if present):
    ```
    SUBJECT: Your subject here
    <html>
      ...your HTML email body...
    </html>
    ```

---

## Progress Tracking
- Progress is tracked per CSV file in the `/progress` directory.
---


## File Structure
```
project/
├── mail.py              # Main backend script
├── mail_gui.py          # GUI application
├── email.txt            # Email subject and plain text body
├── email.html           # (Optional) Email subject and HTML body
└── README.md            # This file
```

---