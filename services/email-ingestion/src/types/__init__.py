"""Email service types."""

from .email import (
    Email,
    EmailAttachment,
    EmailSender,
    EmailRecipients,
    Inbox,
    ProviderCapabilities,
    WatchHandle,
    RateLimitInfo,
)

__all__ = [
    'Email',
    'EmailAttachment',
    'EmailSender',
    'EmailRecipients',
    'Inbox',
    'ProviderCapabilities',
    'WatchHandle',
    'RateLimitInfo',
]
