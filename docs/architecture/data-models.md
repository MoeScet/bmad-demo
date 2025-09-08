# Data Models

## User
**Purpose:** Represents Teams users with persistent context and preferences for personalized troubleshooting experiences

**Key Attributes:**
- `id`: UUID - Primary identifier
- `teams_user_id`: String - Microsoft Teams user identifier
- `skill_level`: Enum(novice, diy_enthusiast, renter) - Detected/selected skill level
- `preferences`: JSONB - User preferences and constraints
- `created_at`: DateTime - Account creation timestamp
- `last_active`: DateTime - Last interaction timestamp

**Relationships:**
- One-to-many with QuerySession (user conversation history)
- One-to-many with UserFeedback (response ratings and success tracking)

## QuerySession
**Purpose:** Tracks individual troubleshooting conversations with context and outcome measurement

**Key Attributes:**
- `id`: UUID - Primary identifier
- `user_id`: UUID - Foreign key to User
- `initial_query`: Text - Original user question
- `conversation_context`: JSONB - Full conversation thread
- `search_strategy_used`: Enum(fast_qa, semantic, hybrid) - Search method employed
- `response_time_ms`: Integer - Total response time for performance tracking
- `resolution_status`: Enum(resolved, escalated, abandoned) - Session outcome
- `created_at`: DateTime - Session start time

**Relationships:**
- Many-to-one with User (session owner)
- One-to-many with QueryResponse (individual responses in conversation)

## QAEntry
**Purpose:** Curated fast-lookup troubleshooting solutions for common washing machine issues

**Key Attributes:**
- `id`: UUID - Primary identifier  
- `question`: Text - Standardized question format
- `answer`: Text - Structured troubleshooting steps
- `keywords`: Array[String] - Search keywords for matching
- `supported_models`: Array[String] - Compatible washing machine models
- `safety_level`: Enum(safe, caution, professional) - DIY safety classification
- `complexity_score`: Integer(1-10) - Technical complexity rating
- `success_rate`: Float - Historical effectiveness percentage
- `created_at`: DateTime - Entry creation time
- `updated_at`: DateTime - Last modification time

**Relationships:**
- One-to-many with QueryResponse (when fast Q&A is used)
- Many-to-many with ManufacturerModel (supported machines)

## ManualContent
**Purpose:** Processed manufacturer manual sections for semantic search and comprehensive coverage

**Key Attributes:**
- `id`: UUID - Primary identifier
- `manufacturer`: String - Washing machine manufacturer  
- `model_series`: String - Applicable model series
- `section_title`: String - Manual section heading
- `content`: Text - Processed manual text
- `embedding`: Vector - Semantic search embedding
- `content_type`: Enum(troubleshooting, maintenance, safety, warranty) - Content category
- `confidence_score`: Float - Content quality/relevance score
- `source_manual`: String - Original manual reference
- `page_reference`: String - Original page/section reference

**Relationships:**
- One-to-many with QueryResponse (when semantic search is used)
- Many-to-one with ManufacturerModel (applicable machines)

## SafetyClassification
**Purpose:** Safety assessment rules and audit trail for professional vs. DIY repair recommendations

**Key Attributes:**
- `id`: UUID - Primary identifier
- `repair_type`: String - Type of repair or maintenance
- `safety_level`: Enum(safe_diy, requires_tools, professional_only, dangerous) - Safety classification
- `reasoning`: Text - Explanation of safety assessment
- `required_tools`: Array[String] - Tools needed for safe completion
- `skill_requirements`: Array[String] - Required technical skills
- `warning_text`: Text - Standardized safety warning
- `created_at`: DateTime - Rule creation time

**Relationships:**
- One-to-many with QueryResponse (safety assessments applied)

## QueryResponse
**Purpose:** Individual responses delivered to users with full context for accuracy tracking and improvement

**Key Attributes:**
- `id`: UUID - Primary identifier
- `session_id`: UUID - Foreign key to QuerySession
- `query_text`: Text - Specific user question
- `response_text`: Text - System response delivered
- `source_type`: Enum(fast_qa, semantic_search, safety_override) - Response source
- `source_id`: UUID - Reference to QAEntry or ManualContent
- `safety_classification_id`: UUID - Applied safety assessment
- `confidence_score`: Float - System confidence in response
- `user_feedback`: Enum(helpful, not_helpful, dangerous) - User rating
- `resolution_successful`: Boolean - User-reported success
- `response_time_ms`: Integer - Individual response timing
- `created_at`: DateTime - Response timestamp

**Relationships:**
- Many-to-one with QuerySession (conversation context)
- Many-to-one with QAEntry or ManualContent (response source)
- Many-to-one with SafetyClassification (applied safety rules)
