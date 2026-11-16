# PRIVACY POLICY (DRAFT)
**AI SOFTWARE DEVELOPMENT FACTORY (`AI-SOFTWARE-FACTORY`)**
*Last Updated: November 2026 | Version 1.0 (Draft for Qualified Legal Review)*

> [!WARNING]
> This policy outlines data processing practices under the Indian Digital Personal Data Protection Act (DPDP 2023) and General Data Protection Regulation (GDPR). Requires formal validation by privacy counsel.

### 1. Categories of Personal Data Collected
- **Account Identity Data:** Name, email address, salted password hash (PBKDF2), organization name, billing contact.
- **Developer & Integration Metadata:** OAuth tokens (GitHub, Meta Graph, AWS IAM), encrypted using tenant-isolated AES-Fernet ciphers.
- **Telemetry & Observability Data:** IP addresses, browser client fingerprints, API invocation latency, OpenTelemetry spans, audit logs.
- **Financial & Payment Records:** Transaction identifiers, invoice history, token consumption records. (Card/UPI details are tokenized directly by Stripe/Razorpay and never stored on Factory servers).

### 2. Legal Basis & Purpose of Processing
Processing is conducted exclusively to:
- Provision and maintain isolated multi-tenant workspaces.
- Execute natural-language software requirement analysis and code generation.
- Dispatch cloud worker containers and build artifacts.
- Enforce Role-Based Access Control (RBAC) and verify webhook integrity.
- Satisfy Indian tax, billing, and accounting compliance obligations.

### 3. Data Localization & International Transfers
Data is hosted within secure AWS data centers with encryption at rest (AWS KMS / AES-256) and in transit (TLS 1.3). Cross-border transfers adhere to standard contractual clauses and DPDP statutory notifications.

### 4. Data Principal & Data Subject Rights
Customers maintain the statutory right to:
1. **Access & Portability:** Request structured JSON export of all projects, requirements, generated code, and invoices.
2. **Correction & Rectification:** Modify team membership, billing emails, and credentials via dashboard settings.
3. **Erasure ("Right to be Forgotten"):** Request permanent tenant purging via automated deletion procedures.
4. **Grievance Redressal:** Submit formal inquiries to the designated Grievance Officer at `privacy-grievance@factory.ai`.
