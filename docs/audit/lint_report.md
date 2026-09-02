# Audit coupling lint report

Started: `2026-08-31T17:27:58.954111Z`
Finished: `2026-08-31T17:27:58.985366Z`

Files scanned: **12** | Findings: hard **0** | warning **0** | info **2**

## Per-rule summary

- `tier1/email`: 1
- `tier1/meeting_ai_workspace`: 1

## Findings

### `info` · `tier1/email` · C:\demo_presentation\tools\audit_coupling_lint.py:286

Hardcoded tenant email address (crm@sgctech.ai); replace with an `ir.config_parameter` lookup.  [suppressed inline — re-enable by removing the audit-lint disable annotation]

```
  message=( ⏎                 "Hardcoded `crm@sgctech.ai` (M5 / 16h audit blocke
```

### `info` · `tier1/meeting_ai_workspace` · C:\demo_presentation\tools\audit_coupling_lint.py:286

Hardcoded `crm@sgctech.ai` (M5 / 16h audit blocker); use `ir.config_parameter('sgc.meeting_ai.workspace_account')`.  [suppressed inline — re-enable by removing the audit-lint disable annotation]

```
  message=( ⏎                 "Hardcoded `crm@sgctech.ai` (M5 / 16h audit blocke
```
