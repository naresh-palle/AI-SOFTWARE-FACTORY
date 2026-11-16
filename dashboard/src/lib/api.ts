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
