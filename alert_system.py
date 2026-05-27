"""
Radioactive Water Predictor — NGO Alert System
================================================
Sends water quality reports to nearby NGOs via Email (primary)
or SMS (fallback via Twilio) when dangerous contamination is detected.
"""

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import (
    GMAIL_USER, GMAIL_APP_PASSWORD, NGO_EMAILS,
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, NGO_PHONE_NUMBERS,
    ALERT_COOLDOWN_MINUTES,
)

# Track last alert time for rate limiting
_last_alert_time = 0
_alert_history = []


def _can_send_alert() -> bool:
    """Check if enough time has passed since the last alert."""
    global _last_alert_time
    now = time.time()
    if now - _last_alert_time < ALERT_COOLDOWN_MINUTES * 60:
        remaining = int((ALERT_COOLDOWN_MINUTES * 60 - (now - _last_alert_time)) / 60)
        return False
    return True


def _build_html_report(analysis: dict) -> str:
    """Build a beautiful HTML email report from the analysis data."""
    params = analysis.get("parameters", {})
    element = analysis.get("radioactive_element", {})
    risk = analysis.get("risk_level", {})
    score = analysis.get("risk_score", 0)
    location = analysis.get("location", "Unknown")
    timestamp = analysis.get("timestamp", datetime.now().isoformat())
    comparison = analysis.get("comparison", [])
    
    # Build parameter rows
    param_rows = ""
    for comp in comparison:
        status_color = comp["color"]
        param_rows += f"""
        <tr>
            <td style="padding:8px; border-bottom:1px solid #333;">{comp['parameter']}</td>
            <td style="padding:8px; border-bottom:1px solid #333;">{comp['value']} {comp['unit']}</td>
            <td style="padding:8px; border-bottom:1px solid #333;">{comp['safe_min']} – {comp['safe_max']} {comp['unit']}</td>
            <td style="padding:8px; border-bottom:1px solid #333; color:{status_color}; font-weight:bold;">{comp['status']}</td>
        </tr>"""
    
    html = f"""
    <html>
    <body style="background:#0a0a0a; color:#e0e0e0; font-family:Arial,sans-serif; padding:20px;">
        <div style="max-width:700px; margin:0 auto; background:#111; border-radius:16px; padding:30px; border:1px solid #333;">
            
            <h1 style="text-align:center; color:#FF4444; margin-bottom:5px;">
                ☢️ RADIOACTIVE WATER ALERT
            </h1>
            <p style="text-align:center; color:#FFD300; font-size:14px; margin-top:0;">
                Automated Report from Radioactive Water Predictor System
            </p>
            
            <hr style="border-color:#333;">
            
            <div style="background:#1a1a1a; padding:15px; border-radius:12px; margin:15px 0;">
                <h3 style="color:#FFD300; margin-top:0;">📍 Location: {location}</h3>
                <p style="color:#aaa;">🕐 Timestamp: {timestamp}</p>
                <p style="color:{risk['color']}; font-size:24px; font-weight:bold;">
                    {risk['emoji']} Risk Level: {risk['level']} ({score}%)
                </p>
            </div>
            
            <div style="background:#1a1a1a; padding:15px; border-radius:12px; margin:15px 0;">
                <h3 style="color:#FF7518; margin-top:0;">☢️ Detected Radioactive Element</h3>
                <table style="width:100%; color:#e0e0e0;">
                    <tr><td style="padding:5px; color:#aaa;">Element:</td><td style="padding:5px; font-weight:bold; color:{element.get('color', '#fff')};">{element.get('element', 'Unknown')}</td></tr>
                    <tr><td style="padding:5px; color:#aaa;">Isotope:</td><td style="padding:5px;">{element.get('isotope', '—')}</td></tr>
                    <tr><td style="padding:5px; color:#aaa;">Half-Life:</td><td style="padding:5px;">{element.get('half_life', '—')}</td></tr>
                    <tr><td style="padding:5px; color:#aaa;">Description:</td><td style="padding:5px;">{element.get('description', '')}</td></tr>
                    <tr><td style="padding:5px; color:#aaa;">Health Effects:</td><td style="padding:5px; color:#FF4444;">{element.get('health_effects', '')}</td></tr>
                </table>
            </div>
            
            <div style="background:#1a1a1a; padding:15px; border-radius:12px; margin:15px 0;">
                <h3 style="color:#39FF14; margin-top:0;">📊 Water Quality Parameters</h3>
                <table style="width:100%; color:#e0e0e0; border-collapse:collapse;">
                    <tr style="background:#222;">
                        <th style="padding:8px; text-align:left; border-bottom:2px solid #444;">Parameter</th>
                        <th style="padding:8px; text-align:left; border-bottom:2px solid #444;">Value</th>
                        <th style="padding:8px; text-align:left; border-bottom:2px solid #444;">Safe Range</th>
                        <th style="padding:8px; text-align:left; border-bottom:2px solid #444;">Status</th>
                    </tr>
                    {param_rows}
                </table>
            </div>
            
            <div style="background:#2a1010; padding:15px; border-radius:12px; margin:15px 0; border:1px solid #FF4444;">
                <h3 style="color:#FF4444; margin-top:0;">⚠️ Recommended Actions</h3>
                <p style="color:#e0e0e0;">{risk.get('advice', 'Contact local health authorities.')}</p>
                <ul style="color:#ddd;">
                    <li>Do NOT consume this water without proper treatment</li>
                    <li>Notify local health authorities immediately</li>
                    <li>Arrange for certified laboratory testing</li>
                    <li>Secure the water source to prevent public access</li>
                </ul>
            </div>
            
            <hr style="border-color:#333;">
            <p style="text-align:center; color:#666; font-size:12px;">
                This is an automated alert from the Radioactive Water Predictor System.<br>
                For emergencies, contact your local disaster response authority.
            </p>
        </div>
    </body>
    </html>
    """
    return html


def _build_sms_text(analysis: dict) -> str:
    """Build a concise SMS text from the analysis data."""
    params = analysis.get("parameters", {})
    element = analysis.get("radioactive_element", {})
    risk = analysis.get("risk_level", {})
    score = analysis.get("risk_score", 0)
    location = analysis.get("location", "Unknown")
    
    return (
        f"☢️ RADIOACTIVE WATER ALERT\n"
        f"Location: {location}\n"
        f"Risk: {risk['level']} ({score}%)\n"
        f"TDS: {params.get('tds', 0)} mg/L\n"
        f"Element: {element.get('element', 'Unknown')} ({element.get('isotope', '')})\n"
        f"pH: {params.get('ph', 0)} | Nitrate: {params.get('nitrate', 0)} mg/L\n"
        f"ACTION: Do NOT drink. Contact health authorities."
    )


def send_email_alert(analysis: dict, custom_email: str = None) -> dict:
    """
    Send HTML water quality report to NGO email addresses.
    If custom_email is provided, sends to that address instead of config defaults.
    """
    if not GMAIL_USER or GMAIL_USER == "your-email@gmail.com":
        return {"success": False, "method": "email", "message": "Gmail not configured. Update config.py with your Gmail credentials."}
    
    # Use custom email if provided, otherwise fall back to config
    recipients = [custom_email] if custom_email else NGO_EMAILS
    
    if not recipients:
        return {"success": False, "method": "email", "message": "No NGO email addresses configured."}
    
    try:
        html_body = _build_html_report(analysis)
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"RADIOACTIVE WATER ALERT - Risk: {analysis.get('risk_score', 0)}% - {analysis.get('location', 'Unknown')}"
        msg["From"] = GMAIL_USER
        msg["To"] = ", ".join(recipients)
        
        msg.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, recipients, msg.as_string())
        
        return {"success": True, "method": "email", "message": f"Alert sent to {', '.join(recipients)} via email."}
    
    except Exception as e:
        return {"success": False, "method": "email", "message": f"Email failed: {str(e)}"}


def send_sms_alert(analysis: dict) -> dict:
    """
    Send SMS alert to NGO phone numbers via Twilio.
    Used as fallback when email fails.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return {"success": False, "method": "sms", "message": "Twilio not configured. Update config.py with Twilio credentials."}
    
    if not NGO_PHONE_NUMBERS:
        return {"success": False, "method": "sms", "message": "No NGO phone numbers configured."}
    
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        sms_body = _build_sms_text(analysis)
        sent_count = 0
        
        for phone in NGO_PHONE_NUMBERS:
            message = client.messages.create(
                body=sms_body,
                from_=TWILIO_FROM_NUMBER,
                to=phone,
            )
            sent_count += 1
        
        return {"success": True, "method": "sms", "message": f"SMS sent to {sent_count} number(s)."}
    
    except Exception as e:
        return {"success": False, "method": "sms", "message": f"SMS failed: {str(e)}"}


def send_alert(analysis: dict, custom_email: str = None) -> dict:
    """
    Send alert to NGOs. Tries email first, falls back to SMS.
    If custom_email is provided, sends to that address.
    """
    global _last_alert_time, _alert_history
    
    # Try email first
    result = send_email_alert(analysis, custom_email=custom_email)
    
    # If email fails, try SMS as fallback
    if not result["success"]:
        sms_result = send_sms_alert(analysis)
        if sms_result["success"]:
            result = sms_result
        else:
            # Both failed
            result["message"] += f" | SMS fallback: {sms_result['message']}"
    
    # Update rate limiter and history
    if result["success"]:
        _last_alert_time = time.time()
        _alert_history.append({
            "timestamp": datetime.now().isoformat(),
            "method": result["method"],
            "risk_score": analysis.get("risk_score", 0),
            "location": analysis.get("location", "Unknown"),
        })
    
    return result


def get_alert_history() -> list:
    """Return history of sent alerts."""
    return list(reversed(_alert_history))
