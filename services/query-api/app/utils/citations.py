"""
Citation Formatting Utilities

Utilities for formatting citations and source metadata.
"""

import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode


def format_inline_citations(
    answer: str,
    sources: List[Dict[str, Any]],
    base_url: Optional[str] = None
) -> str:
    """
    Format answer with inline citations [1], [2], etc.
    
    Args:
        answer: Answer text (may already contain [Source N] references)
        sources: List of source dictionaries
        base_url: Base URL for dashboard links (optional)
        
    Returns:
        Answer text with inline citations formatted as [1], [2], etc.
    """
    # Replace [Source N] with [N] citations
    for i, source in enumerate(sources, start=1):
        source_ref = f"[Source {i}]"
        citation = f"[{i}]"
        answer = answer.replace(source_ref, citation)
    
    return answer


def format_source_list(
    sources: List[Dict[str, Any]],
    base_url: Optional[str] = None,
    app_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Format source list with metadata and dashboard links.
    
    Args:
        sources: List of source dictionaries
        base_url: Base URL for dashboard links (optional)
        app_id: App ID for dashboard links (optional)
        
    Returns:
        List of formatted source dictionaries
    """
    formatted_sources = []
    
    for i, source in enumerate(sources, start=1):
        formatted_source = {
            "citation_number": i,
            "chunk_id": source.get("chunk_id"),
            "email_id": source.get("email_id"),
            "email_subject": source.get("email_subject"),
            "attachment_id": source.get("attachment_id"),
            "attachment_filename": source.get("attachment_filename"),
            "similarity": source.get("similarity", 0.0),
            "content_preview": source.get("content_preview") or source.get("content", "")[:200],
        }
        
        # Add dashboard links if base_url provided
        if base_url:
            links = {}
            
            # Link to query/document in dashboard
            if app_id and source.get("chunk_id"):
                query_params = {
                    "app_id": app_id,
                    "chunk_id": source.get("chunk_id"),
                }
                links["dashboard"] = f"{base_url}/documents?{urlencode(query_params)}"
            
            # Link to email if available
            if app_id and source.get("email_id"):
                query_params = {
                    "app_id": app_id,
                    "email_id": source.get("email_id"),
                }
                links["email"] = f"{base_url}/documents/email?{urlencode(query_params)}"
            
            # Link to attachment if available
            if app_id and source.get("attachment_id"):
                query_params = {
                    "app_id": app_id,
                    "attachment_id": source.get("attachment_id"),
                }
                links["attachment"] = f"{base_url}/documents/attachment?{urlencode(query_params)}"
            
            formatted_source["links"] = links
        
        formatted_sources.append(formatted_source)
    
    return formatted_sources


def format_source_description(source: Dict[str, Any]) -> str:
    """
    Format human-readable source description.
    
    Args:
        source: Source dictionary
        
    Returns:
        Formatted source description
    """
    parts = []
    
    # Email subject
    if source.get("email_subject"):
        parts.append(f"Email: {source['email_subject']}")
    
    # Attachment filename
    if source.get("attachment_filename"):
        parts.append(f"Attachment: {source['attachment_filename']}")
    
    # Similarity score
    similarity = source.get("similarity", 0.0)
    if similarity > 0:
        parts.append(f"Relevance: {similarity:.1%}")
    
    return " | ".join(parts) if parts else "Source"


def extract_citations_from_answer(answer: str) -> List[int]:
    """
    Extract citation numbers from answer text.
    
    Args:
        answer: Answer text with citations like [1], [2], etc.
        
    Returns:
        List of citation numbers found in answer
    """
    # Find all [N] patterns
    pattern = r'\[(\d+)\]'
    matches = re.findall(pattern, answer)
    return [int(m) for m in matches]


def format_html_response(
    answer: str,
    sources: List[Dict[str, Any]],
    base_url: Optional[str] = None,
    app_id: Optional[str] = None
) -> str:
    """
    Format response as HTML.
    
    Args:
        answer: Answer text with citations
        sources: List of source dictionaries
        base_url: Base URL for links (optional)
        app_id: App ID for links (optional)
        
    Returns:
        HTML formatted response
    """
    # Format answer with citation links
    html_answer = answer
    for i, source in enumerate(sources, start=1):
        citation = f"[{i}]"
        if base_url and app_id and source.get("chunk_id"):
            link = f"{base_url}/documents?app_id={app_id}&chunk_id={source.get('chunk_id')}"
            html_answer = html_answer.replace(
                citation,
                f'<a href="{link}" class="citation-link">[{i}]</a>'
            )
        else:
            html_answer = html_answer.replace(
                citation,
                f'<span class="citation">[{i}]</span>'
            )
    
    # Format sources list
    sources_html = "<ol class='sources-list'>"
    for i, source in enumerate(sources, start=1):
        source_desc = format_source_description(source)
        sources_html += f"<li><strong>[{i}]</strong> {source_desc}</li>"
    sources_html += "</ol>"
    
    return f"""
    <div class="query-response">
        <div class="answer">{html_answer}</div>
        <div class="sources">
            <h3>Sources</h3>
            {sources_html}
        </div>
    </div>
    """


def format_plain_text_response(
    answer: str,
    sources: List[Dict[str, Any]]
) -> str:
    """
    Format response as plain text (for email).
    
    Args:
        answer: Answer text with citations
        sources: List of source dictionaries
        
    Returns:
        Plain text formatted response
    """
    # Format sources list
    sources_text = "\n\nSources:\n"
    for i, source in enumerate(sources, start=1):
        source_desc = format_source_description(source)
        sources_text += f"[{i}] {source_desc}\n"
    
    return f"{answer}\n{sources_text}"
