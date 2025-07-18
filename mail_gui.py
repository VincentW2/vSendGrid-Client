import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, scrolledtext, ttk
import threading
import os
import json
import sys
from mail import (
    SETTINGS_FILE, DEFAULT_SETTINGS, SETTINGS, SENDER_EMAIL, SENDER_NAME, SENDGRID_API_KEY, CSV_FILE,
    EmailCampaignManager, run_email_campaign, send_campaign_email
)

def gui_first_run_settings():
    root = tk.Tk()
    root.withdraw()  # Hide main window
    # Custom top-level window for setup
    setup_win = tk.Toplevel()
    setup_win.title("SendGrid GUI Setup")
    setup_win.geometry("540x350")  # Widened window
    setup_win.resizable(False, False)
    setup_win.configure(bg="#f7f7fa")
    setup_win.grab_set()
    # Fonts
    font_title = ("Segoe UI Variable", 20, "bold")
    font_label = ("Segoe UI Variable", 12)
    font_entry = ("Segoe UI Variable", 13)
    # Title
    title = tk.Label(setup_win, text="SendGrid GUI Setup", font=font_title, bg="#f7f7fa", pady=14)
    title.pack()
    # Frame for fields
    frame = tk.Frame(setup_win, bg="#f7f7fa")
    frame.pack(padx=28, pady=8, fill=tk.BOTH, expand=True)
    # Sender Email
    lbl_email = tk.Label(frame, text="Sender Email (must be verified):", font=font_label, bg="#f7f7fa", anchor='w')
    lbl_email.pack(fill=tk.X, pady=(8, 2))
    entry_email = tk.Entry(frame, font=font_entry, width=32, bd=2, relief="groove")
    entry_email.pack(fill=tk.X, pady=(0, 8))
    # Sender Name
    lbl_name = tk.Label(frame, text="Sender Name (required):", font=font_label, bg="#f7f7fa", anchor='w')
    lbl_name.pack(fill=tk.X, pady=(8, 2))
    entry_name = tk.Entry(frame, font=font_entry, width=32, bd=2, relief="groove")
    entry_name.pack(fill=tk.X, pady=(0, 8))
    # SendGrid API Key
    lbl_key = tk.Label(frame, text="SendGrid API Key:", font=font_label, bg="#f7f7fa", anchor='w')
    lbl_key.pack(fill=tk.X, pady=(8, 2))
    entry_key = tk.Entry(frame, font=font_entry, width=32, bd=2, relief="groove", show="*")
    entry_key.pack(fill=tk.X, pady=(0, 2))
    hint_key = tk.Label(frame, text="Find your API key at: sendgrid.com > Settings > API Keys", font=("Segoe UI", 9), fg="#888", bg="#f7f7fa", anchor='w')
    hint_key.pack(fill=tk.X, pady=(0, 8))
    # Buttons
    btn_frame = tk.Frame(setup_win, bg="#f7f7fa")
    btn_frame.pack(pady=(8, 12))
    def on_submit():
        sender_email = entry_email.get().strip()
        sender_name = entry_name.get().strip()
        sendgrid_api_key = entry_key.get().strip()
        if not sender_email or '@' not in sender_email:
            messagebox.showerror("Invalid Email", "Please enter a valid sender email.")
            return
        if not sender_name:
            messagebox.showerror("Missing Sender Name", "Please enter a sender name.")
            return
        if not sendgrid_api_key or sendgrid_api_key == DEFAULT_SETTINGS["sendgrid_api_key"]:
            messagebox.showerror("Invalid API Key", "Please enter a valid SendGrid API key.")
            return
        settings = {
            "sender_email": sender_email,
            "sender_name": sender_name,
            "sendgrid_api_key": sendgrid_api_key
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        messagebox.showinfo("Setup Complete", "Settings saved! You can now use the app.")
        setup_win.destroy()
        root.destroy()
        return settings
    submit_btn = tk.Button(btn_frame, text="Save Settings", font=font_label, bg="#50C878", fg="white", relief="flat", padx=18, pady=6, command=on_submit)
    submit_btn.pack(side=tk.LEFT, padx=8)
    cancel_btn = tk.Button(btn_frame, text="Cancel", font=font_label, bg="#e74c3c", fg="white", relief="flat", padx=18, pady=6, command=lambda: (setup_win.destroy(), root.destroy(), sys.exit(0)))
    cancel_btn.pack(side=tk.LEFT, padx=8)
    def on_close():
        setup_win.destroy()
        root.destroy()
        sys.exit(0)
    setup_win.protocol("WM_DELETE_WINDOW", on_close)
    setup_win.mainloop()
    return None

def check_settings_gui():
    # If settings.json is missing or incomplete, run GUI setup
    if not os.path.exists(SETTINGS_FILE):
        gui_first_run_settings()
    else:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        if (
            not settings.get("sender_email") or settings["sender_email"] == DEFAULT_SETTINGS["sender_email"] or
            not settings.get("sendgrid_api_key") or settings["sendgrid_api_key"] == DEFAULT_SETTINGS["sendgrid_api_key"]
        ):
            gui_first_run_settings()

# --- GUI ---
class EmailGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sendgrid Campaign Manager")
        self.root.geometry("750x520")
        self.root.minsize(750, 520)
        self.root.configure(bg="#f7f7fa")
        self.font_main = ("Segoe UI Variable", 11)
        self.font_console = ("Consolas", 11)
        self.font_label = ("Segoe UI Variable", 12)
        self.font_entry = ("Segoe UI Variable", 13)
        self.create_widgets()
        self.refresh_status()

    def create_widgets(self):
        # Add menu bar with Tools menu
        menubar = tk.Menu(self.root)
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="App Info", command=self.show_app_info)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        self.root.config(menu=menubar)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=self.font_main, padding=8, relief="flat", borderwidth=0, focusthickness=3, focuscolor='none')
        style.map('TButton', background=[('active', '#e0e0e0')], relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        # Emerald style for Run Batch and Custom Batch
        style.configure('Green.TButton', background='#50C878', foreground='white')
        style.map('Green.TButton', background=[('active', '#43b06c')])
        # Red style for Exit
        style.configure('Red.TButton', background='#e74c3c', foreground='white')
        style.map('Red.TButton', background=[('active', '#c0392b')])
        # Button frame
        btn_frame = tk.Frame(self.root, bg="#f7f7fa")
        btn_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        btn_width = 12
        btns = [
            ("Run Batch", self.run_batch, 'Green.TButton'),
            ("Custom Batch", self.custom_batch, 'Green.TButton'),
            ("Test Email", self.test_email, 'TButton'),
            ("Print List", self.print_list, 'TButton'),
            ("Change CSV", self.change_csv, 'TButton'),
            ("Exit", self.root.quit, 'Red.TButton')
        ]
        for text, cmd, style_name in btns:
            b = ttk.Button(btn_frame, text=text, command=cmd, width=btn_width, style=style_name)
            b.pack(side=tk.LEFT, padx=8, pady=2, anchor='s')
        # Status/info area
        self.info_label = tk.Label(self.root, text="", anchor='w', justify='left', font=self.font_main, bg="#f7f7fa")
        self.info_label.pack(fill=tk.X, padx=16, pady=4)
        # Console output area
        self.console = scrolledtext.ScrolledText(self.root, height=20, font=self.font_console, bg="#f0f0f0", bd=1, relief="solid")
        self.console.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        self.console.config(state=tk.DISABLED)

    def refresh_status(self):
        campaign = EmailCampaignManager(csv_file=SETTINGS.get("csv_file", ""))
        emails = campaign.load_email_list()
        stats = campaign.get_campaign_stats()
        sender = SETTINGS.get("sender_email", "N/A")
        csv_file = SETTINGS.get("csv_file", "")
        info = f"Current CSV: {csv_file if csv_file else 'Not set'}\nCurrent sender email: {sender}\nTotal emails in CSV: {len(emails)}\nTotal sent: {stats.get('emails_sent', 0)}\nFirst 5 emails: {', '.join(emails[:5]) if emails else 'None'}"
        self.info_label.config(text=info)
        if csv_file and not os.path.exists(csv_file):
            messagebox.showerror("CSV File Not Found", f"The selected CSV file '{csv_file}' does not exist. Please choose a valid file.")

    def append_console(self, text):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, text + '\n')
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def run_batch(self):
        self.append_console("Running batch (up to 5000 emails)...")
        threading.Thread(target=self._run_batch_thread, daemon=True).start()
    def _run_batch_thread(self):
        run_email_campaign(batch_size=5000)
        self.append_console("Batch run complete.")
        self.refresh_status()

    def custom_batch_thread(self, batch_size):
        run_email_campaign(batch_size=batch_size)
        self.append_console("Custom batch run complete.")
        self.refresh_status()

    def custom_batch(self):
        self._show_custom_batch_dialog()

    def _show_custom_batch_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Custom Batch Size")
        dialog.geometry("400x180")
        dialog.minsize(400, 180)
        dialog.grab_set()
        dialog.transient(self.root)
        dialog.configure(bg="#f7f7fa")
        frame = tk.Frame(dialog, bg="#f7f7fa")
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=(20, 10))
        label = tk.Label(frame, text="Enter batch size:", font=self.font_label, bg="#f7f7fa")
        label.pack(anchor='w', pady=(0, 8))
        entry = tk.Entry(frame, font=self.font_entry, width=32, bd=2, relief="groove")
        entry.pack(fill=tk.X, pady=(0, 16))
        entry.focus_set()
        btn_frame = tk.Frame(frame, bg="#f7f7fa")
        btn_frame.pack(fill=tk.X, pady=(0, 0))
        def run():
            value = entry.get().strip()
            try:
                batch_size = int(value)
                if batch_size <= 0:
                    raise ValueError
            except Exception:
                messagebox.showerror("Invalid Batch Size", "Please enter a positive integer.")
                return
            dialog.destroy()
            self.append_console(f"Running custom batch ({batch_size} emails)...")
            threading.Thread(target=self.custom_batch_thread, args=(batch_size,), daemon=True).start()
        run_btn = ttk.Button(btn_frame, text="Run", style='Green.TButton', command=run)
        run_btn.pack(side=tk.RIGHT, padx=12)
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)

    def test_email(self):
        self._show_test_email_dialog()

    def _show_test_email_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Send Test Email")
        dialog.geometry("400x180")
        dialog.minsize(400, 180)
        dialog.grab_set()
        dialog.transient(self.root)
        dialog.configure(bg="#f7f7fa")
        frame = tk.Frame(dialog, bg="#f7f7fa")
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=(20, 10))
        label = tk.Label(frame, text="Recipient Email:", font=self.font_label, bg="#f7f7fa")
        label.pack(anchor='w', pady=(0, 8))
        entry = tk.Entry(frame, font=self.font_entry, width=32, bd=2, relief="groove")
        entry.pack(fill=tk.X, pady=(0, 16))
        entry.focus_set()
        btn_frame = tk.Frame(frame, bg="#f7f7fa")
        btn_frame.pack(fill=tk.X, pady=(0, 0))
        def is_valid_email(email):
            if not email or '@' not in email:
                return False
            local, _, domain = email.partition('@')
            return '.' in domain and len(local) > 0 and len(domain) > 2
        def send():
            recipient = entry.get().strip()
            if is_valid_email(recipient):
                dialog.destroy()
                self.append_console(f"Sending test email to {recipient}...")
                threading.Thread(target=self._test_email_thread, args=(recipient,), daemon=True).start()
            else:
                messagebox.showerror("Invalid Email", "Please enter a valid email address.")
        send_btn = ttk.Button(btn_frame, text="Send", style='Green.TButton', command=send)
        send_btn.pack(side=tk.RIGHT, padx=12)
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)

    def _test_email_thread(self, recipient):
        send_campaign_email(recipient, show_output=True)
        self.append_console(f"Test email sent to {recipient}.")
        self.refresh_status()

    def print_list(self):
        campaign = EmailCampaignManager(csv_file=SETTINGS.get("csv_file", "final_emails_master.csv"))
        emails = campaign.load_email_list()
        self.append_console(f"Current email list (first 5):\n" + '\n'.join(emails[:5]))

    def change_csv(self):
        new_csv = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if new_csv:
            if not os.path.exists(new_csv):
                messagebox.showerror("File Not Found", f"File '{new_csv}' does not exist.")
                return
            SETTINGS["csv_file"] = new_csv
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(SETTINGS, f, indent=2)
            self.append_console(f"CSV file changed to: {new_csv}")
            self.refresh_status()
        else:
            messagebox.showwarning("No File Selected", "No CSV file was selected.")

    def show_app_info(self):
        info = (
            "SendGrid Email Manager\n"
            "Version: 1.0\n"
            "Author: Vincent L\n"
            "\nA simple tool for managing and sending email campaigns using SendGrid.\n"
            "Features: batch sending, CSV import, progress tracking, and more."
        )
        messagebox.showinfo("App Info", info)

if __name__ == "__main__":
    check_settings_gui()
    root = tk.Tk()
    app = EmailGUI(root)
    root.mainloop() 