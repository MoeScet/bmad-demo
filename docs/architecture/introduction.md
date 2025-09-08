# Introduction

This document outlines the overall project architecture for **RAG-Powered Washing Machine Troubleshooting Assistant**, including backend systems, shared services, and non-UI specific concerns. Its primary goal is to serve as the guiding architectural blueprint for AI-driven development, ensuring consistency and adherence to chosen patterns and technologies.

**Relationship to Frontend Architecture:**
Since the project includes a significant user interface (Microsoft Teams bot integration), a separate Frontend Architecture Document will detail the frontend-specific design and MUST be used in conjunction with this document. Core technology stack choices documented herein are definitive for the entire project, including any frontend components.

## Starter Template or Existing Project

**Decision:** The project will leverage existing Microsoft Teams Bot Framework scaffolding and FastAPI project templates for rapid setup while maintaining architectural consistency with PRD requirements.

**Rationale:** Using official Microsoft Bot Framework templates and FastAPI project generators provides faster time-to-market, established best practices, and community support while allowing customization for our specific troubleshooting requirements.

**Implementation:** N/A - No specific starter template dependency, using framework-native scaffolding tools.

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-09-05 | v1.0 | Initial architecture document creation | Winston (Architect) |
