import os
import json
from openai import OpenAI


def get_openai_client():
    return OpenAI(
        api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
        base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    )


def summarize_chat_history(messages):
    """
    Use OpenAI to summarize chat history and extract key context.
    
    Args:
        messages: List of chat messages with 'sender_type' and 'message' keys
    
    Returns:
        dict: Structured context with intent, preferences, key_points, etc.
    """
    if not messages:
        return {}
    
    chat_transcript = "\n".join([
        f"{'Client' if m.get('sender_type') == 'client' else 'Bot'}: {m.get('message', '')}"
        for m in messages
    ])
    
    prompt = f"""Analyze this chat conversation and extract key information in JSON format.

Chat Transcript:
{chat_transcript}

Extract and return a JSON object with these fields:
- intent: What is the client's main purpose/goal? (string)
- preferences: Any preferences mentioned (list of strings)
- key_points: Important details or requirements (list of strings)
- sentiment: Overall sentiment (positive/neutral/negative)
- urgency: How urgent is their need? (low/medium/high)
- summary: Brief 1-2 sentence summary

Return ONLY valid JSON, no other text."""

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured information from chat conversations. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        return json.loads(content)
    
    except json.JSONDecodeError:
        return {
            "intent": "Unable to parse",
            "summary": "Chat history collected but parsing failed",
            "raw_response": content if 'content' in locals() else None
        }
    except Exception as e:
        return {
            "error": str(e),
            "summary": "Failed to summarize chat history"
        }
