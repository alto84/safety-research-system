"""
Unit tests for src/data/pharma_org.py

Tests the pharmaceutical company organizational data model including:
- Org hierarchy validity (no orphan roles, valid reports_to chains)
- Regulatory framework coverage (all IDs referenced exist in the map)
- Pipeline stage ordering and consistency
- Quality metrics reasonableness
- Skill library completeness
"""

import pytest

from src.data.pharma_org import (
    ORG_ROLES,
    PIPELINE_STAGES,
    REGULATORY_MAP,
    SKILL_LIBRARY,
    get_all_regulatory_ids_from_pipeline,
    get_all_regulatory_ids_from_roles,
    get_all_skill_ids_from_roles,
    get_quality_metrics,
    get_role,
    get_role_skills,
)


# ============================================================================
# Org hierarchy validity
# ============================================================================


class TestOrgHierarchy:
    """Tests that the org hierarchy is structurally valid."""

    def test_ceo_has_no_manager(self):
        """The CEO should report to no one (reports_to is None)."""
        assert ORG_ROLES["ceo"]["reports_to"] is None

    def test_every_reports_to_exists(self):
        """Every role's reports_to must reference an existing role ID (except CEO)."""
        for role_id, role in ORG_ROLES.items():
            manager = role["reports_to"]
            if manager is not None:
                assert manager in ORG_ROLES, (
                    f"Role '{role_id}' reports to '{manager}' which does not exist"
                )

    def test_no_orphan_roles(self):
        """Every role except CEO must have a valid reports_to."""
        orphans = []
        for role_id, role in ORG_ROLES.items():
            if role_id == "ceo":
                continue
            if role["reports_to"] is None:
                orphans.append(role_id)
        assert orphans == [], f"Orphan roles (no manager, not CEO): {orphans}"

    def test_only_one_root(self):
        """There should be exactly one root role (reports_to is None)."""
        roots = [
            role_id for role_id, role in ORG_ROLES.items()
            if role["reports_to"] is None
        ]
        assert len(roots) == 1, f"Expected 1 root, found {len(roots)}: {roots}"
        assert roots[0] == "ceo"

    def test_no_self_reporting(self):
        """No role should report to itself."""
        for role_id, role in ORG_ROLES.items():
            assert role["reports_to"] != role_id, (
                f"Role '{role_id}' reports to itself"
            )

    def test_role_id_matches_key(self):
        """The role_id field must match the dict key."""
        for key, role in ORG_ROLES.items():
            assert role["role_id"] == key, (
                f"Key '{key}' does not match role_id '{role['role_id']}'"
            )

    def test_every_role_has_title(self):
        """Every role must have a non-empty title."""
        for role_id, role in ORG_ROLES.items():
            assert role["title"], f"Role '{role_id}' has empty title"

    def test_every_role_has_responsibilities(self):
        """Every role must have at least 3 responsibilities."""
        for role_id, role in ORG_ROLES.items():
            resps = role["responsibilities"]
            assert len(resps) >= 3, (
                f"Role '{role_id}' has only {len(resps)} responsibilities (need >= 3)"
            )

    def test_every_role_has_valid_status(self):
        """Status must be one of: active, idle, escalation."""
        valid = {"active", "idle", "escalation"}
        for role_id, role in ORG_ROLES.items():
            assert role["status"] in valid, (
                f"Role '{role_id}' has invalid status '{role['status']}'"
            )

    def test_every_role_has_current_task(self):
        """Every role must have a non-empty current_task description."""
        for role_id, role in ORG_ROLES.items():
            assert role["current_task"], (
                f"Role '{role_id}' has empty current_task"
            )

    def test_ceo_direct_reports(self):
        """CEO should have CMO, Head CMC, Head QA, and Head Commercial as directs."""
        direct_reports = {
            role_id for role_id, role in ORG_ROLES.items()
            if role["reports_to"] == "ceo"
        }
        expected = {"cmo", "head_cmc", "head_qa", "head_commercial"}
        assert direct_reports == expected

    def test_cmo_direct_reports(self):
        """CMO should have VP ClinOps, VP MedAffairs, Head PV, VP Regulatory,
        Head Biostats, and Head ClinDev as directs."""
        direct_reports = {
            role_id for role_id, role in ORG_ROLES.items()
            if role["reports_to"] == "cmo"
        }
        expected = {
            "vp_clinops", "vp_med_affairs", "head_pv",
            "vp_regulatory", "head_biostats", "head_clindev",
        }
        assert direct_reports == expected

    def test_total_role_count(self):
        """There should be exactly 11 roles defined:
        CEO + 4 C-suite/SVP directs + 6 CMO directs = 11."""
        assert len(ORG_ROLES) == 11


# ============================================================================
# Regulatory framework coverage
# ============================================================================


class TestRegulatoryFramework:
    """Tests that all referenced regulatory IDs exist in the mapping."""

    def test_all_role_regulatory_ids_in_map(self):
        """Every regulatory ID referenced by any role must exist in REGULATORY_MAP."""
        role_ids = get_all_regulatory_ids_from_roles()
        missing = role_ids - set(REGULATORY_MAP.keys())
        assert missing == set(), (
            f"Regulatory IDs referenced by roles but missing from map: {missing}"
        )

    def test_all_pipeline_regulatory_ids_in_map(self):
        """Every regulatory ID referenced by pipeline stages must exist in REGULATORY_MAP."""
        pipeline_ids = get_all_regulatory_ids_from_pipeline()
        missing = pipeline_ids - set(REGULATORY_MAP.keys())
        assert missing == set(), (
            f"Regulatory IDs referenced by pipeline but missing from map: {missing}"
        )

    def test_every_regulation_has_title(self):
        """Every regulatory framework entry must have a non-empty title."""
        for reg_id, reg in REGULATORY_MAP.items():
            assert reg.get("title"), f"Regulation '{reg_id}' has no title"

    def test_every_regulation_has_category(self):
        """Every regulatory framework entry must have a category."""
        for reg_id, reg in REGULATORY_MAP.items():
            assert reg.get("category"), f"Regulation '{reg_id}' has no category"

    def test_every_regulation_has_url(self):
        """Every regulatory framework entry must have a URL."""
        for reg_id, reg in REGULATORY_MAP.items():
            assert reg.get("url"), f"Regulation '{reg_id}' has no url"

    def test_every_regulation_has_description(self):
        """Every regulatory framework entry must have a description."""
        for reg_id, reg in REGULATORY_MAP.items():
            assert reg.get("description"), f"Regulation '{reg_id}' has no description"

    def test_map_has_at_least_30_entries(self):
        """The regulatory map should have at least 30 entries to cover
        ICH, CFR, CIOMS, and EU frameworks."""
        assert len(REGULATORY_MAP) >= 30

    def test_map_covers_key_categories(self):
        """The regulatory map should cover clinical, safety, quality,
        manufacturing, and regulatory categories."""
        categories = {reg["category"] for reg in REGULATORY_MAP.values()}
        required = {"clinical", "safety", "quality", "manufacturing", "regulatory"}
        assert required.issubset(categories), (
            f"Missing categories: {required - categories}"
        )


# ============================================================================
# Pipeline stage ordering and consistency
# ============================================================================


class TestPipelineStages:
    """Tests that the clinical pipeline is logically consistent."""

    def test_pipeline_starts_with_preclinical(self):
        """The first stage should be preclinical."""
        assert PIPELINE_STAGES[0]["id"] == "preclinical"

    def test_pipeline_ends_with_approval(self):
        """The last stage should be approval."""
        assert PIPELINE_STAGES[-1]["id"] == "approval"

    def test_completed_stages_come_first(self):
        """All completed stages should precede any non-completed stages."""
        seen_non_completed = False
        for stage in PIPELINE_STAGES:
            if stage["status"] != "completed":
                seen_non_completed = True
            elif seen_non_completed:
                pytest.fail(
                    f"Completed stage '{stage['id']}' appears after "
                    f"non-completed stages"
                )

    def test_in_progress_before_planned(self):
        """In-progress stages should precede planned stages."""
        seen_planned = False
        for stage in PIPELINE_STAGES:
            if stage["status"] == "planned":
                seen_planned = True
            elif stage["status"] == "in_progress" and seen_planned:
                pytest.fail(
                    f"In-progress stage '{stage['id']}' appears after "
                    f"planned stages"
                )

    def test_every_stage_has_owner(self):
        """Every pipeline stage must have an owner that exists in ORG_ROLES."""
        for stage in PIPELINE_STAGES:
            owner = stage["owner"]
            assert owner in ORG_ROLES, (
                f"Stage '{stage['id']}' has owner '{owner}' not found in ORG_ROLES"
            )

    def test_every_stage_has_regulations(self):
        """Every pipeline stage must reference at least one regulation."""
        for stage in PIPELINE_STAGES:
            assert len(stage["regulations"]) >= 1, (
                f"Stage '{stage['id']}' has no regulations"
            )

    def test_completed_stages_have_dates(self):
        """Completed stages should have both start and end dates."""
        for stage in PIPELINE_STAGES:
            if stage["status"] == "completed":
                assert stage["start"] is not None, (
                    f"Completed stage '{stage['id']}' has no start date"
                )
                assert stage["end"] is not None, (
                    f"Completed stage '{stage['id']}' has no end date"
                )

    def test_valid_stage_statuses(self):
        """All stage statuses must be one of the valid values."""
        valid = {"completed", "in_progress", "pending", "planned"}
        for stage in PIPELINE_STAGES:
            assert stage["status"] in valid, (
                f"Stage '{stage['id']}' has invalid status '{stage['status']}'"
            )

    def test_stage_ids_are_unique(self):
        """All pipeline stage IDs must be unique."""
        ids = [stage["id"] for stage in PIPELINE_STAGES]
        assert len(ids) == len(set(ids)), "Duplicate pipeline stage IDs found"

    def test_total_stage_count(self):
        """There should be 12 pipeline stages."""
        assert len(PIPELINE_STAGES) == 12


# ============================================================================
# Quality metrics reasonableness
# ============================================================================


class TestQualityMetrics:
    """Tests that simulated quality metrics are reasonable."""

    def test_returns_dict(self):
        """get_quality_metrics should return a dict."""
        metrics = get_quality_metrics()
        assert isinstance(metrics, dict)

    def test_has_all_sections(self):
        """Metrics must include deviations, capa, audits, training, batches."""
        metrics = get_quality_metrics()
        required = {"deviations", "capa", "audits", "training", "batches"}
        assert required == set(metrics.keys())

    def test_no_critical_deviations(self):
        """Simulated data: critical deviations should be 0."""
        metrics = get_quality_metrics()
        assert metrics["deviations"]["critical"] == 0

    def test_training_compliance_between_0_and_100(self):
        """Training compliance percentage should be 0-100."""
        metrics = get_quality_metrics()
        pct = metrics["training"]["compliance_pct"]
        assert 0 <= pct <= 100

    def test_batch_failure_rate_is_reasonable(self):
        """Batch failure rate should be between 0 and 50 percent."""
        metrics = get_quality_metrics()
        rate = metrics["batches"]["failure_rate_pct"]
        assert 0 <= rate <= 50

    def test_capa_avg_closure_days_positive(self):
        """CAPA average closure time should be a positive number."""
        metrics = get_quality_metrics()
        days = metrics["capa"]["avg_closure_days"]
        assert days > 0

    def test_open_deviations_non_negative(self):
        """Open deviations cannot be negative."""
        metrics = get_quality_metrics()
        assert metrics["deviations"]["open"] >= 0

    def test_audits_completed_le_scheduled(self):
        """Completed audits should not exceed scheduled audits."""
        metrics = get_quality_metrics()
        assert metrics["audits"]["completed"] <= metrics["audits"]["scheduled_ytd"]

    def test_batches_released_plus_failed_le_manufactured(self):
        """Released + failed batches should not exceed manufactured batches."""
        metrics = get_quality_metrics()
        b = metrics["batches"]
        assert b["released"] + b["failed"] <= b["manufactured_ytd"]


# ============================================================================
# Skill library and role skill coverage
# ============================================================================


class TestSkillLibrary:
    """Tests for the skill library and role-skill mappings."""

    def test_all_role_skill_ids_in_library(self):
        """Every skill ID referenced by roles must exist in SKILL_LIBRARY."""
        role_skill_ids = get_all_skill_ids_from_roles()
        missing = role_skill_ids - set(SKILL_LIBRARY.keys())
        assert missing == set(), (
            f"Skill IDs referenced by roles but missing from library: {missing}"
        )

    def test_every_role_has_at_least_one_skill(self):
        """Every role must have at least one skill assigned."""
        for role_id, role in ORG_ROLES.items():
            assert len(role["skills"]) >= 1, (
                f"Role '{role_id}' has no skills assigned"
            )

    def test_every_skill_has_name(self):
        """Every skill in the library must have a non-empty name."""
        for skill_id, skill in SKILL_LIBRARY.items():
            assert skill.get("name"), f"Skill '{skill_id}' has no name"

    def test_every_skill_has_category(self):
        """Every skill in the library must have a category."""
        for skill_id, skill in SKILL_LIBRARY.items():
            assert skill.get("category"), f"Skill '{skill_id}' has no category"

    def test_every_skill_has_description(self):
        """Every skill in the library must have a description."""
        for skill_id, skill in SKILL_LIBRARY.items():
            assert skill.get("description"), (
                f"Skill '{skill_id}' has no description"
            )

    def test_skill_library_size(self):
        """There should be at least 15 skills in the library."""
        assert len(SKILL_LIBRARY) >= 15


# ============================================================================
# Helper functions
# ============================================================================


class TestHelperFunctions:
    """Tests for the module-level helper functions."""

    def test_get_role_existing(self):
        """get_role should return the role dict for a valid role_id."""
        role = get_role("ceo")
        assert role is not None
        assert role["title"] == "Chief Executive Officer"

    def test_get_role_missing(self):
        """get_role should return None for a non-existent role_id."""
        assert get_role("nonexistent") is None

    def test_get_role_skills_existing(self):
        """get_role_skills should return skill details for a valid role."""
        skills = get_role_skills("ceo")
        assert skills is not None
        assert len(skills) >= 1
        for skill in skills:
            assert "skill_id" in skill
            assert "name" in skill
            assert "category" in skill
            assert "description" in skill

    def test_get_role_skills_missing(self):
        """get_role_skills should return None for a non-existent role."""
        assert get_role_skills("nonexistent") is None

    def test_get_all_regulatory_ids_from_roles_non_empty(self):
        """Should return a non-empty set."""
        ids = get_all_regulatory_ids_from_roles()
        assert len(ids) > 0

    def test_get_all_regulatory_ids_from_pipeline_non_empty(self):
        """Should return a non-empty set."""
        ids = get_all_regulatory_ids_from_pipeline()
        assert len(ids) > 0

    def test_get_all_skill_ids_from_roles_non_empty(self):
        """Should return a non-empty set."""
        ids = get_all_skill_ids_from_roles()
        assert len(ids) > 0
