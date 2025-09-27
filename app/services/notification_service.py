import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from ..database.config import get_settings

# Initialize settings instance
settings = get_settings()


class NotificationService:
    """Service for sending notifications via email and SMS."""
    
    @staticmethod
    async def send_email(
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send email notification."""
        try:
            # In production, this would integrate with a real email service
            # like SendGrid, AWS SES, or SMTP
            if settings.SMTP_HOST:
                # Use configured SMTP settings
                await NotificationService._send_smtp_email(
                    recipient, subject, body, html_body
                )
            else:
                # Mock email sending for development
                await NotificationService._mock_send_email(
                    recipient, subject, body, html_body
                )
            
            print(f"Email sent to {recipient}: {subject}")
            return True
            
        except Exception as e:
            print(f"Error sending email to {recipient}: {e}")
            return False
    
    @staticmethod
    async def send_sms(
        recipient: str,
        message: str
    ) -> bool:
        """Send SMS notification."""
        try:
            # In production, this would integrate with a real SMS service
            # like Twilio, AWS SNS, or local SMS gateway
            if settings.SMS_API_KEY:
                # Use configured SMS service
                await NotificationService._send_sms_via_provider(
                    recipient, message
                )
            else:
                # Mock SMS sending for development
                await NotificationService._mock_send_sms(
                    recipient, message
                )
            
            print(f"SMS sent to {recipient}: {message[:50]}...")
            return True
            
        except Exception as e:
            print(f"Error sending SMS to {recipient}: {e}")
            return False
    
    @staticmethod
    async def send_booking_confirmation(
        email: str,
        booking_id: str,
        booking_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send booking confirmation email."""
        subject = "Booking Confirmation - Cheetah Transport"
        
        # Generate email body
        body = f"""
Dear Customer,

Your booking has been confirmed successfully!

Booking Reference: {booking_id}
Booking Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Thank you for choosing Cheetah Transport. Your journey includes:
- Free accident insurance coverage
- Free WiFi access during travel

For any questions, please contact our customer support.

Best regards,
Cheetah Transport Team
        """
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Booking Confirmation</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Booking Confirmation</h2>
        <p>Dear Customer,</p>
        <p>Your booking has been confirmed successfully!</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <strong>Booking Reference:</strong> {booking_id}<br>
            <strong>Booking Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        
        <p>Thank you for choosing Cheetah Transport. Your journey includes:</p>
        <ul>
            <li>✅ Free accident insurance coverage</li>
            <li>✅ Free WiFi access during travel</li>
        </ul>
        
        <p>For any questions, please contact our customer support.</p>
        
        <p>Best regards,<br>
        <strong>Cheetah Transport Team</strong></p>
    </div>
</body>
</html>
        """
        
        return await NotificationService.send_email(email, subject, body, html_body)
    
    @staticmethod
    async def send_insurance_details(
        email: str,
        policy_number: str,
        coverage_amount: float,
        start_date: str,
        end_date: str
    ) -> bool:
        """Send insurance policy details email."""
        subject = "Free Accident Insurance - Policy Details"
        
        body = f"""
Dear Customer,

Your free accident insurance policy has been activated!

Policy Number: {policy_number}
Coverage Amount: ₦{coverage_amount:,.2f}
Coverage Period: {start_date} to {end_date}

This policy provides comprehensive accident coverage during your journey.
For claims or questions, please contact our insurance partner.

Best regards,
Cheetah Transport Team
        """
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Insurance Policy Details</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Free Accident Insurance</h2>
        <p>Dear Customer,</p>
        <p>Your free accident insurance policy has been activated!</p>
        
        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <strong>Policy Number:</strong> {policy_number}<br>
            <strong>Coverage Amount:</strong> ₦{coverage_amount:,.2f}<br>
            <strong>Coverage Period:</strong> {start_date} to {end_date}
        </div>
        
        <p>This policy provides comprehensive accident coverage during your journey.</p>
        <p>For claims or questions, please contact our insurance partner.</p>
        
        <p>Best regards,<br>
        <strong>Cheetah Transport Team</strong></p>
    </div>
</body>
</html>
        """
        
        return await NotificationService.send_email(email, subject, body, html_body)
    
    @staticmethod
    async def send_wifi_details(
        email: str,
        wifi_code: str,
        expiry_time: str,
        bandwidth_limit_mb: int
    ) -> bool:
        """Send WiFi access details email."""
        subject = "Free WiFi Access - Your Access Code"
        
        body = f"""
Dear Customer,

Your free WiFi access has been activated!

WiFi Code: {wifi_code}
Expires: {expiry_time}
Bandwidth Limit: {bandwidth_limit_mb}MB

Use this code to connect to WiFi during your journey.
The code is valid only during your travel period.

Best regards,
Cheetah Transport Team
        """
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>WiFi Access Details</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Free WiFi Access</h2>
        <p>Dear Customer,</p>
        <p>Your free WiFi access has been activated!</p>
        
        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <strong>WiFi Code:</strong> <span style="font-family: monospace; font-size: 18px; font-weight: bold;">{wifi_code}</span><br>
            <strong>Expires:</strong> {expiry_time}<br>
            <strong>Bandwidth Limit:</strong> {bandwidth_limit_mb}MB
        </div>
        
        <p>Use this code to connect to WiFi during your journey.</p>
        <p>The code is valid only during your travel period.</p>
        
        <p>Best regards,<br>
        <strong>Cheetah Transport Team</strong></p>
    </div>
</body>
</html>
        """
        
        return await NotificationService.send_email(email, subject, body, html_body)
    
    @staticmethod
    async def send_booking_reminder(
        email: str,
        booking_reference: str,
        departure_time: str,
        origin: str,
        destination: str
    ) -> bool:
        """Send booking reminder email."""
        subject = "Travel Reminder - Your Journey Tomorrow"
        
        body = f"""
Dear Customer,

This is a friendly reminder about your upcoming journey.

Booking Reference: {booking_reference}
Departure Time: {departure_time}
Route: {origin} to {destination}

Please arrive at least 30 minutes before departure.
Don't forget to bring your booking confirmation and valid ID.

Safe travels!
Cheetah Transport Team
        """
        
        return await NotificationService.send_email(email, subject, body)
    
    @staticmethod
    async def send_booking_cancellation(
        email: str,
        booking_reference: str,
        refund_amount: Optional[float] = None
    ) -> bool:
        """Send booking cancellation email."""
        subject = "Booking Cancellation Confirmation"
        
        body = f"""
Dear Customer,

Your booking has been cancelled successfully.

Booking Reference: {booking_reference}
"""
        
        if refund_amount:
            body += f"Refund Amount: ₦{refund_amount:,.2f}\n"
        
        body += """
The refund will be processed within 5-7 business days.

We hope to serve you again soon.

Best regards,
Cheetah Transport Team
        """
        
        return await NotificationService.send_email(email, subject, body)
    
    # Private methods for actual email/SMS sending
    @staticmethod
    async def _send_smtp_email(
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ):
        """Send email via SMTP."""
        # This would implement actual SMTP email sending
        # For now, just simulate the process
        await asyncio.sleep(0.1)
        print(f"SMTP Email sent to {recipient}")
    
    @staticmethod
    async def _mock_send_email(
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ):
        """Mock email sending for development."""
        await asyncio.sleep(0.1)
        print(f"Mock Email sent to {recipient}")
        print(f"Subject: {subject}")
        print(f"Body: {body[:100]}...")
    
    @staticmethod
    async def _send_sms_via_provider(
        recipient: str,
        message: str
    ):
        """Send SMS via configured provider."""
        # This would implement actual SMS sending
        # For now, just simulate the process
        await asyncio.sleep(0.1)
        print(f"SMS sent to {recipient} via provider")
    
    @staticmethod
    async def _mock_send_sms(
        recipient: str,
        message: str
    ):
        """Mock SMS sending for development."""
        await asyncio.sleep(0.1)
        print(f"Mock SMS sent to {recipient}")
        print(f"Message: {message[:50]}...") 