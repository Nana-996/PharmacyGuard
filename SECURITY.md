# PharmacyGuard Security & Governance

This document details the security architecture, data protection policies, access controls, and **Human-in-the-Loop (HITL) safety boundaries** implemented within **PharmacyGuard**.

---

## Human-in-the-Loop Safety Boundary

**Most importantly, the agent provides clinical evidence and decision-support findings but is strictly prohibited from independently authorizing or executing medication dispensing.**

Patient safety is the foundational constraint of PharmacyGuard's architecture. The system establishes a rigid, non-bypassable safety barrier between AI analysis and real-world clinical action:

```
+-------------------------------------------------------------------------------+
|                      HUMAN-IN-THE-LOOP SAFETY BARRIER                         |
|                                                                               |
|   Electronic Prescription Order Ingested                                      |
|                     │                                                         |
|                     ▼                                                         |
|   Strands AI Agent Evaluates Evidence                                         |
|   (Indication, Allergy, Duplication, Interactions, Dosage, Stock)             |
|                     │                                                         |
|                     ▼                                                         |
|   Synthesizes Decision-Support Findings                                       |
|   (Triage: CLEAR 🟢 | REVIEW 🟡 | HIGH_PRIORITY_REVIEW 🔴)                    |
|                     │                                                         |
|   ══════════════════▼══════════════════════════════════════════════════════   |
|   ║              MANDATORY LICENSED CLINICIAN GATEWAY                    ║   |
|   ║  • AI has NO programmatic connection to automated dispensing systems ║   |
|   ║  • AI cannot alter prescriptions, dosages, or formulations           ║   |
|   ║  • Only a verified human pharmacist can finalize dispensing           ║   |
|   ══════════════════╤══════════════════════════════════════════════════════   |
|                     │                                                         |
|         ┌───────────┼───────────────────────────┐                             |
|         ▼           ▼                           ▼                             |
|    [Approve]    [Reject]            [Override Safety Flag]                    |
|    (Routine)    (Prescriber         (Requires MANDATORY written rationale;    |
|                  contacted)          rejected at API layer if omitted)        |
|         │           │                           │                             |
|         └───────────┼───────────────────────────┘                             |
|                     ▼                                                         |
|   [Immutable Audit Log: User ID, Timestamp, Action, Rationale]                |
+-------------------------------------------------------------------------------+
```

### Core Safety Boundary Principles:
1. **Zero Autonomous Dispensing:** The agent has no programmatic hooks or network access to automated dispensing cabinets (e.g., Pyxis, Omnicell), intravenous compounders, or patient discharge systems.
2. **Advisory Role Only:** Agent outputs are presented as decision-support findings. Every prescription requires an explicit human action (Approve, Reject, or Override).
3. **Mandatory Clinical Override Rationale:** When a clinician chooses to approve an order flagged as `HIGH_PRIORITY_REVIEW` (such as a documented anaphylactic allergy or major drug interaction), the system mandates a written clinical justification. The backend rejects override submissions without justification (HTTP 422).
4. **Permanent Attribution:** Every clinical decision is permanently attributed to the logged-in clinician's identity and timestamped in the audit trail.

---

## Authentication

PharmacyGuard implements secure, stateless authentication for all users:

- **Token Standard:** JSON Web Tokens (JWT) signed using the HMAC-SHA256 (`HS256`) cryptographic algorithm.
- **Password Hashing:** All user passwords are encrypted using one-way salted `bcrypt` hashing with work factor 12. Plaintext passwords are never stored.
- **Session Lifespan:** Access tokens are configured with a strict expiration window (`ACCESS_TOKEN_EXPIRE_MINUTES=480`, default 8 hours).
- **Session Verification:** Protected endpoints validate token signature, expiration timestamp (`exp`), and active user status before processing requests.
- **Auth Endpoint:** `POST /api/auth/login` validates credentials, logs login events, and issues Bearer tokens.

---

## Authorization

Endpoint authorization is enforced at the framework level via FastAPI dependency injection:

- **Dependency Gates:** Routes utilize `Depends(require_roles([...]))` to restrict access based on user role claims extracted from verified JWT tokens.
- **Token Claims:** JWT payloads contain `sub` (user ID), `email`, `role`, and `full_name`.
- **Unauthorized Handling:** Requests with invalid or expired tokens receive HTTP 401 Unauthorized. Requests with valid tokens but insufficient role privileges receive HTTP 403 Forbidden.

---

## Role-Based Access Control (RBAC)

PharmacyGuard enforces strict separation of duties across four defined user roles:

| Role | System Identifier | Permissions & Capabilities | Restrictions |
|---|---|---|---|
| **Staff Pharmacist** | `STAFF_PHARMACIST` | View review queue, run AI clinical checks, approve routine orders, reject unsafe orders, override safety flags with mandatory justification. | Cannot access institutional override audit logs or edit hospital formulary catalogs. |
| **Chief Pharmacist** | `CHIEF_PHARMACIST` | Full staff pharmacist privileges, plus operational workload analytics, institutional override ledger inspection, and formulary inventory controls. | User account provisioning and server management. |
| **Pharmacy Student** | `PHARMACY_STUDENT` | Access to Student Simulation Workspace, blind case reviews, and automated AI educational benchmark scoring. | Strictly blocked from accessing live patient review queues or authorizing medication dispensing. |
| **Administrator** | `ADMIN` | User account provisioning, system health monitoring, and system-level configuration. | Does not make clinical dispensing decisions. |

---

## Secrets Management

Application secrets and credentials are managed according to industry best practices:

- **Environment-Based Isolation:** All configuration parameters and secrets (JWT keys, AWS tokens, database paths) are loaded exclusively via environment variables using `python-dotenv`.
- **Centralized Configuration:** Settings are read through environment variables rather than hardcoded constants in application source code.
- **Development vs. Production:** Development environments use local `.env` files, while production deployments ingest secrets via cloud secret management services (e.g., AWS Secrets Manager).

---

## No Credentials Committed

PharmacyGuard enforces strict hygiene to prevent secret leakage in version control:

- **`.gitignore` Enforcement:** The `.gitignore` file explicitly blocks `.env`, `*.pem`, `*.key`, `*.token`, `__pycache__`, virtual environments (`.venv`), and local database files (`*.db`).
- **Sanitized Templates:** The repository provides `.env.example` containing only placeholder values (`your_bedrock_bearer_token_here`) with zero live credentials.
- **Secret Scanning:** All commits are verified to ensure no AWS access keys, secret keys, bearer tokens, or private certificates are committed to the repository history.

---

## Synthetic Data

PharmacyGuard was developed with privacy as a foundational principle:

- **100% Synthetic Records:** All patient demographics, names, dates of birth, medical record numbers (MRNs), diagnoses, and prescription orders are entirely synthetic and fictional.
- **No Protected Health Information (PHI):** The repository contains zero actual patient data under HIPAA (Health Insurance Portability and Accountability Act) definitions.
- **HIPAA Safe Harbor Compliance:** The synthetic data was generated following the HIPAA Safe Harbor de-identification method, ensuring the platform can be safely demonstrated and evaluated in open-source and hackathon settings without regulatory liability.

---

## Human Approval

The prescription verification lifecycle is governed by mandatory human approval gates:

```
[Ingested Order] ──▶ [AI Clinical Check] ──▶ [Pharmacist Inspection] ──▶ [Human Approval Gate]
                                                                                │
                                           ┌────────────────────────────────────┴──────────┐
                                           ▼                                               ▼
                                      [Approved]                                      [Rejected]
                               (Routine or Overridden)                         (Withhold & Prescriber Alert)
```

1. **Review Verification Workspace:** The reviewing pharmacist inspects patient medical history, active diagnoses, and prescribed drugs alongside the agent's itemized clinical evidence cards.
2. **Standard Approval:** Orders with `CLEAR` or verified `REVIEW` statuses can be authorized with a single click.
3. **Clinical Rejection:** Orders with unresolvable clinical risks can be rejected, triggering an alert to the prescribing physician.
4. **Supervised Student Mode:** Pharmacy students submit practice determinations; their assessments are scored for educational purposes but cannot authorize dispensing.

---

## Audit Logging

Every critical state change, authentication attempt, and clinical action is committed to an immutable, append-only audit ledger in SQLite (`audit_events`):

```sql
CREATE TABLE audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,       -- LOGIN_SUCCESS, DECISION_OVERRIDDEN, etc.
    actor_type TEXT NOT NULL,       -- USER, AGENT, SYSTEM
    actor_id TEXT NOT NULL,         -- USR-STAFF-001, PharmacyGuard-FullAgent
    prescription_id TEXT,          -- RX-1003 or N/A
    event_data TEXT NOT NULL,       -- Structured JSON payload
    timestamp TEXT NOT NULL         -- ISO-8601 UTC timestamp
);
```

### Logged Security & Clinical Events:
- **`LOGIN_SUCCESS` / `LOGIN_FAILURE`:** User identity, role, client IP, and UTC timestamp.
- **`REVIEW_GENERATED`:** Agent findings, triage status, and tool evidence sources.
- **`DECISION_APPROVED`:** Pharmacist ID, prescription ID, and approval timestamp.
- **`DECISION_REJECTED`:** Rejection rationale and prescriber communication notes.
- **`DECISION_OVERRIDDEN`:** Mandatory clinical justification, approving clinician credentials, and flagged risks.
- **`INVENTORY_ADJUSTED`:** Quantity changes, batch numbers, and adjustment reasons.

---

## Public Competition Demo Guardrails

To ensure safety, cost-control, and data integrity during the public competition evaluation, PharmacyGuard includes dedicated demonstration guardrails:

1. **Strict Server-Side Credential Isolation:** The frontend single-page application contains zero AWS credentials, Bedrock bearer tokens, or sensitive API keys. All model invocations are executed strictly server-side through authenticated FastAPI endpoints.
2. **Sliding-Window IP Rate Limiting:** The backend enforces an in-memory sliding-window rate limit (default: 60 requests/minute per IP) to protect the public demonstration server against automated denial-of-service or script looping.
3. **Per-Session AI Agent Invocation Quota:** Each client session/IP is allocated an in-memory quota of **20 AI agent verification runs** (`DEMO_MAX_AGENT_CALLS_PER_SESSION`). Once consumed, subsequent review creation requests return `HTTP 429 Too Many Requests` with transparent guidance to protect AWS Bedrock API credits.
4. **Synthetic-Only Data Barrier (PHI Prevention):** Creation of arbitrary external patient profiles is blocked by `is_approved_synthetic_patient()`. Users must evaluate existing synthetic hospital records or preconfigured clinical case scenarios, preventing unintended entry of real Protected Health Information (PHI/PII).
5. **Persistent Demonstration Labeling:** Every view, modal, and header features explicit demonstration notices and badges to ensure clinicians and evaluators recognize the simulated scope.

---

## Current Prototype Limitations

As a demonstration prototype developed for the Amazon Agents for Humans Hackathon, the following limitations should be noted:

1. **Curated Clinical Knowledge Base:** The local knowledge base covers core cardiovascular, anti-infective, analgesic, and metabolic drug classes. It is not an exhaustive replacement for commercial clinical compendia (e.g., Lexicomp, Micromedex).
2. **Simulated EHR Data:** The system operates against simulated SQLite hospital records rather than live production EHR integrations (such as Epic Systems or Oracle Cerner).
3. **Single-Node Deployment:** The prototype runs on a local SQLite database and Uvicorn server; enterprise deployments require PostgreSQL/Aurora with multi-AZ failover and connection pooling.
4. **Authentication Scope:** Uses internal username/password authentication; production hospital deployment requires integration with enterprise identity providers via SAML 2.0 or OAuth2/OIDC.
5. **Regulatory Classification:** PharmacyGuard is an educational and operations support prototype. It is not cleared as a medical device by the FDA or other regulatory bodies.
6. **Dosage Engine Scope:** The deterministic dosage tool relies on regex pattern matching and recognized interval sigs for synthetic compendium entries. Unrecognized sig formats default safely to single-dose multipliers and are flagged for human review; the prototype does not perform patient-specific pharmacokinetic calculations (e.g., renal CrCl adjustments or weight-based pediatric dosing).
