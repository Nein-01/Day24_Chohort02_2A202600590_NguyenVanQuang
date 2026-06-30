# ND13/2023 Compliance Checklist - MedViet AI Platform

## A. Data Localization
- [ ] Store all patient data on servers located in Vietnam.
- [ ] Keep backups inside Vietnam territory.
- [ ] Log and approve any cross-border transfer before it occurs.

## B. Explicit Consent
- [ ] Collect consent before using patient data for AI training.
- [ ] Provide a user withdrawal and right-to-erasure workflow.
- [ ] Store consent records with timestamp, purpose, and data scope.

## C. Breach Notification - 72h
- [ ] Maintain an incident response plan with severity levels.
- [ ] Trigger automated alerts for suspicious data access and export.
- [ ] Notify the competent authority within 72 hours for reportable breaches.

## D. DPO Appointment
- [ ] Appoint a Data Protection Officer.
- [ ] DPO contact: dpo@medviet.example

## E. Technical Controls

| ND13 Requirement | Technical Control | Status | Owner |
| --- | --- | --- | --- |
| Data minimization | PII anonymization pipeline with Presidio-compatible recognizers | Done | AI Team |
| Access control | RBAC with Casbin and ABAC policy with OPA | Done | Platform Team |
| Encryption | AES-256-GCM envelope encryption for sensitive fields; TLS 1.3 for transit | In Progress | Infra Team |
| Audit logging | FastAPI access logs, authentication events, and data export logs shipped to SIEM | Todo | Platform Team |
| Breach detection | Prometheus metrics, anomaly alerts, and security scan reports | Todo | Security Team |

## F. Implementation Notes For Open Items

Encryption:
Use `SimpleVault` for local development and replace the file-based KEK with a production KMS or HSM. Encrypt raw PII columns at rest, rotate DEKs per dataset export, and restrict KEK decrypt permission to service identities.

Audit logging:
Add middleware to record user, role, endpoint, action, resource, status code, request ID, and timestamp. Send logs to a centralized SIEM with immutable retention and alerts for repeated 401/403 responses or bulk export.

Breach detection:
Expose API and data-pipeline metrics to Prometheus, alert on unusual raw-data access, failed authentication spikes, high-volume downloads, and restricted-data export attempts. Store incident evidence and response actions in `reports/`.
