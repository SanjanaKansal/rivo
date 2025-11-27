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
    
    prompt = f"""Analyze this mortgage-related chat conversation and extract key information in JSON format.

Chat Transcript:
{chat_transcript}

Extract and return a JSON object with these fields:
- intent: What is the client's main goal? (e.g., refinance, new mortgage, loan inquiry)
- loan_details: Object with any mentioned loan information:
  - current_loan_amount: Amount if mentioned (string or null)
  - monthly_payment: Current payment if mentioned (string or null)
  - interest_rate: Current rate if mentioned (string or null)
  - loan_type: Type of loan (mortgage, refinance, HELOC, etc.)
  - property_type: Type of property if mentioned (string or null)
  - property_value: Estimated value if mentioned (string or null)
- financial_info: Object with financial details:
  - income: Income if mentioned (string or null)
  - credit_score: Credit score range if mentioned (string or null)
  - debt_to_income: DTI if mentioned (string or null)
  - employment_status: Employment info if mentioned (string or null)
- preferences: Any preferences mentioned (list of strings)
- key_points: Other important details or requirements (list of strings)
- sentiment: Overall sentiment (positive/neutral/negative)
- urgency: How urgent is their need? (low/medium/high)
- summary: Brief 1-2 sentence summary focusing on their mortgage needs

Return ONLY valid JSON, no other text."""

    try:
        openai_client = get_openai_client()
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a mortgage industry assistant that extracts structured information from client conversations. Focus on loan details, financial information, and mortgage-related needs. Always respond with valid JSON only."},
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
