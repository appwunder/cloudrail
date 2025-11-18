import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime
import requests

from app.models.budget import Budget, BudgetAlert
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via email, Slack, and webhooks"""

    @staticmethod
    def send_email(
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email notification using SMTP"""
        try:
            # Check if SMTP is configured
            if not hasattr(settings, 'SMTP_HOST') or not settings.SMTP_HOST:
                logger.warning("SMTP not configured, skipping email notification")
                return False

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = ', '.join(to_emails)

            # Add text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)

            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_emails, msg.as_string())

            logger.info(f"Email sent successfully to {to_emails}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    @staticmethod
    def send_slack_notification(webhook_url: str, message: dict) -> bool:
        """Send notification to Slack via webhook"""
        try:
            response = requests.post(webhook_url, json=message, timeout=10)
            response.raise_for_status()
            logger.info("Slack notification sent successfully")
            return True

        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False

    @staticmethod
    def send_custom_webhook(webhook_url: str, data: dict) -> bool:
        """Send notification to custom webhook"""
        try:
            response = requests.post(webhook_url, json=data, timeout=10)
            response.raise_for_status()
            logger.info(f"Webhook notification sent successfully to {webhook_url}")
            return True

        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False

    @staticmethod
    def generate_budget_alert_email(budget: Budget, alert: BudgetAlert) -> tuple[str, str, str]:
        """Generate email subject and content for a budget alert"""

        # Determine alert severity
        if alert.percentage_used >= 100:
            severity = "🔴 CRITICAL"
            severity_color = "#dc2626"
        elif alert.percentage_used >= budget.threshold_percentage:
            severity = "🟡 WARNING"
            severity_color = "#f59e0b"
        else:
            severity = "🟢 INFO"
            severity_color = "#10b981"

        # Subject
        subject = f"{severity}: Budget Alert - {budget.name}"

        # Text content
        text_content = f"""
CloudCostly Budget Alert

Budget: {budget.name}
Status: {severity}
Current Spending: ${alert.current_amount:,.2f}
Budget Amount: ${alert.budget_amount:,.2f}
Percentage Used: {alert.percentage_used:.1f}%
Threshold: {budget.threshold_percentage}%

Period: {alert.period_start.strftime('%Y-%m-%d')} to {alert.period_end.strftime('%Y-%m-%d')}

{'Your budget has been exceeded!' if alert.percentage_used >= 100 else 'Your spending is approaching the budget threshold.'}

View your budget details at: {settings.FRONTEND_URL}/budgets

---
CloudCostly - Cloud Cost Optimization Platform
        """.strip()

        # HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px 8px 0 0;
            text-align: center;
        }}
        .content {{
            background: #ffffff;
            padding: 30px;
            border: 1px solid #e5e7eb;
            border-top: none;
        }}
        .alert-box {{
            background: {severity_color};
            color: white;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
            text-align: center;
            font-size: 18px;
            font-weight: bold;
        }}
        .stats {{
            background: #f9fafb;
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e5e7eb;
        }}
        .stat-row:last-child {{
            border-bottom: none;
        }}
        .stat-label {{
            font-weight: 600;
            color: #6b7280;
        }}
        .stat-value {{
            font-weight: bold;
            color: #111827;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e5e7eb;
            border-radius: 15px;
            overflow: hidden;
            margin: 15px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: {severity_color};
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 14px;
        }}
        .button {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6b7280;
            font-size: 14px;
            border-top: 1px solid #e5e7eb;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin: 0;">💰 CloudCostly</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">Budget Alert Notification</p>
    </div>

    <div class="content">
        <div class="alert-box">
            {severity} - Budget Threshold Alert
        </div>

        <h2>{budget.name}</h2>
        <p>{budget.description or 'Budget monitoring alert'}</p>

        <div class="progress-bar">
            <div class="progress-fill" style="width: {min(alert.percentage_used, 100)}%;">
                {alert.percentage_used:.1f}%
            </div>
        </div>

        <div class="stats">
            <div class="stat-row">
                <span class="stat-label">Current Spending</span>
                <span class="stat-value">${alert.current_amount:,.2f}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Budget Amount</span>
                <span class="stat-value">${alert.budget_amount:,.2f}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Remaining</span>
                <span class="stat-value">${max(alert.budget_amount - alert.current_amount, 0):,.2f}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Threshold</span>
                <span class="stat-value">{budget.threshold_percentage}%</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Period</span>
                <span class="stat-value">{alert.period_start.strftime('%b %d')} - {alert.period_end.strftime('%b %d, %Y')}</span>
            </div>
        </div>

        <p>
            {'<strong>⚠️ Your budget has been exceeded!</strong> Please review your cloud spending to identify optimization opportunities.' if alert.percentage_used >= 100 else '<strong>⚠️ Your spending is approaching the budget threshold.</strong> Consider reviewing your cloud resources to prevent budget overruns.'}
        </p>

        <center>
            <a href="{settings.FRONTEND_URL}/budgets" class="button">
                View Budget Details →
            </a>
        </center>
    </div>

    <div class="footer">
        <p>This is an automated notification from CloudCostly.</p>
        <p>© {datetime.now().year} CloudCostly - Cloud Cost Optimization Platform</p>
    </div>
</body>
</html>
        """.strip()

        return subject, text_content, html_content

    @staticmethod
    def generate_slack_message(budget: Budget, alert: BudgetAlert) -> dict:
        """Generate Slack message for a budget alert"""

        # Determine color based on percentage
        if alert.percentage_used >= 100:
            color = "danger"
            emoji = "🔴"
        elif alert.percentage_used >= budget.threshold_percentage:
            color = "warning"
            emoji = "🟡"
        else:
            color = "good"
            emoji = "🟢"

        return {
            "text": f"{emoji} Budget Alert: {budget.name}",
            "attachments": [
                {
                    "color": color,
                    "title": f"{budget.name} - Budget Alert",
                    "text": f"Current spending has reached {alert.percentage_used:.1f}% of the budget",
                    "fields": [
                        {
                            "title": "Current Spending",
                            "value": f"${alert.current_amount:,.2f}",
                            "short": True
                        },
                        {
                            "title": "Budget Amount",
                            "value": f"${alert.budget_amount:,.2f}",
                            "short": True
                        },
                        {
                            "title": "Percentage Used",
                            "value": f"{alert.percentage_used:.1f}%",
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": f"{budget.threshold_percentage}%",
                            "short": True
                        },
                        {
                            "title": "Period",
                            "value": f"{alert.period_start.strftime('%Y-%m-%d')} to {alert.period_end.strftime('%Y-%m-%d')}",
                            "short": False
                        }
                    ],
                    "footer": "CloudCostly",
                    "footer_icon": "https://cloudcostly.com/icon.png",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }

    @staticmethod
    def send_budget_alert(budget: Budget, alert: BudgetAlert) -> dict:
        """Send budget alert through all configured notification channels"""
        results = {
            "email": False,
            "slack": False,
            "webhook": False,
            "channels_used": []
        }

        # Send email notification
        if "email" in budget.notification_channels and budget.notification_emails:
            subject, text_content, html_content = NotificationService.generate_budget_alert_email(budget, alert)
            if NotificationService.send_email(budget.notification_emails, subject, html_content, text_content):
                results["email"] = True
                results["channels_used"].append("email")

        # Send Slack notification
        if "slack" in budget.notification_channels and budget.slack_webhook_url:
            slack_message = NotificationService.generate_slack_message(budget, alert)
            if NotificationService.send_slack_notification(budget.slack_webhook_url, slack_message):
                results["slack"] = True
                results["channels_used"].append("slack")

        # Send custom webhook notification
        if "webhook" in budget.notification_channels and budget.custom_webhook_url:
            webhook_data = {
                "event": "budget_alert",
                "budget_id": str(budget.id),
                "budget_name": budget.name,
                "alert_type": alert.alert_type,
                "current_amount": alert.current_amount,
                "budget_amount": alert.budget_amount,
                "percentage_used": alert.percentage_used,
                "period_start": alert.period_start.isoformat(),
                "period_end": alert.period_end.isoformat(),
                "timestamp": datetime.now().isoformat()
            }
            if NotificationService.send_custom_webhook(budget.custom_webhook_url, webhook_data):
                results["webhook"] = True
                results["channels_used"].append("webhook")

        return results
