from typing import TypedDict, Optional, List


class EmailClassification(TypedDict, total=False):
    """Schema for email classification result."""
    type: str  # inquiry, complaint, status_check, other
    priority_score: float  # 0.0 - 1.0
    urgency: str  # low, medium, high
    language: str  # en, pt, es, etc.
    products_mentioned: list[str]
    customer_region: str
    requires_human: bool
    suggested_route: str  # quote_flow, complaint_flow, status_flow, general_flow


CLASSIFIER_PROMPT = """
You are an email classification specialist for pharmaceutical distribution.

Classify the following email and return a JSON object with the classification result.

【Subject】
{subject}

【Email Body】
{email_body}

Return a JSON object with this exact schema:
{{
  "type": "<inquiry|complaint|status_check|other>",
  "priority_score": <float 0.0-1.0>,
  "urgency": "<low|medium|high>",
  "language": "<en|pt|es|fr|de|zh|ar>",
  "products_mentioned": ["<product name>", ...],
  "customer_region": "<region/country>",
  "requires_human": <true|false>,
  "suggested_route": "<quote_flow|complaint_flow|status_flow|general_flow>"
}}

Classification guidelines:
1. Type:
   - inquiry: Request for quote, product information, or pricing
   - complaint: Issue with order, quality, delivery, or service
   - status_check: Asking about order status or shipment tracking
   - other: Everything else

2. Priority score:
   - 0.9-1.0: VIP customer, large order (>50k USD), urgent deadline
   - 0.7-0.9: Regular inquiry, time-sensitive
   - 0.4-0.6: Standard inquiry
   - 0.0-0.3: Low priority, spam, or unclear

3. Urgency:
   - high: Mentions deadline, urgent, ASAP, or VIP customer
   - medium: Normal business timeframe
   - low: No urgency indicated

4. Products: List all pharmaceutical products mentioned

5. Region: Infer from email content, company domain, or explicit mention

6. Requires human: true if complaint, complex issue, or priority > 0.8

7. Suggested route:
   - quote_flow: Type is inquiry
   - complaint_flow: Type is complaint
   - status_flow: Type is status_check
   - general_flow: Type is other

Output ONLY the JSON, no additional text.
"""
