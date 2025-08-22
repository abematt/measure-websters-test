"""
Web Enrichment Endpoint
Performs keyword synthesis, web search, content fetching, and concise synthesis
"""

from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from llama_index.llms.openai import OpenAI
import traceback
import os
from dotenv import load_dotenv
import aiohttp
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import HTMLToDocument
from haystack import Pipeline

from ..models import WebEnrichmentRequest, WebEnrichmentResponse
from ..auth.utils import update_chat_message_web_response

load_dotenv()


class WebEnrichmentWorkflow:
    """
    Workflow for web enrichment with concise synthesis
    """
    
    def __init__(self):
        self.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        
    async def execute(self, request: WebEnrichmentRequest) -> WebEnrichmentResponse:
        """Execute web enrichment workflow"""
        try:
            # Step 1: Synthesize or use provided keywords
            if request.keywords:
                search_keywords = request.keywords
            else:
                search_keywords = await self._synthesize_keywords(
                    query=request.query,
                    context=request.local_context
                )
            
            print(f"\n=== Web Enrichment Workflow ===")
            print(f"Query: {request.query}")
            print(f"Keywords: {search_keywords}")
            print(f"Preferred sources: {request.preferred_sources}")
            
            # Step 2: Perform web search
            web_search_results = await self._perform_web_search(
                keywords=search_keywords,
                preferred_sources=request.preferred_sources,
                max_results=request.max_results
            )
            
            if not web_search_results:
                return WebEnrichmentResponse(
                    synthesized_keywords=search_keywords,
                    web_search_results=[],
                    enriched_response="No web results found for the given query.",
                    sources_fetched=0
                )
            
            # Step 3: Fetch content from URLs
            web_content = await self._fetch_web_content(web_search_results)
            
            # Step 4: Synthesize enriched response (concise mode)
            enriched_response = await self._synthesize_enriched_response(
                query=request.query,
                web_content=web_content,
                concise_mode=request.concise_mode
            )
            
            return WebEnrichmentResponse(
                synthesized_keywords=search_keywords,
                web_search_results=web_search_results[:request.max_results],
                enriched_response=enriched_response,
                sources_fetched=len(web_content)
            )
            
        except Exception as e:
            print(f"Error in web enrichment: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _synthesize_keywords(self, query: str, context: Optional[str]) -> List[str]:
        """Synthesize focused search keywords"""
        if not context:
            # Extract key terms from query
            return self._extract_key_terms(query)[:3]
        
        prompt = f"""Generate 2-3 concise search keywords for finding technical documentation.

Query: {query}
Context: {context[:300] if context else 'None'}

Requirements:
- Focus on the MOST specific technology/platform
- Use short terms (2-4 words max)
- Prioritize product/vendor names

Return ONLY keywords, one per line, no numbering."""
        
        try:
            response = await self.llm.acomplete(prompt)
            keywords = [line.strip() for line in str(response).split('\n') if line.strip()]
            return keywords[:3] if keywords else self._extract_key_terms(query)[:3]
        except Exception:
            return self._extract_key_terms(query)[:3]
    
    def _extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from query"""
        stopwords = {'what', 'is', 'are', 'the', 'how', 'to', 'in', 'for', 'of', 'and', 'or', 'a', 'an'}
        words = query.lower().split()
        key_terms = [word for word in words if word not in stopwords and len(word) > 2]
        return key_terms if key_terms else [query]
    
    async def _perform_web_search(
        self, 
        keywords: List[str], 
        preferred_sources: Optional[List[str]],
        max_results: int
    ) -> List[Dict]:
        """Perform Serper web search"""
        if not self.serper_api_key:
            print("Warning: SERPER_API_KEY not found")
            return []
        
        # Build search query
        search_query = keywords[0]  # Use first 2 keywords
        
        # Add site restrictions if available
        if preferred_sources:
            site_query = " OR ".join([f"site:{source}" for source in preferred_sources[:2]])
            search_query = f"{search_query} {site_query}"
        
        print(f"Search query: {search_query}")
        
        async with aiohttp.ClientSession() as session:
            url = "https://google.serper.dev/search"
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            payload = {
                'q': search_query,
                'num': max_results,
                'gl': 'us',
                'hl': 'en'
            }
            
            try:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        organic_results = data.get('organic', [])
                        return [{
                            'title': r.get('title', ''),
                            'link': r.get('link', ''),
                            'snippet': r.get('snippet', ''),
                            'position': r.get('position', 0)
                        } for r in organic_results]
                    return []
            except Exception as e:
                print(f"Serper API error: {e}")
                return []
    
    async def _fetch_web_content(self, search_results: List[Dict]) -> List[Dict]:
        """Fetch content from URLs"""
        if not search_results:
            return []
        
        urls = [r['link'] for r in search_results if r.get('link')][:3]  # Limit to top 3
        
        try:
            pipeline = Pipeline()
            fetcher = LinkContentFetcher(retry_attempts=1, timeout=8)
            converter = HTMLToDocument()
            
            pipeline.add_component("fetcher", fetcher)
            pipeline.add_component("converter", converter)
            pipeline.connect("fetcher.streams", "converter.sources")
            
            result = pipeline.run({"fetcher": {"urls": urls}})
            documents = result.get("converter", {}).get("documents", [])
            
            web_content = []
            for i, doc in enumerate(documents):
                if i < len(search_results):
                    web_content.append({
                        "url": doc.meta.get("url", urls[i] if i < len(urls) else ""),
                        "title": search_results[i].get("title", ""),
                        "snippet": search_results[i].get("snippet", ""),
                        "content": doc.content[:2000] if doc.content else "",
                    })
            
            return web_content
            
        except Exception as e:
            print(f"Error fetching content: {e}")
            # Return snippets only as fallback
            return [{
                "url": r.get("link", ""),
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "content": ""
            } for r in search_results[:3]]
    
    async def _synthesize_enriched_response(
        self,
        query: str,
        web_content: List[Dict],
        concise_mode: bool
    ) -> str:
        """Synthesize enriched response from web content"""
        if not web_content:
            return "No web content available for synthesis."
        
        # Prepare web sources text
        sources_text = ""
        for i, content in enumerate(web_content, 1):
            sources_text += f"\nSource {i}: {content['title']}\n"
            if content.get('content'):
                sources_text += f"{content['content'][:800]}...\n"
            else:
                sources_text += f"{content['snippet']}\n"
        
        if concise_mode:
            prompt = f"""Based on the web sources below, provide a CONCISE answer to the query.

Query: {query}

Web Sources:
{sources_text}

Requirements:
- Answer in 2-3 sentences maximum
- Focus on the most relevant information
- Include specific details or values when available
- Cite source numbers [1], [2], etc.

Answer:"""
        else:
            prompt = f"""Based on the web sources below, provide a comprehensive answer to the query.

Query: {query}

Web Sources:
{sources_text}

Requirements:
- Provide specific technical details
- Highlight best practices or recommendations
- Cite sources with [1], [2], etc.
- Structure with clear sections if needed

Answer:"""
        
        try:
            response = await self.llm.acomplete(prompt)
            return str(response)
        except Exception as e:
            print(f"Error in synthesis: {e}")
            # Fallback to snippets
            fallback = "Web search results:\n"
            for content in web_content:
                fallback += f"- {content['title']}: {content['snippet']}\n"
            return fallback


# FastAPI endpoint function
async def web_enrichment(request: WebEnrichmentRequest, user_id: Optional[str] = None) -> WebEnrichmentResponse:
    """Web enrichment endpoint"""
    print(f"=== WEB ENRICHMENT DEBUG ===")
    print(f"user_id: {user_id}")
    print(f"message_id: {request.message_id}")
    print(f"query: {request.query}")
    
    workflow = WebEnrichmentWorkflow()
    response = await workflow.execute(request)
    
    print(f"Web search results count: {len(response.web_search_results)}")
    
    # Auto-update existing message if message_id is provided and user is authenticated
    if user_id and request.message_id:
        try:
            # Convert web search results to citations format
            web_citations = []
            for result in response.web_search_results:
                title = result.get("title", "")
                link = result.get("link", "")
                snippet = result.get("snippet", "")
                
                # Create rich text that includes both the snippet and the link
                citation_text = f"{snippet}\n\nSource: {title}\nURL: {link}" if title else f"{snippet}\nURL: {link}"
                
                web_citations.append({
                    "text": citation_text,
                    "metadata": {
                        "source_type": "web_search",
                        "url": link,
                        "title": title,
                        "source_origin": "web_search",
                        "position": result.get("position", 0),
                        "snippet": snippet  # Keep original snippet separate
                    },
                    "score": 1.0 - (result.get("position", 1) / 10)  # Higher position = higher score
                })
            
            success = update_chat_message_web_response(
                message_id=request.message_id,
                web_response=response.enriched_response,
                web_citations=web_citations
            )
            
            if success:
                print(f"Successfully updated message {request.message_id} with web enrichment")
            else:
                print(f"Failed to update message {request.message_id}")
                
        except Exception as e:
            print(f"Failed to update message: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Don't fail the query if update fails
    
    return response