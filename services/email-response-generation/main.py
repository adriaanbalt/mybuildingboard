"""
Email Response Generation Cloud Function

GCP Cloud Function to send email responses with formatted answers.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from supabase import create_client, Client

from src.factory.email_service_factory import EmailServiceFactory
from src.interfaces.email_service import EmailService
from src.types.email import Email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
EMAIL_PROVIDER_TYPE = os.environ.get('EMAIL_PROVIDER_TYPE', 'gmail')
APP_BASE_URL = os.environ.get('APP_BASE_URL', 'https://localhost:3000')


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
    }
    
    if EMAIL_PROVIDER_TYPE == 'gmail':
        config.update({
            'client_id': os.environ.get('GMAIL_CLIENT_ID'),
            'client_secret': os.environ.get('GMAIL_CLIENT_SECRET'),
            'refresh_token': os.environ.get('GMAIL_REFRESH_TOKEN'),
            'access_token': os.environ.get('GMAIL_ACCESS_TOKEN'),
        })
    
    return config


def format_email_answer_html(
    answer: str,
    sources: List[Dict[str, Any]],
    app_id: str,
    query_id: Optional[str] = None
) -> str:
    """
    Format answer as HTML email.
    
    Args:
        answer: Answer text with citations
        sources: List of source dictionaries
        app_id: App ID
        query_id: Optional query ID for dashboard link
        
    Returns:
        HTML formatted email body
    """
    # Format sources list
    sources_html = ""
    if sources:
        sources_html = "<h3>Sources:</h3><ol>"
        for i, source in enumerate(sources, start=1):
            source_desc = f"Source {i}"
            if source.get('email_subject'):
                source_desc = source.get('email_subject')
            elif source.get('attachment_filename'):
                source_desc = source.get('attachment_filename')
            
            sources_html += f"<li><strong>[{i}]</strong> {source_desc}"
            if source.get('similarity'):
                sources_html += f" (Relevance: {source.get('similarity'):.1%})"
            sources_html += "</li>"
        sources_html += "</ol>"
    
    # Dashboard link
    dashboard_link = ""
    if query_id:
        dashboard_link = f'<p><a href="{APP_BASE_URL}/query/{query_id}?app_id={app_id}">View in Dashboard</a></p>'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .answer {{ margin: 20px 0; padding: 15px; background-color: #f9f9f9; border-left: 4px solid #4CAF50; }}
            .sources {{ margin: 20px 0; }}
            .sources ol {{ margin-left: 20px; }}
            .sources li {{ margin: 10px 0; }}
            a {{ color: #4CAF50; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="answer">
            {answer.replace(chr(10), '<br>')}
        </div>
        {sources_html}
        {dashboard_link}
        <hr>
        <p style="color: #666; font-size: 12px;">
            This is an automated response. Reply to this email to ask a follow-up question.
        </p>
    </body>
    </html>
    """
    
    return html


def format_email_answer_plain(
    answer: str,
    sources: List[Dict[str, Any]],
    app_id: str,
    query_id: Optional[str] = None
) -> str:
    """
    Format answer as plain text email.
    
    Args:
        answer: Answer text with citations
        sources: List of source dictionaries
        app_id: App ID
        query_id: Optional query ID for dashboard link
        
    Returns:
        Plain text formatted email body
    """
    text = answer + "\n\n"
    
    # Format sources list
    if sources:
        text += "Sources:\n"
        for i, source in enumerate(sources, start=1):
            source_desc = f"Source {i}"
            if source.get('email_subject'):
                source_desc = source.get('email_subject')
            elif source.get('attachment_filename'):
                source_desc = source.get('attachment_filename')
            
            text += f"[{i}] {source_desc}"
            if source.get('similarity'):
                text += f" (Relevance: {source.get('similarity'):.1%})"
            text += "\n"
    
    # Dashboard link
    if query_id:
        text += f"\nView in Dashboard: {APP_BASE_URL}/query/{query_id}?app_id={app_id}\n"
    
    text += "\n---\n"
    text += "This is an automated response. Reply to this email to ask a follow-up question.\n"
    
    return text


def send_query_response(
    email_service: EmailService,
    supabase: Client,
    query_record: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send email response for a query.
    
    Args:
        email_service: Email service instance
        supabase: Supabase client
        query_record: Query record from email_queries table
        
    Returns:
        Result dictionary with status
    """
    try:
        app_id = query_record.get('app_id')
        sender_email = query_record.get('sender_email')
        answer = query_record.get('answer_text', '')
        query_id = query_record.get('id')
        thread_id = query_record.get('thread_id')
        sources_used = query_record.get('sources_used', [])
        
        if not sender_email or not answer:
            return {'status': 'failed', 'error': 'Missing sender_email or answer_text'}
        
        # Get original email to reply to
        original_email_id = None
        original_subject = "Re: Your Question"
        
        # Try to find original email
        if thread_id:
            try:
                # Find email with this thread_id
                email_result = supabase.table('emails').select('id, subject').eq('app_id', app_id).eq('thread_id', thread_id).order('received_at', desc=True).limit(1).execute()
                if email_result.data:
                    original_email_id = email_result.data[0].get('id')
                    original_subject = f"Re: {email_result.data[0].get('subject', 'Your Question')}"
            except Exception as e:
                logger.warning(f"Failed to find original email: {e}")
        
        # Get sources metadata
        sources = []
        if sources_used:
            try:
                # Get chunk metadata
                chunks_result = supabase.table('document_chunks').select('id, email_id, attachment_id').in_('id', sources_used).execute()
                chunk_map = {chunk['id']: chunk for chunk in chunks_result.data if chunks_result.data}
                
                for chunk_id in sources_used:
                    chunk = chunk_map.get(chunk_id, {})
                    source = {'chunk_id': chunk_id}
                    
                    # Get email metadata
                    if chunk.get('email_id'):
                        email_result = supabase.table('emails').select('subject').eq('id', chunk['email_id']).single().execute()
                        if email_result.data:
                            source['email_subject'] = email_result.data.get('subject')
                    
                    # Get attachment metadata
                    if chunk.get('attachment_id'):
                        attachment_result = supabase.table('attachments').select('filename').eq('id', chunk['attachment_id']).single().execute()
                        if attachment_result.data:
                            source['attachment_filename'] = attachment_result.data.get('filename')
                    
                    sources.append(source)
            except Exception as e:
                logger.warning(f"Failed to get sources metadata: {e}")
        
        # Format email
        html_body = format_email_answer_html(answer, sources, app_id, query_id)
        plain_body = format_email_answer_plain(answer, sources, app_id, query_id)
        
        # Send email
        email_service.sendEmail(
            to=sender_email,
            subject=original_subject,
            body=plain_body,
            htmlBody=html_body,
            inReplyTo=original_email_id
        )
        
        # Update query record
        supabase.table('email_queries').update({
            'answered_at': 'now()',
            'status': 'completed',
        }).eq('id', query_id).execute()
        
        logger.info(f"Successfully sent response for query {query_id} to {sender_email}")
        return {'status': 'success', 'query_id': query_id}
        
    except Exception as e:
        logger.error(f"Failed to send query response: {e}", exc_info=True)
        
        # Update query record with error
        try:
            supabase.table('email_queries').update({
                'status': 'failed',
            }).eq('id', query_record.get('id')).execute()
        except:
            pass
        
        return {'status': 'failed', 'error': str(e)}


def send_query_responses(request):
    """
    Cloud Function entry point for sending query responses.
    
    Triggered by Pub/Sub (after query processing) or Cloud Scheduler.
    
    Args:
        request: Cloud Function request object
    """
    start_time = datetime.utcnow()
    sent_count = 0
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
        
        # Get pending queries (completed but not answered)
        queries_result = supabase.table('email_queries').select('*').eq('status', 'completed').is_('answered_at', 'null').limit(50).execute()
        
        queries = queries_result.data if queries_result.data else []
        logger.info(f"Found {len(queries)} pending query responses")
        
        # Send responses
        for query_record in queries:
            try:
                result = send_query_response(email_service, supabase, query_record)
                
                if result['status'] == 'success':
                    sent_count += 1
                else:
                    failed_count += 1
                    logger.error(f"Failed to send response for query {query_record.get('id')}: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error sending response for query {query_record.get('id')}: {e}")
                failed_count += 1
        
        # Log summary
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Query response sending complete: {sent_count} sent, "
            f"{failed_count} failed (took {processing_time:.2f}s)"
        )
        
        return {
            'status': 'success',
            'sent': sent_count,
            'failed': failed_count,
            'processing_time': processing_time,
        }
        
    except Exception as e:
        logger.error(f"Query response sending failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
        }
