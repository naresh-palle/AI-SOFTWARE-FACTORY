/**
 * Factory API Client Layer
 * Connects the Next.js Dashboard to the FastAPI Master Orchestrator backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function fetchJSON<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error ${response.status}: ${errorText || response.statusText}`);
  }
  return response.json();
}

// System & Health
export async function fetchHealth() {
  return fetchJSON<{
    status: string;
    app_name: string;
    environment: string;
    default_execution_mode: string;
    llm_provider: string;
    database: string;
  }>("/health");
}

export async function fetchSystemSettings() {
  return fetchJSON<{
    app_name: string;
    environment: string;
    default_execution_mode: string;
    default_llm_provider: string;
    ollama_base_url: string;
    ollama_model: string;
    github_username: string;
    has_github_token: boolean;
    has_meta_app: boolean;
    encryption_configured: boolean;
  }>("/api/v1/system/settings");
}

// Overview
export async function fetchOverviewStats() {
  return fetchJSON<{
    total_projects: number;
    active_projects: number;
    completed_projects: number;
    failed_projects: number;
    total_agents: number;
    active_agents_count: number;
    pending_approvals_count: number;
    running_workflows: number;
    total_cost_usd: number;
    system_status: string;
    recent_activities: Array<{
      id: string;
      project_id: string;
      action: string;
      actor: string;
      details: any;
      created_at: string;
    }>;
  }>("/api/v1/overview/stats");
}

// Projects
export async function fetchProjects() {
  return fetchJSON<
    Array<{
      id: string;
      name: string;
      platform_target: string;
      execution_mode: string;
      status: string;
      current_stage: number;
      created_at: string;
    }>
  >("/api/v1/projects");
}

export async function fetchProject(id: string) {
  return fetchJSON<{
    project_id: string;
    project_name: string;
    requirement_text: string;
    execution_mode: string;
    current_stage: number;
    total_stages: number;
    stages: Record<
      number,
      {
        stage_number: number;
        title: string;
        status: string;
        tasks_count: number;
        completed_tasks: number;
        execution_evidence: string[];
        artifacts: Record<string, any>;
        error_message?: string;
      }
    >;
    total_cost_usd: number;
    pending_approvals: Array<{
      id: string;
      stage: number;
      action_type: string;
      description: string;
    }>;
    is_completed: boolean;
    is_failed: boolean;
  }>(`/api/v1/projects/${id}`);
}

export async function analyzeRequirement(requirement_text: string, platform_target: string = "fullstack") {
  return fetchJSON<{
    project_title: string;
    platform_targets: string[];
    technology_stack: {
      frontend: string;
      backend: string;
      mobile?: string;
      database: string;
      cache?: string;
      payments?: string;
      auth: string;
      cloud_infra: string;
      ci_cd: string;
      rationale: Record<string, string>;
    };
    selected_agent_roles: string[];
    selected_agent_numbers: number[];
    api_dependencies: string[];
    licensing_requirements: string[];
    approval_checkpoints: string[];
    estimated_monthly_cost_usd: number;
    mermaid_architecture: string;
  }>("/api/v1/analyze", {
    method: "POST",
    body: JSON.stringify({ requirement_text, platform_target }),
  });
}

export async function createProject(payload: {
  name: string;
  requirement_text: string;
  platform_target: string;
  execution_mode: string;
}) {
  return fetchJSON<{ project_id: string; name: string; state: any }>("/api/v1/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function executeProject(id: string, stop_at_stage: number = 23) {
  return fetchJSON<any>(`/api/v1/projects/${id}/execute?stop_at_stage=${stop_at_stage}`, {
    method: "POST",
  });
}

// Tasks & Architecture
export async function fetchProjectTasks(projectId: string) {
  return fetchJSON<
    Array<{
      id: string;
      project_id: string;
      stage: number;
      agent_name: string;
      title: string;
      description?: string;
      status: string;
      execution_evidence?: string;
      started_at?: string;
      completed_at?: string;
    }>
  >(`/api/v1/projects/${projectId}/tasks`);
}

export async function fetchProjectArchitecture(projectId: string) {
  return fetchJSON<{
    project_id: string;
    frontend_stack: string;
    backend_stack: string;
    mobile_stack?: string;
    database_stack: string;
    cache_stack?: string;
    cloud_stack: string;
    ci_cd_stack: string;
    selected_agents: string[];
    mermaid_diagram?: string;
    estimated_cost_usd: number;
    created_at: string;
  }>(`/api/v1/projects/${projectId}/architecture`);
}

export async function fetchProjectGithub(projectId: string) {
  return fetchJSON<{
    connected: boolean;
    repo_name?: string;
    repo_url?: string;
    default_branch: string;
    current_branch: string;
    latest_commit_hash?: string;
    pull_requests?: Array<{
      pr_id: string;
      source_branch: string;
      target_branch: string;
      status: string;
    }>;
  }>(`/api/v1/projects/${projectId}/github`);
}

// Agents
export async function fetchAgents() {
  return fetchJSON<
    Array<{
      role_number: number;
      name: string;
      role_title: string;
      category: string;
      description: string;
      capabilities: string[];
    }>
  >("/api/v1/agents");
}

// Governance & Approvals
export async function fetchProjectApprovals(projectId: string) {
  return fetchJSON<
    Array<{
      id: string;
      project_id: string;
      stage: number;
      action_type: string;
      description: string;
      status: string;
      notes?: string;
      created_at: string;
      decided_at?: string;
    }>
  >(`/api/v1/projects/${projectId}/approvals`);
}

export async function respondApproval(approvalId: string, decision: "approved" | "rejected", notes?: string) {
  return fetchJSON<{ status: string; approval_id: string; decision: string }>(
    `/api/v1/approvals/${approvalId}/respond`,
    {
      method: "POST",
      body: JSON.stringify({ decision, notes }),
    }
  );
}

// Ecosystem Modules
export async function fetchMetaStatus() {
  return fetchJSON<{
    configured: boolean;
    app_id: string;
    has_app_secret: boolean;
    accounts_connected: number;
    active_integrations: any[];
    supported_products: Array<{
      product: string;
      status: string;
      permissions: string[];
    }>;
  }>("/api/v1/meta/status");
}

export async function fetchIntegrations() {
  return fetchJSON<
    Array<{
      id: string;
      project_id: string;
      provider: string;
      integration_type: string;
      is_active: boolean;
      config: any;
    }>
  >("/api/v1/integrations");
}

export async function fetchSecurityFindings() {
  return fetchJSON<
    Array<{
      id: string;
      project_id: string;
      severity: string;
      title: string;
      description: string;
      tool: string;
      status: string;
      created_at: string;
    }>
  >("/api/v1/security/findings");
}

export async function fetchQAResults() {
  return fetchJSON<
    Array<{
      id: string;
      project_id: string;
      test_suite: string;
      total_tests: number;
      passed_tests: number;
      failed_tests: number;
      evidence_path?: string;
      executed_at: string;
    }>
  >("/api/v1/qa/results");
}

export async function fetchDeployments() {
  return fetchJSON<
    Array<{
      id: string;
      project_id: string;
      environment: string;
      status: string;
      commit_sha?: string;
      endpoint_url?: string;
      deployed_at: string;
    }>
  >("/api/v1/deployments");
}

export async function fetchCosts() {
  return fetchJSON<{
    total_usd: number;
    by_category: Record<string, number>;
    records: Array<{
      id: string;
      project_id: string;
      category: string;
      amount_usd: number;
      details: any;
      recorded_at: string;
    }>;
  }>("/api/v1/costs");
}

export async function fetchDatabaseStatus() {
  return fetchJSON<{
    engine: string;
    connection: string;
    tables: Record<string, number>;
  }>("/api/v1/database/status");
}

export async function fetchAuditLogs(projectId?: string) {
  const query = projectId ? `?project_id=${projectId}` : "";
  return fetchJSON<
    Array<{
      id: string;
      project_id: string;
      action: string;
      actor: string;
      details_json: any;
      created_at: string;
    }>
  >(`/api/v1/audit-logs${query}`);
}


// ==========================================
// Social Platform Developer Automation APIs
// ==========================================

export async function fetchSocialMetaStatus() {
  return fetchJSON<{
    app_id: string;
    app_type: string;
    status: string;
    webhook_url: string;
    verify_token_configured: boolean;
    privacy_policy_url: string;
    data_deletion_url: string;
    redirect_uris: string[];
    enabled_products: string[];
    permissions_tracked: string[];
    app_review_readiness: {
      is_ready: boolean;
      issues: string[];
    };
    connection_test?: {
      success: boolean;
      latency_ms: number;
      error?: string;
    };
  }>("/api/v1/social/meta/status");
}

export async function testSocialMetaConnection() {
  return fetchJSON<{
    success: boolean;
    platform: string;
    app_id?: string;
    latency_ms: number;
    error?: string;
  }>("/api/v1/social/meta/test-connection", {
    method: "POST",
  });
}

export async function submitAppReview(payload: {
  submission_type: string;
  requested_permissions: string[];
  submission_notes?: string;
}) {
  return fetchJSON<{
    review_id: string;
    app_id: string;
    status: string;
    submitted_at: string;
    notes?: string;
  }>("/api/v1/social/meta/app-review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchSocialConnections(tenantId?: string) {
  const query = tenantId ? `?tenant_id=${tenantId}` : "";
  return fetchJSON<
    Array<{
      id: string;
      tenant_id?: string;
      platform: string;
      account_type?: string;
      account_name?: string;
      scopes?: string[];
      is_active: boolean;
      status: string;
      rate_limit_remaining?: number;
      last_refreshed_at?: string;
      expires_at?: string;
    }>
  >(`/api/v1/social/connections${query}`);
}

export async function fetchSocialLogs(limit: number = 20) {
  return fetchJSON<
    Array<{
      id: string;
      platform: string;
      endpoint: string;
      method: string;
      status_code: number;
      latency_ms: number;
      success: boolean;
      error_message?: string;
      timestamp: string;
    }>
  >(`/api/v1/social/logs?limit=${limit}`);
}

export async function fetchXPricing() {
  return fetchJSON<Record<string, {
    monthly_cost_usd: number;
    read_limit_monthly: number;
    write_limit_monthly: number;
    description: string;
    endpoints_included: string[];
  }>>("/api/v1/social/x/pricing");
}

export async function initiateSocialOAuth(platform: string, tenantId?: string, redirectUri?: string) {
  return fetchJSON<{
    authorization_url: string;
    state: string;
    code_verifier?: string;
    platform: string;
  }>("/api/v1/social/oauth/authorize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      platform,
      tenant_id: tenantId || "factory_default",
      redirect_uri: redirectUri || "http://localhost:3000/auth/callback",
    }),
  });
}


// ==========================================
// Cloud Worker & Execution Engine APIs
// ==========================================

export async function fetchCloudStatus() {
  return fetchJSON<{
    infrastructure: {
      provider: string;
      cluster_name: string;
      region: string;
      s3_bucket: string;
      status: string;
    };
    workers: {
      total_registered: number;
      active: number;
      idle: number;
      busy: number;
      unhealthy: number;
      terminated: number;
    };
    jobs: {
      queued: number;
      running: number;
      paused: number;
      blocked_on_approval: number;
      completed: number;
      failed: number;
      cancelled: number;
      dead_letter_queue: number;
    };
    cost_governance: {
      default_project_budget_usd: number;
      vcpu_hourly_rate_usd: number;
      memory_gb_hourly_rate_usd: number;
    };
  }>("/api/v1/cloud/status");
}

export async function fetchCloudJobs(projectId?: string) {
  const query = projectId ? `?project_id=${projectId}` : "";
  return fetchJSON<
    Array<{
      id: string;
      project_id: string;
      job_type: string;
      status: string;
      priority: number;
      current_stage: number;
      target_stage: number;
      assigned_worker_id?: string;
      retry_count: number;
      error_message?: string;
      checkpoint_data?: any;
      created_at: string;
      updated_at: string;
    }>
  >(`/api/v1/cloud/jobs${query}`);
}

export async function fetchCloudWorkers() {
  return fetchJSON<
    Array<{
      id: string;
      worker_name: string;
      hostname: string;
      ip_address: string;
      status: string;
      cpu_cores: number;
      memory_mb: number;
      current_job_id?: string;
      last_heartbeat: string;
      total_jobs_completed: number;
    }>
  >("/api/v1/cloud/workers");
}

export async function submitCloudJob(projectId: string, targetStage: number = 23, priority: number = 5) {
  return fetchJSON<{
    job_id: string;
    project_id: string;
    status: string;
    current_stage: number;
    target_stage: number;
  }>("/api/v1/cloud/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, target_stage: targetStage, priority }),
  });
}

export async function pauseCloudJob(jobId: string) {
  return fetchJSON<{ job_id: string; status: string }>(`/api/v1/cloud/jobs/${jobId}/pause`, {
    method: "POST",
  });
}

export async function resumeCloudJob(jobId: string) {
  return fetchJSON<{ job_id: string; status: string }>(`/api/v1/cloud/jobs/${jobId}/resume`, {
    method: "POST",
  });
}

export async function cancelCloudJob(jobId: string) {
  return fetchJSON<{ job_id: string; status: string }>(`/api/v1/cloud/jobs/${jobId}/cancel`, {
    method: "POST",
  });
}

export async function retryCloudJob(jobId: string) {
  return fetchJSON<{ job_id: string; status: string; retries_reset: boolean }>(`/api/v1/cloud/jobs/${jobId}/retry`, {
    method: "POST",
  });
}

export async function triggerCloudRecovery() {
  return fetchJSON<{
    status: string;
    recovered_jobs_count: number;
    unhealthy_workers_count: number;
  }>("/api/v1/cloud/recovery", {
    method: "POST",
  });
}


// ==========================================
// Deployment & Release Management APIs
// ==========================================

export async function fetchDeploymentOverviewStatus() {
  return fetchJSON<{
    summary: {
      total_deployments: number;
      total_releases: number;
      total_build_artifacts: number;
      total_rollbacks: number;
    };
    environments: Array<{
      name: string;
      status: string;
      type: string;
      url: string;
    }>;
    cost_estimate: {
      monthly_total_usd: number;
      breakdown: Record<string, number>;
      currency: string;
      tier: string;
    };
    supported_strategies: string[];
  }>("/api/v1/deployment/status");
}

export async function fetchDeploymentAnalysis(projectId: string) {
  return fetchJSON<{
    app_type: string;
    frontend_framework?: string;
    backend_framework?: string;
    primary_language: string;
    database_required?: string;
    cache_required?: string;
    container_required: boolean;
    target_architecture: string;
    recommended_strategy: string;
    scaling_tier: string;
    estimated_monthly_cost_usd: number;
    env_vars_required: string[];
    secrets_required: string[];
    rationale: string;
  }>(`/api/v1/deployment/analysis/${projectId}`);
}

export async function fetchBuildArtifacts(projectId: string) {
  return fetchJSON<
    Array<{
      id: string;
      version: string;
      build_id: string;
      commit_sha: string;
      image_tag?: string;
      sha256: string;
      size_bytes: number;
      status: string;
      security_scan: any;
      created_at: string;
    }>
  >(`/api/v1/deployment/artifacts/${projectId}`);
}

export async function fetchDeploymentReleases(projectId: string) {
  return fetchJSON<
    Array<{
      id: string;
      version: string;
      environment: string;
      strategy: string;
      status: string;
      is_current: boolean;
      endpoint_url?: string;
      commit_sha: string;
      created_at: string;
      deployed_at?: string;
    }>
  >(`/api/v1/deployment/releases/${projectId}`);
}

export async function fetchDatabaseMigrations(projectId: string) {
  return fetchJSON<
    Array<{
      id: string;
      version_num: string;
      description: string;
      script_name: string;
      is_destructive: boolean;
      backup_checkpoint?: string;
      status: string;
      created_at: string;
      executed_at?: string;
    }>
  >(`/api/v1/deployment/migrations/${projectId}`);
}

export async function fetchEnvironmentConfigs(projectId: string) {
  return fetchJSON<
    Array<{
      environment: string;
      config_data: Record<string, any>;
      secret_references: Record<string, string>;
      cpu_limits: string;
      memory_limits: string;
      min_replicas: number;
      max_replicas: number;
    }>
  >(`/api/v1/deployment/environments/${projectId}`);
}

export async function triggerDeploymentBuild(payload: {
  project_id: string;
  version: string;
  commit_sha?: string;
  artifact_type?: string;
}) {
  return fetchJSON<{
    artifact_id: string;
    build_id: string;
    version: string;
    image_tag: string;
    status: string;
    security_gate_passed: boolean;
  }>("/api/v1/deployment/build", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deployRelease(releaseId: string, simulateHealthy: boolean = true, approved: boolean = false) {
  return fetchJSON<{
    success: boolean;
    status: string;
    release_id?: string;
    version?: string;
    environment?: string;
    smoke_tests?: any;
    rollback?: any;
    reason?: string;
  }>(`/api/v1/deployment/release/${releaseId}/deploy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ simulate_healthy: simulateHealthy, approved }),
  });
}

export async function triggerRollback(payload: {
  project_id: string;
  current_release_id: string;
  reason: string;
}) {
  return fetchJSON<{
    success: boolean;
    rollback_id: string;
    from_version: string;
    to_version: string;
    environment: string;
    reason: string;
  }>("/api/v1/deployment/rollback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Phase 7: Observability, AIOps & Self-Healing APIs
// ---------------------------------------------------------------------------
export async function fetchTelemetryMetrics(projectId?: string, metricName?: string) {
  const params = new URLSearchParams();
  if (projectId) params.append("project_id", projectId);
  if (metricName) params.append("metric_name", metricName);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return fetchJSON<Array<{
    id: string;
    project_id: string;
    metric_name: string;
    metric_value: number;
    unit: string;
    dimensions: any;
    timestamp: string;
  }>>(`/api/v1/observability/metrics${qs}`);
}

export async function ingestMetric(payload: {
  project_id: string;
  metric_name: string;
  metric_value: number;
  unit?: string;
  dimensions?: any;
}) {
  return fetchJSON<{ status: string; records_flushed: number }>("/api/v1/observability/metrics", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function runAppProbe(payload: {
  project_id: string;
  endpoint_url?: string;
  timeout_seconds?: number;
}) {
  return fetchJSON<{
    status: string;
    status_code: number;
    latency_ms: number;
    is_healthy: boolean;
    error_message?: string;
  }>("/api/v1/observability/probe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function sampleInfra(payload: { project_id: string }) {
  return fetchJSON<{
    status: string;
    metrics_count: number;
    metrics: Array<{ metric_name: string; value: number; unit: string }>;
  }>("/api/v1/observability/sample-infra", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchAlerts(projectId?: string, status?: string) {
  const params = new URLSearchParams();
  if (projectId) params.append("project_id", projectId);
  if (status) params.append("status", status);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return fetchJSON<Array<{
    id: string;
    rule_id: string;
    project_id: string;
    title: string;
    severity: string;
    metric_value: number;
    threshold: number;
    status: string;
    fingerprint: string;
    context_json: any;
    triggered_at: string;
    resolved_at?: string;
  }>>(`/api/v1/observability/alerts${qs}`);
}

export async function fetchAlertRules(projectId?: string) {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return fetchJSON<Array<{
    id: string;
    project_id: string;
    name: string;
    metric_name: string;
    condition: string;
    threshold: number;
    duration_seconds: number;
    severity: string;
    is_enabled: boolean;
    notification_channels: string[];
  }>>(`/api/v1/observability/alerts/rules${qs}`);
}

export async function createAlertRule(payload: {
  project_id: string;
  name: string;
  metric_name: string;
  condition?: string;
  threshold: number;
  duration_seconds?: number;
  severity?: string;
  notification_channels?: string[];
}) {
  return fetchJSON<{ id: string; name: string; metric_name: string }>("/api/v1/observability/alerts/rules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchIncidents(projectId?: string) {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return fetchJSON<Array<{
    id: string;
    project_id: string;
    title: string;
    environment: string;
    severity: string;
    status: string;
    affected_service: string;
    impact_summary: string;
    lead_alert_id?: string;
    trace_id?: string;
    detected_at: string;
    acknowledged_at?: string;
    resolved_at?: string;
  }>>(`/api/v1/observability/incidents${qs}`);
}

export async function fetchIncidentDetails(incidentId: string) {
  return fetchJSON<{
    incident: {
      id: string;
      project_id: string;
      title: string;
      environment: string;
      severity: string;
      status: string;
      affected_service: string;
      impact_summary: string;
      trace_id?: string;
      detected_at: string;
      acknowledged_at?: string;
      resolved_at?: string;
    };
    rca?: {
      id: string;
      probable_root_cause: string;
      confidence_score: number;
      supporting_evidence: any;
      alternative_explanations: string[];
      recommended_action: string;
      healing_tier: number;
      risk_assessment: string;
      generated_at: string;
    };
    actions: Array<{
      id: string;
      action_type: string;
      tier: number;
      status: string;
      duration_ms: number;
      execution_log: string;
      created_at: string;
    }>;
  }>(`/api/v1/observability/incidents/${incidentId}`);
}

export async function triggerIncidentRCA(incidentId: string) {
  return fetchJSON<{
    incident_id: string;
    probable_root_cause: string;
    confidence_score: number;
    recommended_action: string;
    healing_tier: number;
    risk_assessment: string;
    supporting_evidence: any;
  }>(`/api/v1/observability/incidents/${incidentId}/rca`, {
    method: "POST",
  });
}

export async function transitionIncident(incidentId: string, payload: { new_status: string; notes?: string }) {
  return fetchJSON<{ id: string; status: string }>(`/api/v1/observability/incidents/${incidentId}/transition`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function executeSelfHealing(payload: {
  project_id: string;
  action_type: string;
  parameters?: any;
  incident_id?: string;
  force_approved?: boolean;
}) {
  return fetchJSON<{
    id: string;
    action_type: string;
    tier: number;
    status: string;
    approval_id?: string;
    duration_ms: number;
    execution_log: string;
  }>("/api/v1/observability/self-healing/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchSelfHealingActions(projectId?: string) {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return fetchJSON<Array<{
    id: string;
    project_id: string;
    incident_id?: string;
    action_type: string;
    tier: number;
    status: string;
    approval_id?: string;
    duration_ms: number;
    execution_log: string;
    created_at: string;
  }>>(`/api/v1/observability/self-healing/actions${qs}`);
}

export async function fetchSLOs(projectId: string) {
  return fetchJSON<Array<{
    id: string;
    name: string;
    target_percentage: number;
    evaluation_window_days: number;
    current_sli: number;
    error_budget_remaining_percent: number;
    status: string;
    updated_at: string;
  }>>(`/api/v1/observability/slo?project_id=${projectId}`);
}

export async function configureSLO(payload: {
  project_id: string;
  name: string;
  target_percentage?: number;
  evaluation_window_days?: number;
}) {
  return fetchJSON<{
    id: string;
    name: string;
    target_percentage: number;
    status: string;
  }>("/api/v1/observability/slo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchReliabilityMetrics(projectId?: string) {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return fetchJSON<{
    total_incidents: number;
    resolved_incidents: number;
    mttd_minutes: number;
    mtta_minutes: number;
    mttr_minutes: number;
  }>(`/api/v1/observability/reliability/metrics${qs}`);
}

export async function fetchFinOpsCosts(projectId?: string) {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return fetchJSON<{
    total_spend_usd: number;
    breakdown: {
      llm_tokens: number;
      cloud_infra: number;
      third_party_api: number;
    };
    monthly_projected_usd: number;
    currency: string;
  }>(`/api/v1/observability/finops/costs${qs}`);
}

export async function fetchFinOpsRecommendations(projectId?: string) {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return fetchJSON<Array<{
    title: string;
    severity: string;
    monthly_savings_usd: number;
    action: string;
  }>>(`/api/v1/observability/finops/recommendations${qs}`);
}

// ---------------------------------------------------------------------------
// Phase 8: Autonomous Maintenance & Continuous Improvement APIs
// ---------------------------------------------------------------------------
export async function fetchMaintenancePolicy(projectId: string) {
  return fetchJSON<{
    id: string;
    project_id: string;
    schedule: string;
    is_enabled: boolean;
    auto_remediate_level1: boolean;
    require_approval_level2: boolean;
    maintenance_window: string;
  }>(`/api/v1/maintenance/policy?project_id=${projectId}`);
}

export async function configureMaintenancePolicy(payload: {
  project_id: string;
  schedule?: string;
  is_enabled?: boolean;
  auto_remediate_level1?: boolean;
  require_approval_level2?: boolean;
  maintenance_window?: string;
}) {
  return fetchJSON<{ id: string; status: string; schedule: string }>("/api/v1/maintenance/policy", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchMaintenanceTasks(projectId?: string, status?: string) {
  const params = new URLSearchParams();
  if (projectId) params.append("project_id", projectId);
  if (status) params.append("status", status);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return fetchJSON<Array<{
    id: string;
    project_id: string;
    maintenance_type: string;
    trigger_type: string;
    priority: string;
    assigned_agents: number[];
    status: string;
    git_branch: string;
    created_at: string;
    completed_at?: string;
  }>>(`/api/v1/maintenance/tasks${qs}`);
}

export async function scheduleMaintenanceTask(payload: {
  project_id: string;
  maintenance_type: string;
  trigger_type?: string;
  priority?: string;
}) {
  return fetchJSON<{
    id: string;
    maintenance_type: string;
    status: string;
    git_branch: string;
  }>("/api/v1/maintenance/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchLatestQualityReport(projectId: string) {
  return fetchJSON<{
    id: string;
    quality_score: number;
    maintainability_rating: string;
    complexity_score: number;
    duplication_percent: number;
    test_coverage_percent: number;
    issues_breakdown: Record<string, number>;
    recommendations: Array<{
      priority: string;
      category: string;
      rule: string;
      message: string;
      file: string;
      remediation: string;
    }>;
  }>(`/api/v1/maintenance/quality/latest?project_id=${projectId}`);
}

export async function runQualityScan(projectId: string) {
  return fetchJSON<{
    id: string;
    quality_score: number;
    maintainability_rating: string;
    test_coverage_percent: number;
    issues_breakdown: Record<string, number>;
    recommendations: any[];
  }>("/api/v1/maintenance/quality/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId }),
  });
}

export async function fetchDependencyVulnerabilities(projectId: string) {
  return fetchJSON<Array<{
    id: string;
    package_name: string;
    current_version: string;
    recommended_version: string;
    vulnerability_cve: string;
    severity: string;
    ecosystem: string;
    status: string;
  }>>(`/api/v1/maintenance/dependencies/scan?project_id=${projectId}`, {
    method: "POST",
  });
}

export async function upgradeDependency(payload: {
  project_id: string;
  package_name: string;
  target_version: string;
}) {
  return fetchJSON<{
    branch_name: string;
    pr_title: string;
    target_version: string;
    approval_id: string;
    status: string;
  }>("/api/v1/maintenance/dependencies/upgrade", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchMaintenanceSecurityFindings(projectId: string) {
  return fetchJSON<Array<{
    id: string;
    tool: string;
    category: string;
    severity: string;
    file: string;
    line: number;
    description: string;
    remediation: string;
  }>>(`/api/v1/maintenance/security/findings?project_id=${projectId}`);
}

export async function remediateSecurityFinding(payload: {
  project_id: string;
  finding_id: string;
  category: string;
  file_path: string;
  proposed_patch?: string;
}) {
  return fetchJSON<{
    finding_id: string;
    branch_name: string;
    pr_title: string;
    approval_id: string;
    status: string;
    security_tests_passed: boolean;
    regression_safe: boolean;
  }>("/api/v1/maintenance/security/remediate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchBugReports(projectId?: string, status?: string) {
  const params = new URLSearchParams();
  if (projectId) params.append("project_id", projectId);
  if (status) params.append("status", status);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return fetchJSON<Array<{
    id: string;
    project_id: string;
    title: string;
    description: string;
    status: string;
    git_branch?: string;
    pr_url?: string;
    test_evidence?: any;
    created_at: string;
  }>>(`/api/v1/maintenance/bugs${qs}`);
}

export async function triggerBugFix(bugId: string) {
  return fetchJSON<{
    bug_id: string;
    branch_name: string;
    pr_url: string;
    approval_id: string;
    status: string;
    test_evidence: any;
  }>(`/api/v1/maintenance/bugs/${bugId}/fix`, {
    method: "POST",
  });
}

export async function runRegressionSuite(payload: {
  project_id: string;
  changed_files?: string[];
  run_full_suite?: boolean;
}) {
  return fetchJSON<{
    project_id: string;
    status: string;
    is_passed: boolean;
    suites_executed: string[];
    total_tests: number;
    passed_tests: number;
    failed_tests: number;
    flaky_tests_filtered: number;
    details_by_suite: any;
    executed_at: string;
  }>("/api/v1/maintenance/regression/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchDatabaseHealth(projectId: string) {
  return fetchJSON<{
    project_id: string;
    engine: string;
    connection_pool: any;
    storage: any;
    backup_status: any;
    slow_queries_detected: any[];
    index_recommendations: any[];
  }>(`/api/v1/maintenance/database/health?project_id=${projectId}`);
}

export async function proposeDatabaseIndex(payload: {
  project_id: string;
  table_name: string;
  index_name: string;
  columns: string[];
}) {
  return fetchJSON<{
    index_name: string;
    sql: string;
    approval_id: string;
    status: string;
    is_destructive: boolean;
  }>("/api/v1/maintenance/database/optimize-index", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchPerformanceBottlenecks(projectId: string) {
  return fetchJSON<{
    project_id: string;
    avg_latency_ms: number;
    bottlenecks_detected: number;
    bottlenecks: any[];
  }>(`/api/v1/maintenance/performance/bottlenecks?project_id=${projectId}`);
}

export async function proposePerformanceOptimization(payload: {
  project_id: string;
  optimization_type: string;
  target_component: string;
}) {
  return fetchJSON<{
    branch_name: string;
    approval_id: string;
    benchmark_evidence: any;
    status: string;
  }>("/api/v1/maintenance/performance/optimize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchTechnicalDebt(projectId: string) {
  return fetchJSON<{
    project_id: string;
    technical_debt_score: number;
    health_grade: string;
    total_debt_hours: number;
    open_items_count: number;
    items: Array<{
      id: string;
      title: string;
      category: string;
      severity: string;
      debt_score_impact: number;
      effort_hours: number;
      remediation_plan: string;
      status: string;
    }>;
  }>(`/api/v1/maintenance/tech-debt?project_id=${projectId}`);
}

export async function syncDocumentation(payload: {
  project_id: string;
  commit_sha?: string;
}) {
  return fetchJSON<{
    project_id: string;
    commit_sha?: string;
    status: string;
    secret_leak_check: string;
    updated_documents: any[];
    last_audited_at: string;
  }>("/api/v1/maintenance/docs/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchImprovementProposals(projectId: string) {
  return fetchJSON<Array<{
    id: string;
    title: string;
    category: string;
    problem_statement: string;
    supporting_evidence: any;
    expected_benefit: string;
    implementation_complexity: string;
    potential_risk: string;
    estimated_cost_usd: number;
    status: string;
    created_at: string;
  }>>(`/api/v1/maintenance/improvements?project_id=${projectId}`);
}

export async function generateImprovementProposals(projectId: string) {
  return fetchJSON<Array<{
    id: string;
    title: string;
    category: string;
    expected_benefit: string;
    status: string;
  }>>(`/api/v1/maintenance/improvements/generate?project_id=${projectId}`, {
    method: "POST",
  });
}
