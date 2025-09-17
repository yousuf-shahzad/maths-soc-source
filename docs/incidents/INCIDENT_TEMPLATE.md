# Incident: <Short Title>

ID: <YYYY-MM-DD-descriptive-slug>  
Date Detected: <YYYY-MM-DDTHH:MMZ>  
Severity: SEV1 | SEV2 | SEV3 | SEV4 | SEV5  
Status: Open | Mitigated | Monitoring | Closed

## 1. Summary
(1–2 sentences: What happened + primary impact.)

## 2. Impact
- User Impact: (What users saw / could not do)
- Technical Impact: (Systems affected, data affected)
- Scope: (Which components / services / regions)

## 3. Timeline (UTC)
| Time (UTC) | Event |
|------------|-------|
| HH:MM | <Event> |
| HH:MM | <Event> |
| ... | ... |

(Record facts only; avoid speculation. Add as the incident unfolds.)

## 4. Detection
- How was it detected? (User report, monitoring alert, log review)
- Was detection timely? (Y/N & why)

## 5. Root Cause
(Once known. Be specific: the exact chain of conditions + triggering action.)

## 6. Contributing Factors
- (E.g. Missing guard rails, privilege misconfiguration, lack of monitoring)

## 7. Mitigation
- Immediate steps taken to stop impact
- Temporary workarounds

## 8. Recovery
- Data restored? (Y/N/explain)
- Steps to return to normal operation
- Gaps / partial restoration notes

## 9. Follow-up Action Items
| ID | Action | Owner | Priority | Due Date | Status |
|----|--------|-------|----------|----------|--------|
| A1 |  |  |  |  | open |
| A2 |  |  |  |  | open |

Guidelines:
- Priority: P1 (must), P2 (soon), P3 (nice)
- Close incident only when immediate risk is mitigated (not when all follow-ups done).

## 10. Lessons Learned
- What worked well
- What didn’t
- Where we got lucky
- Process improvements

## 11. Prevention / Long-Term Changes
(Policies, automation, monitoring, role separation, test isolation.)

## 12. Communications
- User Messaging: (Link / summary)
- Internal Announcement: (Link / summary)

## 13. Evidence & References
- Related Issue: #
- PRs: #, #
- Logs / Dashboards: (links)
- Commands Run: (if relevant)
- Commit(s): (short SHAs)

## 14. Appendix (Optional)
- Architectural diagrams
- Query snippets
- Forensic notes

---
Meta:
- Template Version: 1.0
- Last Updated: 2025-09-17