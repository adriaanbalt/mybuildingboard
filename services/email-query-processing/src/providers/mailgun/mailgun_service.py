"""
Mailgun Email Service Implementation

Implements EmailService interface for Mailgun API.
Supports receiving emails via webhooks (inbound routes) and sending via REST API.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
import base64
from email.utils import parseaddr, parsedate_to_datetime
from email.message import EmailMessage
import email

from ...interfaces.email_service import EmailService
from ...types.email import (
    Email,
    EmailAttachment,
    EmailSender,
    EmailRecipients,
    Inbox,
    ProviderCapabilities,
    WatchHandle,
    RateLimitInfo,
)


class MailgunEmailService(EmailService):
    """
    Mailgun API implementation of EmailService.
    
    Uses API key authentication and supports:
    - Receiving emails via webhooks (inbound routes)
    - Sending emails via REST API
    """
    
    MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25MB
    API_BASE_URL = "https://api.mailgun.net/v3"
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Mailgun email service.
        
        Args:
            config: Mailgun configuration with API key and domain
        """
        self.config = config
        self.api_key = config.get('api_key') or config.get('credentials', {}).get('api_key')
        self.domain = config.get('domain') or config.get('credentials', {}).get('domain')
        self.inbox_address = config.get('inbox_address', '')
        
        if not self.api_key:
            raise ValueError("Mailgun API key is required")
        if not self.domain:
            raise ValueError("Mailgun domain is required")
        
        self._webhook_url = config.get('webhook_url')  # URL for receiving webhooks
        self._processed_emails = set()  # Track processed emails (in-memory, should use DB in production)
    
    def fetchEmails(self, inbox: str, since: Optional[datetime] = None) -> List[Email]:
        """
        Fetch emails from Mailgun.
        
        Note: Mailgun doesn't support polling for received emails.
        Emails are received via webhooks (inbound routes).
        This method returns empty list as Mailgun uses webhooks, not polling.
        
        Args:
            inbox: Inbox address (not used for Mailgun)
            since: Optional date (not used for Mailgun)
            
        Returns:
            Empty list (Mailgun uses webhooks, not polling)
        """
        # Mailgun doesn't support polling - emails come via webhooks
        # Return empty list and log warning
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Mailgun doesn't support polling. Use webhooks (watchInbox) instead.")
        return []
    
    def getEmailById(self, emailId: str) -> Optional[Email]:
        """
        Get email by Mailgun storage URL or event ID.
        
        Note: Mailgun doesn't provide a direct API to fetch stored emails.
        This method attempts to retrieve from Mailgun's storage API if available.
        
        Args:
            emailId: Mailgun storage URL or event ID
            
        Returns:
            Email object or None
        """
        # Mailgun doesn't have a direct "get email by ID" API
        # Emails are typically retrieved via webhooks or events API
        # For now, return None - emails should be processed via webhooks
        return None
    
    def markAsProcessed(self, emailId: str, label: Optional[str] = None) -> None:
        """
        Mark email as processed.
        
        Note: Mailgun doesn't support labels. This method tracks processed emails
        in memory (should use database in production).
        
        Args:
            emailId: Mailgun email ID or storage URL
            label: Not used for Mailgun
        """
        # Track processed emails (in production, use database)
        self._processed_emails.add(emailId)
    
    def sendEmail(
        self,
        to: str,
        subject: str,
        body: str,
        htmlBody: Optional[str] = None,
        inReplyTo: Optional[str] = None
    ) -> None:
        """
        Send email via Mailgun API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            htmlBody: Optional HTML body
            inReplyTo: Optional email ID to reply to (sets In-Reply-To header)
        """
        url = f"{self.API_BASE_URL}/{self.domain}/messages"
        
        data = {
            'from': self.inbox_address or f"noreply@{self.domain}",
            'to': to,
            'subject': subject,
            'text': body,
        }
        
        if htmlBody:
            data['html'] = htmlBody
        
        if inReplyTo:
            data['h:In-Reply-To'] = inReplyTo
            data['h:References'] = inReplyTo
        
        response = requests.post(
            url,
            auth=('api', self.api_key),
            data=data,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to send email via Mailgun: {response.status_code} - {response.text}")
    
    def getAttachment(self, emailId: str, attachmentId: str) -> bytes:
        """
        Get email attachment.
        
        Note: Mailgun stores attachments in webhook payloads. This method
        attempts to retrieve from Mailgun's storage if available.
        
        Args:
            emailId: Mailgun email ID or storage URL
            attachmentId: Attachment identifier
            
        Returns:
            Attachment data as bytes
        """
        # Mailgun attachments are typically received in webhook payloads
        # For stored emails, would need to use Mailgun's storage API
        # For now, raise NotImplementedError
        raise NotImplementedError("Mailgun attachment retrieval not yet implemented. Attachments should be processed from webhook payloads.")
    
    def listInboxes(self) -> List[Inbox]:
        """
        List available inboxes (Mailgun domains).
        
        Returns:
            List of inboxes (domains)
        """
        return [Inbox(
            id=self.domain,
            name=f"Mailgun Domain: {self.domain}",
            address=self.inbox_address or f"noreply@{self.domain}"
        )]
    
    def watchInbox(self, inbox: str, callback: callable) -> WatchHandle:
        """
        Watch inbox for new emails via Mailgun webhooks.
        
        Note: This sets up the webhook configuration. The actual webhook
        endpoint should be configured in Mailgun dashboard (inbound routes).
        
        Args:
            inbox: Inbox address
            callback: Callback function for new emails
            
        Returns:
            Watch handle
        """
        # Mailgun webhooks are configured in Mailgun dashboard, not via API
        # This method returns a handle but the actual webhook setup is manual
        # The webhook URL should be set in config and configured in Mailgun dashboard
        return WatchHandle(id=f"mailgun-{self.domain}")
    
    def parseWebhookPayload(self, payload: Dict[str, Any]) -> Optional[Email]:
        """
        Parse Mailgun webhook payload to Email object.
        
        This is a helper method for processing Mailgun inbound webhooks.
        Call this from your webhook endpoint when Mailgun POSTs email data.
        
        Args:
            payload: Mailgun webhook payload (form data)
            
        Returns:
            Email object or None if invalid
        """
        try:
            # Extract sender
            sender_email = payload.get('sender', '').strip()
            sender_name = None
            if '<' in sender_email:
                sender_name, sender_email = parseaddr(sender_email)
            else:
                sender_email = sender_email.split('@')[0] if '@' in sender_email else sender_email
            
            # Extract recipients
            to_emails = [e.strip() for e in payload.get('recipient', '').split(',')]
            cc_emails = [e.strip() for e in payload.get('Cc', '').split(',')] if payload.get('Cc') else []
            
            # Extract subject
            subject = payload.get('subject', '')
            
            # Extract body
            body_text = payload.get('body-plain', '')
            body_html = payload.get('body-html')
            
            # Extract date
            date_str = payload.get('Date') or payload.get('timestamp', '')
            if date_str:
                try:
                    if isinstance(date_str, str) and date_str.isdigit():
                        # Unix timestamp
                        received_at = datetime.fromtimestamp(int(date_str))
                    else:
                        # RFC 2822 date
                        received_at = parsedate_to_datetime(date_str)
                except:
                    received_at = datetime.utcnow()
            else:
                received_at = datetime.utcnow()
            
            # Extract thread ID (from Message-ID or In-Reply-To)
            thread_id = payload.get('In-Reply-To') or payload.get('References', '').split()[0] if payload.get('References') else None
            
            # Extract attachments
            attachments = []
            attachment_count = int(payload.get('attachment-count', 0))
            for i in range(1, attachment_count + 1):
                attachment_name = payload.get(f'attachment-{i}')
                attachment_size = int(payload.get(f'attachment-size-{i}', 0))
                attachment_content_type = payload.get(f'attachment-content-type-{i}', 'application/octet-stream')
                
                if attachment_name:
                    attachments.append(EmailAttachment(
                        id=f"attachment-{i}",
                        filename=attachment_name,
                        contentType=attachment_content_type,
                        size=attachment_size
                    ))
            
            # Create email ID from Message-ID or generate one
            email_id = payload.get('Message-Id') or payload.get('message-id') or f"mailgun-{received_at.timestamp()}"
            
            return Email(
                id=email_id,
                providerType='mailgun',
                threadId=thread_id,
                sender=EmailSender(
                    email=sender_email,
                    name=sender_name
                ),
                recipients=EmailRecipients(
                    to=to_emails,
                    cc=cc_emails if cc_emails else None
                ),
                subject=subject,
                bodyText=body_text,
                bodyHtml=body_html,
                receivedAt=received_at,
                attachments=attachments if attachments else None,
                metadata={
                    'mailgun_id': email_id,
                    'message_id': payload.get('Message-Id'),
                    'signature': payload.get('signature'),
                    'token': payload.get('token'),
                    'timestamp': payload.get('timestamp'),
                    'domain': self.domain
                }
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to parse Mailgun webhook payload: {e}")
            return None
    
    def getProviderName(self) -> str:
        """Get provider name."""
        return 'mailgun'
    
    def getProviderCapabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return ProviderCapabilities(
            supportsWebhooks=True,  # Via inbound routes
            supportsPolling=False,  # Mailgun doesn't support polling
            supportsLabels=False,  # Mailgun doesn't support labels
            supportsThreading=True,  # Via In-Reply-To header
            maxAttachmentSize=self.MAX_ATTACHMENT_SIZE,
            rateLimits=RateLimitInfo(
                requestsPerDay=1000  # Free tier: 1000 emails/day
            ),
            authenticationType='api_key'
        )
