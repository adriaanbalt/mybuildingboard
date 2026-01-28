"""
Email Ingestion Cloud Function

GCP Cloud Function to ingest emails from email providers (Gmail, IMAP, etc.)
and store them in the database for processing.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from google.cloud import storage
from supabase import create_client, Client

from src.factory.email_service_factory import EmailServiceFactory
from src.interfaces.email_service import EmailService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
STORAGE_BUCKET = os.environ.get('STORAGE_BUCKET', 'email-attachments')
EMAIL_PROVIDER_TYPE = os.environ.get('EMAIL_PROVIDER_TYPE', 'gmail')
INBOX_ADDRESS = os.environ.get('INBOX_ADDRESS', 'documents@mybuildingboard.com')


def get_email_provider_config() -> Dict[str, Any]:
    """
    Get email provider configuration from environment variables or Secret Manager.
    
    Returns:
        Provider configuration dictionary
    """
    # TODO: Load from Secret Manager in production
    # For now, load from environment variables
    config = {
        'provider_type': EMAIL_PROVIDER_TYPE,
        'inbox_address': INBOX_ADDRESS,
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


def get_supabase_client() -> Client:
    """Get Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL and key must be set")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_storage_client() -> storage.Client:
    """Get GCP Cloud Storage client."""
    return storage.Client(project=GCP_PROJECT_ID)


def check_sender_whitelist(supabase: Client, app_id: str, sender_email: str) -> bool:
    """
    Check if sender is whitelisted for the app.
    
    Args:
        supabase: Supabase client
        app_id: App ID
        sender_email: Sender email address
        
    Returns:
        True if whitelisted, False otherwise
    """
    try:
        result = supabase.table('sender_whitelist').select('*').eq('app_id', app_id).eq('email', sender_email).execute()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Failed to check sender whitelist: {e}")
        return False


def detect_app_id_from_sender(supabase: Client, sender_email: str) -> str:
    """
    Detect app_id from sender email.
    
    Args:
        supabase: Supabase client
        sender_email: Sender email address
        
    Returns:
        App ID or None
    """
    # TODO: Implement app_id detection from sender email
    # For now, return None (will need to be set per app configuration)
    return None


def upload_attachment_to_storage(
    storage_client: storage.Client,
    email_id: str,
    attachment_id: str,
    attachment_data: bytes,
    filename: str
) -> str:
    """
    Upload attachment to Cloud Storage.
    
    Args:
        storage_client: GCP Storage client
        email_id: Email ID
        attachment_id: Attachment ID
        attachment_data: Attachment data
        filename: Filename
        
    Returns:
        Storage path (gs://bucket/path)
    """
    bucket = storage_client.bucket(STORAGE_BUCKET)
    blob_path = f"attachments/{email_id}/{attachment_id}/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(attachment_data)
    
    return f"gs://{STORAGE_BUCKET}/{blob_path}"


def ingest_email(
    email_service: EmailService,
    supabase: Client,
    storage_client: storage.Client,
    email: Any,
    app_id: str
) -> Dict[str, Any]:
    """
    Ingest a single email into the database.
    
    Args:
        email_service: Email service instance
        supabase: Supabase client
        storage_client: GCP Storage client
        email: Email object
        app_id: App ID
        
    Returns:
        Result dictionary with status and email_id
    """
    try:
        # Check if email already processed (idempotency)
        existing = supabase.table('emails').select('id').eq('app_id', app_id).eq('provider_id', email.id).eq('provider_type', email.providerType).execute()
        if existing.data:
            logger.info(f"Email {email.id} already processed, skipping")
            return {'status': 'skipped', 'email_id': existing.data[0]['id'], 'reason': 'already_processed'}
        
        # Insert email record
        email_record = {
            'app_id': app_id,
            'provider_id': email.id,
            'provider_type': email.providerType,
            'thread_id': email.threadId,
            'sender_email': email.sender.email,
            'sender_name': email.sender.name,
            'subject': email.subject,
            'body_text': email.bodyText,
            'body_html': email.bodyHtml,
            'received_at': email.receivedAt.isoformat(),
            'status': 'pending',
            'provider_metadata': {
                **(email.metadata or {}),
                'recipient_to': email.recipients.to,
                'recipient_cc': email.recipients.cc,
                'recipient_bcc': email.recipients.bcc,
            },
        }
        
        result = supabase.table('emails').insert(email_record).execute()
        email_db_id = result.data[0]['id']
        
        # Process attachments
        if email.attachments:
            for attachment in email.attachments:
                try:
                    # Download attachment
                    attachment_data = email_service.getAttachment(email.id, attachment.id)
                    
                    # Upload to Cloud Storage
                    storage_path = upload_attachment_to_storage(
                        storage_client,
                        email.id,
                        attachment.id,
                        attachment_data,
                        attachment.filename
                    )
                    
                    # Insert attachment record
                    attachment_record = {
                        'email_id': email_db_id,
                        'provider_attachment_id': attachment.id,
                        'filename': attachment.filename,
                        'content_type': attachment.contentType,
                        'file_size': attachment.size,
                        'storage_path': storage_path,
                        'status': 'pending',
                    }
                    
                    supabase.table('attachments').insert(attachment_record).execute()
                except Exception as e:
                    logger.error(f"Failed to process attachment {attachment.id}: {e}")
        
        # Update email status to processing
        supabase.table('emails').update({'status': 'processing'}).eq('id', email_db_id).execute()
        
        # Mark email as processed in provider
        email_service.markAsProcessed(email.id)
        
        logger.info(f"Successfully ingested email {email.id} (DB ID: {email_db_id})")
        return {'status': 'success', 'email_id': email_db_id}
        
    except Exception as e:
        logger.error(f"Failed to ingest email {email.id}: {e}")
        return {'status': 'failed', 'email_id': None, 'error': str(e)}


def log_processing_result(
    supabase: Client,
    function_name: str,
    status: str,
    email_id: str = None,
    error: str = None,
    processing_time: float = None
):
    """
    Log processing result to processing_logs table.
    
    Args:
        supabase: Supabase client
        function_name: Function name
        status: Status ('success', 'failed', 'skipped')
        email_id: Email ID (optional)
        error: Error message (optional)
        processing_time: Processing time in seconds (optional)
    """
    try:
        log_record = {
            'function_name': function_name,
            'status': status,
            'email_id': email_id,
            'error_message': error,
            'processing_time_ms': int(processing_time * 1000) if processing_time else None,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        supabase.table('processing_logs').insert(log_record).execute()
    except Exception as e:
        logger.error(f"Failed to log processing result: {e}")


def email_ingestion(request):
    """
    Cloud Function entry point for email ingestion.
    
    Triggered by Cloud Scheduler (every 5-10 minutes) or Pub/Sub.
    
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
        storage_client = get_storage_client()
        
        # Get email provider configuration
        provider_config = get_email_provider_config()
        
        # Create email service
        email_service = EmailServiceFactory.create(
            provider_config['provider_type'],
            provider_config
        )
        
        # Fetch emails from inbox
        # Fetch emails from last 24 hours (or since last run)
        since = datetime.utcnow() - timedelta(hours=24)
        emails = email_service.fetchEmails(provider_config['inbox_address'], since)
        
        logger.info(f"Fetched {len(emails)} emails from {provider_config['provider_type']}")
        
        # Process each email
        for email in emails:
            try:
                # Detect app_id from sender email
                app_id = detect_app_id_from_sender(supabase, email.sender.email)
                if not app_id:
                    logger.warning(f"Could not detect app_id for sender {email.sender.email}, skipping")
                    skipped_count += 1
                    continue
                
                # Check sender whitelist
                if not check_sender_whitelist(supabase, app_id, email.sender.email):
                    logger.info(f"Sender {email.sender.email} not whitelisted for app {app_id}, skipping")
                    skipped_count += 1
                    continue
                
                # Ingest email
                result = ingest_email(email_service, supabase, storage_client, email, app_id)
                
                if result['status'] == 'success':
                    processed_count += 1
                elif result['status'] == 'skipped':
                    skipped_count += 1
                else:
                    failed_count += 1
                    log_processing_result(
                        supabase,
                        'email-ingestion',
                        'failed',
                        email_id=email.id,
                        error=result.get('error')
                    )
                    
            except Exception as e:
                logger.error(f"Error processing email {email.id}: {e}")
                failed_count += 1
                log_processing_result(
                    supabase,
                    'email-ingestion',
                    'failed',
                    email_id=email.id,
                    error=str(e)
                )
        
        # Log summary
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Email ingestion complete: {processed_count} processed, "
            f"{skipped_count} skipped, {failed_count} failed "
            f"(took {processing_time:.2f}s)"
        )
        
        return {
            'status': 'success',
            'processed': processed_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'processing_time': processing_time
        }
        
    except Exception as e:
        logger.error(f"Email ingestion failed: {e}")
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        log_processing_result(
            supabase if 'supabase' in locals() else None,
            'email-ingestion',
            'failed',
            error=str(e),
            processing_time=processing_time
        )
        raise


# For local testing
if __name__ == '__main__':
    class MockRequest:
        pass
    
    result = email_ingestion(MockRequest())
    print(json.dumps(result, indent=2))
