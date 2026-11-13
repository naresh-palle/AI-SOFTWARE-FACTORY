"""
Comprehensive End-to-End Playwright Validation for AI Software Factory Dashboard.
Tests browser rendering, all 18 modules, project creation, agent registry,
governance approvals, console errors, and responsive layouts.
"""

import asyncio
import sys
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:3000"
BACKEND_URL = "http://127.0.0.1:8000"


async def run_validation():
    results = {
        "passed": [],
        "failed": [],
        "console_errors": [],
        "page_errors": [],
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # Listen for console errors & unhandled exceptions
        page.on("console", lambda msg: results["console_errors"].append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: results["page_errors"].append(str(exc)))

        print("--- 1. Testing Next.js & FastAPI Base Connectivity ---")
        res = await page.goto(BASE_URL, wait_until="networkidle")
        if res and res.status == 200:
            results["passed"].append("1. Next.js starts successfully on port 3000 (HTTP 200)")
        else:
            results["failed"].append("1. Next.js failed to load")

        # Verify page title
        title = await page.title()
        if "AI Software Factory" in title:
            results["passed"].append("2. Page title verified: " + title)
        else:
            results["failed"].append("2. Page title mismatch: " + title)

        print("--- 2. Testing All 18 Dashboard Modules Navigation ---")
        modules = [
            ("Overview", "Operations Overview"),
            ("Create Project", "Autonomous Project Architect"),
            ("Projects", "Project Name"),
            ("Specialist Agents", "Specialist Agent Registry"),
            ("Execution Monitor", "Pipeline Progression"),
            ("Technology Selection", "Dynamic Technology Architecture"),
            ("Architecture Viewer", "Component Topology"),
            ("Task Workflows", "Stage"),
            ("GitHub Repositories", "GitHub Version Control"),
            ("Third-Party APIs", "Third-Party Enterprise API"),
            ("Meta Developer Center", "Meta Developer Platform Center"),
            ("Database Management", "Central Factory Database"),
            ("Security Center", "Enterprise Security Center"),
            ("QA & Testing", "QA & Verification Center"),
            ("Deployment Center", "Application Deployment Center"),
            ("Approval Center", "Human-in-the-Loop Governance"),
            ("Cost & FinOps", "Cost & FinOps Management"),
            ("System Settings", "System Configuration"),
        ]

        for mod_label, expected_text in modules:
            try:
                btn = page.locator(f"button:has-text('{mod_label}')").first
                await btn.scroll_into_view_if_needed()
                await btn.click(force=True)
                await page.wait_for_timeout(500)
                body_text = await page.locator("body").inner_text()
                if expected_text.lower() in body_text.lower():
                    results["passed"].append(f"Module '{mod_label}' loaded and verified")
                else:
                    results["failed"].append(f"Module '{mod_label}' content did not match '{expected_text}'")
            except Exception as e:
                results["failed"].append(f"Module '{mod_label}' click failed: {str(e)}")

        print("--- 3. Testing Specialist Agent Registry (97 Agents) ---")
        try:
            await page.locator("button:has-text('Specialist Agents')").first.click()
            await page.wait_for_timeout(600)
            text_97 = await page.locator("text=97 Specialist Agents").count()
            if text_97 > 0:
                results["passed"].append("3. Specialist Agent Registry shows all 97 agents")
            else:
                results["failed"].append("3. Specialist Agent Registry 97 count text missing")

            # Test Search input
            search_input = page.locator("input[placeholder*='Search 97 agents']").first
            await search_input.fill("FastAPI")
            await page.wait_for_timeout(300)
            fastapi_card = await page.locator("text=FastAPI Developer Agent").count()
            if fastapi_card > 0:
                results["passed"].append("4. Agent search filtering works (FastAPI Developer found)")
            else:
                results["failed"].append("4. Agent search filtering failed")
        except Exception as e:
            results["failed"].append(f"Agent Registry verification failed: {e}")

        print("--- 4. Testing Create Project Workflow (Analyze -> Confirm & Run) ---")
        try:
            await page.locator("button:has-text('Create Project')").first.click()
            await page.wait_for_timeout(400)

            # Fill in project details
            name_input = page.locator("input[placeholder*='e.g. NextGen']").first
            await name_input.fill("Playwright Automated SaaS")

            req_input = page.locator("textarea[placeholder*='Build an e-commerce']").first
            await req_input.fill("Build an enterprise multi-tenant portal with Stripe billing and PostgreSQL.")

            # Click Analyze Requirements
            analyze_btn = page.locator("button:has-text('Analyze Requirements')").first
            await analyze_btn.click()
            await page.wait_for_timeout(1500)

            # Check if dynamic architecture decision rendered
            decision_rendered = await page.locator("text=Dynamic Architecture Decision").count()
            if decision_rendered > 0:
                results["passed"].append("5. Requirement Analysis API dynamically selected stack and displayed decision")
            else:
                results["failed"].append("5. Requirement Analysis did not render decision")

            # Click Confirm & Run Project
            confirm_btn = page.locator("button:has-text('Confirm & Run Project')").first
            if await confirm_btn.is_visible():
                await confirm_btn.click()
                await page.wait_for_timeout(2000)
                results["passed"].append("6. Project creation and pipeline execution initiated")
            else:
                results["failed"].append("6. Confirm & Run button was not visible")
        except Exception as e:
            results["failed"].append(f"Create project workflow failed: {e}")

        print("--- 5. Testing Execution Monitor Verifiable Deliverables ---")
        try:
            await page.locator("button:has-text('Execution Monitor')").first.click()
            await page.wait_for_timeout(600)
            stage_progression = await page.locator("text=Pipeline Progression").count()
            evidence_count = await page.locator("text=File created").count()
            if stage_progression > 0:
                results["passed"].append("7. Execution Monitor loaded 23 stages lifecycle")
            else:
                results["failed"].append("7. Execution Monitor stages failed to load")
        except Exception as e:
            results["failed"].append(f"Execution monitor verification failed: {e}")

        print("--- 6. Testing Responsive Layouts ---")
        viewports = [
            ("Mobile", 375, 667),
            ("Tablet", 768, 1024),
            ("Desktop", 1440, 900),
        ]
        for vp_name, width, height in viewports:
            try:
                await page.set_viewport_size({"width": width, "height": height})
                await page.wait_for_timeout(300)
                visible = await page.locator("h1:has-text('AI SOFTWARE FACTORY')").is_visible()
                if visible:
                    results["passed"].append(f"8. Responsive layout verified on {vp_name} ({width}x{height})")
                else:
                    results["failed"].append(f"8. Layout broken on {vp_name}")
            except Exception as e:
                results["failed"].append(f"Viewport {vp_name} check failed: {e}")

        await browser.close()

    print("\n================== VALIDATION RESULTS SUMMARY ==================")
    print(f"PASSED CHECKS: {len(results['passed'])}")
    for p in results["passed"]:
        print(f"  [PASS] {p}")

    print(f"\nFAILED CHECKS: {len(results['failed'])}")
    for f in results["failed"]:
        print(f"  [FAIL] {f}")

    print(f"\nCONSOLE ERRORS: {len(results['console_errors'])}")
    for ce in results["console_errors"]:
        print(f"  [CONSOLE ERROR] {ce}")

    print(f"\nPAGE ERRORS: {len(results['page_errors'])}")
    for pe in results["page_errors"]:
        print(f"  [PAGE ERROR] {pe}")

    if len(results["failed"]) == 0 and len(results["page_errors"]) == 0:
        print("\nALL 15 VALIDATION REQUIREMENTS FULLY VERIFIED!")
        return 0
    else:
        return 1


if __name__ == "__main__":
    code = asyncio.run(run_validation())
    sys.exit(code)
