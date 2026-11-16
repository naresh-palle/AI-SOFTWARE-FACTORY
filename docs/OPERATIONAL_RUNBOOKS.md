# AI Software Factory - Operational Runbooks & SRE Guides

This document defines standard operating procedures (SOPs) and runbooks for engineers and SREs operating the AI Software Factory in staging and production environments.

---

## Runbook 1: Production Incident Response & Anomaly Triage

### Trigger
- CloudWatch or Prometheus alarm fires: Error rate > 1.0% or API p95 latency > 2000ms.
- Sentry / OpenTelemetry alerts on uncaught exceptions.

### Severity Levels
- **SEV-1 (Critical)**: Platform API unreachable or cross-tenant data leak risk. Response: Immediate (< 15 mins).
- **SEV-2 (Major)**: Autonomous agent swarm stalled, or billing/payment webhooks failing. Response: < 30 mins.
- **SEV-3 (Moderate)**: Non-critical dashboard views slow, non-blocking background workers delayed. Response: < 2 hours.

### Triage Procedure
1. Inspect live telemetry:
   ```bash
   curl -s -H "Authorization: Bearer $ADMIN_TOKEN" https://api.factory.ai/api/v1/observability/metrics | jq .
   ```
2. Inspect active incidents and RCA recommendations:
   ```bash
   curl -s -H "Authorization: Bearer $ADMIN_TOKEN" https://api.factory.ai/api/v1/observability/incidents
   ```
3. Check ECS cluster container health:
   ```bash
   aws ecs list-tasks --cluster ai-software-factory-prod --desired-status RUNNING
   ```
4. If a failing microservice is identified, trigger Tier-1 or Tier-2 self-healing:
   ```bash
   curl -X POST https://api.factory.ai/api/v1/observability/self-heal \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -d '{"action": "restart_service", "target": "worker-pool-1"}'
   ```

---

## Runbook 2: Automated & Manual Deployment Rollback

### Trigger
- Staging or Production smoke tests fail after deployment.
- Increased 5xx error spike (> 2%) detected within 10 minutes post-release.

### Procedure
1. **Automated Rollback**: The deployment engine automatically initiates rollback if smoke tests fail within 300 seconds.
2. **Manual Rollback**:
   Execute rollback via API:
   ```bash
   curl -X POST https://api.factory.ai/api/v1/deployments/{deployment_id}/rollback \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"reason": "Elevated 502 Bad Gateway responses detected post-release"}'
   ```
3. Verify traffic routing switches back to previous stable container tag:
   ```bash
   aws elbv2 describe-target-health --target-group-arn $TG_ARN
   ```
4. Confirm error rates drop below 0.1%.

---

## Runbook 3: Disaster Recovery, Database Point-In-Time Restore & Checksum Validation

### Trigger
- Accidental table dropping, catastrophic data corruption, or multi-AZ infrastructure loss.
- Target RTO: 15 minutes. Target RPO: 5 minutes.

### Procedure
1. Retrieve latest verified backup metadata:
   ```bash
   python -c "
   import asyncio
   from factory.core.disaster_recovery import DisasterRecoveryManager
   dr = DisasterRecoveryManager()
   latest = dr.get_latest_backup()
   print(f'Backup: {latest[\"backup_id\"]} SHA256: {latest[\"sha256\"]}')
   "
   ```
2. Verify integrity before restoring:
   - Ensure the SHA-256 digest calculated from file contents matches the signed metadata record.
   - Any checksum mismatch will immediately abort restoration.
3. Execute restore operation:
   ```bash
   python -c "
   import asyncio
   from factory.core.disaster_recovery import DisasterRecoveryManager
   dr = DisasterRecoveryManager()
   success = asyncio.run(dr.restore_backup('$BACKUP_ID'))
   print('Restoration status:', success)
   "
   ```
4. Run validation queries:
   - Verify tenant count, project records, and active workflow states are preserved.

---

## Runbook 4: Cloud Worker Container Crash Recovery & Workflow State Resumption

### Trigger
- Spot instance termination, OOM kill, or container crash during active code generation workflow.

### Procedure
1. The Cloud Worker Engine maintains persistent execution checkpoints in the database.
2. Query stalled tasks:
   ```sql
   SELECT id, project_id, status, updated_at FROM tasks WHERE status = 'in_progress' AND updated_at < NOW() - INTERVAL '10 MINUTE';
   ```
3. Restart cloud worker container:
   ```bash
   aws ecs update-service --cluster ai-software-factory-prod --service worker-agent-swarm --force-new-deployment
   ```
4. The worker picks up unacknowledged tasks from the persistent checkpoint without restarting completed stages.

---

## Runbook 5: Payment Reconciliation & Subscription Webhook Recovery

### Trigger
- Stripe / Razorpay webhook missed due to network partition.
- Customer account shows "Free" despite successful checkout.

### Procedure
1. Re-query Stripe events API for missing `checkout.session.completed` events:
   ```bash
   stripe events list --type=checkout.session.completed --limit=10
   ```
2. Replay webhook event to platform endpoint:
   ```bash
   stripe events resend evt_12345
   ```
3. In SaaS workspace, verify subscription status updates to `active` and quota expands immediately.

---

## Runbook 6: Security Incident Escalation & Compromise Remediation

### Trigger
- Anomalous token usage spike, repeated auth brute-force alerts, or potential secret exposure.

### Procedure
1. **Isolate Compromised Tenant**:
   Temporarily suspend tenant API access:
   ```bash
   curl -X POST https://api.factory.ai/api/v1/saas/tenants/{tenant_id}/suspend \
     -H "Authorization: Bearer $SEC_ADMIN_TOKEN"
   ```
2. **Rotate Secrets**:
   Rotate master encryption key and database connection passwords.
   Re-encrypt stored third-party credentials using `factory.core.encryption`.
3. **Audit Trail Review**:
   Query immutable security audit logs for affected tenant IP, user agents, and endpoints called:
   ```sql
   SELECT * FROM audit_logs WHERE tenant_id = '$TENANT_ID' ORDER BY timestamp DESC LIMIT 100;
   ```
4. **Issue Incident Disclosure**:
   Notify tenant owner within 72 hours per GDPR Article 33 and DPDP requirements.
