Generate realistic mocked data files for the Zeus Memory prototype.

Context:
The prototype is for Lululemon and focuses on ML demand forecasting documentation drift.

Create the following local demo artifacts:

1. Confluence-like markdown docs:
- demand_forecasting_overview.md
- forecast_assumptions.md
- forecast_runbook.md

2. Git change artifacts:
- pr_1042_summary.json
- feature_logic_diff.txt

3. Jira artifact:
- epic_forecast_override_update.json

4. Meeting / decision artifact:
- merch_planning_decision_2026_04_05.md

Requirements:
- The existing docs must be plausible but slightly stale
- The source change should reflect a real business-logic update
- The updated logic should affect markdown-sensitive SKUs in North America
- Include references to thresholds, exception rules, fallback behavior, and operational implications
- The docs should have enough specificity that drift is obvious
- The change should be easy to explain in a demo

Output format:
For each file:
- filename
- full contents

Make the data coherent across all files so the story hangs together.