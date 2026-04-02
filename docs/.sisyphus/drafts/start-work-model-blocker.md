# Draft: start-work model blocker

## Requirements (confirmed)
- User attempted `/start-work ai-fake-project-detector-v1`
- Execution failed because `claude code sonnet4.6` model is unavailable

## Technical Decisions
- Treat this as an execution-environment blocker, not a product-scope blocker
- Resolve runner/model configuration before retrying `/start-work`

## Research Findings
- No in-repo reference found for `sonnet4.6`, `gpt-5.4`, or `/start-work` command configuration under the project workspace
- This strongly suggests the failing model selection lives in external OpenCode / Claude Code command configuration rather than project source files

## Technical Decisions
- Preferred replacement target requested by user: `OPENAI GPT-5.4 high`

## Open Questions
- Which models are currently available in the user's OpenCode/Claude environment?
- Is the missing model hardcoded in framework config, slash command config, or local settings?

## Scope Boundaries
- INCLUDE: diagnosing the model-selection blocker, planning the fix path
- EXCLUDE: direct code implementation by Prometheus
