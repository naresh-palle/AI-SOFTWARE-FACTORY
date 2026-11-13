"""
Tests for Dynamic Agent Selection and Technology Decision Engine.
"""

import pytest
from factory.agents.dynamic_selector import DynamicAgentSelector


@pytest.mark.asyncio
async def test_dynamic_selection_ecommerce():
    selector = DynamicAgentSelector()
    prompt = "Create an e-commerce website and mobile application with payment gateway, user authentication, order management and an admin dashboard."
    plan = await selector.analyze_and_select(prompt)

    # Validate Platform Detection
    assert "website" in plan.platform_targets
    assert "mobile_android" in plan.platform_targets or "mobile_ios" in plan.platform_targets

    # Validate Tech Decisions
    assert "Next.js" in plan.technology_stack.frontend
    assert "FastAPI" in plan.technology_stack.backend
    assert "React Native" in str(plan.technology_stack.mobile)
    assert plan.technology_stack.database == "PostgreSQL"
    assert plan.technology_stack.cache == "Redis"
    assert "Stripe" in str(plan.technology_stack.payments)

    # Validate Agents Selected (Exact subset, not all 97!)
    assert len(plan.selected_agent_roles) < 97
    assert "Business Analyst Agent" in plan.selected_agent_roles
    assert "Payment Gateway Agent" in plan.selected_agent_roles
    assert "React Native Developer Agent" in plan.selected_agent_roles


@pytest.mark.asyncio
async def test_dynamic_selection_social_meta():
    selector = DynamicAgentSelector()
    prompt = "Build a marketing automation tool that posts to Instagram and Facebook and receives WhatsApp webhooks."
    plan = await selector.analyze_and_select(prompt)

    assert "Meta Developer Agent" in plan.selected_agent_roles
    assert "Instagram API Agent" in plan.selected_agent_roles
    assert "WhatsApp Business API Agent" in plan.selected_agent_roles
    assert any("Meta" in dep for dep in plan.api_dependencies)
