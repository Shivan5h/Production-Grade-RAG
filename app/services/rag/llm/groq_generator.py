"""
LLM generation using Groq with grounded, citation-enforced prompting.

Implements hallucination-minimized generation through:
- Strict retrieval grounding (context-only responses)
- Mandatory citation enforcement using [Source N] format
- Controlled generation parameters (temperature, top_p)
- Fast inference with Groq's LPU technology
"""
import logging
from typing import List, Dict, Optional
from groq import Groq

from config.settings import settings

logger = logging.getLogger(__name__)


class GroqLLMGenerator:
    """LLM generation using Groq."""
    
    def __init__(self):
        """Initialize Groq LLM."""
        self.client = Groq(api_key=settings.groq_api_key)
        self.model_name = settings.groq_model
        logger.info(f"Initialized GroqLLMGenerator with model: {self.model_name}")
    
    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict],
        temperature: float = None,
        top_p: float = None,
        max_tokens: int = None
    ) -> Dict:
        """
        Generate grounded answer using Groq.
        
        Args:
            query: User question
            context_chunks: Retrieved context from vector database
            temperature: Sampling temperature (default from settings)
            top_p: Nucleus sampling parameter (default from settings)
            max_tokens: Maximum tokens to generate (default from settings)
            
        Returns:
            Dict with 'answer' and 'model' keys
        """
        # Use settings defaults if not provided
        temperature = temperature if temperature is not None else settings.llm_temperature
        top_p = top_p if top_p is not None else settings.llm_top_p
        max_tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens
        
        # Validate context
        if not context_chunks:
            return {
                "answer": "I could not find any relevant information in the uploaded documents to answer your question.",
                "model": self.model_name
            }
        
        # Group chunks by document (filename)
        from collections import defaultdict
        docs_chunks = defaultdict(list)
        for chunk in context_chunks:
            filename = chunk.get('metadata', {}).get('filename', 'unknown')
            content = chunk.get('content') or chunk.get('metadata', {}).get('content', '')
            if content:
                docs_chunks[filename].append(content)
        
        if not docs_chunks:
            return {
                "answer": "The retrieved chunks do not contain readable content.",
                "model": self.model_name
            }
        
        # Build context with document-level source numbers
        context_parts = []
        source_mapping = {}  # Map filenames to source numbers
        for idx, (filename, chunks) in enumerate(docs_chunks.items(), 1):
            source_mapping[filename] = idx
            combined_content = "\n\n".join(chunks)
            context_parts.append(f"[Source {idx}: {filename}]\n{combined_content}\n")
        
        context_text = "\n".join(context_parts)
        
        # Build grounded prompt
        source_list = ", ".join([f"Source {idx} ({filename})" for filename, idx in source_mapping.items()])
        prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context.

IMPORTANT INSTRUCTIONS:
1. Answer ONLY using information from the context below
2. Cite your sources using [Source N] format where N corresponds to the document number
3. Available sources: {source_list}
4. If the context doesn't contain enough information, say so clearly
5. Do not use external knowledge or make assumptions
6. Be concise but complete

Context:
{context_text}

Question: {query}

Answer (with citations):"""
        
        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides accurate answers based on given context with proper citations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens
            )
            
            answer = response.choices[0].message.content
            
            logger.info(f"Generated answer using {self.model_name}")
            
            return {
                "answer": answer,
                "model": self.model_name,
                "source_mapping": {f"Source {idx}": filename for filename, idx in source_mapping.items()}
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise
