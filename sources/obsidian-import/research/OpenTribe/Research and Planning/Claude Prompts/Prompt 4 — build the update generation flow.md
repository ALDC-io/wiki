Implement the update generation flow for the Zeus Memory prototype.

Inputs:
- impacted doc
- impacted section
- source evidence from Git, Jira, and meeting note
- stale reason

Need:
1. Create a concise explanation of why the doc is stale
2. Generate a proposed updated section
3. Preserve important nuance
4. Attach provenance in a structured way
5. Avoid hallucinating facts not supported by the inputs

Output format:
{
  "summary_of_change": "...",
  "stale_reason": "...",
  "proposed_updated_text": "...",
  "evidence_links": [...],
  "confidence_score": 0-100,
  "human_review_required": true/false
}

Constraints:
- Be conservative
- Only rewrite the section that changed
- Keep wording enterprise-friendly
- Do not invent metrics, thresholds, or approvals unless supported by inputs

Please generate the code for this module and show example outputs using the mocked Lululemon artifacts.