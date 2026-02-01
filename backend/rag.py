from typing import Tuple, List, Dict
import os
from dotenv import load_dotenv
import json

load_dotenv()  # Reads .env automatically

from google import genai
from google.genai.types import GenerateContentConfig

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def classify_query(question: str) -> Dict:
    """
    Agent 1: Query Classification
    Classifies the user's question to determine retrieval strategy.
    
    Returns:
        {
            "type": "simple" | "comparison" | "unclear" | "multi_hop",
            "entities": [list of key terms to search],
            "clarification_needed": bool,
            "clarification_question": str (if needed)
        }
    """
    classification_prompt = f"""
You are a query analysis agent for a medical document RAG system. The user has uploaded documents and wants to query them.

Question: "{question}"

IMPORTANT CONTEXT:
- The user has uploaded documents to a database
- When user says "reports", "files", "documents", they mean the uploaded documents in the system
- Queries about "all files", "3 reports", "uploaded documents" are CLEAR and refer to the database
- Medical queries about RBC, WBC, hemoglobin, etc. are CLEAR medical terms
- Do NOT ask for clarification if the query mentions medical data extraction or comparison

Determine:
1. Type: Is it a simple lookup, comparison between items, unclear/vague, or requires multiple steps?
2. Key entities: What specific terms should be searched?
3. Clarity: Is the question clear enough to answer from uploaded documents?

Respond in JSON format:
{{
    "type": "simple|comparison|unclear|multi_hop",
    "entities": ["entity1", "entity2"],
    "clarification_needed": true/false,
    "clarification_question": "What specific aspect are you asking about?"
}}

Examples:
- "What are side effects of aspirin?" → {{"type": "simple", "entities": ["aspirin", "side effects"], "clarification_needed": false}}
- "Compare aspirin and ibuprofen" → {{"type": "comparison", "entities": ["aspirin", "ibuprorin"], "clarification_needed": false}}
- "extract all subjects from reports and compare" → {{"type": "comparison", "entities": ["RBC", "WBC", "hemoglobin", "platelets"], "clarification_needed": false}}
- "do trend analysis for all files" → {{"type": "comparison", "entities": ["trend", "analysis"], "clarification_needed": false}}
- "compare all 3 reports" → {{"type": "comparison", "entities": ["comparison", "reports"], "clarification_needed": false}}
- "What about that medication?" → {{"type": "unclear", "entities": [], "clarification_needed": true, "clarification_question": "Which medication are you asking about? Please specify the name."}}
- "Tell me about it" → {{"type": "unclear", "entities": [], "clarification_needed": true, "clarification_question": "Could you please specify what you'd like to know more about?"}}

ONLY classify as "unclear" if the question has NO context and uses vague pronouns like "it", "that", "this" without specifying what they refer to.

Analyze:
"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=classification_prompt
        )
        
        # Extract JSON from response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        classification = json.loads(response_text)
        return classification
    except Exception as e:
        # Fallback: treat as simple query
        return {
            "type": "simple",
            "entities": [question],
            "clarification_needed": False
        }


def retrieve_for_entities(entities: List[str], vector_store, top_k: int = 4) -> List[dict]:
    """
    Agent 2: Multi-entity Retrieval
    Retrieves relevant chunks for each entity separately, then combines.
    """
    all_chunks = []
    seen_ids = set()
    
    for entity in entities:
        chunks = vector_store.similarity_search(entity, top_k=top_k)
        for chunk in chunks:
            # Deduplicate based on text + doc_name + page
            chunk_id = f"{chunk['doc_name']}_{chunk['page_number']}_{chunk['text'][:50]}"
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                all_chunks.append(chunk)
    
    return all_chunks


def extract_relevant_snippets(answer: str, evidence_chunks: List[dict]) -> List[dict]:
    """
    Agent 4: Evidence Snippet Extraction
    Extracts only the specific sentence/phrase from each evidence chunk that supports the answer.
    """
    snippets = []
    
    for chunk in evidence_chunks:
        try:
            extraction_prompt = f"""
Extract ONLY the specific sentence or phrase from the text below that directly supports this answer.
Return just the relevant quote, nothing else. If multiple sentences are needed, combine them.
Keep it concise - maximum 1-2 sentences.

Answer: {answer[:500]}

Text: {chunk['text'][:1000]}

Relevant quote:
"""
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=extraction_prompt
            )
            snippet_text = response.text.strip()
            
            # Remove quotes if LLM added them
            snippet_text = snippet_text.strip('"').strip("'")
            
            # If snippet is too long, truncate
            if len(snippet_text) > 200:
                snippet_text = snippet_text[:200] + "..."
            
            snippets.append({
                "doc_name": chunk['doc_name'],
                "page_number": chunk['page_number'],
                "text": snippet_text
            })
        except Exception as e:
            print(f"Error extracting snippet: {e}")
            # Fallback: use first 150 characters
            snippets.append({
                "doc_name": chunk['doc_name'],
                "page_number": chunk['page_number'],
                "text": chunk['text'][:150] + "..."
            })
    
    return snippets


def verify_answer_grounding(answer: str, context_text: str) -> bool:
    """
    Agent 3: Grounding Verification
    Ensures the answer is actually supported by the retrieved context.
    """
    verification_prompt = f"""
You are a fact-checker. Determine if the answer is FULLY supported by the context.

Context:
{context_text[:2000]}  

Answer: {answer}

Is this answer fully grounded in the context above? Respond ONLY with "YES" or "NO".
If the answer makes ANY claims not present in the context, respond "NO".
"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=verification_prompt
        )
        result = response.text.strip().upper()
        return "YES" in result
    except:
        return True  # Fallback: trust the answer


def retrieve_and_answer(question: str, vector_store, top_k: int = 5, conversation_history: List[dict] = None) -> Tuple[str, List[dict]]:
    """
    Main Agentic RAG Pipeline
    
    Steps:
    1. Check if this is a follow-up question that can be answered from conversation history
    2. Classify query (simple, comparison, unclear, multi-hop)
    3. If unclear → request clarification
    4. Retrieve using appropriate strategy
    5. Generate answer with strict grounding
    6. Verify answer is grounded in context
    7. Extract concise evidence snippets
    8. Return answer + evidence
    """
    
    # Step 1: Check if question can be answered from conversation history
    if conversation_history and len(conversation_history) > 0:
        # Get last few messages for context
        recent_context = conversation_history[-4:]  # Last 2 Q&A pairs
        
        # Keywords that indicate need for document retrieval
        retrieval_keywords = [
            "retrieve", "get data", "show me", "find", "search",
            "trend analysis", "compare all", "all counts", "all data",
            "summarize", "summary", "complete", "everything",
            "how many documents", "how many files", "list all", "what documents",
            "which documents", "all documents", "uploaded documents", "current documents"
        ]
        
        # Check if question contains retrieval keywords
        needs_retrieval = any(keyword in question.lower() for keyword in retrieval_keywords)
        
        # Only try follow-up detection if no retrieval keywords present
        if not needs_retrieval:
            # Check if this is a simple follow-up question
            followup_check = f"""
Is this a simple follow-up question that can be answered using ONLY the previous conversation, without needing to retrieve new data?

Recent conversation:
{json.dumps(recent_context, indent=2)}

Current question: {question}

Examples of SIMPLE follow-ups (answer from conversation):
- "which is higher?" (when previous answer showed values)
- "what about the other one?"
- "is that normal?"

Examples that NEED retrieval (don't answer from conversation):
- "compare all counts" (needs complete data)
- "show me trend analysis" (needs full dataset)
- "what are all the values?" (needs retrieval)

If this is a SIMPLE follow-up, respond with "FOLLOWUP: [answer based on conversation]"
Otherwise, respond with "NEW_QUERY"

Response:
"""
            
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=followup_check
                )
                result = response.text.strip()
                
                if result.startswith("FOLLOWUP:"):
                    followup_answer = result.replace("FOLLOWUP:", "").strip()
                    # Return answer without new evidence since it's from conversation
                    return followup_answer, []
            except Exception as e:
                print(f"Error in follow-up detection: {e}")
                # Continue with normal processing
    
    # Step 2: Classify Query
    classification = classify_query(question)
    
    # Step 3: Handle unclear queries
    if classification.get("clarification_needed", False):
        clarification_msg = classification.get(
            "clarification_question",
            "Could you please provide more details or context for your question? This will help me find the most relevant information from your documents."
        )
        return clarification_msg, []
    
    # Step 4: Retrieve based on query type
    query_type = classification.get("type", "simple")
    entities = classification.get("entities", [question])
    
    if query_type == "comparison" and len(entities) >= 2:
        # Multi-entity retrieval for comparisons
        retrieved_chunks = retrieve_for_entities(entities, vector_store, top_k=3)
    else:
        # Standard retrieval
        retrieved_chunks = vector_store.similarity_search(question, top_k=top_k)
    
    # Step 4: Check if we have relevant chunks
    if not retrieved_chunks or all(not c["text"].strip() for c in retrieved_chunks):
        return (
            "I cannot find relevant information in your uploaded documents to answer this question. "
            "Please try uploading documents that contain information about this topic, or rephrase your question.",
            []
        )
    
    # Step 5: Build context
    context_text = ""
    for i, chunk in enumerate(retrieved_chunks):
        context_text += f"[Source {i+1}: {chunk['doc_name']}, Page {chunk['page_number']}]\n{chunk['text']}\n\n"
    
    # Step 6: Generate answer with strict instructions
    if query_type == "comparison":
        prompt = f"""
You are a medical document assistant. Answer the comparison question using ONLY the information in the context below.

STRICT RULES:
1. Use ONLY information present in the context
2. If comparing items, clearly separate information about each
3. Cite sources like [Source X]
4. If information is missing for comparison, state "Information about [item] is not available in the documents"
5. DO NOT make assumptions or use external knowledge
6. If you cannot answer from the context, say "I cannot find sufficient information in your documents to answer this comparison"

Context:
{context_text}

Question: {question}

Provide a structured comparison:
"""
    else:
        prompt = f"""
You are a medical document assistant. Answer the question using ONLY the information in the context below.

STRICT RULES:
1. Use ONLY information from the context provided
2. Cite sources using [Source X] format
3. If the answer is not in the context, respond: "I cannot find this information in your uploaded documents. Please upload relevant documents or rephrase your question."
4. DO NOT use any external knowledge or make assumptions
5. DO NOT hallucinate or guess

Context:
{context_text}

Question: {question}

Answer:
"""
    
    # Step 7: Generate answer
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        answer = response.text.strip()
        
        # Step 8: Verify grounding
        is_grounded = verify_answer_grounding(answer, context_text)
        
        if not is_grounded:
            return (
                "I cannot provide a reliable answer from your uploaded documents. "
                "The available information may not be sufficient to answer this question accurately. "
                "Please upload more relevant documents or rephrase your question.",
                []
            )
        
        # Step 9: Extract used evidence
        used_evidence = []
        for chunk in retrieved_chunks:
            # Check if source was mentioned in answer
            if chunk['doc_name'] in answer or f"Source" in answer:
                used_evidence.append(chunk)
        
        # Fallback: use top chunks if no explicit citations
        if not used_evidence:
            used_evidence = retrieved_chunks[:min(3, len(retrieved_chunks))]
        
        # Step 10: Extract concise snippets from evidence
        evidence_snippets = extract_relevant_snippets(answer, used_evidence)
            
    except Exception as e:
        return (
            f"An error occurred while processing your question. Please try again or rephrase your question.",
            []
        )
    
    return answer, evidence_snippets
