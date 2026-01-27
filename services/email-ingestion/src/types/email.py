"""
Email Service Types

Provider-agnostic types for email operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class EmailAttachment:
    """Email attachment."""
    id: str  # Provider-specific attachment ID
    filename: str
    contentType: str
    size: int
    data: Optional[bytes] = None  # Optional: inline data


@dataclass
class EmailSender:
    """Email sender information."""
    email: str
    name: Optional[str] = None


@dataclass
class EmailRecipients:
    """Email recipients."""
    to: List[str]
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


@dataclass
class Email:
    """Provider-agnostic Email model."""
    id: str  # Provider-specific ID (Gmail ID, IMAP UID, etc.)
    providerType: str  # "gmail", "imap", "sendgrid", etc.
    threadId: Optional[str] = None  # Thread/conversation ID (if supported)
    sender: EmailSender = None
    recipients: EmailRecipients = None
    subject: str = ''
    bodyText: str = ''
    bodyHtml: Optional[str] = None
    receivedAt: datetime = None
    attachments: Optional[List[EmailAttachment]] = None
    metadata: Optional[Dict[str, Any]] = None  # Provider-specific metadata


@dataclass
class Inbox:
    """Inbox information."""
    id: str
    name: str
    address: str


@dataclass
class RateLimitInfo:
    """Rate limit information."""
    requestsPerSecond: Optional[int] = None
    requestsPerMinute: Optional[int] = None
    requestsPerHour: Optional[int] = None
    requestsPerDay: Optional[int] = None
    quotaUnits: Optional[int] = None  # For Gmail API quota units


@dataclass
class ProviderCapabilities:
    """Provider capabilities."""
    supportsWebhooks: bool  # Can receive push notifications
    supportsPolling: bool  # Can poll for emails
    supportsLabels: bool  # Can use labels/folders
    supportsThreading: bool  # Supports email threading
    maxAttachmentSize: int  # Max attachment size in bytes
    rateLimits: RateLimitInfo  # Rate limit information
    authenticationType: str  # "oauth2", "api_key", "password", etc.


@dataclass
class WatchHandle:
    """Watch handle for inbox watching."""
    id: str
    
    def stop(self) -> None:
        """Stop watching inbox."""
        pass
