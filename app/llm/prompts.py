from typing import List, Dict

# System prompt - defines the LLM's role and constraints
SYSTEM_PROMPT = """You are a system design expert and mentor. Your role is to explain WHY certain components matter in system design, helping students understand the reasoning behind best practices.

CRITICAL RULES:
1. You ONLY explain components that are already identified as missing (provided to you).
2. You NEVER invent or suggest additional missing components.
3. You ALWAYS respond with valid JSON only - no markdown, no extra text.
4. Your explanations should be educational, not generic.
5. Focus on interview preparation and production realities.

OUTPUT FORMAT (strict JSON):
{
  "explanations": [
    {
      "category": "CACHING",
      "why_it_matters": "Clear explanation of importance...",
      "interview_angle": "How this comes up in interviews...",
      "production_angle": "Real-world implications..."
    }
  ]
}

VALID CATEGORIES: CACHING, SCALABILITY, SECURITY, RELIABILITY, PERFORMANCE, DATABASE, API_DESIGN, GENERAL

If you cannot provide explanations, return: {"explanations": []}
"""


def build_explanation_prompt(
    design_content: str,
    missing_components: List[Dict],
) -> str:
    """
    Build the prompt for generating explanations.
    
    Args:
        design_content: The user's system design text
        missing_components: List of rule-based findings (suggestions)
    
    Returns:
        Formatted prompt string
    """
    
    # Format the missing components for the prompt
    components_text = "\n".join([
        f"- {comp['category']}: {comp['title']}"
        for comp in missing_components
    ])
    
    # Truncate design content if too long (keep first 2000 chars)
    if len(design_content) > 2000:
        design_excerpt = design_content[:2000] + "... [truncated]"
    else:
        design_excerpt = design_content
    
    prompt = f"""Analyze the following system design and explain why the identified missing components are important.

## User's System Design:
{design_excerpt}

## Missing Components (identified by rule-based analysis):
{components_text}

## Your Task:
For EACH missing component listed above, provide:
1. why_it_matters: Why is this component important? (educational explanation)
2. interview_angle: How might an interviewer ask about this?
3. production_angle: What happens in production without this?

RESPOND WITH VALID JSON ONLY. No markdown, no explanations outside JSON.

Example output format:
{{
  "explanations": [
    {{
      "category": "CACHING",
      "why_it_matters": "Caching reduces database load and improves response times by storing frequently accessed data in memory...",
      "interview_angle": "Interviewers often ask: 'Where would you add caching?' or 'How do you handle cache invalidation?'...",
      "production_angle": "Without caching, your database becomes a bottleneck. At scale, every request hitting the DB causes..."
    }}
  ]
}}
"""
    
    return prompt


def build_simple_prompt(category: str, title: str) -> str:
    """
    Build a simple single-component explanation prompt.
    
    Used when we want to explain just one missing component.
    """
    
    return f"""Explain why {title} ({category}) is important in system design.

Provide your response as JSON with this structure:
{{
  "explanations": [
    {{
      "category": "{category}",
      "why_it_matters": "...",
      "interview_angle": "...",
      "production_angle": "..."
    }}
  ]
}}

RESPOND WITH JSON ONLY.
"""