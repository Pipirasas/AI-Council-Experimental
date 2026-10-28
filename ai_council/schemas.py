from __future__ import annotations

EVIDENCE_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["path", "symbol", "text"]},
        "query": {"type": "string", "maxLength": 160},
        "reason": {"type": "string", "maxLength": 240},
    },
    "required": ["kind", "query", "reason"],
    "additionalProperties": False,
}

SPECIALIST_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["READY", "NEED_EVIDENCE", "BLOCKED"]},
        "summary": {"type": "string", "maxLength": 700},
        "findings": {"type": "array", "items": {"type": "string", "maxLength": 320}, "maxItems": 5},
        "risks": {"type": "array", "items": {"type": "string", "maxLength": 320}, "maxItems": 4},
        "must_preserve": {"type": "array", "items": {"type": "string", "maxLength": 260}, "maxItems": 4},
        "evidence_requests": {"type": "array", "items": EVIDENCE_REQUEST_SCHEMA, "maxItems": 3},
    },
    "required": ["status", "summary", "findings", "risks", "must_preserve", "evidence_requests"],
    "additionalProperties": False,
}

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "goal": {"type": "string", "maxLength": 700},
        "steps": {"type": "array", "items": {"type": "string", "maxLength": 900}, "maxItems": 8},
        "constraints": {"type": "array", "items": {"type": "string", "maxLength": 900}, "maxItems": 6},
        "verification": {"type": "array", "items": {"type": "string", "maxLength": 900}, "maxItems": 6},
        "assumptions": {"type": "array", "items": {"type": "string", "maxLength": 280}, "maxItems": 4},
    },
    "required": ["goal", "steps", "constraints", "verification", "assumptions"],
    "additionalProperties": False,
}

SIGNOFF_FINDING_SCHEMA = {
    "type": "object",
    "properties": {
        "issue_code": {
            "type": "string",
            "enum": [
                "MISSING_BASELINE_EVIDENCE",
                "REQUIREMENT_CONFLICT",
                "SAFETY_OR_SECURITY",
                "SCOPE_VIOLATION",
                "TESTABILITY_GAP",
                "IMPLEMENTATION_RISK",
                "GPT_PLAN_CHANGE_UNRESOLVED",
                "OTHER_MATERIAL_CONCERN",
            ],
        },
        "subject": {"type": "string", "maxLength": 180},
        "severity": {"type": "string", "enum": ["BLOCKING", "ADVISORY"]},
        "reason": {"type": "string", "maxLength": 520},
        "evidence_ids": {"type": "array", "items": {"type": "string", "maxLength": 32}, "maxItems": 6},
    },
    "required": ["issue_code", "subject", "severity", "reason", "evidence_ids"],
    "additionalProperties": False,
}

SIGNOFF_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["APPROVE", "ADVISORY", "NEED_EVIDENCE", "BLOCK_CANDIDATE"]},
        "findings": {"type": "array", "items": SIGNOFF_FINDING_SCHEMA, "maxItems": 5},
        "evidence_requests": {"type": "array", "items": EVIDENCE_REQUEST_SCHEMA, "maxItems": 2},
    },
    "required": ["verdict", "findings", "evidence_requests"],
    "additionalProperties": False,
}


AUDIT_EVIDENCE_REQUEST_SCHEMA = EVIDENCE_REQUEST_SCHEMA

AUDIT_FINDING_TYPES = ["VERIFIED_BUG", "IMPROVEMENT", "OPTIONAL_IDEA"]
AUDIT_PRIORITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
AUDIT_CONFIDENCE = ["HIGH", "MEDIUM", "LOW"]

AUDIT_SPECIALIST_FINDING_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": AUDIT_FINDING_TYPES},
        "priority": {"type": "string", "enum": AUDIT_PRIORITIES},
        "area": {"type": "string", "maxLength": 180},
        "location": {"type": "string", "maxLength": 240},
        "evidence_ids": {"type": "array", "items": {"type": "string", "maxLength": 24}, "maxItems": 6},
        "reason": {"type": "string", "maxLength": 520},
        "recommendation": {"type": "string", "maxLength": 520},
        "confidence": {"type": "string", "enum": AUDIT_CONFIDENCE},
    },
    "required": ["type", "priority", "area", "location", "evidence_ids", "reason", "recommendation", "confidence"],
    "additionalProperties": False,
}

AUDIT_SPECIALIST_KEEP_SCHEMA = {
    "type": "object",
    "properties": {
        "area": {"type": "string", "maxLength": 180},
        "location": {"type": "string", "maxLength": 240},
        "evidence_ids": {"type": "array", "items": {"type": "string", "maxLength": 24}, "maxItems": 6},
        "reason": {"type": "string", "maxLength": 420},
        "confidence": {"type": "string", "enum": AUDIT_CONFIDENCE},
    },
    "required": ["area", "location", "evidence_ids", "reason", "confidence"],
    "additionalProperties": False,
}

AUDIT_SPECIALIST_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["READY", "NEED_EVIDENCE"]},
        "summary": {"type": "string", "maxLength": 900},
        "findings": {"type": "array", "items": AUDIT_SPECIALIST_FINDING_SCHEMA, "maxItems": 8},
        "keep_as_is": {"type": "array", "items": AUDIT_SPECIALIST_KEEP_SCHEMA, "maxItems": 6},
        "evidence_requests": {"type": "array", "items": AUDIT_EVIDENCE_REQUEST_SCHEMA, "maxItems": 3},
        "audit_limits": {"type": "array", "items": {"type": "string", "maxLength": 300}, "maxItems": 4},
    },
    "required": ["status", "summary", "findings", "keep_as_is", "evidence_requests", "audit_limits"],
    "additionalProperties": False,
}

# The LLM synthesizer may only select/group/rank already validated IDs. It cannot
# author findings, locations, evidence IDs, reasons, or recommendations.
AUDIT_SYNTHESIS_ID_GROUP_SCHEMA = {
    "type": "object",
    "properties": {
        "source_finding_ids": {"type": "array", "items": {"type": "string", "maxLength": 32}, "maxItems": 4},
    },
    "required": ["source_finding_ids"],
    "additionalProperties": False,
}

AUDIT_SYNTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "finding_groups": {"type": "array", "items": AUDIT_SYNTHESIS_ID_GROUP_SCHEMA, "maxItems": 10},
        "strength_ids": {"type": "array", "items": {"type": "string", "maxLength": 32}, "maxItems": 8},
        "disagreement_groups": {"type": "array", "items": AUDIT_SYNTHESIS_ID_GROUP_SCHEMA, "maxItems": 8},
        "ranked_action_groups": {"type": "array", "items": AUDIT_SYNTHESIS_ID_GROUP_SCHEMA, "maxItems": 5},
    },
    "required": ["finding_groups", "strength_ids", "disagreement_groups", "ranked_action_groups"],
    "additionalProperties": False,
}

AUDIT_FINDING_SCHEMA = {
    "type": "object",
    "properties": {
        "finding_id": {"type": "string", "maxLength": 32},
        "type": {"type": "string", "enum": AUDIT_FINDING_TYPES},
        "priority": {"type": "string", "enum": AUDIT_PRIORITIES},
        "area": {"type": "string", "maxLength": 220},
        "location": {"type": "string", "maxLength": 240},
        "evidence_ids": {"type": "array", "items": {"type": "string", "maxLength": 24}, "maxItems": 12},
        "source_finding_ids": {"type": "array", "items": {"type": "string", "maxLength": 32}, "maxItems": 4},
        "reason": {"type": "string", "maxLength": 1100},
        "recommendation": {"type": "string", "maxLength": 1100},
        "confidence": {"type": "string", "enum": AUDIT_CONFIDENCE},
    },
    "required": ["finding_id", "type", "priority", "area", "location", "evidence_ids", "source_finding_ids", "reason", "recommendation", "confidence"],
    "additionalProperties": False,
}

AUDIT_KEEP_SCHEMA = {
    "type": "object",
    "properties": {
        "strength_id": {"type": "string", "maxLength": 32},
        "area": {"type": "string", "maxLength": 180},
        "location": {"type": "string", "maxLength": 240},
        "evidence_ids": {"type": "array", "items": {"type": "string", "maxLength": 24}, "maxItems": 8},
        "source_strength_ids": {"type": "array", "items": {"type": "string", "maxLength": 32}, "maxItems": 4},
        "reason": {"type": "string", "maxLength": 900},
        "confidence": {"type": "string", "enum": AUDIT_CONFIDENCE},
    },
    "required": ["strength_id", "area", "location", "evidence_ids", "source_strength_ids", "reason", "confidence"],
    "additionalProperties": False,
}

AUDIT_DISAGREEMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "source_finding_ids": {"type": "array", "items": {"type": "string", "maxLength": 32}, "maxItems": 4},
        "summary": {"type": "string", "maxLength": 900},
    },
    "required": ["source_finding_ids", "summary"],
    "additionalProperties": False,
}

AUDIT_NEXT_ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "rank": {"type": "integer"},
        "source_finding_ids": {"type": "array", "items": {"type": "string", "maxLength": 32}, "maxItems": 4},
        "action": {"type": "string", "maxLength": 900},
    },
    "required": ["rank", "source_finding_ids", "action"],
    "additionalProperties": False,
}

AUDIT_REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_assessment": {"type": "string", "maxLength": 1600},
        "completion_status": {"type": "string", "enum": ["COMPLETE", "INCOMPLETE"]},
        "pending_evidence_requests": {
            "type": "array", "maxItems": 64,
            "items": {
                "type": "object",
                "properties": {
                    "specialist": {"type": "string", "maxLength": 180},
                    "kind": {"type": "string", "enum": ["path", "symbol", "text", "unknown"]},
                    "query": {"type": "string", "maxLength": 160},
                    "reason_code": {"type": "string", "enum": [
                        "EVIDENCE_NOT_FOUND", "REQUEST_NOT_ATTEMPTED", "REQUEST_PENDING",
                        "SPECIALIST_NEEDS_EVIDENCE", "INVALID_EVIDENCE_REQUEST"]},
                },
                "required": ["specialist", "kind", "query", "reason_code"],
                "additionalProperties": False,
            },
        },
        "findings": {"type": "array", "items": AUDIT_FINDING_SCHEMA, "maxItems": 10},
        "keep_as_is": {"type": "array", "items": AUDIT_KEEP_SCHEMA, "maxItems": 8},
        "disagreements": {"type": "array", "items": AUDIT_DISAGREEMENT_SCHEMA, "maxItems": 8},
        "audit_limits": {"type": "array", "items": {"type": "string", "maxLength": 420}, "maxItems": 8},
        "recommended_next_actions": {"type": "array", "items": AUDIT_NEXT_ACTION_SCHEMA, "maxItems": 5},
        "rejected_unverified_count": {"type": "integer"},
    },
    "required": ["completion_status", "pending_evidence_requests", "overall_assessment", "findings", "keep_as_is", "disagreements", "audit_limits", "recommended_next_actions", "rejected_unverified_count"],
    "additionalProperties": False,
}

EXECUTOR_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["COMPLETED", "PARTIAL", "BLOCKED"]},
        "changed_files": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
        "tests": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "warnings": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
    },
    "required": ["status", "changed_files", "tests", "warnings"],
    "additionalProperties": False,
}

POST_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL", "BLOCK"]},
        "required_fixes": {"type": "array", "items": {"type": "string", "maxLength": 360}, "maxItems": 6},
    },
    "required": ["verdict", "required_fixes"],
    "additionalProperties": False,
}
