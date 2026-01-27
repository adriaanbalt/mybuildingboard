"""
Gmail Email Service Implementation

Implements EmailService interface for Gmail API.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
from typing import Dict, Any


class GmailEmailService(EmailService):
    """
    Gmail API implementation of EmailService.
    
    Uses OAuth2 authentication and Gmail API v1.
    """

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']
    MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25MB

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Gmail email service.
        
        Args:
            config: Gmail configuration with credentials
        """
        self.config = config
        self.service = None
        self.inbox_address = config.get('inbox_address', '')
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Gmail API using OAuth2."""
        creds_dict = self.config.get('credentials', {})
        creds = Credentials(
            token=creds_dict.get('access_token'),
            refresh_token=creds_dict.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=creds_dict.get('client_id'),
            client_secret=creds_dict.get('client_secret'),
        )

        # Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        if not creds or not creds.valid:
            raise ValueError("Invalid Gmail credentials")

        self.service = build('gmail', 'v1', credentials=creds)

    def fetchEmails(self, inbox: str, since: Optional[datetime] = None) -> List[Email]:
        """
        Fetch emails from Gmail inbox.
        
        Args:
            inbox: Email address (not used for Gmail, uses authenticated user)
            since: Optional date to fetch emails since
            
        Returns:
            List of Email objects
        """
        try:
            query = 'in:inbox'
            if since:
                # Gmail query format: after:YYYY/MM/DD
                query += f' after:{since.strftime("%Y/%m/%d")}'
            
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email = self.getEmailById(msg['id'])
                if email:
                    emails.append(email)
            
            return emails
        except HttpError as error:
            raise Exception(f"Failed to fetch emails: {error}")

    def getEmailById(self, emailId: str) -> Optional[Email]:
        """
        Get email by Gmail message ID.
        
        Args:
            emailId: Gmail message ID
            
        Returns:
            Email object or None
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=emailId,
                format='full'
            ).execute()
            
            return self._parseGmailMessage(message)
        except HttpError as error:
            if error.resp.status == 404:
                return None
            raise Exception(f"Failed to get email: {error}")

    def _parseGmailMessage(self, message: Dict[str, Any]) -> Email:
        """
        Parse Gmail API message to Email model.
        
        Args:
            message: Gmail API message object
            
        Returns:
            Email object
        """
        headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
        
        # Extract sender
        sender_email = headers.get('From', '').split('<')[-1].replace('>', '').strip()
        sender_name = headers.get('From', '').split('<')[0].strip() if '<' in headers.get('From', '') else None
        
        # Extract recipients
        to_emails = [e.strip() for e in headers.get('To', '').split(',')]
        cc_emails = [e.strip() for e in headers.get('Cc', '').split(',')] if headers.get('Cc') else []
        
        # Extract body
        body_text, body_html = self._extractBody(message['payload'])
        
        # Extract attachments
        attachments = self._extractAttachments(message['payload'])
        
        # Extract date
        received_at = datetime.fromtimestamp(int(message['internalDate']) / 1000)
        
        return Email(
            id=message['id'],
            providerType='gmail',
            threadId=message.get('threadId'),
            sender=EmailSender(
                email=sender_email,
                name=sender_name
            ),
            recipients=EmailRecipients(
                to=to_emails,
                cc=cc_emails if cc_emails else None
            ),
            subject=headers.get('Subject', ''),
            bodyText=body_text,
            bodyHtml=body_html,
            receivedAt=received_at,
            attachments=attachments if attachments else None,
            metadata={
                'gmail_id': message['id'],
                'thread_id': message.get('threadId'),
                'label_ids': message.get('labelIds', [])
            }
        )

    def _extractBody(self, payload: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Extract plain text and HTML body from Gmail message payload."""
        body_text = ''
        body_html = None
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    data = part['body'].get('data')
                    if data:
                        body_html = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data')
                if data:
                    body_text = base64.urlsafe_b64decode(data).decode('utf-8')
            elif payload['mimeType'] == 'text/html':
                data = payload['body'].get('data')
                if data:
                    body_html = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body_text, body_html

    def _extractAttachments(self, payload: Dict[str, Any]) -> List[EmailAttachment]:
        """Extract attachments from Gmail message payload."""
        attachments = []
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename') and part['body'].get('attachmentId'):
                    attachments.append(EmailAttachment(
                        id=part['body']['attachmentId'],
                        filename=part['filename'],
                        contentType=part['mimeType'],
                        size=part['body'].get('size', 0)
                    ))
        
        return attachments

    def markAsProcessed(self, emailId: str, label: Optional[str] = None) -> None:
        """
        Mark email as processed by adding label or marking as read.
        
        Args:
            emailId: Gmail message ID
            label: Optional label name (defaults to "Processed")
        """
        try:
            label_name = label or 'Processed'
            
            # Get or create label
            labels = self.service.users().labels().list(userId='me').execute()
            label_id = None
            for lbl in labels.get('labels', []):
                if lbl['name'] == label_name:
                    label_id = lbl['id']
                    break
            
            if not label_id:
                # Create label if it doesn't exist
                label_obj = self.service.users().labels().create(
                    userId='me',
                    body={'name': label_name, 'labelListVisibility': 'labelShow'}
                ).execute()
                label_id = label_obj['id']
            
            # Add label to message
            self.service.users().messages().modify(
                userId='me',
                id=emailId,
                body={'addLabelIds': [label_id]}
            ).execute()
        except HttpError as error:
            raise Exception(f"Failed to mark email as processed: {error}")

    def sendEmail(
        self,
        to: str,
        subject: str,
        body: str,
        htmlBody: Optional[str] = None,
        inReplyTo: Optional[str] = None
    ) -> None:
        """
        Send email via Gmail API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            htmlBody: Optional HTML body
            inReplyTo: Optional email ID to reply to
        """
        try:
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject
            
            if inReplyTo:
                message['In-Reply-To'] = inReplyTo
                message['References'] = inReplyTo
            
            message.attach(MIMEText(body, 'plain'))
            if htmlBody:
                message.attach(MIMEText(htmlBody, 'html'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
        except HttpError as error:
            raise Exception(f"Failed to send email: {error}")

    def getAttachment(self, emailId: str, attachmentId: str) -> bytes:
        """
        Get email attachment data.
        
        Args:
            emailId: Gmail message ID
            attachmentId: Gmail attachment ID
            
        Returns:
            Attachment data as bytes
        """
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=emailId,
                id=attachmentId
            ).execute()
            
            return base64.urlsafe_b64decode(attachment['data'])
        except HttpError as error:
            raise Exception(f"Failed to get attachment: {error}")

    def listInboxes(self) -> List[Inbox]:
        """
        List available inboxes (Gmail only has one inbox per user).
        
        Returns:
            List of inboxes
        """
        return [Inbox(
            id='me',
            name='Inbox',
            address=self.inbox_address
        )]

    def watchInbox(self, inbox: str, callback: callable) -> WatchHandle:
        """
        Watch inbox for new emails (Gmail Push notifications).
        
        Args:
            inbox: Inbox address (not used for Gmail)
            callback: Callback function for new emails
            
        Returns:
            Watch handle
        """
        # TODO: Implement Gmail Push notifications
        # This requires setting up a Pub/Sub topic and subscription
        raise NotImplementedError("Gmail Push notifications not yet implemented")

    def getProviderName(self) -> str:
        """Get provider name."""
        return 'gmail'

    def getProviderCapabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return ProviderCapabilities(
            supportsWebhooks=True,  # Via Gmail Push notifications
            supportsPolling=True,
            supportsLabels=True,
            supportsThreading=True,
            maxAttachmentSize=self.MAX_ATTACHMENT_SIZE,
            rateLimits=RateLimitInfo(
                quotaUnits=250  # 250 quota units per user per second
            ),
            authenticationType='oauth2'
        )
