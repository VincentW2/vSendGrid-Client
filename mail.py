#!/usr/bin/env python3
"""
Generic SendGrid Email Campaign Script
Sends emails using SendGrid API with error handling and progress tracking
"""

import os
import sys
import csv
import json
import random
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, From, Subject, PlainTextContent, HtmlContent
import logging
from typing import List, Optional, Dict, Any
from typing import Tuple

# --- SETTINGS MANAGEMENT ---
SETTINGS_FILE = 'settings.json'
DEFAULT_SETTINGS = {
    "sender_email": "your_verified_sender@example.com",
    "sender_name": "John Doe",
    "sendgrid_api_key": "YOUR_SENDGRID_API_KEY",
    "csv_file": "example.csv"
}

def prompt_for_settings():
    # This function is now unused in GUI-only mode, but kept for reference or CLI fallback.
    print("\n--- Initial Setup: Please enter your email campaign settings ---")
    sender_email = input("Enter your verified sender email: ").strip()
    while not sender_email or '@' not in sender_email:
        sender_email = input("Please enter a valid sender email: ").strip()
    sender_name = input("Enter sender name (default: John Doe): ").strip() or "John Doe"
    sendgrid_api_key = input("Enter your SendGrid API key: ").strip()
    while not sendgrid_api_key or sendgrid_api_key == DEFAULT_SETTINGS["sendgrid_api_key"]:
        sendgrid_api_key = input("Please enter a valid SendGrid API key: ").strip()
    settings = {
        "sender_email": sender_email,
        "sender_name": sender_name,
        "sendgrid_api_key": sendgrid_api_key
    }
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)
    print("Settings saved to settings.json!\n")
    return settings

# Only load settings from file; do not prompt on import
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, 'r') as f:
        SETTINGS = json.load(f)
else:
    SETTINGS = {}

SENDER_EMAIL: str = str(SETTINGS.get("sender_email", "")).strip()
SENDER_NAME: str = str(SETTINGS.get("sender_name", "John Doe"))
SENDGRID_API_KEY: str = str(SETTINGS.get("sendgrid_api_key", ""))
CSV_FILE: str = str(SETTINGS.get("csv_file", "final_emails_master.csv"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class SendGridEmailer:
    """A robust SendGrid email client with error handling and validation"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("SendGrid API key is required.")
        self.sg = SendGridAPIClient(api_key=self.api_key)
        logging.info("SendGrid client initialized successfully")
    def validate_email(self, email: str) -> bool:
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    def send_email(self, from_email: str, to_emails: List[str], subject: str, plain_text_content: str = "", html_content: str = "", from_name: str = "") -> Dict[str, Any]:
        plain_text_content = str(plain_text_content or '')
        html_content = str(html_content or '')
        try:
            if not self.validate_email(from_email):
                raise ValueError(f"Invalid sender email: {from_email}")
            if not to_emails:
                raise ValueError("At least one recipient email is required")
            for email in to_emails:
                if not self.validate_email(email):
                    raise ValueError(f"Invalid recipient email: {email}")
            if not subject.strip():
                raise ValueError("Email subject cannot be empty")
            if not plain_text_content and not html_content:
                raise ValueError("Either plain text or HTML content is required")
            from_address = From(from_email, from_name) if from_name else From(from_email)
            to_list = [To(email) for email in to_emails]
            message = Mail(
                from_email=from_address,
                to_emails=to_list,
                subject=Subject(subject)
            )
            if plain_text_content:
                message.content = PlainTextContent(plain_text_content or '')
            if html_content:
                if plain_text_content:
                    message.add_content(HtmlContent(html_content or ''))
                else:
                    message.content = HtmlContent(html_content or '')
            logging.info(f"Sending email to {len(to_emails)} recipient(s)")
            response = self.sg.send(message)
            if response.status_code in [200, 201, 202]:
                logging.info(f"Email sent successfully! Status code: {response.status_code}")
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'message': 'Email sent successfully',
                    'response_headers': dict(response.headers),
                    'recipients': to_emails
                }
            else:
                logging.error(f"Email sending failed. Status code: {response.status_code}")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'message': f'Email sending failed with status code: {response.status_code}',
                    'response_body': response.body,
                    'response_headers': dict(response.headers)
                }
        except Exception as e:
            logging.error(f"Error sending email: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to send email due to an error'
            }
    def send_simple_email(self, from_email: str, to_email: str, subject: str, message: str, from_name: str = "") -> Dict[str, Any]:
        return self.send_email(
            from_email=from_email,
            to_emails=[to_email],
            subject=subject,
            plain_text_content=message,
            from_name=from_name
        )

def read_email_content() -> Tuple[str, str, str]:
    if os.path.exists('email.html'):
        with open('email.html', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if not lines or not lines[0].startswith('SUBJECT:'):
            raise RuntimeError("First line of email.html must be 'SUBJECT: ...'")
        subject = lines[0].replace('SUBJECT:', '').strip()
        html_message = ''.join(lines[1:]).lstrip()
        return subject, '', html_message  # always return str, not None
    elif os.path.exists('email.txt'):
        with open('email.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if not lines or not lines[0].startswith('SUBJECT:'):
            raise RuntimeError("First line of email.txt must be 'SUBJECT: ...'")
        subject = lines[0].replace('SUBJECT:', '').strip()
        plain_text_message = ''.join(lines[1:]).lstrip()
        return subject, plain_text_message, ''  # always return str, not None
    else:
        raise RuntimeError("No email.html or email.txt found. Please create one with 'SUBJECT: ...' as the first line.")

def send_campaign_email(recipient_email: str, show_output: bool = True):
    emailer = SendGridEmailer(api_key=SENDGRID_API_KEY)
    try:
        subject, plain_text_message, html_message = read_email_content()
        plain_text_message = plain_text_message if plain_text_message is not None else ''
        html_message = html_message if html_message is not None else ''
    except Exception as e:
        if show_output:
            print(str(e))
        return {'success': False, 'error': str(e)}
    if show_output:
        print(f"Sending campaign email to {recipient_email}...")
    result = emailer.send_email(
        from_email=SENDER_EMAIL,
        to_emails=[recipient_email],
        subject=subject,
        plain_text_content=str(plain_text_message),
        html_content=str(html_message),
        from_name=SENDER_NAME
    )
    if show_output:
        if result['success']:
            print(f"✅ Email sent to {recipient_email}!")
        else:
            print(f"❌ Failed to send to {recipient_email}: {result.get('error', result.get('message'))}")
    return result

class EmailCampaignManager:
    """Manages email campaigns with CSV reading and progress tracking"""
    def __init__(self, csv_file: str = "", progress_file: str = ""):
        self.csv_file = csv_file or CSV_FILE
        progress_dir = "progress"
        if not os.path.exists(progress_dir):
            os.makedirs(progress_dir)
        csv_base = os.path.basename(self.csv_file)
        progress_name = os.path.splitext(csv_base)[0] + "_progress.json"
        self.progress_file = os.path.join(progress_dir, progress_name)
        self.progress_data = self.load_progress()
    def load_progress(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                    logging.info(f"Loaded progress: {len(progress.get('sent_emails', []))} emails already sent")
                    return progress
            else:
                logging.info("No progress file found, starting fresh")
                return {"sent_emails": [], "campaign_stats": {"total_sent": 0, "last_run": None}}
        except Exception as e:
            logging.error(f"Error loading progress file: {e}")
            return {"sent_emails": [], "campaign_stats": {"total_sent": 0, "last_run": None}}
    def save_progress(self):
        try:
            self.progress_data["campaign_stats"]["last_run"] = datetime.now().isoformat()
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress_data, f, indent=2)
            logging.info(f"Progress saved: {len(self.progress_data['sent_emails'])} total emails sent")
        except Exception as e:
            logging.error(f"Error saving progress: {e}")
    def load_email_list(self) -> List[str]:
        emails = []
        try:
            if not os.path.exists(self.csv_file):
                logging.error(f"CSV file not found: {self.csv_file}")
                return []
            encodings_to_try = ['utf-8', 'utf-8-sig', 'iso-8859-1', 'cp1252']
            for encoding in encodings_to_try:
                try:
                    with open(self.csv_file, 'r', newline='', encoding=encoding) as csvfile:
                        reader = csv.DictReader(csvfile)
                        if reader.fieldnames:
                            email_column = None
                            for column in reader.fieldnames:
                                column_clean = column.strip().lower()
                                if column_clean in ['email', 'emails', 'email_address', 'e-mail']:
                                    email_column = column
                                    break
                            if not email_column:
                                for column in reader.fieldnames:
                                    if 'email' in column.strip().lower():
                                        email_column = column
                                        break
                            if not email_column:
                                print(f"No email column found in CSV. Available columns: {reader.fieldnames}")
                                continue
                            for row in reader:
                                email_value = row.get(email_column, '').strip()
                                if email_value and '@' in email_value and '.' in email_value:
                                    if len(email_value.split('@')) == 2:
                                        emails.append(email_value.lower())
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logging.error(f"Error with encoding {encoding}: {e}")
                    continue
            if not emails:
                logging.error("Could not read any emails from the CSV file")
                return []
            unique_emails = list(dict.fromkeys(emails))
            return unique_emails
        except Exception as e:
            logging.error(f"Error reading CSV file: {e}")
            return []
    def get_unsent_emails(self, limit: int = 50) -> List[str]:
        all_emails = self.load_email_list()
        sent_email_addresses = set()
        for item in self.progress_data.get("sent_emails", []):
            if isinstance(item, dict):
                email = item.get("email", "")
            else:
                email = str(item)
            if email:
                sent_email_addresses.add(email.lower())
        unsent_emails = [email for email in all_emails if email.lower() not in sent_email_addresses]
        if not unsent_emails:
            logging.warning("No unsent emails remaining!")
            return []
        selected_count = min(limit, len(unsent_emails))
        selected_emails = random.sample(unsent_emails, selected_count)
        return selected_emails
    def mark_email_sent(self, email: str, success: bool, error_message: str = ""):
        email_record = {
            "email": email,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "error": error_message or ""
        }
        if "sent_emails" not in self.progress_data:
            self.progress_data["sent_emails"] = []
        existing_emails = []
        for item in self.progress_data["sent_emails"]:
            if isinstance(item, dict):
                existing_emails.append(item.get("email", ""))
            else:
                existing_emails.append(str(item))
        if email not in existing_emails:
            self.progress_data["sent_emails"].append(email_record)
        if "campaign_stats" not in self.progress_data:
            self.progress_data["campaign_stats"] = {"total_sent": 0, "successful": 0, "failed": 0}
        self.progress_data["campaign_stats"]["total_sent"] = len(self.progress_data["sent_emails"])
        successful = sum(1 for item in self.progress_data["sent_emails"] 
                        if isinstance(item, dict) and item.get("success", False))
        failed = sum(1 for item in self.progress_data["sent_emails"] 
                    if isinstance(item, dict) and not item.get("success", True))
        self.progress_data["campaign_stats"]["successful"] = successful
        self.progress_data["campaign_stats"]["failed"] = failed
    def get_campaign_stats(self) -> Dict[str, Any]:
        stats = self.progress_data.get("campaign_stats", {})
        all_emails = self.load_email_list()
        sent_count = len(self.progress_data.get("sent_emails", []))
        return {
            "total_emails_in_csv": len(all_emails),
            "emails_sent": sent_count,
            "emails_remaining": len(all_emails) - sent_count,
            "successful_sends": stats.get("successful", 0),
            "failed_sends": stats.get("failed", 0),
            "last_run": stats.get("last_run", "Never")
        }

def run_email_campaign(batch_size: int = 5000):
    csv_file = SETTINGS.get("csv_file", "final_emails_master.csv")
    campaign = EmailCampaignManager(csv_file=csv_file)
    stats = campaign.get_campaign_stats()
    print(f"\n📊 CAMPAIGN STATUS:")
    print(f"   Total emails in CSV: {stats['total_emails_in_csv']}")
    print(f"   Already sent: {stats['emails_sent']}")
    print(f"   Remaining: {stats['emails_remaining']}")
    print(f"   Success rate: {stats['successful_sends']}/{stats['emails_sent']} successful")
    print(f"   Last run: {stats['last_run']}")
    print("-" * 50)
    if stats['emails_remaining'] == 0:
        print("🎉 Campaign complete! All emails have been sent.")
        return
    target_emails = campaign.get_unsent_emails(batch_size)
    if not target_emails:
        print("No emails to send!")
        return
    try:
        emailer = SendGridEmailer(api_key=SENDGRID_API_KEY)
    except ValueError as e:
        print(f"Error initializing emailer: {e}")
        return
    print(f"🚀 Starting batch send to {len(target_emails)} recipients...")
    print(f"📧 Sender: {SENDER_NAME} <{SENDER_EMAIL}>")
    print("-" * 50)
    successful_sends = 0
    failed_sends = 0
    for i, recipient_email in enumerate(target_emails, 1):
        print(f"[{i}/{len(target_emails)}] Sending to {recipient_email}...")
        result = send_campaign_email(
            recipient_email=recipient_email,
            show_output=False
        )
        if result and result['success']:
            print(f"   ✅ Success")
            successful_sends += 1
            campaign.mark_email_sent(recipient_email, True)
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No response'
            print(f"   ❌ Failed: {error_msg}")
            failed_sends += 1
            campaign.mark_email_sent(recipient_email, False, error_msg)
        campaign.save_progress()
        import time
        time.sleep(2)
    print("\n" + "=" * 50)
    print("📊 BATCH COMPLETE!")
    print(f"✅ Successful: {successful_sends}")
    print(f"❌ Failed: {failed_sends}")
    print(f"📈 Success rate: {(successful_sends/len(target_emails)*100):.1f}%")
    updated_stats = campaign.get_campaign_stats()
    print(f"\n📋 UPDATED CAMPAIGN STATUS:")
    print(f"   Total sent: {updated_stats['emails_sent']}")
    print(f"   Remaining: {updated_stats['emails_remaining']}")
    print("=" * 50)

# Remove CLI entry point and helpers, add a message if run directly
if __name__ == "__main__":
    print("This module is for backend use only. Please run mail_gui.py for the GUI.")