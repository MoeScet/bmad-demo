# Requirements

## Functional Requirements

**FR1:** The system shall implement tiered search architecture with fast Q&A lookup containing 100 diverse common washing machine error solutions
**FR2:** The system shall provide semantic manual search fallback for uncommon issues not covered in fast-path Q&A database
**FR3:** The system shall integrate natively with Microsoft Teams as a bot interface for user queries and responses
**FR4:** The system shall detect user skill level through initial questions or interface choice to adapt response complexity
**FR5:** The system shall classify repairs as DIY-appropriate or professional-required using safety boundary recognition system
**FR6:** The system shall maintain knowledge base of manufacturer manual content with transparent coverage disclosure
**FR7:** The system shall provide clear "I don't know" responses when queries fall outside supported knowledge domains
**FR8:** The system shall display supported machine models and brands proactively to set user expectations
**FR9:** The system shall deliver contextually appropriate instructions based on user skill level (novice, DIY enthusiast, renter constraints)
**FR10:** The system shall include safety warnings and referral recommendations for professional-only repairs
**FR11:** The system shall process and respond to natural language troubleshooting queries in conversational format
**FR12:** The system shall maintain response accuracy tracking for continuous improvement and transparency reporting

## Non-Functional Requirements

**NFR1:** Response time must be ≤ 10 seconds for 95% of user queries with target of 7 seconds for fast-path and 15 seconds for manual search
**NFR2:** System must achieve 85% solution accuracy rate as measured by user follow-up surveys and resolution tracking
**NFR3:** Architecture must operate within free-tier cloud platform constraints without premium API dependencies
**NFR4:** System must handle 100+ concurrent users during peak hours without performance degradation
**NFR5:** Safety boundary recognition must achieve 95% accuracy in flagging professional-required repairs
**NFR6:** Knowledge base coverage must successfully match 90% of user queries to manufacturer manual content
**NFR7:** User context adaptation must appropriately tailor 85% of responses to detected skill levels
**NFR8:** System must maintain 99% uptime availability during business hours across supported time zones
**NFR9:** All user interactions must comply with Microsoft Teams security and data privacy requirements
**NFR10:** Vector database and embedding operations must function effectively within open-source tool limitations
