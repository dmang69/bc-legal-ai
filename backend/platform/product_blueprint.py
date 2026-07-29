"""Static product blueprint for the Executive & Developer Edition platform."""

from __future__ import annotations

from typing import Any


PRODUCT_BLUEPRINT: dict[str, Any] = {
    "product_name": "AI-Powered Legal Assistant Platform — Executive & Developer Edition",
    "tagline": "The enterprise legal intelligence platform that helps leadership teams make confident decisions and enables developers to build compliant systems faster.",
    "one_line_description": "An AI-powered legal assistant platform designed for modern companies that need executive-ready legal guidance, developer-friendly technical documentation, and scalable compliance operations in one secure environment.",
    "elevator_pitch": "A dual-audience legal intelligence system built to serve both business leadership and technical teams. For executives, it converts legal complexity into strategic, boardroom-ready guidance, risk alerts, and decision-support materials. For developers, it delivers structured legal requirements, policy-aware workflows, API-ready outputs, and implementation guidance across contracts, privacy, employment, governance, IP, and regulatory compliance.",
    "vision": "Create a secure, intelligent legal operating platform that bridges the gap between legal complexity, executive decision-making, and technical implementation.",
    "positioning_statement": "A dual-audience legal intelligence platform that equips executives with strategic clarity and developers with compliant implementation guidance.",
    "messaging_safeguard": "Position the platform as a legal intelligence and workflow support system, not as a replacement for licensed legal counsel in high-risk or jurisdiction-specific matters.",
    "audiences": {
        "executive": ["CEOs", "COOs", "General Counsel", "Board members", "Compliance officers"],
        "operational": ["Legal operations managers", "HR leaders", "Contract managers", "Risk and security teams"],
        "technical": ["CTOs", "Engineering managers", "Product managers", "Software developers", "DevSecOps teams"],
    },
    "ideal_customers": [
        "Venture-backed startups",
        "Mid-market companies scaling into regulated environments",
        "Enterprise innovation teams",
        "SaaS platforms handling multi-jurisdictional compliance",
        "In-house legal, compliance, product, and engineering organizations",
    ],
    "strategic_benefits": [
        "Reduces time spent interpreting legal obligations",
        "Improves board and leadership decision quality",
        "Accelerates contract and policy workflows",
        "Strengthens privacy, governance, and compliance readiness",
        "Translates legal requirements into technical implementation artifacts",
        "Creates scalable legal infrastructure for growing organizations",
    ],
    "core_modules": [
        {
            "id": "governance_compliance",
            "title": "Corporate Governance & Compliance",
            "description": "Governance documentation, board support materials, entity compliance checklists, and continuous compliance oversight.",
        },
        {
            "id": "ip_management",
            "title": "Intellectual Property Management",
            "description": "Structured IP strategy, portfolio guidance, open-source posture, and jurisdiction-aware protection frameworks.",
        },
        {
            "id": "contract_review",
            "title": "Contract Drafting & Review",
            "description": "Clause analysis, risk exposure identification, suggested issue explanations, and safer agreement workflows.",
        },
        {
            "id": "employment_labor",
            "title": "Employment & Labor Law",
            "description": "Role-aware workforce policy guidance across federal, state/provincial, and international employment standards.",
        },
        {
            "id": "data_privacy",
            "title": "Data Privacy Regulations",
            "description": "Operational privacy requirements, obligations mapping, retention guidance, and workflow integration.",
        },
        {
            "id": "liability_risk",
            "title": "Liability Risk Assessment",
            "description": "Proactive legal profiling, categorized risk flags, and mitigation recommendations before issues escalate.",
        },
        {
            "id": "regulatory_navigation",
            "title": "Regulatory Framework Navigation",
            "description": "Market-by-market obligation mapping using continuously updated legislative intelligence and jurisdiction-specific guidance.",
        },
    ],
    "key_features": [
        "AI chatbot with contextual, multi-turn legal assistance",
        "Upload and analyze contracts, policies, and internal documentation",
        "Version-controlled document management",
        "Automated compliance checklists and deadline tracking",
        "Risk dashboards and categorized matter tracking",
        "Secure communications architecture with enterprise-grade encryption",
        "Human attorney escalation pathways for higher-risk matters",
    ],
    "feature_tiers": {
        "mvp": [
            "Chat assistant",
            "Document upload and summarization",
            "Contract clause risk flagging",
            "Basic compliance checklists",
            "Executive dashboard with risk snapshots",
            "Developer console with privacy/open-source guidance",
            "Manual human escalation workflow",
        ],
        "phase_2": [
            "Regulatory change monitoring",
            "Board packet generation",
            "Advanced clause rewrite suggestions",
            "Jurisdiction comparison engine",
            "Workflow automation and reminders",
            "Enhanced permissions and audit tooling",
        ],
        "phase_3": [
            "Industry packs by vertical",
            "Cross-border compliance mapping",
            "API/webhook ecosystem",
            "Third-party system integrations",
            "Advanced analytics and trend forecasting",
            "Knowledge graph for legal relationships and precedent tracking",
        ],
    },
}


EXECUTIVE_BRIEF: dict[str, Any] = {
    "headline": "Legal Intelligence for the Boardroom and the Build Team",
    "subheadline": "Transform legal complexity into strategic decisions, compliant systems, and operational confidence with an AI-powered legal assistant built for executives and developers.",
    "primary_cta": "Request a Demo",
    "secondary_cta": "Explore Platform Modules",
    "problem_statement": "Legal obligations are growing more complex across governance, privacy, employment, IP, contracting, and sector regulation. Fragmented systems, external counsel bottlenecks, and manual interpretation create delays, inconsistency, hidden risk, and execution friction.",
    "solution": [
        "Synthesizes legal complexity into executive insight",
        "Converts obligations into operational and technical actions",
        "Tracks compliance deadlines and regulatory changes",
        "Supports document review, analysis, and risk identification",
        "Creates a reliable interface between business, legal, compliance, and engineering",
    ],
    "business_outcomes": [
        "Faster decision cycles",
        "Lower legal interpretation overhead",
        "More consistent compliance execution",
        "Stronger audit and governance readiness",
        "Reduced contract and regulatory risk exposure",
        "Better alignment between legal strategy and product delivery",
    ],
    "use_cases": [
        "Board meeting preparation and governance reporting",
        "M&A readiness and diligence support",
        "Multi-state or multi-country regulatory expansion planning",
        "Employment policy harmonization",
        "Privacy risk review before product launches",
        "Contract risk triage for strategic deals",
    ],
    "kpis": [
        "Contract review turnaround time",
        "Compliance task completion rate",
        "Number of identified high-risk clauses before execution",
        "Time-to-policy update after regulatory change",
        "Executive decision-support satisfaction score",
        "Reduction in external counsel spend for routine matters",
    ],
}


DEVELOPER_BLUEPRINT: dict[str, Any] = {
    "architecture_overview": "A modular, service-oriented platform with separate experiences for executives and developers built on shared intelligence, document processing, and compliance services.",
    "layers": [
        {"name": "Experience Layer", "components": ["Executive web dashboard", "Developer console", "Conversational assistant interface", "Admin/compliance management portal"]},
        {"name": "Application Services Layer", "components": ["User and identity service", "Matter/case management service", "Document ingestion service", "Clause analysis service", "Compliance rules engine", "Alerting and notification service", "Escalation and workflow orchestration service", "Reporting and export service"]},
        {"name": "Intelligence Layer", "components": ["LLM orchestration service", "Retrieval engine", "Prompt/template management", "Risk scoring engine", "Citation and explanation generator", "Policy constraint engine"]},
        {"name": "Data Layer", "components": ["Relational DB", "Vector database", "Object storage", "Search index", "Audit log store"]},
    ],
    "service_map": [
        "auth-service",
        "user-profile-service",
        "document-ingestion-service",
        "clause-analysis-service",
        "compliance-engine",
        "regulatory-update-service",
        "chat-orchestrator",
        "risk-scoring-service",
        "notification-service",
        "escalation-service",
        "export-service",
    ],
    "api_domains": {
        "conversational": ["POST /chat/sessions", "POST /chat/sessions/{id}/messages", "GET /chat/sessions/{id}"],
        "documents": ["POST /documents/upload", "GET /documents/{id}", "POST /documents/{id}/analyze", "GET /documents/{id}/risks", "GET /documents/{id}/versions"],
        "compliance": ["POST /compliance/assessments", "GET /compliance/assessments/{id}", "GET /compliance/obligations", "POST /compliance/checklists", "GET /compliance/alerts"],
        "governance": ["GET /governance/templates", "POST /governance/resolutions/generate", "GET /governance/board-packets/{id}"],
        "escalation": ["POST /escalations", "GET /escalations/{id}", "POST /escalations/{id}/assign"],
    },
    "output_formats": ["JSON legal requirement sets", "YAML policy configs", "Clause risk arrays", "Markdown reports", "Webhooks for legal/compliance events"],
    "sample_legal_requirement": {
        "matter_id": "mat_1029",
        "domain": "data_privacy",
        "jurisdictions": ["US-CA", "CA", "EU"],
        "risk_level": "high",
        "issues": [
            {
                "type": "retention_policy_gap",
                "severity": "high",
                "description": "No defined deletion schedule for user account data.",
                "recommendation": "Implement a documented retention and deletion schedule mapped to data categories.",
            }
        ],
        "escalation_recommended": True,
    },
    "security_architecture": [
        "SSO and MFA",
        "Tenant isolation",
        "KMS-backed encryption key management",
        "Private document storage",
        "Signed access URLs",
        "Fine-grained audit logs",
        "Admin policy controls for model usage and data retention",
    ],
    "ai_requirements": [
        "Retrieval-augmented generation for legal sources and internal documents",
        "Model routing by task type",
        "Guardrails against unsupported legal conclusions",
        "Confidence scoring and fallback pathways",
        "Continuous update pipeline for legal knowledge sources",
    ],
}


def get_product_blueprint() -> dict[str, Any]:
    return PRODUCT_BLUEPRINT


def get_executive_brief() -> dict[str, Any]:
    return EXECUTIVE_BRIEF


def get_developer_blueprint() -> dict[str, Any]:
    return DEVELOPER_BLUEPRINT
