"""
Query Routes

API routes for query processing.
"""

import time
import uuid
from typing import Tuple, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import create_client, Client

from app.models.query import QueryRequest, QueryResponse, Source, TokenUsage
from app.middleware.auth import require_app_membership
from app.services.embedding_service import generate_query_embedding
from app.services.vector_search import search_similar_chunks
from app.factory.query_service_factory import create_query_service
from app.utils.citations import (
    format_inline_citations,
    format_source_list,
    format_html_response,
    format_plain_text_response
)
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()


def get_supabase_client() -> Client:
    """Get Supabase client."""
    from supabase import create_client
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    request_obj: Request,
    user_app: Tuple[str, str] = Depends(require_app_membership)
):
    """
    Process a query using RAG (Retrieval Augmented Generation).
    
    Flow:
    1. Generate query embedding
    2. Search for similar chunks (vector search)
    3. Generate answer using LLM with context
    4. Format response with citations
    """
    start_time = time.time()
    user_id, app_id = user_app
    
    # Use app_id from request if provided, otherwise use from auth
    app_id = request.app_id or app_id
    
    if not app_id:
        raise HTTPException(status_code=400, detail="app_id is required")
    
    query_id = str(uuid.uuid4())
    
    try:
        # Step 1: Generate query embedding
        logger.info(f"Generating embedding for query: {request.query[:50]}...")
        query_embedding = await generate_query_embedding(request.query)
        
        # Step 2: Search for similar chunks
        logger.info(f"Searching for similar chunks (app_id: {app_id}, top_k: {request.top_k})")
        search_results = await search_similar_chunks(
            query_embedding=query_embedding,
            app_id=app_id,
            top_k=request.top_k or 5,
            similarity_threshold=request.similarity_threshold or 0.0,
        )
        
        if not search_results:
            processing_time = int((time.time() - start_time) * 1000)
            error_message = (
                "I couldn't find any relevant information to answer your question. "
                "Please try rephrasing your query or check if documents have been indexed."
            )
            
            # Log query with no results
            try:
                supabase = get_supabase_client()
                supabase.table("email_queries").insert({
                    "id": query_id,
                    "app_id": app_id,
                    "user_id": user_id,
                    "query_text": request.query,
                    "answer_text": error_message,
                    "sources_used": [],
                    "status": "no_results",
                    "processing_time_ms": processing_time,
                }).execute()
            except Exception as e:
                logger.error(f"Failed to log query: {e}")
            
            return QueryResponse(
                answer=error_message,
                sources=[],
                query_id=query_id,
                processing_time_ms=processing_time,
                metadata={
                    "chunks_retrieved": 0,
                    "app_id": app_id,
                    "status": "no_results",
                }
            )
        
        # Step 3: Generate answer using LLM via QueryService
        logger.info(f"Generating answer with {len(search_results)} context chunks")
        
        # Create QueryService instance
        query_service = create_query_service()
        
        # Prepare context chunks for QueryService
        context_chunks = [
            {
                "content": result.get("content", ""),
                "chunk_id": result.get("chunk_id"),
                "email_id": result.get("email_id"),
                "attachment_id": result.get("attachment_id"),
                "similarity": result.get("similarity", 0.0),
            }
            for result in search_results
        ]
        
        # Process query with QueryService
        query_result = await query_service.process_query(
            query=request.query,
            context_chunks=context_chunks,
            conversation_history=None  # TODO: Add conversation history support
        )
        
        answer = query_result.answer
        
        # Step 4: Format sources with metadata
        sources = []
        sources_dict = []  # For citation formatting
        if request.include_sources:
            # Fetch additional metadata for sources
            supabase = get_supabase_client()
            
            for result in search_results:
                email_subject = None
                attachment_filename = None
                
                # Fetch email metadata if available
                if result.get("email_id"):
                    try:
                        email_data = supabase.table("emails").select("subject").eq("id", result["email_id"]).single().execute()
                        if email_data.data:
                            email_subject = email_data.data.get("subject")
                    except Exception as e:
                        logger.warning(f"Failed to fetch email metadata: {e}")
                
                # Fetch attachment metadata if available
                if result.get("attachment_id"):
                    try:
                        attachment_data = supabase.table("attachments").select("filename").eq("id", result["attachment_id"]).single().execute()
                        if attachment_data.data:
                            attachment_filename = attachment_data.data.get("filename")
                    except Exception as e:
                        logger.warning(f"Failed to fetch attachment metadata: {e}")
                
                source_obj = Source(
                    chunk_id=result.get("chunk_id"),
                    email_id=result.get("email_id"),
                    email_subject=email_subject,
                    attachment_id=result.get("attachment_id"),
                    attachment_filename=attachment_filename,
                    similarity=result.get("similarity", 0.0),
                    content_preview=result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                )
                sources.append(source_obj)
                
                # Also create dict for citation formatting
                sources_dict.append({
                    "chunk_id": source_obj.chunk_id,
                    "email_id": source_obj.email_id,
                    "email_subject": source_obj.email_subject,
                    "attachment_id": source_obj.attachment_id,
                    "attachment_filename": source_obj.attachment_filename,
                    "similarity": source_obj.similarity,
                    "content_preview": source_obj.content_preview,
                })
        
        # Format answer based on response format
        response_format = request.response_format or "text"
        base_url = os.getenv("NEXT_PUBLIC_APP_URL", "https://localhost:3000")
        
        if response_format == "html":
            answer = format_html_response(answer, sources_dict, base_url, app_id)
        elif response_format == "plain":
            answer = format_plain_text_response(answer, sources_dict)
        else:
            # Default: text with inline citations
            answer = format_inline_citations(answer, sources_dict)
        
        # Format sources with dashboard links for metadata
        formatted_sources_metadata = format_source_list(sources_dict, base_url, app_id) if sources_dict else []
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Step 5: Log query with token usage
        try:
            supabase = get_supabase_client()
            supabase.table("email_queries").insert({
                "id": query_id,
                "app_id": app_id,
                "user_id": user_id,
                "query_text": request.query,
                "answer_text": answer,
                "sources_used": [s.chunk_id for s in sources],
                "status": "completed",
                "processing_time_ms": processing_time,
                "token_usage": {
                    "input_tokens": query_result.token_usage.input_tokens,
                    "output_tokens": query_result.token_usage.output_tokens,
                    "total_tokens": query_result.token_usage.total_tokens,
                    "cost_usd": query_result.token_usage.cost_usd,
                } if query_result.token_usage else None,
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log query: {e}")
        
        # Format token usage for response
        token_usage = None
        if query_result.token_usage:
            token_usage = TokenUsage(
                input_tokens=query_result.token_usage.input_tokens,
                output_tokens=query_result.token_usage.output_tokens,
                total_tokens=query_result.token_usage.total_tokens,
                cost_usd=query_result.token_usage.cost_usd,
            )
        
        # Add dashboard links to metadata
        source_links = {}
        if formatted_sources_metadata:
            for formatted_source in formatted_sources_metadata:
                citation_num = formatted_source.get("citation_number", 0)
                if citation_num > 0:
                    source_links[str(citation_num)] = formatted_source.get("links", {})
        
        response_metadata = {
            "chunks_retrieved": len(search_results),
            "app_id": app_id,
            "provider": query_result.model,
            "model": query_result.model,
            "response_format": response_format,
            "source_links": source_links,
        }
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            query_id=query_id,
            processing_time_ms=processing_time,
            token_usage=token_usage,
            metadata=response_metadata
        )
        
    except ValueError as e:
        # User input errors
        logger.warning(f"Invalid query request: {e}")
        processing_time = int((time.time() - start_time) * 1000)
        
        # Log failed query
        try:
            supabase = get_supabase_client()
            supabase.table("email_queries").insert({
                "id": query_id,
                "app_id": app_id,
                "user_id": user_id,
                "query_text": request.query,
                "status": "failed",
                "error_message": str(e),
                "processing_time_ms": processing_time,
            }).execute()
        except:
            pass
        
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid request",
                "error_code": "INVALID_QUERY",
                "message": str(e),
                "query_id": query_id,
            }
        )
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        processing_time = int((time.time() - start_time) * 1000)
        
        # Log failed query
        try:
            supabase = get_supabase_client()
            supabase.table("email_queries").insert({
                "id": query_id,
                "app_id": app_id,
                "user_id": user_id,
                "query_text": request.query,
                "status": "failed",
                "error_message": str(e),
                "processing_time_ms": processing_time,
            }).execute()
        except:
            pass
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Query processing failed",
                "error_code": "PROCESSING_ERROR",
                "message": "An error occurred while processing your query. Please try again later.",
                "query_id": query_id,
            }
        )
