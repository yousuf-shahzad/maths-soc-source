# Incident Archive

| Date | ID | Title | Severity | Status | Issue |
|------|----|-------|----------|--------|-------|
| 2025-09-17 | 2025-09-17-db-wipe | Production DB wiped by tests | SEV1 | Closed | #<issue_number> |

We follow a lightweight process:

1. Open an Incident Issue (`label: incident`, severity label e.g. `sev1`).
2. Maintain real-time updates in the issue.
3. After closure, capture a permanent record under `docs/incidents/`.
4. Maintain an index in `docs/incidents/README.md`.

Use the template: [`docs/incidents/INCIDENT_TEMPLATE.md`](docs/incidents/INCIDENT_TEMPLATE.md)

### Severity Scale

| Severity | Description |
|----------|-------------|
| SEV1 | Full outage / data loss |
| SEV2 | Major feature down / degraded |
| SEV3 | Partial functionality issue |
| SEV4 | Minor bug with workaround |
| SEV5 | Cosmetic / informational |

### Standard Sections

Summary, Impact, Timeline, Root Cause, Contributing Factors, Mitigation, Recovery, Action Items, Lessons Learned, References.

## Backup & Recovery Guidelines (NEW)

(Implement if not already in place.)

| Layer | Recommendation |
|-------|---------------|
| Logical Backups | Nightly `pg_dump` stored offsite |
| Point-in-Time | WAL archiving (if Postgres) |
| Verification | Automated restore to ephemeral DB + integrity checks |
| Retention | 30 days standard (adjust as needed) |
| Secrets | Rotate DB credentials after incidents |

Disaster Recovery Drill (Quarterly):

1. Restore most recent backup to fresh DB.
2. Run integrity script (row counts, key tables).
3. Document time-to-recover.
