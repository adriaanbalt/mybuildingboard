"""
EmailService Interface

Provider-agnostic interface for email services.
Enables swapping providers (Gmail API, IMAP, SendGrid, etc.) without refactoring.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..types.email import (
    Email,
    EmailAttachment,
    Inbox,
    ProviderCapabilities,
    WatchHandle,
)


class EmailService(ABC):
    """
    Abstract interface for email services.
    
    All email providers must implement this interface.
    """
    
    @abstractmethod
    def fetchEmails(self, inbox: str, since: Optional[datetime] = None) -> List[Email]:
        """
        Fetch emails from inbox.
        
        Args:
            inbox: Inbox address or identifier
            since: Optional date to fetch emails since
            
        Returns:
            Array of emails
        """
        pass
    
    @abstractmethod
    def getEmailById(self, emailId: str) -> Optional[Email]:
        """
        Get email by provider-specific ID.
        
        Args:
            emailId: Provider-specific email ID
            
        Returns:
            Email or None if not found
        """
        pass
    
    @abstractmethod
    def markAsProcessed(self, emailId: str, label: Optional[str] = None) -> None:
        """
        Mark email as processed (label, read, etc.).
        
        Args:
            emailId: Provider-specific email ID
            label: Optional label/folder name
        """
        pass
    
    @abstractmethod
    def sendEmail(
        self,
        to: str,
        subject: str,
        body: str,
        htmlBody: Optional[str] = None,
        inReplyTo: Optional[str] = None
    ) -> None:
        """
        Send email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            htmlBody: Optional HTML body
            inReplyTo: Optional email ID to reply to
        """
        pass
    
    @abstractmethod
    def getAttachment(self, emailId: str, attachmentId: str) -> bytes:
        """
        Get email attachment.
        
        Args:
            emailId: Provider-specific email ID
            attachmentId: Provider-specific attachment ID
            
        Returns:
            Attachment data as bytes
        """
        pass
    
    @abstractmethod
    def listInboxes(self) -> List[Inbox]:
        """
        List available inboxes.
        
        Returns:
            Array of inboxes
        """
        pass
    
    @abstractmethod
    def watchInbox(
        self,
        inbox: str,
        callback: callable
    ) -> WatchHandle:
        """
        Watch inbox for new emails (webhooks, push notifications).
        
        Args:
            inbox: Inbox address or identifier
            callback: Callback function for new emails
            
        Returns:
            Watch handle to stop watching
        """
        pass
    
    @abstractmethod
    def getProviderName(self) -> str:
        """
        Get provider name (e.g., "gmail", "imap", "sendgrid").
        
        Returns:
            Provider name
        """
        pass
    
    @abstractmethod
    def getProviderCapabilities(self) -> ProviderCapabilities:
        """
        Get provider capabilities.
        
        Returns:
            Provider capabilities
        """
        pass
