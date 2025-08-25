from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Optional
import traceback

from ..models import QueryRequest, QueryResponse
from ..utils import get_source_instruction_and_format
from ..utils.local_rag import create_standard_local_rag
from ..auth.utils import save_chat_message

async def simplify_query_for_web_search(complex_query: str, context: str) -> dict:
    """Use AI to determine if web search is needed and create optimized search strategy"""
    simplifier_llm = ChatOpenAI(model="gpt-4o-mini")
    
    simplifier_prompt = f"""You are analyzing a query about proprietary event data collected from various platforms (social media, e-commerce, apps, etc.).

Query: {complex_query}
Database Context: {context[:500]}...

This database contains INTERNAL event data that is not publicly available. Determine if this query would benefit from web search supplementation.

DEFAULT TO web search (needs_web_search: true) UNLESS the query is PURELY about internal capabilities with NO conceptual terms that need explanation.

SKIP web search (set needs_web_search: false) ONLY if the query is:
- Purely technical about data schema/fields ("What columns do we have for X?")
- Simple yes/no about data collection ("Do we track user login times?") 
- Internal data format questions ("How is timestamp stored?")
- Questions with zero conceptual terms that could benefit from context

Return JSON:
{{"needs_web_search": true/false, "reasoning": "why web search is/isn't needed", "search_terms": ["term1", "term2"], "query_type": "factual/comparison/recent_events/how_to", "focus_areas": ["what to search for"], "avoid_duplicating": ["what database already covers"]}}"""

    try:
        response = simplifier_llm.invoke([HumanMessage(content=simplifier_prompt)])
        import json
        # Try to parse JSON response, fallback to simple terms extraction
        try:
            result = json.loads(response.content)
            return result
        except:
            # Fallback: default to web search when in doubt
            return {
                "needs_web_search": True,
                "reasoning": "Fallback - defaulting to web search for safety",
                "search_terms": [complex_query],
                "query_type": "factual",
                "focus_areas": ["additional context"],
                "avoid_duplicating": []
            }
    except Exception as e:
        print(f"Query simplification failed: {e}")
        return {
            "needs_web_search": True,
            "reasoning": "Error in analysis - defaulting to web search",
            "search_terms": [complex_query],
            "query_type": "factual", 
            "focus_areas": ["additional context"],
            "avoid_duplicating": []
        }

def extract_preferred_sources(nodes, source_preferences) -> list:
    """Clean extraction of preferred sources from nodes and preferences"""
    if not source_preferences or not nodes:
        return []
    
    preferred_sources = []
    categories = set()
    platforms = set()
    datatypes = set()
    
    # Extract metadata from nodes
    for node in nodes:
        metadata = node.node.metadata if hasattr(node, 'node') else node.get('metadata', {})
        if 'category' in metadata:
            categories.add(metadata['category'])
        if 'platform' in metadata:
            platforms.add(metadata['platform'])
        if 'datatype' in metadata:
            datatype = metadata['datatype']
            if '.' in datatype and len(datatype.split('.')) > 1:
                datatypes.add(datatype.split('.')[1])
    
    # Get preferences from categories
    source_prefs = source_preferences.get('source_preferences', {})
    by_category = source_prefs.get('by_category', {})
    by_platform = source_prefs.get('by_platform', {})
    
    for category in categories:
        if category in by_category:
            cat_prefs = by_category[category]
            for datatype in datatypes:
                if datatype in cat_prefs:
                    platform_prefs = cat_prefs[datatype]
                    preferred_sources.extend(platform_prefs.get('preferred_sources', []))
    
    for platform in platforms:
        if platform in by_platform:
            plat_prefs = by_platform[platform]
            preferred_sources.extend(plat_prefs.get('preferred_sources', []))
    
    # Remove duplicates and limit to reasonable number
    return list(set(preferred_sources))[:5]

async def query_combined(request: QueryRequest, index, source_preferences, user_id: Optional[str] = None) -> QueryResponse:
    """Combined local RAG + web search query"""
    if not index:
        raise HTTPException(status_code=503, detail="Index not loaded")
    
    try:
        # Step 1: Get standardized local RAG results
        local_rag = create_standard_local_rag(index, top_k=request.top_k)
        rag_results = local_rag.execute_full_pipeline(
            query=request.query,
            filters=request.filters
        )
        
        local_response_text = rag_results["response"]
        context_str = rag_results["context_string"]
        nodes = rag_results["raw_nodes"]
        
        # Step 2: Prepare for enhanced web search
        # Get source-specific instructions and response format
        source_instruction, response_format = get_source_instruction_and_format(
            nodes, source_preferences
        ) if source_preferences else ("", {})
        
        # Extract preferred sources using clean helper function
        preferred_sources = extract_preferred_sources(nodes, source_preferences)
        
        # Use AI to determine if web search is needed and get strategy
        search_strategy = await simplify_query_for_web_search(request.query, context_str)
        
        print("Search strategy:", search_strategy)
        print("Web search needed:", search_strategy.get("needs_web_search", True))
        print("Reasoning:", search_strategy.get("reasoning", "No reasoning provided"))
        
        # Skip web search if AI determined it's not needed
        if not search_strategy.get("needs_web_search", True):
            print(f"Skipping web search: {search_strategy.get('reasoning', 'Query is about internal data')}")
            
            # Auto-save to database if user is authenticated (local-only response)
            if user_id:
                try:
                    save_chat_message(
                        user_id=user_id,
                        message=request.query,
                        local_response=local_response_text,
                        local_citations=rag_results["source_nodes"],
                        endpoint_type="query-combined-local-only",
                        metadata=request.filters
                    )
                except Exception as e:
                    print(f"Failed to save message: {e}")
            
            return QueryResponse(
                response=local_response_text,
                source_nodes=rag_results["source_nodes"]
            )
        
        print("Preferred sources:", preferred_sources)
        
        # Create improved web search prompts based on AI analysis
        max_sentences = response_format.get('max_context_sentences', 3)
        search_terms = " ".join(search_strategy.get("search_terms", [request.query]))
        query_type = search_strategy.get("query_type", "factual")
        focus_areas = search_strategy.get("focus_areas", [])
        avoid_duplicating = search_strategy.get("avoid_duplicating", [])
        
        # Domain constraints (cleaner approach)
        domain_constraint = ""
        if preferred_sources:
            domain_list = ", ".join(preferred_sources[:3])
            domain_constraint = f"Prioritize information from: {domain_list}. "
        
        # Query-type specific system messages
        query_type_prompts = {
            "factual": "You are a technical research assistant. Provide factual information and explanations.",
            "comparison": "You are a comparison specialist. Focus on differences, pros/cons, and trade-offs.", 
            "recent_events": "You are a technology news researcher. Focus on recent developments and updates.",
            "how_to": "You are a technical guide. Focus on practical steps and best practices.",
            "troubleshooting": "You are a problem-solving expert. Focus on solutions and fixes."
        }
        
        system_prompt = query_type_prompts.get(query_type, query_type_prompts["factual"])
        
        web_search_system = SystemMessage(content=(
            f"{system_prompt} "
            f"Your role is to SUPPLEMENT the existing database information, not replace it. "
            f"{domain_constraint}"
            f"Focus on: {', '.join(focus_areas) if focus_areas else 'additional context and recent information'}. "
            f"Avoid repeating: {', '.join(avoid_duplicating) if avoid_duplicating else 'basic information already covered'}. "
            f"Keep response to {max_sentences} sentences maximum."
        ))
        
        # Cleaner human message
        web_search_human = HumanMessage(content=(
            f"Search terms: {search_terms}\n"
            f"Original query: {request.query}\n"
            f"Database already covers: {context_str[:400]}...\n\n"
            f"Use web search to find supplementary information about: {search_terms}. "
            f"Focus on what the database might be missing or outdated information."
        ))
        
        # Execute web search with improved prompts
        llm = ChatOpenAI(model="gpt-4o-mini", output_version="responses/v1")
        tool = {"type": "web_search_preview"}
        llm_with_tools = llm.bind_tools([tool])
        
        web_response = llm_with_tools.invoke([web_search_system, web_search_human])
        
        # Debug output (can be removed in production)
        print(f"Query type detected: {query_type}")
        print(f"Search terms used: {search_terms}")
        print(f"Focus areas: {focus_areas}")
        print(f"Avoiding duplication of: {avoid_duplicating}")
        
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
        
        # Step 3: Intelligently combine responses
        if web_response_text.strip() and web_search_performed:
            # Create contextual response based on query type
            if query_type == "recent_events":
                combined_response = f"""**DATABASE CONTEXT:**
{local_response_text}

**RECENT DEVELOPMENTS:**
{web_response_text}"""
            elif query_type == "comparison":
                combined_response = f"""**FOUNDATIONAL INFORMATION:**
{local_response_text}

**COMPARATIVE ANALYSIS:**
{web_response_text}"""
            elif query_type == "how_to":
                combined_response = f"""**CORE METHODS:**
{local_response_text}

**ADDITIONAL TECHNIQUES:**
{web_response_text}"""
            else:
                combined_response = f"""**DATABASE INFORMATION:**
{local_response_text}

**SUPPLEMENTARY WEB INFORMATION:**
{web_response_text}"""
        else:
            combined_response = local_response_text
        
        # Build source nodes with both local and web sources
        source_nodes = []
        
        # Add standardized local sources
        for source_node in rag_results["source_nodes"]:
            source_info = {
                **source_node,
                "metadata": {
                    **source_node["metadata"],
                    "source_origin": "local_database"
                }
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