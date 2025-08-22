from fastapi import HTTPException
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Optional
import traceback

from ..models import QueryRequest, QueryResponse
from ..utils import build_metadata_filters, get_source_instruction_and_format
from ..auth.utils import save_chat_message

async def query_combined(request: QueryRequest, index, source_preferences, user_id: Optional[str] = None) -> QueryResponse:
    """Combined local RAG + web search query"""
    if not index:
        raise HTTPException(status_code=503, detail="Index not loaded")
    
    try:
        # Create retriever with optional filters
        filters_obj = build_metadata_filters(request.filters)
        
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=request.top_k,
            filters=filters_obj
        )
        
        # Step 1: Get local semantic search results
        nodes = retriever.retrieve(request.query)
        context_str = "\n\n".join([node.node.get_content() for node in nodes])
        
        # Create local query engine for focused local response
        QA_TEMPLATE = PromptTemplate(
            "Below are multiple sources containing data schemas, event types, and data samples.\n"
            "Sources are organized by category (e.g., appusage, social) and platform (e.g., ios, android).\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Using the information above, please answer the following question: {query_str}\n"
            "Focus on providing specific details from the sources. Be concise and factual."
        )
        
        local_query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            text_qa_template=QA_TEMPLATE,
        )
        
        local_response = local_query_engine.query(request.query)
        local_response_text = str(local_response)
        
        # Step 2: Get web search results with GPT-4o-mini
        llm = ChatOpenAI(model="gpt-4o-mini", output_version="responses/v1")
        tool = {"type": "web_search_preview"}
        llm_with_tools = llm.bind_tools([tool])
        
        # Get source-specific instructions and response format
        source_instruction, response_format = get_source_instruction_and_format(
            nodes, source_preferences
        ) if source_preferences else ("", {})
        
        # Extract preferred sources for domain restriction
        preferred_sources = []
        if source_preferences:
            categories = set()
            platforms = set()
            datatypes = set()
            
            for node in nodes:
                metadata = node.node.metadata if hasattr(node, 'node') else node.get('metadata', {})
                if 'category' in metadata:
                    categories.add(metadata['category'])
                if 'platform' in metadata:
                    platforms.add(metadata['platform'])
                if 'datatype' in metadata:
                    datatype = metadata['datatype']
                    if '.' in datatype:
                        parts = datatype.split('.')
                        if len(parts) > 1:
                            datatypes.add(parts[1])
            
            # Collect preferred sources from all relevant categories/platforms
            for category in categories:
                if category in source_preferences['source_preferences']['by_category']:
                    cat_prefs = source_preferences['source_preferences']['by_category'][category]
                    for platform in datatypes:
                        if platform in cat_prefs:
                            platform_prefs = cat_prefs[platform]
                            preferred_sources.extend(platform_prefs.get('preferred_sources', []))
            
            for platform in platforms:
                if platform in source_preferences['source_preferences']['by_platform']:
                    plat_prefs = source_preferences['source_preferences']['by_platform'][platform]
                    preferred_sources.extend(plat_prefs.get('preferred_sources', []))
        
        print("Source:", source_instruction)
        print("Response format:", response_format)
        print("Preferred sources:", preferred_sources)
        
        # Simplified web search prompt
        max_sentences = response_format.get('max_context_sentences', 2)
        
        # Simple domain constraint
        domain_note = ""
        if preferred_sources:
            domain_note = f"{', '.join(preferred_sources[:2])}. CRITICAL:  DO NOT CONSIDER ANY OTHER WEBPAGE OTHER THAN THIS"
        
        # Create system message for web search
        web_search_system = SystemMessage(content=(
            "You are a web search assistant for a RAG pipeline. "
            "When 'domain_note' contains a URL, limit all information sourcing exclusively to that specific domain. "
            "Begin with a concise checklist (3-7 bullets) outlining your sub-tasks before sourcing information. "
            "When conducting the web search, focus on explaining or elaborating on the relevant concepts. NEVER directly answer the query; "
            "this is intended to support a RAG pipeline workflow. "
            "After each sourcing step, briefly validate that all retrieved information originated from the specified domain and proceed, "
            "or correct if this is not the case."
        ))
        
        # Create human message with the query
        web_search_human = HumanMessage(content=(
            f"Query: {request.query}\n\n"
            f"Database context: {context_str[:300]}...\n\n"
            f"Use web search to answer the following question. What is {request.query} using{domain_note}. Do not answer the question directly using web search."
            f"Keep to {max_sentences} sentences."
        ))
        
        print("request_query", request.query)
        print("contextstr300", context_str[:300])
        print("domain_note", domain_note)
        print("max_sentences", max_sentences)
        
        # Invoke with system and human messages
        web_response = llm_with_tools.invoke([web_search_system, web_search_human])

        print("System prompt:", web_search_system.content)
        print("Human prompt:", web_search_human.content)
        
        # Extract web response
        web_response_text = ""
        web_urls = []
        web_search_performed = False
        
        if hasattr(web_response, 'content') and isinstance(web_response.content, list):
            for block in web_response.content:
                if isinstance(block, dict):
                    if block.get('type') == 'text':
                        web_response_text = block.get('text', '')
                        annotations = block.get('annotations', [])
                        for ann in annotations:
                            if ann.get('type') == 'url_citation':
                                web_urls.append({
                                    'url': ann.get('url', ''),
                                    'title': ann.get('title', '')
                                })
                    elif block.get('type') == 'web_search_call':
                        web_search_performed = True
        else:
            web_response_text = str(web_response)
        
        # Step 3: Combine responses with clear annotations
        if web_response_text.strip() and web_search_performed:
            combined_response = f"""**LOCAL DATABASE INFORMATION:**
{local_response_text}

**WEB SEARCH RESULTS:**
{web_response_text}"""
        else:
            combined_response = local_response_text
        
        # Build source nodes with both local and web sources
        source_nodes = []
        
        # Add local sources
        for node in nodes:
            source_info = {
                "text": node.node.get_content(),
                "metadata": {
                    **node.node.metadata,
                    "source_origin": "local_database"
                },
                "score": node.score if hasattr(node, 'score') else None
            }
            source_nodes.append(source_info)
        
        # Add web sources if used
        if web_search_performed or web_urls:
            web_source_info = {
                "text": web_response_text,
                "metadata": {
                    "source_type": "web_search",
                    "source_origin": "web_search",
                    "category": "web",
                    "platform": "gpt-4o-mini_web_search",
                    "description": "Current web information retrieved via GPT-4o-mini web search",
                    "web_sources": web_urls
                },
                "score": 1.0
            }
            source_nodes.insert(0, web_source_info)
        
        query_response = QueryResponse(
            response=combined_response,
            source_nodes=source_nodes
        )
        
        # Auto-save to database if user is authenticated
        if user_id:
            try:
                save_chat_message(
                    user_id=user_id,
                    message=request.query,
                    local_response=combined_response,  # Save the combined response as local response
                    local_citations=source_nodes,
                    endpoint_type="query-combined",
                    metadata=request.filters
                )
            except Exception as e:
                print(f"Failed to save message: {e}")
                # Don't fail the query if save fails
        
        return query_response
    except Exception as e:
        print(f"Error in query-combined: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))