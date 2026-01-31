from typing import List, Dict
from prisma import Prisma
import logging
from app.llm.client import get_llm_client, LLMError
from app.llm.prompts import build_explanation_prompt
from app.llm.schemas import LLMResponse

logger = logging.getLogger(__name__)

# ============== Concept Buckets (Keyword Constants) ==============

CACHE_KEYWORDS = ["cache", "caching", "redis", "memcached", "cdn", "varnish", "in-memory"]
SCALING_KEYWORDS = ["horizontal scaling", "load balancer", "auto-scaling", "scale out", "multiple instances", "kubernetes", "k8s", "elasticity"]
RATE_LIMITING_KEYWORDS = ["rate limit", "rate-limit", "throttle", "throttling", "api gateway", "quota", "leaky bucket", "token bucket"]
INDEXING_KEYWORDS = ["index", "indexing", "query optimization", "explain", "primary key", "foreign key", "b-tree", "full text search"]
AUTH_KEYWORDS = ["authentication", "authorization", "auth", "jwt", "oauth", "rbac", "permissions", "abac", "mfa", "sso"]
ERROR_HANDLING_KEYWORDS = ["error handling", "exception", "retry", "fallback", "circuit breaker", "graceful degradation", "dead letter queue"]
OBSERVABILITY_KEYWORDS = ["monitoring", "logging", "metrics", "alerting", "observability", "tracing", "prometheus", "grafana", "elk stack"]
BACKUP_KEYWORDS = ["backup", "disaster recovery", "replication", "snapshot", "restore", "dr", "point-in-time recovery"]
VERSIONING_KEYWORDS = ["api version", "versioning", "v1", "v2", "backward compatible", "deprecation", "semantic versioning"]
SHARDING_KEYWORDS = ["shard", "sharding", "partition", "partitioning", "distributed database", "horizontal partitioning"]
ASYNC_KEYWORDS = ["queue", "message queue", "kafka", "rabbitmq", "sqs", "async", "event-driven", "pubsub", "worker", "celery"]
VALIDATION_KEYWORDS = ["validation", "sanitize", "sanitization", "input validation", "schema validation", "pydantic", "cors"]

# ============== Rule Definitions ==============

ANALYSIS_RULES: List[Dict] = [
    # Caching Rules
    {
        "keywords": CACHE_KEYWORDS,
        "suggestion": {
            "title": "Consider Adding Caching Layer",
            "description": (
                "Your design doesn't mention caching. Consider adding a caching layer "
                "(Redis, Memcached, or CDN) to improve response times and reduce database load. "
                "Cache frequently accessed data like user sessions, API responses, or computed results."
            ),
            "category": "CACHING",
            "severity": "WARNING"
        }
    },
    
    # Scalability Rules
    {
        "keywords": SCALING_KEYWORDS,
        "suggestion": {
            "title": "Add Horizontal Scaling Strategy",
            "description": (
                "Your design doesn't mention horizontal scaling. Consider how your system will "
                "handle increased load. Add load balancers and design services to be stateless "
                "so they can run as multiple instances. Consider container orchestration (K8s) for auto-scaling."
            ),
            "category": "SCALABILITY",
            "severity": "CRITICAL"
        }
    },
    
    # Rate Limiting Rules
    {
        "keywords": RATE_LIMIT_KEYWORDS if 'RATE_LIMIT_KEYWORDS' in locals() else RATE_LIMITING_KEYWORDS,
        "suggestion": {
            "title": "Implement Rate Limiting",
            "description": (
                "Your design doesn't mention rate limiting. Protect your APIs from abuse and "
                "ensure fair usage by implementing rate limiting. Consider using an API gateway "
                "or middleware to enforce request quotas per user/IP."
            ),
            "category": "SECURITY",
            "severity": "WARNING"
        }
    },
    
    # Database Indexing
    {
        "keywords": INDEXING_KEYWORDS,
        "suggestion": {
            "title": "Define Database Indexing Strategy",
            "description": (
                "Your design doesn't mention database indexing. Proper indexes are crucial for "
                "query performance. Identify frequently queried fields and create appropriate "
                "indexes. Consider composite indexes for queries with multiple conditions."
            ),
            "category": "DATABASE",
            "severity": "WARNING"
        }
    },
    
    # Authentication & Authorization
    {
        "keywords": AUTH_KEYWORDS,
        "suggestion": {
            "title": "Define Authentication & Authorization",
            "description": (
                "Your design doesn't clearly mention authentication or authorization. "
                "Define how users will authenticate (JWT, OAuth, sessions) and how you'll "
                "handle authorization (RBAC, ABAC). This is critical for security."
            ),
            "category": "SECURITY",
            "severity": "CRITICAL"
        }
    },
    
    # Error Handling
    {
        "keywords": ERROR_HANDLING_KEYWORDS,
        "suggestion": {
            "title": "Add Error Handling Strategy",
            "description": (
                "Your design doesn't mention error handling patterns. Consider implementing "
                "retry logic with exponential backoff, circuit breakers for external services, "
                "and graceful degradation when dependencies fail."
            ),
            "category": "RELIABILITY",
            "severity": "WARNING"
        }
    },
    
    # Monitoring & Logging
    {
        "keywords": OBSERVABILITY_KEYWORDS,
        "suggestion": {
            "title": "Implement Observability",
            "description": (
                "Your design doesn't mention monitoring or logging. Add structured logging, "
                "metrics collection (Prometheus), and distributed tracing for debugging. "
                "Set up alerting for critical failures and performance degradation."
            ),
            "category": "RELIABILITY",
            "severity": "INFO"
        }
    },
    
    # Data Backup
    {
        "keywords": BACKUP_KEYWORDS,
        "suggestion": {
            "title": "Plan for Data Backup & Recovery",
            "description": (
                "Your design doesn't mention backup or disaster recovery. Define your backup "
                "strategy (frequency, retention), replication for high availability, and "
                "document recovery procedures. Consider RPO and RTO requirements."
            ),
            "category": "RELIABILITY",
            "severity": "WARNING"
        }
    },
    
    # API Versioning
    {
        "keywords": VERSIONING_KEYWORDS,
        "suggestion": {
            "title": "Consider API Versioning Strategy",
            "description": (
                "Your design doesn't mention API versioning. Plan how you'll handle breaking "
                "changes. Use URL versioning (/api/v1) or header-based versioning. Define "
                "deprecation policies for old versions."
            ),
            "category": "API_DESIGN",
            "severity": "INFO"
        }
    },
    
    # Database Sharding
    {
        "keywords": SHARDING_KEYWORDS,
        "suggestion": {
            "title": "Consider Database Partitioning",
            "description": (
                "For large-scale systems, consider database sharding or partitioning strategies. "
                "This helps distribute data across multiple nodes and improves query performance. "
                "Choose a sharding key carefully based on your access patterns."
            ),
            "category": "SCALABILITY",
            "severity": "INFO"
        }
    },
    
    # Message Queue (for async processing)
    {
        "keywords": ASYNC_KEYWORDS,
        "suggestion": {
            "title": "Consider Asynchronous Processing",
            "description": (
                "Your design doesn't mention message queues or async processing. For operations "
                "that don't need immediate response (emails, notifications, heavy processing), "
                "consider using message queues (Kafka, RabbitMQ, SQS) to decouple services."
            ),
            "category": "PERFORMANCE",
            "severity": "INFO"
        }
    },
    
    # Data Validation
    {
        "keywords": VALIDATION_KEYWORDS,
        "suggestion": {
            "title": "Add Input Validation",
            "description": (
                "Your design doesn't explicitly mention input validation. Validate all user "
                "inputs at API boundaries to prevent injection attacks and ensure data integrity. "
                "Use schema validation libraries and sanitize inputs before processing."
            ),
            "category": "SECURITY",
            "severity": "WARNING"
        }
    },
]



def analyze_design_content(content: str) -> List[Dict]:
    """
    Analyze design content and generate suggestions.
    
    Args:
        content: The LLD text content to analyze
    
    Returns:
        List of suggestion dictionaries
    
    Algorithm:
    1. Convert content to lowercase for case-insensitive matching
    2. For each rule, check if ANY keyword is present
    3. If no keywords found, add the suggestion
    """
    suggestions = []
    content_lower = content.lower()
    
    for rule in ANALYSIS_RULES:
        keywords = rule["keywords"]
        
        # Check if any keyword is mentioned in the content
        keyword_found = any(kw.lower() in content_lower for kw in keywords)
        
        if not keyword_found:
            suggestions.append(rule["suggestion"])
    
    return suggestions

async def enrich_with_llm_explanations(
    design_content: str,
    suggestions: List[Dict],
) -> Dict[str, Dict]:
    """
    Call LLM to get explanations for missing components.
    
    Args:
        design_content: The original design text
        suggestions: List of rule-based suggestions
    
    Returns:
        Dict mapping category to LLM explanation
        Empty dict if LLM unavailable or fails
    
    Flow:
        1. Check if LLM is available
        2. Build prompt with design + missing components
        3. Call LLM
        4. Parse and validate response
        5. Return explanations mapped by category
        6. On any error, return empty dict (graceful fallback)
    """
    # Get LLM client (returns None if not configured)
    llm_client = get_llm_client()
    
    if not llm_client:
        logger.info("LLM not configured, skipping enrichment")
        return {}
    
    if not suggestions:
        logger.info("No suggestions to enrich")
        return {}
    
    try:
        # Build prompt
        prompt = build_explanation_prompt(design_content, suggestions)
        
        # Call LLM
        llm_response: LLMResponse = await llm_client.generate(prompt)
        
        # Map explanations by category for easy lookup
        explanations_map = {}
        for explanation in llm_response.explanations:
            explanations_map[explanation.category] = {
                "why_it_matters": explanation.why_it_matters,
                "interview_angle": explanation.interview_angle,
                "production_angle": explanation.production_angle,
            }
        
        logger.info(f"LLM enrichment successful: {len(explanations_map)} explanations")
        return explanations_map
        
    except LLMError as e:
        logger.warning(f"LLM enrichment failed: {e.message}")
        return {}
    
    except Exception as e:
        logger.error(f"Unexpected error in LLM enrichment: {e}")
        return {}
async def run_analysis(db: Prisma, project_id: int) -> List:
    """
    Run analysis on a project's design and save suggestions.
    
    This is the main entry point for analysis:
    1. Fetches project with design details
    2. Clears previous suggestions (for re-analysis)
    3. Runs rule-based analysis
    4. Saves new suggestions
    5. Updates project status
    
    Args:
        db: Prisma client
        project_id: ID of the project to analyze
    
    Returns:
        List of created Suggestion objects
    """
    # Get project with design details
    project = await db.project.find_unique(
        where={"id": project_id},
        include={"designDetails": True}
    )
    
    if not project or not project.designDetails:
        return []
    
    design_content = project.designDetails.content
    design_version = project.designDetails.version
    
    # Clear previous suggestions for this project
    await db.suggestion.delete_many(where={"projectId": project_id})
    
    # Run rule-based analysis
    suggestion_data = analyze_design_content(design_content)
    
    # ========== LLM ENRICHMENT ==========
    # Get LLM explanations for missing components
    llm_explanations = await enrich_with_llm_explanations(
        design_content,
        suggestion_data
    )
    
    # Enrich suggestions with LLM explanations
    for suggestion in suggestion_data:
        category = suggestion["category"]
        if category in llm_explanations:
            # Append LLM insights to the description
            llm_data = llm_explanations[category]
            enhanced_description = (
                f"{suggestion['description']}\n\n"
                f"**Why It Matters:** {llm_data['why_it_matters']}\n\n"
                f"**Interview Perspective:** {llm_data['interview_angle']}\n\n"
                f"**Production Reality:** {llm_data['production_angle']}"
            )
            suggestion["description"] = enhanced_description
    # ========== END LLM ENRICHMENT ==========
    
    # Create new suggestions
    created_suggestions = []
    for data in suggestion_data:
        suggestion = await db.suggestion.create(
            data={
                "title": data["title"],
                "description": data["description"],
                "category": data["category"],
                "severity": data["severity"],
                "designVersion": design_version,
                "projectId": project_id
            }
        )
        created_suggestions.append(suggestion)
    
    # Update project status to ANALYZED
    await db.project.update(
        where={"id": project_id},
        data={"status": "ANALYZED"}
    )
    
    return created_suggestions


async def get_suggestions_for_project(db: Prisma, project_id: int) -> List:
    """Get all suggestions for a project, ordered by creation date."""
    return await db.suggestion.find_many(
        where={"projectId": project_id},
        order={"createdAt": "desc"}
    )
