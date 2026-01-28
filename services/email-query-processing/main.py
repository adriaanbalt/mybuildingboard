"""
Email Query Processing Cloud Function

GCP Cloud Function to process query emails, extract questions,
and call the Query Processing API to generate answers.
"""

import os
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
import httpx

from src.factory.email_service_factory import EmailServiceFactory
from src.interfaces.email_service import EmailService
from src.types.email import Email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
QUERY_API_URL = os.environ.get('QUERY_API_URL', 'http://localhost:8000')
QUERY_API_KEY = os.environ.get('QUERY_API_KEY')  # Optional API key for query API
EMAIL_PROVIDER_TYPE = os.environ.get('EMAIL_PROVIDER_TYPE', 'gmail')
QUERY_INBOX_ADDRESS = os.environ.get('QUERY_INBOX_ADDRESS', 'questions@mybuildingboard.com')


def get_supabase_client() -> Client:
    """Get Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL and key must be set")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_email_provider_config() -> Dict[str, Any]:
    """
    Get email provider configuration from environment variables.
    
    Returns:
        Provider configuration dictionary
    """
    config = {
        'provider_type': EMAIL_PROVIDER_TYPE,
        'inbox_address': QUERY_INBOX_ADDRESS,
    }
    
    if EMAIL_PROVIDER_TYPE == 'gmail':
        config.update({
            'client_id': os.environ.get('GMAIL_CLIENT_ID'),
            'client_secret': os.environ.get('GMAIL_CLIENT_SECRET'),
            'refresh_token': os.environ.get('GMAIL_REFRESH_TOKEN'),
            'access_token': os.environ.get('GMAIL_ACCESS_TOKEN'),
        })
    elif EMAIL_PROVIDER_TYPE == 'mailgun':
        config.update({
            'api_key': os.environ.get('MAILGUN_API_KEY'),
            'domain': os.environ.get('MAILGUN_DOMAIN'),
            'webhook_url': os.environ.get('MAILGUN_WEBHOOK_URL'),  # Optional
        })
    
    return config


def detect_app_id_from_sender(supabase: Client, sender_email: str) -> Optional[str]:
    """
    Detect app_id from sender email by looking up user in app_members.
    
    Args:
        supabase: Supabase client
        sender_email: Sender email address
        
    Returns:
        App ID or None if not found
    """
    try:
        # First, get user_id from auth.users by email
        # Note: This requires service role key to access auth.users
        # We'll use a direct query to auth.users via Supabase admin API
        # For now, we'll query app_members joined with a user lookup
        # Since we can't directly query auth.users, we'll need to use a different approach
        
        # Alternative: Query query_whitelist table which has email_address
        # This is a simpler approach for now
        result = supabase.table('query_whitelist').select('app_id').eq('email_address', sender_email).eq('enabled', True).execute()
        
        if result.data and len(result.data) > 0:
            # If user is in multiple apps, return the first one
            # TODO: Handle multiple apps (require selection or use first)
            return result.data[0]['app_id']
        
        # Fallback: Try to find user by email in app_members
        # This requires a database function or view that joins auth.users
        # For now, return None if not found in query_whitelist
        logger.warning(f"Could not find app_id for sender {sender_email} in query_whitelist")
        return None
        
    except Exception as e:
        logger.error(f"Failed to detect app_id from sender {sender_email}: {e}")
        return None


def check_query_whitelist(supabase: Client, app_id: str, sender_email: str) -> bool:
    """
    Check if sender is whitelisted for querying the app.
    
    Args:
        supabase: Supabase client
        app_id: App ID
        sender_email: Sender email address
        
    Returns:
        True if whitelisted, False otherwise
    """
    try:
        result = supabase.table('query_whitelist').select('*').eq('app_id', app_id).eq('email_address', sender_email).eq('enabled', True).execute()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Failed to check query whitelist: {e}")
        return False


def check_rate_limit(supabase: Client, app_id: str, sender_email: str) -> tuple[bool, Optional[str]]:
    """
    Check if sender has exceeded rate limit for queries.
    
    Rate limits:
    - Per sender: 10 queries per hour
    - Per app: 100 queries per hour
    
    Args:
        supabase: Supabase client
        app_id: App ID
        sender_email: Sender email address
        
    Returns:
        Tuple of (is_allowed, error_message)
    """
    try:
        from datetime import datetime, timedelta
        
        # Check per-sender rate limit (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        sender_queries = supabase.table('email_queries').select('id', count='exact').eq('app_id', app_id).eq('sender_email', sender_email).gte('created_at', one_hour_ago.isoformat()).execute()
        
        sender_count = sender_queries.count if hasattr(sender_queries, 'count') else len(sender_queries.data) if sender_queries.data else 0
        if sender_count >= 10:
            return False, f"Rate limit exceeded: {sender_count} queries in the last hour (limit: 10)"
        
        # Check per-app rate limit (last hour)
        app_queries = supabase.table('email_queries').select('id', count='exact').eq('app_id', app_id).gte('created_at', one_hour_ago.isoformat()).execute()
        
        app_count = app_queries.count if hasattr(app_queries, 'count') else len(app_queries.data) if app_queries.data else 0
        if app_count >= 100:
            return False, f"App rate limit exceeded: {app_count} queries in the last hour (limit: 100)"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to check rate limit: {e}")
        # On error, allow the request (fail open)
        return True, None


def extract_question_from_email(email_body: str, email_html: Optional[str] = None) -> str:
    """
    Extract question text from email body, removing signatures and quoted text.
    
    Args:
        email_body: Plain text email body
        email_html: Optional HTML email body
        
    Returns:
        Extracted question text
    """
    # Use plain text if available, otherwise parse HTML
    text = email_body or ""
    
    if not text and email_html:
        # Simple HTML stripping (basic implementation)
        text = re.sub(r'<[^>]+>', '', email_html)
        text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove email signatures (common patterns)
    # Look for common signature delimiters
    signature_patterns = [
        r'--\s*$',  # Standard signature delimiter
        r'^Sent from.*$',  # Mobile signatures
        r'^Best regards.*$',  # Closing signatures
        r'^Regards.*$',
        r'^Thanks.*$',
    ]
    
    lines = text.split('\n')
    cleaned_lines = []
    found_signature = False
    
    for line in lines:
        if found_signature:
            continue
        
        # Check for signature patterns
        for pattern in signature_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                found_signature = True
                break
        
        if not found_signature:
            cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines).strip()
    
    # Remove quoted/replied text (common email patterns)
    # Look for "On ... wrote:" or "> " patterns
    quoted_patterns = [
        r'^On .+ wrote:.*$',
        r'^>.*$',
        r'^From:.*$',
        r'^Sent:.*$',
        r'^To:.*$',
        r'^Subject:.*$',
    ]
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        is_quoted = False
        for pattern in quoted_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                is_quoted = True
                break
        
        if not is_quoted:
            cleaned_lines.append(line)
        else:
            # Stop processing if we hit quoted text
            break
    
    text = '\n'.join(cleaned_lines).strip()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def extract_thread_id(email: Any) -> Optional[str]:
    """
    Extract thread ID from email.
    
    Args:
        email: Email object from EmailService
        
    Returns:
        Thread ID or None
    """
    # Use provider thread ID if available
    if hasattr(email, 'threadId') and email.threadId:
        return email.threadId
    
    # Fallback: Use subject as thread identifier
    if hasattr(email, 'subject') and email.subject:
        # Normalize subject (remove "Re:", "Fwd:", etc.)
        subject = email.subject
        subject = re.sub(r'^(Re:|Fwd:|RE:|FWD:)\s*', '', subject, flags=re.IGNORECASE)
        return f"subject:{subject}"
    
    return None


def get_conversation_history(supabase: Client, app_id: str, thread_id: str) -> Optional[List[Dict[str, str]]]:
    """
    Get conversation history for a thread.
    
    Args:
        supabase: Supabase client
        app_id: App ID
        thread_id: Thread ID
        
    Returns:
        Conversation history as list of {user, assistant} dicts, or None
    """
    try:
        result = supabase.table('query_threads').select('conversation_history').eq('app_id', app_id).eq('thread_id', thread_id).single().execute()
        
        if result.data and result.data.get('conversation_history'):
            return result.data['conversation_history']
        
        return None
        
    except Exception as e:
        logger.warning(f"Failed to get conversation history for thread {thread_id}: {e}")
        return None


def call_query_api(
    query: str,
    app_id: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Call Query Processing API to process query.
    
    Args:
        query: Query text
        app_id: App ID
        conversation_history: Optional conversation history
        auth_token: Optional auth token for query API
        
    Returns:
        Query response dictionary
    """
    url = f"{QUERY_API_URL}/api/query"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    elif QUERY_API_KEY:
        headers["X-API-Key"] = QUERY_API_KEY
    
    # Add app_id to headers for query API
    headers["X-App-Id"] = app_id
    
    payload = {
        "query": query,
        "app_id": app_id,
        "top_k": 5,
        "include_sources": True,
        "response_format": "text",
    }
    
    if conversation_history:
        payload["conversation_id"] = "email_thread"  # Use thread ID if available
    
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)
        response.raise_for_status()
        return response.json()
        
    except httpx.HTTPError as e:
        logger.error(f"Query API request failed: {e}")
        raise Exception(f"Query API request failed: {str(e)}")


def process_query_email(
    email_service: EmailService,
    supabase: Client,
    email: Any
) -> Dict[str, Any]:
    """
    Process a single query email.
    
    Args:
        email_service: Email service instance
        supabase: Supabase client
        email: Email object
        
    Returns:
        Result dictionary with status and details
    """
    try:
        sender_email = email.sender.email if hasattr(email, 'sender') else None
        if not sender_email:
            return {'status': 'failed', 'error': 'No sender email'}
        
        # Detect app_id from sender
        app_id = detect_app_id_from_sender(supabase, sender_email)
        if not app_id:
            logger.warning(f"Could not detect app_id for sender {sender_email}")
            return {'status': 'failed', 'error': 'App ID not found for sender'}
        
        # Check query whitelist
        if not check_query_whitelist(supabase, app_id, sender_email):
            logger.info(f"Sender {sender_email} not whitelisted for queries in app {app_id}")
            return {'status': 'skipped', 'reason': 'not_whitelisted'}
        
        # Check rate limit
        is_allowed, rate_limit_error = check_rate_limit(supabase, app_id, sender_email)
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {sender_email} in app {app_id}: {rate_limit_error}")
            return {'status': 'skipped', 'reason': 'rate_limit_exceeded', 'error': rate_limit_error}
        
        # Extract question from email body
        email_body = email.bodyText if hasattr(email, 'bodyText') else ""
        email_html = email.bodyHtml if hasattr(email, 'bodyHtml') else None
        question = extract_question_from_email(email_body, email_html)
        
        if not question or len(question.strip()) < 3:
            return {'status': 'failed', 'error': 'No valid question found in email'}
        
        # Extract thread ID
        thread_id = extract_thread_id(email)
        
        # Get conversation history if thread exists
        conversation_history = None
        if thread_id:
            conversation_history = get_conversation_history(supabase, app_id, thread_id)
        
        # Call Query API
        query_response = call_query_api(question, app_id, conversation_history)
        
        answer = query_response.get('answer', '')
        sources = query_response.get('sources', [])
        query_id = query_response.get('query_id')
        
        # Log query to database
        query_record = {
            'app_id': app_id,
            'sender_email': sender_email,
            'query_text': question,
            'answer_text': answer,
            'thread_id': thread_id,
            'sources_used': [s.get('chunk_id') for s in sources] if sources else [],
            'status': 'completed',
        }
        
        supabase.table('email_queries').insert(query_record).execute()
        
        # Update or create thread
        if thread_id:
            thread_data = {
                'app_id': app_id,
                'thread_id': thread_id,
                'sender_email': sender_email,
                'conversation_history': (conversation_history or []) + [
                    {'user': question, 'assistant': answer}
                ],
            }
            
            # Try to update existing thread, or insert new one
            try:
                supabase.table('query_threads').upsert(thread_data, on_conflict='app_id,thread_id').execute()
            except Exception as e:
                logger.warning(f"Failed to update thread: {e}")
                # Try insert instead
                try:
                    supabase.table('query_threads').insert(thread_data).execute()
                except:
                    pass
        
        # Mark email as processed
        try:
            email_service.markAsProcessed(email.id)
        except Exception as e:
            logger.warning(f"Failed to mark email as processed: {e}")
        
        return {
            'status': 'success',
            'query_id': query_id,
            'answer': answer,
            'sources_count': len(sources),
        }
        
    except Exception as e:
        logger.error(f"Failed to process query email: {e}", exc_info=True)
        return {'status': 'failed', 'error': str(e)}


def process_query_emails(request):
    """
    Cloud Function entry point for processing query emails.
    
    Triggered by Cloud Scheduler (every 15 minutes) or Pub/Sub.
    
    Args:
        request: Cloud Function request object
    """
    start_time = datetime.utcnow()
    processed_count = 0
    skipped_count = 0
    failed_count = 0
    
    try:
        # Initialize clients
        supabase = get_supabase_client()
        
        # Get email provider configuration
        provider_config = get_email_provider_config()
        
        # Create email service
        email_service = EmailServiceFactory.create(
            provider_config['provider_type'],
            provider_config
        )
        
        # Fetch emails from query inbox
        since = datetime.utcnow() - timedelta(hours=24)
        emails = email_service.fetchEmails(provider_config['inbox_address'], since)
        
        logger.info(f"Found {len(emails)} emails in query inbox")
        
        # Process each email
        for email in emails:
            try:
                result = process_query_email(email_service, supabase, email)
                
                if result['status'] == 'success':
                    processed_count += 1
                elif result['status'] == 'skipped':
                    skipped_count += 1
                else:
                    failed_count += 1
                    logger.error(f"Failed to process email {email.id}: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error processing email {email.id}: {e}")
                failed_count += 1
        
        # Log summary
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Query email processing complete: {processed_count} processed, "
            f"{skipped_count} skipped, {failed_count} failed "
            f"(took {processing_time:.2f}s)"
        )
        
        return {
            'status': 'success',
            'processed': processed_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'processing_time': processing_time,
        }
        
    except Exception as e:
        logger.error(f"Query email processing failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
        }
