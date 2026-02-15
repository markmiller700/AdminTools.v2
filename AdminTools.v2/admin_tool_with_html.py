import os
import csv
import smtplib
import ssl
import time
import re
import binascii
import hashlib
import random
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid, formatdate
from getpass import getpass
from datetime import datetime


USERS_CSV = "users.csv"
USERS_TXT = "users.txt"            # file used to read 100 recipients (one per line)
EXPORT_CSV_DEFAULT = "users_export.csv"
LOG_FILE = "messages_sent.log"
HTML_TEMPLATE = "email_template.html"  # HTML template file

# Sender info (as provided earlier)
SENDER_EMAIL = "PUT--YOUR--GMAIL"
# App password you gave (no spaces)
APP_PASSWORD = "**** **** **** ****"

SENDER_NAME = "Admin Team"

# Subjects
WELCOME_SUBJECT = "Welcome to the system"
CUSTOM_SUBJECT = "Admin Message"

# Hashing params
SALT_BYTES = 16
PBKDF2_ROUNDS = 200_000

# Admin login (kept)
ADMIN_USER = "admin"
ADMIN_PASS = "12345"

# Bulk sending SAFE delay (seconds)
BULK_DELAY_SECONDS = 3

# Safe mode defaults for 100-send
SAFE_100_DELAY = 0.5
JITTER = 0.15

# Max recipients when using users.txt
MAX_BATCH = 100

# Colors
BLUE = "\033[94m"
RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"

# ---------- helpers ----------
def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def gen_salt():
    return binascii.hexlify(os.urandom(SALT_BYTES)).decode()

def hash_password(password, salt_hex):
    salt = binascii.unhexlify(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return binascii.hexlify(dk).decode()

def verify_password(password, salt_hex, hash_hex):
    return hash_password(password, salt_hex) == hash_hex

# ---------- HTML template loading ----------
def load_html_template():
    """Load HTML email template from file"""
    try:
        if os.path.exists(HTML_TEMPLATE):
            with open(HTML_TEMPLATE, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print(f"{YELLOW}Warning: {HTML_TEMPLATE} not found. Using plain text emails.{RESET}")
            return None
    except Exception as e:
        print(f"{YELLOW}Warning: Could not load HTML template: {e}. Using plain text.{RESET}")
        return None

# ---------- CSV storage ----------
def ensure_csv_exists():
    if not os.path.exists(USERS_CSV):
        with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "email", "salt", "pw_hash", "created_at"])

def load_users():
    ensure_csv_exists()
    users = []
    with open(USERS_CSV, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(row)
    return users

def save_users_list(users):
    with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "email", "salt", "pw_hash", "created_at"])
        for u in users:
            writer.writerow([u["username"], u["email"], u["salt"], u["pw_hash"], u.get("created_at","")])

def find_user(users, username):
    for i, u in enumerate(users):
        if u["username"] == username:
            return i, u
    return None, None

# ---------- email validation ----------
# Basic Gmail check (only gmail.com, basic local-part rules)
GMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+\-]+@gmail\.com$")

def is_valid_gmail(email):
    if not isinstance(email, str):
        return False
    email = email.strip()
    if not email:
        return False
    if not GMAIL_REGEX.match(email):
        return False
    return True

# ---------- email building & sending ----------
def build_welcome_message(to_email, username, subject=None, body=None, add_unique=False, use_html=True):
    """
    Build email message with HTML template or plain text fallback
    
    Args:
        to_email: Recipient email
        username: Recipient username
        subject: Email subject (default: WELCOME_SUBJECT)
        body: Plain text body (used if HTML template not available or use_html=False)
        add_unique: Add unique headers to avoid spam filters
        use_html: Whether to use HTML template
    """
    if subject is None:
        subject = WELCOME_SUBJECT
    
    # Try to load HTML template
    html_content = None
    if use_html:
        html_template = load_html_template()
        if html_template:
            # Replace placeholders in HTML template
            html_content = html_template.replace('{{username}}', username)
    
    # Fallback to plain text if HTML not available
    if body is None:
        body = f"Hello mr {username},\n\nWelcome to -ADMIN- tools you are now in admin data thank you for login\n\nBest regards,\n{SENDER_NAME}\n"
    
    # Create multipart message if HTML is available
    if html_content:
        msg = MIMEMultipart('alternative')
        msg["Subject"] = subject
        msg["From"] = formataddr((SENDER_NAME, SENDER_EMAIL))
        msg["To"] = to_email
        msg["Reply-To"] = SENDER_EMAIL
        
        # Add both plain text and HTML parts
        text_part = MIMEText(body, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
    else:
        # Plain text only
        msg = MIMEText(body, _subtype="plain", _charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr((SENDER_NAME, SENDER_EMAIL))
        msg["To"] = to_email
        msg["Reply-To"] = SENDER_EMAIL
    
    # Add unique headers if requested
    if add_unique:
        try:
            msg_id = make_msgid()
            msg["Message-ID"] = msg_id
        except Exception:
            msg["Message-ID"] = f"<{uuid.uuid4()}@local>"
        msg["X-Unique"] = str(uuid.uuid4())
    
    return msg

def open_smtp_connection():
    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        return server, None
    except Exception as e:
        return None, str(e)

def send_email_message_using_connection(server, msg, to_email):
    try:
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string().encode("utf-8"))
        return True, None
    except Exception as e:
        return False, str(e)

def send_email_message(msg, to_email):
    # fallback single-send (kept for calls that used original function)
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string().encode("utf-8"))
        return True, None
    except Exception as e:
        return False, str(e)

# ---------- read users.txt (for batch 100) ----------
def read_users_txt(path=USERS_TXT, max_count=MAX_BATCH):
    """
    Read users from users.txt. Accepts lines:
      username,email
      or
      username,email,password
    Ignores blank lines and lines starting with '#'.
    Returns a list of dicts: {'username':..., 'email':...}
    """
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if len(out) >= max_count:
                break
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2 and parts[1]:
                uname = parts[0] if parts[0] else parts[1].split("@")[0]
                email = parts[1]
                out.append({"username": uname, "email": email})
            # else ignore malformed lines
    return out

# ---------- UI ----------
def print_banner():
    print(RED + r'      _     ____  __  __ ___ _   _ ' + RESET)
    print(RED + r'     / \   |  _ \|  \/  |_ _| \ | |' + RESET)
    print(RED + r'    / _ \  | | | | |\/| || ||  \| |' + RESET)
    print(RED + r'   / ___ \ | |_| | |  | || || |\  |' + RESET)
    print(RED + r'  /_/   \_\|____/|_|  |_|___|_| \_|' + RESET)
    print(RED + "------------ ADMIN TOOL ------------" + RESET)
    print()

def show_menu():
    print(BLUE + "1" + RESET + " - Add user")
    print(BLUE + "2" + RESET + " - Remove user")
    print(BLUE + "3" + RESET + " - Show users")
    print(BLUE + "4" + RESET + " - Export users (CSV)")
    print(BLUE + "5" + RESET + " - Send Welcome Email to ONE user")
    print(BLUE + "6" + RESET + f" - Send Welcome Email to ALL users in users.csv (SAFE, {BULK_DELAY_SECONDS}s delay)")
    print(BLUE + "7" + RESET + f" - Send Welcome Email to up to {MAX_BATCH} users from users.txt (SAFE, {BULK_DELAY_SECONDS}s delay)")
    print(BLUE + "8" + RESET + " - Send 100 WELCOME emails to ONE user (safe mode)")
    print(BLUE + "9" + RESET + " - Send 100 CUSTOM emails to ONE user (safe mode, one-line custom message)")
    print(BLUE + "0" + RESET + " - Exit")

def show_users(users):
    if not users:
        print(YELLOW + "No users found.\n" + RESET)
        return
    u_w = max(len("Username"), max((len(u['username']) for u in users), default=0))
    e_w = max(len("Email"), max((len(u['email']) for u in users), default=0))
    sep = "-" * (u_w + e_w + 25)
    print(sep)
    print(f"{'Username'.ljust(u_w)} | {'Email'.ljust(e_w)} | {'Created at'}")
    print(sep)
    for u in users:
        print(f"{u['username'].ljust(u_w)} | {u['email'].ljust(e_w)} | {u.get('created_at','')}")
    print(sep + "\n")

# ---------- operations ----------
def add_user(users):
    username = input("New username: ").strip()
    if not username:
        print("Empty username — canceled.")
        return
    idx, _ = find_user(users, username)
    if idx is not None:
        print("User already exists.")
        return

    raw_email = input("Gmail (user@gmail.com): ").strip()
    email = raw_email.strip()
    if not is_valid_gmail(email):
        print(f"{RED}Invalid Gmail address — only valid @gmail.com addresses accepted. Canceled.{RESET}")
        return

    password = getpass("Password: ").strip()
    salt = gen_salt()
    pw_hash = hash_password(password, salt)
    user = {
        "username": username,
        "email": email,
        "salt": salt,
        "pw_hash": pw_hash,
        "created_at": now_iso()
    }
    users.append(user)
    save_users_list(users)
    print(f"{GREEN}User '{username}' added.{RESET}")

def remove_user(users):
    username = input("Username to remove: ").strip()
    idx, u = find_user(users, username)
    if idx is None:
        print("User not found.")
        return
    confirm = input(f"Confirm remove {username}? (y/N): ").strip().lower()
    if confirm != "y":
        print("Canceled.")
        return
    users.pop(idx)
    save_users_list(users)
    print(f"{GREEN}User '{username}' removed.{RESET}")

def export_users(users):
    fname = input(f"Export filename (default: {EXPORT_CSV_DEFAULT}): ").strip()
    if not fname:
        fname = EXPORT_CSV_DEFAULT
    try:
        with open(fname, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "email", "created_at"])
            for u in users:
                writer.writerow([u["username"], u["email"], u.get("created_at","")])
        print(f"{GREEN}Exported {len(users)} users to {fname}{RESET}")
    except Exception as e:
        print(f"{RED}Export failed: {e}{RESET}")

def send_email_to_user(users):
    username = input("Username to email: ").strip()
    idx, u = find_user(users, username)
    if idx is None:
        print("User not found.")
        return
    to_email_raw = u["email"]
    to_email = to_email_raw.strip()
    if not is_valid_gmail(to_email):
        print(f"Skipped: {to_email}")  # simple log
        return
    msg = build_welcome_message(to_email, username, use_html=True)
    print(f"Sending HTML email to {to_email} ...")
    ok, err = send_email_message(msg, to_email)
    if ok:
        print(f"{GREEN}Sent welcome email to {to_email}{RESET}")
    else:
        print(f"{RED}Failed to send email to {to_email}: {err}{RESET}")

def send_email_to_all(users):
    if not users:
        print(YELLOW + "No users to email.\n" + RESET)
        return
    total = len(users)
    print(f"Sending HTML welcome email to ALL users ({total}) in SAFE mode: {BULK_DELAY_SECONDS}s delay between sends.")
    sent = 0
    skipped = 0
    failed = 0
    for i, u in enumerate(users, start=1):
        raw = u.get("email", "")
        email = raw.strip()
        username = u.get("username", "")
        if not is_valid_gmail(email):
            print(f"[{i}/{total}] Skipped: {email}")
            skipped += 1
            continue
        msg = build_welcome_message(email, username, use_html=True)
        print(f"[{i}/{total}] Sending to {email} ... ", end="", flush=True)
        ok, err = send_email_message(msg, email)
        if ok:
            print(f"{GREEN}✅{RESET}")
            sent += 1
        else:
            print(f"{RED}❌ Failed: {err}{RESET}")
            failed += 1
        if i < total:
            time.sleep(BULK_DELAY_SECONDS)
    print(f"\nSummary: sent={sent}, skipped={skipped}, failed={failed}")

def send_email_to_100_from_txt():
    batch = read_users_txt(USERS_TXT, max_count=MAX_BATCH)
    if not batch:
        print(YELLOW + f"No valid lines found in {USERS_TXT} (or file missing).\n" + RESET)
        return
    total = len(batch)
    print(f"Sending HTML emails to up to {MAX_BATCH} users from {USERS_TXT} (found {total}) — SAFE mode: {BULK_DELAY_SECONDS}s delay")
    sent = 0
    skipped = 0
    failed = 0
    for i, entry in enumerate(batch, start=1):
        email_raw = entry.get("email", "")
        email = email_raw.strip()
        username = entry.get("username", "") or email.split("@")[0]
        if not is_valid_gmail(email):
            print(f"[{i}/{total}] Skipped: {email}")
            skipped += 1
            continue
        msg = build_welcome_message(email, username, use_html=True)
        print(f"[{i}/{total}] Sending to {email} ... ", end="", flush=True)
        ok, err = send_email_message(msg, email)
        if ok:
            print(f"{GREEN}✅{RESET}")
            sent += 1
        else:
            print(f"{RED}❌ Failed: {err}{RESET}")
            failed += 1
        if i < total:
            time.sleep(BULK_DELAY_SECONDS)
    print(f"\nBatch summary: sent={sent}, skipped={skipped}, failed={failed}")

# ---------- NEW: send 100 WELCOME to ONE user ----------
def send_100_welcome_to_one_user(users):
    username = input("Target username for 100 WELCOME emails: ").strip()
    idx, u = find_user(users, username)
    if idx is None:
        print(YELLOW + "User not found." + RESET)
        return
    to_email = u.get("email", "").strip()
    if not is_valid_gmail(to_email):
        print(YELLOW + "User has no valid Gmail. Aborting." + RESET)
        return

    confirm = input(f"Are you sure? This will send 100 HTML welcome emails to {to_email}. Type 'yes' to continue: ").strip().lower()
    if confirm != "yes":
        print("Canceled.")
        return

    try:
        delay = float(input(f"Delay between messages in seconds (recommended {SAFE_100_DELAY}): ").strip() or SAFE_100_DELAY)
    except Exception:
        delay = SAFE_100_DELAY

    # open one SMTP connection and reuse it (faster and fewer logins)
    server, err = open_smtp_connection()
    if server is None:
        print(RED + f"SMTP login failed: {err}" + RESET)
        return

    total = 100
    sent = 0
    failed = 0
    for i in range(1, total + 1):
        msg = build_welcome_message(to_email, username, subject=WELCOME_SUBJECT, use_html=True, add_unique=True)
        ok, err_send = send_email_message_using_connection(server, msg, to_email)
        if ok:
            sent += 1
            print(GREEN + f"[{i}/{total}] Sent HTML email" + RESET)
        else:
            failed += 1
            print(RED + f"[{i}/{total}] Failed: {err_send}" + RESET)
        # throttle with jitter
        if i < total:
            time.sleep(max(0, delay + (random.random() - 0.5) * 2 * JITTER))

    try:
        server.quit()
    except Exception:
        try:
            server.close()
        except Exception:
            pass

    print(f"Done. attempted={total}, sent={sent}, failed={failed}")

# ---------- NEW: send 100 CUSTOM to ONE user (one-line) ----------
def send_100_custom_to_one_user(users):
    username = input("Target username for 100 CUSTOM emails: ").strip()
    idx, u = find_user(users, username)
    if idx is None:
        print(YELLOW + "User not found." + RESET)
        return
    to_email = u.get("email", "").strip()
    if not is_valid_gmail(to_email):
        print(YELLOW + "User has no valid Gmail. Aborting." + RESET)
        return

    custom = input("Enter your ONE-LINE custom message to send (single line): ").rstrip("\n")
    if not custom:
        print(YELLOW + "Empty message. Aborting." + RESET)
        return

    confirm = input(f"Are you sure? This will send 100 custom emails to {to_email}. Type 'yes' to continue: ").strip().lower()
    if confirm != "yes":
        print("Canceled.")
        return

    try:
        delay = float(input(f"Delay between messages in seconds (recommended {SAFE_100_DELAY}): ").strip() or SAFE_100_DELAY)
    except Exception:
        delay = SAFE_100_DELAY

    # open SMTP connection once
    server, err = open_smtp_connection()
    if server is None:
        print(RED + f"SMTP login failed: {err}" + RESET)
        return

    total = 100
    sent = 0
    failed = 0
    for i in range(1, total + 1):
        body = custom
        # For custom messages, use plain text (no HTML template)
        msg = build_welcome_message(to_email, username, subject=CUSTOM_SUBJECT, body=body, use_html=False, add_unique=True)
        ok, err_send = send_email_message_using_connection(server, msg, to_email)
        if ok:
            sent += 1
            print(GREEN + f"[{i}/{total}] Sent" + RESET)
        else:
            failed += 1
            print(RED + f"[{i}/{total}] Failed: {err_send}" + RESET)
        if i < total:
            time.sleep(max(0, delay + (random.random() - 0.5) * 2 * JITTER))

    try:
        server.quit()
    except Exception:
        try:
            server.close()
        except Exception:
            pass

    print(f"Done. attempted={total}, sent={sent}, failed={failed}")

# ---------- main ----------
def main():
    ensure_csv_exists()
    users = load_users()
    print_banner()

    # simple admin auth
    admin_user = input("Admin username: ").strip()
    admin_pw = getpass("Admin password: ").strip()
    if admin_user != ADMIN_USER or admin_pw != ADMIN_PASS:
        print(f"{RED}Access denied{RESET}")
        return

    while True:
        show_menu()
        choice = input("Choice: ").strip()
        if choice == "1":
            add_user(users)
        elif choice == "2":
            remove_user(users)
        elif choice == "3":
            show_users(users)
        elif choice == "4":
            export_users(users)
        elif choice == "5":
            send_email_to_user(users)
        elif choice == "6":
            send_email_to_all(users)
        elif choice == "7":
            send_email_to_100_from_txt()
        elif choice == "8":
            send_100_welcome_to_one_user(users)
        elif choice == "9":
            send_100_custom_to_one_user(users)
        elif choice == "0":
            print("Bye.")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
