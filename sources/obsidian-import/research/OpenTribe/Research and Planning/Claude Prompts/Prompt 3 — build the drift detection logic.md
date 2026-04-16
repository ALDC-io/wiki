Implement the drift detection layer for the Zeus Memory prototype.

Prototype context:
- Local mocked artifacts only
- Python + Streamlit
- Lululemon demand forecasting example

Need:
1. Parse source artifacts
2. Identify likely impacted docs based on keywords, business-logic entities, and rule references
3. Detect stale sections in docs
4. Produce a structured output:
   - impacted_doc
   - impacted_section
   - stale_reason
   - evidence
   - confidence_score

Constraints:
- Do not overengineer
- Prefer deterministic rules + simple heuristics
- Use explicit mappings when helpful
- Make the outputs demo-friendly and understandable

The system should detect a change involving:
- markdown sensitivity threshold
- region-specific override behavior
- fallback forecast behavior
- operational handoff implications

Please generate:
- the Python modules
- helper functions
- clean comments
- example outputs for the mocked data