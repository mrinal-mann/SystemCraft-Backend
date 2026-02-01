from typing import List, Dict, Tuple
from datetime import datetime
from prisma import Prisma
import logging
from app.llm.client import get_llm_client, LLMError
from app.llm.prompts import build_explanation_prompt
from app.llm.schemas import LLMResponse

logger = logging.getLogger(__name__)

# ============== Master Concept Buckets ==============

API_KEYWORDS = ["api", "rest", "http", "endpoint", "graphql", "grpc", "request", "response", "gateway", "controller"]
AUTH_KEYWORDS = ["auth", "authentication", "authorization", "jwt", "oauth", "login", "signup", "session", "cookie", "token", "rbac"]
DB_KEYWORDS = ["database", "postgres", "mysql", "nosql", "mongodb", "dynamodb", "cassandra", "sql", "storage", "persist"]
CACHE_KEYWORDS = ["cache", "redis", "memcached", "in-memory", "lru", "ttl", "hot data"]
SCALING_KEYWORDS = ["scale", "scaling", "horizontal", "load balancer", "replica", "multiple instances", "autoscale", "hpa"]
REALTIME_KEYWORDS = ["websocket", "websockets", "socket.io", "realtime", "long polling", "server sent events", "grpc stream", "pub/sub", "presence", "live updates"]
QUEUE_KEYWORDS = ["queue", "kafka", "rabbitmq", "pubsub", "asynchronous", "worker", "background job", "event driven"]
INDEXING_KEYWORDS = ["index", "indexing", "query optimization", "composite index", "search index"]
OBSERVABILITY_KEYWORDS = ["logging", "monitoring", "metrics", "tracing", "prometheus", "grafana", "alerts", "observability"]
RELIABILITY_KEYWORDS = ["retry", "timeout", "circuit breaker", "fallback", "graceful failure", "idempotent"]
SAFETY_KEYWORDS = ["rate limit", "throttle", "token bucket", "abuse", "spam prevention"]
STORAGE_KEYWORDS = ["s3", "object storage", "blob storage", "cdn", "file upload", "media storage"]
SEARCH_KEYWORDS = ["search", "elasticsearch", "full text search", "filter", "query search"]
BACKUP_KEYWORDS = ["backup", "restore", "replication", "disaster recovery"]
VERSIONING_KEYWORDS = ["versioning", "v1", "v2", "backward compatibility"]
SHARDING_KEYWORDS = ["shard", "sharding", "partition", "data partitioning", "consistent hashing"]
INFRA_KEYWORDS = ["docker", "kubernetes", "cloud", "aws", "gcp", "azure", "container", "vm"]
VALIDATION_KEYWORDS = ["validation", "sanitize", "sanitization", "input validation", "schema validation", "pydantic", "cors"]

# ============== Domain-Specific Hints ==============

CHAT_HINTS = ["chat", "message", "room", "conversation"]
MEDIA_HINTS = ["video", "image", "upload", "stream"]
RIDE_HINTS = ["driver", "rider", "location", "gps"]
ECOM_HINTS = ["cart", "order", "payment", "inventory"]
SOCIAL_HINTS = ["post", "feed", "follow", "like"]

# ============== Step 3: Maturity Score Concept Groups ==============

MATURITY_CONCEPTS = {
    "API": {
        "keywords": API_KEYWORDS + REALTIME_KEYWORDS,
        "description": "API/Communication layer defined"
    },
    "DATABASE": {
        "keywords": DB_KEYWORDS + STORAGE_KEYWORDS,
        "description": "Storage strategy present"
    },
    "CACHE": {
        "keywords": CACHE_KEYWORDS,
        "description": "Caching layer considered"
    },
    "SCALING": {
        "keywords": SCALING_KEYWORDS + SHARDING_KEYWORDS,
        "description": "Scaling strategy defined"
    },
    "SAFETY": {
        "keywords": AUTH_KEYWORDS + SAFETY_KEYWORDS + RELIABILITY_KEYWORDS + VALIDATION_KEYWORDS,
        "description": "Safety & Integrity measures"
    }
}

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
        "keywords": SAFETY_KEYWORDS,
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
        "keywords": RELIABILITY_KEYWORDS,
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
        "keywords": QUEUE_KEYWORDS,
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
    
    # Real-time Communication
    {
        "keywords": REALTIME_KEYWORDS,
        "suggestion": {
            "title": "Implement Real-time Communication",
            "description": (
                "Your design doesn't mention real-time components. For interactive features "
                "like chat, notifications, or live updates, consider implementing WebSockets, "
                "Server-Sent Events (SSE), or a real-time framework like Socket.io."
            ),
            "category": "API_DESIGN",
            "severity": "WARNING"
        }
    },
    
    # Media Storage
    {
        "keywords": STORAGE_KEYWORDS,
        "suggestion": {
            "title": "Define Media Storage Strategy",
            "description": (
                "Your design doesn't mention how files or media are stored. For images, videos, "
                "or documents, use a dedicated blob storage service (like S3, Cloudinary, or GCS) "
                "rather than storing them directly in your database. Consider a CDN for global delivery."
            ),
            "category": "DATABASE",
            "severity": "INFO"
        }
    },
    
    # Infrastructure
    {
        "keywords": INFRA_KEYWORDS,
        "suggestion": {
            "title": "Consider Containerization & Cloud Infra",
            "description": (
                "Your design doesn't mention deployment or infrastructure. Consider using "
                "Docker for containerization and Kubernetes for orchestration. Leverage "
                "cloud provider services (AWS, GCP, Azure) for managed infrastructure."
            ),
            "category": "PERFORMANCE",
            "severity": "INFO"
        }
    },
    
    # Search
    {
        "keywords": SEARCH_KEYWORDS,
        "suggestion": {
            "title": "Add Full-Text Search Capability",
            "description": (
                "Your design mentions search but lacks a specialized search engine. "
                "Consider integrating Elasticsearch or Algolia for fast, full-text search "
                "capabilities with features like fuzzy matching and highlighting."
            ),
            "category": "PERFORMANCE",
            "severity": "INFO"
        }
    },
]


# ============== Step 3: Maturity Score Calculation ==============

def calculate_maturity_score(content: str) -> Tuple[int, str]:
    """
    Calculate maturity score based on concept presence.
    
    Args:
        content: The design content to analyze
    
    Returns:
        Tuple of (score, reason_string)
        Score is 0-5 based on presence of key concepts
    """
    content_lower = content.lower()
    score = 0
    present_concepts = []
    
    for concept_name, concept_data in MATURITY_CONCEPTS.items():
        keywords = concept_data["keywords"]
        if any(kw.lower() in content_lower for kw in keywords):
            score += 1
            present_concepts.append(f"✓ {concept_data['description']}")
    
    # Build reason string
    if score == 0:
        reason = "No key architectural concepts detected. Start by adding API and database layers."
    elif score < 3:
        reason = f"Basic design ({score}/5): " + ", ".join(present_concepts)
    elif score < 5:
        reason = f"Good design ({score}/5): " + ", ".join(present_concepts)
    else:
        reason = f"Comprehensive design ({score}/5): " + ", ".join(present_concepts)
    
    return score, reason


def analyze_design_content(content: str) -> List[Dict]:
    """
    Analyze design content and generate suggestions.
    
    Algorithm:
    1. Convert content to lowercase for case-insensitive matching
    2. For each rule, check if ANY keyword is present
    3. If no keywords found, add the suggestion
    4. Run Domain-Specific Hint Logic (Conditional Suggestions)
    """
    suggestions = []
    content_lower = content.lower()
    
    # Standard Rule-based Analysis
    for rule in ANALYSIS_RULES:
        keywords = rule["keywords"]
        keyword_found = any(kw.lower() in content_lower for kw in keywords)
        
        if not keyword_found:
            suggestion = rule["suggestion"].copy()
            suggestion["trigger_keywords"] = keywords
            suggestions.append(suggestion)
    
    # ========== Domain-Specific Conditional Logic ==========
    
    # 1. Chat App but Missing Real-time
    is_chat_app = any(h.lower() in content_lower for h in CHAT_HINTS)
    has_realtime = any(kw.lower() in content_lower for kw in REALTIME_KEYWORDS)
    
    if is_chat_app and not has_realtime:
        suggestions.append({
            "title": "Add Real-time Messaging (Chat Context)",
            "description": (
                "You mentioned chat/messaging features. Real-time delivery is essential here. "
                "Consider using WebSockets (Socket.io) to ensure instant message delivery."
            ),
            "category": "API_DESIGN",
            "severity": "CRITICAL",
            "trigger_keywords": REALTIME_KEYWORDS
        })
    
    # 2. Media App but Missing Storage/CDN
    is_media_app = any(h.lower() in content_lower for h in MEDIA_HINTS)
    has_storage = any(kw.lower() in content_lower for kw in STORAGE_KEYWORDS)
    
    if is_media_app and not has_storage:
        suggestions.append({
            "title": "Implement Media Strategy (S3/CDN)",
            "description": (
                "Your design handles videos/images. Storing these in a database is inefficient. "
                "Consider Object Storage (S3) combined with a CDN for fast global delivery."
            ),
            "category": "DATABASE",
            "severity": "WARNING",
            "trigger_keywords": STORAGE_KEYWORDS
        })

    return suggestions


# ============== Step 2: Auto-detect Addressed Suggestions ==============

async def check_and_update_addressed_suggestions(
    db: Prisma,
    project_id: int,
    content: str,
    new_version: int
) -> int:
    """
    Check existing OPEN suggestions and mark as ADDRESSED if keywords now exist.
    
    IMPROVED: Now matches by TITLE to find the correct rule and keywords.
    
    Args:
        db: Prisma client
        project_id: Project ID
        content: New design content
        new_version: The new version number
    
    Returns:
        Count of newly addressed suggestions
    """
    content_lower = content.lower()
    addressed_count = 0
    
    # Get all OPEN suggestions for this project
    open_suggestions = await db.suggestion.find_many(
        where={
            "projectId": project_id,
            "status": "OPEN"
        }
    )
    
    logger.info(f"[AUTO-ADDRESS] Checking {len(open_suggestions)} OPEN suggestions for project {project_id}")
    
    for suggestion in open_suggestions:
        # Get the trigger keywords - FIRST from stored, then from rule by TITLE
        trigger_keywords = suggestion.triggerKeywords or []
        
        # If no stored keywords, find by matching TITLE (more reliable than category)
        if not trigger_keywords:
            for rule in ANALYSIS_RULES:
                if rule["suggestion"]["title"] == suggestion.title:
                    trigger_keywords = rule["keywords"]
                    logger.debug(f"[AUTO-ADDRESS] Found keywords for '{suggestion.title}': {trigger_keywords[:3]}...")
                    break
        
        if not trigger_keywords:
            logger.debug(f"[AUTO-ADDRESS] No keywords found for suggestion: {suggestion.title}")
            continue
        
        # Check if any keyword is now present in design
        matched_keyword = None
        for kw in trigger_keywords:
            if kw.lower() in content_lower:
                matched_keyword = kw
                break
        
        if matched_keyword:
            # Mark as addressed
            await db.suggestion.update(
                where={"id": suggestion.id},
                data={
                    "status": "ADDRESSED",
                    "addressedAt": datetime.utcnow(),
                    "addressedInVersion": new_version
                }
            )
            addressed_count += 1
            logger.info(f"[AUTO-ADDRESS] ✓ '{suggestion.title}' marked ADDRESSED (matched: '{matched_keyword}')")
    
    logger.info(f"[AUTO-ADDRESS] Total addressed: {addressed_count} suggestions")
    return addressed_count


# ============== Step 1: Design Version Management ==============

async def create_design_version(
    db: Prisma,
    project_id: int,
    content: str,
    version_number: int,
    maturity_score: int,
    suggestions_count: int
):
    """
    Create a new design version snapshot.
    
    IMPROVED: Checks for existing version to avoid duplicates.
    
    Args:
        db: Prisma client
        project_id: Project ID
        content: Design content at this version
        version_number: Version number
        maturity_score: Maturity score at this version
        suggestions_count: Number of suggestions at this version
    """
    # Check if this version already exists (avoid duplicates)
    existing = await db.designversion.find_first(
        where={
            "projectId": project_id,
            "versionNumber": version_number
        }
    )
    
    if existing:
        # Update existing version instead of creating duplicate
        await db.designversion.update(
            where={"id": existing.id},
            data={
                "content": content,
                "maturityScore": maturity_score,
                "suggestionsCount": suggestions_count
            }
        )
        logger.info(f"[VERSION] Updated existing version {version_number} for project {project_id}")
    else:
        # Create new version
        await db.designversion.create(
            data={
                "projectId": project_id,
                "versionNumber": version_number,
                "content": content,
                "maturityScore": maturity_score,
                "suggestionsCount": suggestions_count
            }
        )
        logger.info(f"[VERSION] Created new version {version_number} for project {project_id}")


async def get_design_versions(db: Prisma, project_id: int) -> List:
    """Get all design versions for a project, ordered by version number."""
    return await db.designversion.find_many(
        where={"projectId": project_id},
        order={"versionNumber": "asc"}
    )


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


async def run_analysis(db: Prisma, project_id: int) -> Dict:
    """
    Run analysis on a project's design and save suggestions.
    
    This is the main entry point for analysis with NEW features:
    1. Fetches project with design details and existing suggestions
    2. Checks if previous OPEN suggestions are now addressed (Step 2)
    3. Runs rule-based analysis for NEW suggestions
    4. Calculates maturity score (Step 3)
    5. Creates design version snapshot (Step 1)
    6. Saves new suggestions (doesn't delete old ones!)
    7. Updates project status and maturity score
    
    Args:
        db: Prisma client
        project_id: ID of the project to analyze
    
    Returns:
        Dict with analysis results including suggestions, maturity, and addressed count
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"[ANALYSIS] Starting analysis for project {project_id}")
    logger.info(f"{'='*60}")
    
    # Get project with design details
    project = await db.project.find_unique(
        where={"id": project_id},
        include={"designDetails": True, "suggestions": True}
    )
    
    if not project or not project.designDetails:
        logger.warning(f"[ANALYSIS] No design content found for project {project_id}")
        return {
            "suggestions": [],
            "maturity_score": 0,
            "maturity_reason": "No design content found",
            "newly_addressed_count": 0
        }
    
    design_content = project.designDetails.content
    old_version = project.designDetails.version
    
    # ========== Determine Correct Design Version ==========
    # Logic: Version = state after analysis. 
    # If content changed since last analysis, it's a new version.
    
    # Get last analyzed version record
    last_version_record = await db.designversion.find_first(
        where={"projectId": project_id},
        order={"versionNumber": "desc"}
    )
    
    if not last_version_record:
        # First analysis ever = Version 1
        design_version = 1
    elif last_version_record.content != design_content:
        # Content changed since last analysis = Next Version
        design_version = last_version_record.versionNumber + 1
    else:
        # Content is the same = Stick with current version
        design_version = last_version_record.versionNumber
    
    # Update project's design version if it's different from current DB state
    if design_version != old_version:
        await db.designdetails.update(
            where={"projectId": project_id},
            data={"version": design_version}
        )
        logger.info(f"[VERSION] Design version updated: {old_version} -> {design_version}")
    
    logger.info(f"[ANALYSIS] Design version for this run: {design_version}")
    logger.info(f"[ANALYSIS] Content length: {len(design_content)} chars")
    logger.info(f"[ANALYSIS] Existing suggestions: {len(project.suggestions)}")
    
    # ========== Step 2: Check for Addressed Suggestions ==========
    logger.info(f"\n[STEP 2] Checking for addressed suggestions...")
    newly_addressed_count = await check_and_update_addressed_suggestions(
        db, project_id, design_content, design_version
    )
    
    # ========== Step 3: Calculate Maturity Score ==========
    logger.info(f"\n[STEP 3] Calculating maturity score...")
    maturity_score, maturity_reason = calculate_maturity_score(design_content)
    logger.info(f"[STEP 3] Maturity: {maturity_score}/5 - {maturity_reason}")
    
    # ========== Run Rule-based Analysis ==========
    logger.info(f"\n[RULES] Running rule-based analysis...")
    suggestion_data = analyze_design_content(design_content)
    logger.info(f"[RULES] Found {len(suggestion_data)} missing concepts")
    for s in suggestion_data:
        logger.debug(f"[RULES] - {s['title']} ({s['severity']})")
    
    # ========== LLM ENRICHMENT ==========
    logger.info(f"\n[LLM] Attempting LLM enrichment...")
    llm_explanations = await enrich_with_llm_explanations(
        design_content,
        suggestion_data
    )
    
    # Enrich suggestions with LLM explanations
    enriched_count = 0
    for suggestion in suggestion_data:
        category = suggestion["category"]
        if category in llm_explanations:
            llm_data = llm_explanations[category]
            enhanced_description = (
                f"{suggestion['description']}\n\n"
                f"**Why It Matters:** {llm_data['why_it_matters']}\n\n"
                f"**Interview Perspective:** {llm_data['interview_angle']}\n\n"
                f"**Production Reality:** {llm_data['production_angle']}"
            )
            suggestion["description"] = enhanced_description
            enriched_count += 1
    logger.info(f"[LLM] Enriched {enriched_count}/{len(suggestion_data)} suggestions")
    
    # ========== Smart Suggestion Creation ==========
    # Only create suggestions that don't already exist (avoid duplicates)
    logger.info(f"\n[SUGGESTIONS] Creating new suggestions...")
    existing_titles = set()
    for s in project.suggestions:
        existing_titles.add(s.title)
    logger.info(f"[SUGGESTIONS] Already existing: {list(existing_titles)}")
    
    created_suggestions = []
    skipped_suggestions = []
    for data in suggestion_data:
        # Skip if this suggestion already exists (regardless of status)
        if data["title"] in existing_titles:
            skipped_suggestions.append(data["title"])
            continue
            
        suggestion = await db.suggestion.create(
            data={
                "title": data["title"],
                "description": data["description"],
                "category": data["category"],
                "severity": data["severity"],
                "designVersion": design_version,
                "projectId": project_id,
                "status": "OPEN",
                "triggerKeywords": data.get("trigger_keywords", [])
            }
        )
        created_suggestions.append(suggestion)
        logger.info(f"[SUGGESTIONS] + Created: {data['title']}")
    
    if skipped_suggestions:
        logger.info(f"[SUGGESTIONS] Skipped (already exist): {skipped_suggestions}")
    
    # ========== Step 1: Create Design Version Snapshot ==========
    logger.info(f"\n[STEP 1] Creating version snapshot...")
    # Get fresh count of open suggestions
    open_suggestions = await db.suggestion.find_many(
        where={"projectId": project_id, "status": "OPEN"}
    )
    
    await create_design_version(
        db, project_id, design_content, design_version,
        maturity_score, len(open_suggestions)
    )
    
    # ========== Update Project Status and Maturity ==========
    await db.project.update(
        where={"id": project_id},
        data={
            "status": "ANALYZED",
            "maturityScore": maturity_score,
            "maturityReason": maturity_reason
        }
    )
    
    # Get all suggestions (fresh query)
    all_suggestions = await db.suggestion.find_many(
        where={"projectId": project_id},
        order={"createdAt": "desc"}
    )
    
    logger.info(f"\n{'='*60}")
    logger.info(f"[ANALYSIS] Complete! Summary:")
    logger.info(f"  - Addressed: {newly_addressed_count} suggestions")
    logger.info(f"  - New: {len(created_suggestions)} suggestions")
    logger.info(f"  - Total open: {len(open_suggestions)}")
    logger.info(f"  - Maturity: {maturity_score}/5")
    logger.info(f"{'='*60}\n")
    
    return {
        "suggestions": all_suggestions,
        "maturity_score": maturity_score,
        "maturity_reason": maturity_reason,
        "newly_addressed_count": newly_addressed_count,
        "new_suggestions_count": len(created_suggestions),
        "design_version": design_version
    }


async def get_suggestions_for_project(db: Prisma, project_id: int) -> List:
    """Get all suggestions for a project, ordered by creation date."""
    return await db.suggestion.find_many(
        where={"projectId": project_id},
        order={"createdAt": "desc"}
    )


async def update_suggestion_status(
    db: Prisma, 
    suggestion_id: int, 
    status: str,
    version: int = None
) -> object:
    """
    Manually update a suggestion's status.
    
    Args:
        db: Prisma client
        suggestion_id: Suggestion ID
        status: New status (OPEN, ADDRESSED, IGNORED)
        version: Version where it was addressed (optional)
    
    Returns:
        Updated suggestion
    """
    update_data = {"status": status}
    
    if status == "ADDRESSED":
        update_data["addressedAt"] = datetime.utcnow()
        if version:
            update_data["addressedInVersion"] = version
    elif status == "OPEN":
        update_data["addressedAt"] = None
        update_data["addressedInVersion"] = None
    
    return await db.suggestion.update(
        where={"id": suggestion_id},
        data=update_data
    )


async def get_project_evolution(db: Prisma, project_id: int) -> Dict:
    """
    Get the evolution history of a project (Step 4).
    
    Returns version history with maturity progression.
    """
    project = await db.project.find_unique(
        where={"id": project_id},
        include={"designDetails": True}
    )
    
    if not project:
        return None
    
    versions = await get_design_versions(db, project_id)
    
    # Build progress summary
    if not versions:
        progress_summary = "No analysis history yet. Run your first analysis!"
    elif len(versions) == 1:
        v = versions[0]
        progress_summary = f"Version 1: {v.suggestionsCount} suggestions, maturity {v.maturityScore}/5"
    else:
        first = versions[0]
        last = versions[-1]
        suggestions_diff = first.suggestionsCount - last.suggestionsCount
        maturity_diff = last.maturityScore - first.maturityScore
        
        progress_parts = []
        if suggestions_diff > 0:
            progress_parts.append(f"Addressed {suggestions_diff} suggestions")
        if maturity_diff > 0:
            progress_parts.append(f"Improved maturity by {maturity_diff} points")
        
        if progress_parts:
            progress_summary = f"Great progress! {' and '.join(progress_parts)} over {len(versions)} versions."
        else:
            progress_summary = f"Tracked {len(versions)} versions. Keep improving your design!"
    
    return {
        "project_id": project_id,
        "current_version": project.designDetails.version if project.designDetails else 0,
        "current_maturity_score": project.maturityScore,
        "versions": versions,
        "progress_summary": progress_summary
    }

