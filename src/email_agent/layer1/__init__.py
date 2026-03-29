from typing import TypedDict


class EmailClassification(TypedDict, total=False):
    """Schema for email classification output."""

    type: str  # inquiry, complaint, question, contract, other
    priority_score: float  # 0.0-1.0
    urgency: str  # low, medium, high
    language: str  # en, pt, zh
    products_mentioned: list[str]
    customer_region: str  # brazil, china, other
    requires_human: bool
    suggested_route: str  # quote_flow, complaint_flow, auto_reply, manual


CLASSIFIER_PROMPT = """
You are an email classification expert for a pharmaceutical distribution company.

Analyze the following email and output a JSON object with this exact schema:
{
  "type": "inquiry|complaint|question|contract|other",
  "priority_score": <float 0.0-1.0>,
  "urgency": "low|medium|high",
  "language": "en|pt|zh",
  "products_mentioned": ["<product1>", "<product2>"],
  "customer_region": "brazil|china|other",
  "requires_human": <boolean>,
  "suggested_route": "quote_flow|complaint_flow|auto_reply|manual"
}

Classification guidelines:
1. Type identification:
   - inquiry: Customer asking about products/prices
   - complaint: Customer reporting issues
   - question: General inquiry not about specific products
   - contract: Contract-related documents or terms
   - other: Anything else

2. Priority scoring:
   - 0.8-1.0: Large orders, urgent requests, key customers
   - 0.5-0.8: Standard inquiries, moderate importance
   - 0.0-0.5: General questions, spam-like content

3. Region detection:
   - Look for country names, city names, timezone references
   - Brazil: mentions of Brazil, Portuguese, ANVISA, São Paulo
   - China: mentions of China, Chinese language, NMPA

4. Human routing:
   - requires_human=true if: complaint, legal/contract issues, very low confidence
   - Otherwise route to automated flow

Email content:
{email_body}

Subject: {subject}

Output ONLY the JSON, no additional text.
"""
