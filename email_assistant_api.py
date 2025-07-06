# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import imaplib
# import email
# from email.header import decode_header
# import re
#
# app = Flask(__name__)
# CORS(app)
#
# # 🧠 Simple NLP classifier
# def classify_message(msg):
#     msg = msg.lower()
#     if "job" in msg:
#         return {"intent": "show_category", "category": "job"}
#     elif "ecommerce" in msg or "amazon" in msg or "flipkart" in msg:
#         return {"intent": "show_category", "category": "ecommerce"}
#     elif "spam" in msg:
#         return {"intent": "show_category", "category": "spam"}
#     elif msg.strip().isdigit():
#         return {"intent": "show_detail", "index": int(msg.strip()) - 1}
#     else:
#         return {"intent": "unknown"}
#
# # 📦 Store last result in memory
# email_cache = []
#
# # 🔐 Clean helper
# def clean_text(text):
#     if isinstance(text, bytes):
#         try:
#             text = text.decode()
#         except:
#             text = text.decode("utf-8", errors="ignore")
#     return text.strip().replace("\r", "").replace("\n", " ")
#
# # ✉️ Email categorizer
# def categorize_email(msg):
#     subject = msg.get("Subject", "")
#     from_email = msg.get("From", "").lower()
#
#     subject_clean = clean_text(subject).lower()
#
#     if any(keyword in subject_clean for keyword in ["interview", "job", "resume", "hiring"]):
#         return "job"
#     elif any(keyword in subject_clean for keyword in ["amazon", "flipkart", "order", "invoice"]):
#         return "ecommerce"
#     elif "spam" in from_email or "junk" in from_email:
#         return "spam"
#     else:
#         return "uncategorized"
#
# # 📬 IMAP connection
# def fetch_emails(email_id, password):
#     imap = imaplib.IMAP4_SSL("imap.gmail.com")
#     imap.login(email_id, password)
#     imap.select("inbox")
#
#     result, data = imap.search(None, "ALL")
#     email_list = []
#
#     for num in data[0].split()[-50:]:  # last 50
#         res, msg_data = imap.fetch(num, "(RFC822)")
#         for response_part in msg_data:
#             if isinstance(response_part, tuple):
#                 msg = email.message_from_bytes(response_part[1])
#                 subject, encoding = decode_header(msg.get("Subject", ""))[0]
#                 if isinstance(subject, bytes):
#                     subject = subject.decode(encoding or "utf-8", errors="ignore")
#                 from_ = msg.get("From")
#                 category = categorize_email(msg)
#
#                 body = ""
#                 if msg.is_multipart():
#                     for part in msg.walk():
#                         content_type = part.get_content_type()
#                         if content_type == "text/plain" and part.get_payload(decode=True):
#                             body = part.get_payload(decode=True).decode(errors="ignore")
#                             break
#                 else:
#                     body = msg.get_payload(decode=True).decode(errors="ignore")
#
#                 email_list.append({
#                     "from": from_,
#                     "subject": clean_text(subject),
#                 })
#
#     imap.logout()
#     return email_list
#
# # 🧠 NLP endpoint
# @app.route("/ask", methods=["POST"])
# def ask():
#     data = request.get_json()
#     msg = data.get("message", "")
#     intent = classify_message(msg)
#     return jsonify(intent)
#
# # 📩 Emails by category
# @app.route("/emails", methods=["POST"])
# def get_emails():
#     data = request.get_json()
#     email_id = data.get("email")
#     password = data.get("password")
#     category = data.get("category")
#
#     try:
#         emails = fetch_emails(email_id, password)
#     except Exception as e:
#         return jsonify({"error": str(e)})
#
#     # filter by category
#     filtered = [e for e in emails if e["category"] == category]
#     global email_cache
#     email_cache = filtered
#
#     return jsonify({
#         "reply": f"📖 Email Details:\nFrom: {email['from']}\nSubject: {email['subject']}"
#     })
#
#
# # 📖 Email detail by index
# @app.route("/email_detail", methods=["POST"])
# def email_detail():
#     data = request.get_json()
#     index = data.get("index")
#
#     try:
#         email_data = email_cache[index]
#         return jsonify(email_data)
#     except Exception as e:
#         return jsonify({"error": "Invalid index or email not cached."})
#
# # 🟢 Run server
# if __name__ == "__main__":
#     app.run(debug=True)
from flask import Flask, request, jsonify
from flask_cors import CORS
import imaplib
import email
from email.header import decode_header
import re

app = Flask(__name__)
CORS(app)

stored_emails = []

def clean(text):
    return "".join(c if c.isalnum() else "_" for c in text)

def get_category(subject):
    subject = subject.lower()
    if any(keyword in subject for keyword in ['job', 'interview', 'resume', 'hiring']):
        return 'job'
    elif any(keyword in subject for keyword in ['order', 'invoice', 'payment', 'transaction']):
        return 'ecommerce'
    elif any(keyword in subject for keyword in ['spam', 'offer', 'win']):
        return 'spam'
    else:
        return 'uncategorized'

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    message = data.get("message", "").lower()

    if re.match(r"^\d+$", message.strip()):
        return jsonify({"intent": "show_detail", "index": int(message.strip()) - 1})

    elif any(word in message for word in ['job', 'jobs', 'interview']):
        return jsonify({"intent": "show_category", "category": "job"})
    elif any(word in message for word in ['order', 'payment', 'buy']):
        return jsonify({"intent": "show_category", "category": "ecommerce"})
    elif 'spam' in message:
        return jsonify({"intent": "show_category", "category": "spam"})
    else:
        return jsonify({"intent": "unknown"})

@app.route("/emails", methods=["POST"])
def fetch_emails():
    global stored_emails
    data = request.json
    user = data.get("email")
    password = data.get("password")
    category = data.get("category")

    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(user, password)
        imap.select("inbox")

        status, messages = imap.search(None, "ALL")
        mail_ids = messages[0].split()[-20:]

        emails = []
        for mail_id in reversed(mail_ids):
            res, msg = imap.fetch(mail_id, "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    msg_obj = email.message_from_bytes(response[1])
                    subject, encoding = decode_header(msg_obj["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")

                    from_ = msg_obj.get("From")
                    if msg_obj.is_multipart():
                        for part in msg_obj.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg_obj.get_payload(decode=True).decode(errors="ignore")

                    emails.append({
                        "from": from_,
                        "subject": subject.strip(),
                        "category": get_category(subject)
                    })

        imap.logout()

        filtered = [e for e in emails if e["category"] == category]
        stored_emails = filtered
        return jsonify({"emails": filtered})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/email_detail", methods=["POST"])
def email_detail():
    data = request.json
    index = data.get("index")
    if stored_emails and 0 <= index < len(stored_emails):
        return jsonify(stored_emails[index])
    return jsonify({"error": "Invalid index"}), 400

if __name__ == "__main__":
    app.run(debug=True)
