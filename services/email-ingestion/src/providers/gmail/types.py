"""
Gmail API Types

Types specific to Gmail API implementation.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class GmailCredentials:
    """Gmail API credentials."""
    client_id: str
    client_secret: str
    refresh_token: str
    access_token: Optional[str] = None  # Auto-refreshed


@dataclass
class GmailConfig:
    """Gmail API configuration."""
    provider_type: str = 'gmail'
    credentials: Dict[str, str] = None
    inbox_address: str = ''
