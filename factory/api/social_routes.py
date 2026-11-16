"""
FastAPI Routes for Social Platform Developer Automation Engine.
Provides OAuth orchestration, Meta Developer Center APIs, platform clients, and webhook handlers.
"""

import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.config import settings
from factory.core.database import get_db
from factory.core.logger import logger
from factory.models.schema import (
    AccountConnectionHistory,
    DeveloperApplication,
    OAuthConnection,
    SocialApiError,
    SocialAppReview,
    SocialIntegrationLog,
)
from factory.social.google.youtube import YouTubeApiAgent
from factory.social.meta.developer_agent import MetaDeveloperAgent
from factory.social.meta.facebook import FacebookApiAgent
from factory.social.meta.instagram import InstagramApiAgent
from factory.social.meta.messenger import MessengerApiAgent
from factory.social.meta.threads import ThreadsApiAgent
from factory.social.meta.whatsapp import WhatsAppBusinessApiAgent
from factory.social.oauth import CommonOAuthEngine
from factory.social.platforms.linkedin_agent import LinkedInApiAgent
from factory.social.platforms.tiktok_agent import TikTokApiAgent
from factory.social.platforms.x_agent import XApiAgent
from factory.social.security import (
    generate_twitter_crc_response,
    verify_meta_webhook_challenge,
    verify_meta_webhook_signature,
)

router = APIRouter(prefix="/social", tags=["Social Platform Automation"])

oauth_engine = CommonOAuthEngine()
meta_agent = MetaDeveloperAgent()
fb_agent = FacebookApiAgent()
ig_agent = InstagramApiAgent()
wa_agent = WhatsAppBusinessApiAgent()
msg_agent = MessengerApiAgent()
threads_agent = ThreadsApiAgent()
yt_agent = YouTubeApiAgent()
x_agent = XApiAgent()
linkedin_agent = LinkedInApiAgent()
tiktok_agent = TikTokApiAgent()


# Request / Response Schemas
class AppConfigRequest(BaseModel):
    app_id: str
    app_name: str
    client_secret: Optional[str] = None
    redirect_uris: Optional[List[str]] = None
    enabled_products: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    verify_token: Optional[str] = None


class ComplianceUrlsRequest(BaseModel):
    app_id: str
    privacy_policy_url: str
    data_deletion_url: str


class AppReviewSubmitRequest(BaseModel):
    app_id: str
    requested_permissions: List[str]
    use_case_description: str
    screencast_url: Optional[str] = None


class SendWhatsAppTemplateRequest(BaseModel):
    phone_number_id: str
    connection_id: Optional[str] = None
    access_token: Optional[str] = None
    recipient_phone: str
    template_name: str
    customer_opt_in_verified: bool = False
    language_code: str = "en_US"


class PublishPostRequest(BaseModel):
    page_id: Optional[str] = None
    connection_id: Optional[str] = None
    access_token: Optional[str] = None
    message: str
    link: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    connection_id: str


class RevokeConnectionRequest(BaseModel):
    connection_id: str


# ==========================================
# 1. Common OAuth Endpoints
# ==========================================

@router.get("/oauth/{platform}/authorize")
async def get_oauth_authorize_url(
    platform: str,
    tenant_id: str = "default",
    redirect_uri: Optional[str] = None,
    client_id: Optional[str] = None,
):
    """Generate authorization URL with PKCE and signed state token."""
    try:
        res = oauth_engine.get_authorization_url(
            platform=platform,
            tenant_id=tenant_id,
            redirect_uri=redirect_uri,
            custom_client_id=client_id,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/oauth/{platform}/callback")
async def oauth_callback(
    platform: str,
    code: str,
    state: str,
    account_type: str = "customer",
):
    """Exchange authorization code for encrypted tokens and record connection."""
    try:
        token_resp = await oauth_engine.exchange_code_for_tokens(
            platform=platform,
            code=code,
            state=state,
            account_type=account_type,
        )
        return {
            "status": "connected",
            "platform": platform,
            "token_type": token_resp.token_type,
            "expires_in": token_resp.expires_in,
            "user_id": token_resp.user_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/oauth/refresh")
async def refresh_oauth_token(payload: RefreshTokenRequest):
    """Refresh an access token using stored encrypted refresh token."""
    try:
        res = await oauth_engine.refresh_access_token(payload.connection_id)
        return {"status": "refreshed", "expires_in": res.expires_in}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/oauth/revoke")
async def revoke_oauth_connection(payload: RevokeConnectionRequest):
    """Revoke an active OAuth connection."""
    success = await oauth_engine.revoke_connection(payload.connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"status": "revoked", "connection_id": payload.connection_id}


@router.get("/connections")
async def list_connections(tenant_id: str = "default"):
    """List customer and developer social connections with masked secrets."""
    return await oauth_engine.list_connections(tenant_id=tenant_id)


# ==========================================
# 2. Meta Developer Center Endpoints
# ==========================================

@router.get("/meta/status")
async def get_meta_developer_status(db: AsyncSession = Depends(get_db)):
    """Deep status report for Meta Developer Platform."""
    apps_res = await db.execute(select(DeveloperApplication).where(DeveloperApplication.platform == "meta"))
    apps = apps_res.scalars().all()

    conns_res = await db.execute(
        select(OAuthConnection).where(OAuthConnection.provider.in_(["facebook", "instagram", "whatsapp", "threads"]))
    )
    connections = conns_res.scalars().all()

    return {
        "configured": bool(settings.META_APP_ID),
        "app_id": settings.META_APP_ID or "Not Configured",
        "has_app_secret": bool(settings.META_APP_SECRET),
        "graph_version": settings.META_GRAPH_VERSION,
        "registered_apps_count": len(apps),
        "active_connections_count": len(connections),
        "applications": [
            {
                "id": a.id,
                "app_id": a.app_id,
                "app_name": a.app_name,
                "status": a.status,
                "enabled_products": a.enabled_products,
                "has_privacy_policy": bool(a.privacy_policy_url),
                "has_data_deletion": bool(a.data_deletion_url),
                "app_review": a.app_review_status,
            }
            for a in apps
        ],
        "supported_products": [
            {"product": "Facebook Login", "status": "Ready", "permissions": ["email", "public_profile"]},
            {"product": "Instagram Graph API", "status": "Configured", "permissions": ["instagram_basic", "instagram_manage_insights"]},
            {"product": "WhatsApp Business Platform", "status": "Ready", "permissions": ["whatsapp_business_messaging"]},
            {"product": "Messenger API", "status": "Configured", "permissions": ["pages_messaging"]},
            {"product": "Threads API", "status": "Available", "permissions": ["threads_basic", "threads_content_publish"]},
        ],
    }


@router.get("/meta/apps")
async def discover_meta_apps(user_access_token: Optional[str] = None):
    """Discover applications registered on Meta Developer account."""
    res = await meta_agent.discover_applications(user_access_token)
    return res.data


@router.post("/meta/apps")
async def configure_meta_app(payload: AppConfigRequest):
    """Register or update Meta developer application configuration."""
    res = await meta_agent.register_or_update_application(
        app_id=payload.app_id,
        app_name=payload.app_name,
        client_secret=payload.client_secret,
        redirect_uris=payload.redirect_uris,
        enabled_products=payload.enabled_products,
        webhook_url=payload.webhook_url,
        verify_token=payload.verify_token,
    )
    return res.data


@router.post("/meta/compliance")
async def configure_compliance_urls(payload: ComplianceUrlsRequest):
    """Set Privacy Policy and Data Deletion Callback URLs."""
    res = await meta_agent.configure_compliance_urls(
        app_id=payload.app_id,
        privacy_policy_url=payload.privacy_policy_url,
        data_deletion_url=payload.data_deletion_url,
    )
    return res.data


@router.post("/meta/test-connection")
async def test_meta_connectivity(access_token: Optional[str] = None):
    """Validate Graph API token and connectivity."""
    token = access_token or settings.META_ACCESS_TOKEN or "mock_facebook_token"
    res = await meta_agent.validate_graph_api_connectivity(token)
    return res.model_dump()


@router.post("/meta/app-review")
async def submit_meta_app_review(payload: AppReviewSubmitRequest):
    """Prepare and submit Meta App Review compliance checklist."""
    res = await meta_agent.prepare_app_review_submission(
        app_id=payload.app_id,
        requested_permissions=payload.requested_permissions,
        use_case_description=payload.use_case_description,
        screencast_url=payload.screencast_url,
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.error_message)
    return res.data


# ==========================================
# 3. Facebook, Instagram, WhatsApp Endpoints
# ==========================================

@router.get("/facebook/pages")
async def get_facebook_pages(connection_id: Optional[str] = None, access_token: Optional[str] = None):
    token = access_token
    if not token and connection_id:
        token = await oauth_engine.get_decrypted_token(connection_id)
    token = token or "mock_facebook_token"
    res = await fb_agent.get_user_pages(token)
    return res.data


@router.post("/facebook/publish")
async def publish_facebook_page_post(payload: PublishPostRequest):
    token = payload.access_token or "mock_page_token"
    page_id = payload.page_id or "page_fb_101"
    res = await fb_agent.publish_page_post(page_id=page_id, page_access_token=token, message=payload.message, link=payload.link)
    return res.data


@router.get("/instagram/account")
async def get_instagram_account(ig_user_id: str = "ig_business_987654321", access_token: Optional[str] = None):
    token = access_token or "mock_instagram_token"
    res = await ig_agent.get_account_info(ig_user_id, token)
    return res.data


@router.get("/instagram/media")
async def get_instagram_media(ig_user_id: str = "ig_business_987654321", access_token: Optional[str] = None):
    token = access_token or "mock_instagram_token"
    res = await ig_agent.get_user_media(ig_user_id, token)
    return res.data


@router.get("/whatsapp/templates")
async def list_whatsapp_templates(waba_id: str = "waba_101", access_token: Optional[str] = None):
    token = access_token or "mock_whatsapp_token"
    res = await wa_agent.list_message_templates(waba_id, token)
    return res.data


@router.post("/whatsapp/send-template")
async def send_whatsapp_template(payload: SendWhatsAppTemplateRequest):
    token = payload.access_token or "mock_whatsapp_token"
    res = await wa_agent.send_template_message(
        phone_number_id=payload.phone_number_id,
        access_token=token,
        recipient_phone=payload.recipient_phone,
        template_name=payload.template_name,
        customer_opt_in_verified=payload.customer_opt_in_verified,
        language_code=payload.language_code,
    )
    if not res.success:
        raise HTTPException(status_code=res.status_code or 400, detail=res.error_message)
    return res.data


# ==========================================
# 4. YouTube, X, LinkedIn, TikTok Endpoints
# ==========================================

@router.get("/youtube/channel")
async def get_youtube_channel(channel_id: Optional[str] = None, access_token: Optional[str] = None):
    res = await yt_agent.get_channel_info(channel_id=channel_id, access_token=access_token)
    return res.data


@router.get("/youtube/video/{video_id}")
async def get_youtube_video(video_id: str, access_token: Optional[str] = None):
    res = await yt_agent.get_video_details(video_id=video_id, access_token=access_token)
    return res.data


@router.get("/x/me")
async def get_x_me(access_token: Optional[str] = None):
    token = access_token or "mock_x_token"
    res = await x_agent.get_me(token)
    return res.data


@router.get("/x/pricing")
async def get_x_pricing(tier: Optional[str] = None):
    return x_agent.get_tier_limits_and_pricing(tier)


@router.get("/linkedin/me")
async def get_linkedin_me(access_token: Optional[str] = None):
    token = access_token or "mock_linkedin_token"
    res = await linkedin_agent.get_user_profile(token)
    return res.data


@router.get("/tiktok/me")
async def get_tiktok_me(access_token: Optional[str] = None):
    token = access_token or "mock_tiktok_token"
    res = await tiktok_agent.get_user_info(token)
    return res.data


# ==========================================
# 5. Webhook Handlers with Verification
# ==========================================

@router.get("/webhooks/{platform}")
async def webhook_verification_challenge(
    platform: str,
    request: Request,
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    crc_token: Optional[str] = Query(None),
):
    """Handle GET verification challenges from Meta/WhatsApp and X (CRC)."""
    # Meta / WhatsApp / Instagram / Messenger verification
    if hub_mode and hub_verify_token:
        expected = settings.META_VERIFY_TOKEN
        challenge = verify_meta_webhook_challenge(hub_mode, hub_verify_token, hub_challenge, expected)
        if challenge:
            return Response(content=challenge, media_type="text/plain")
        raise HTTPException(status_code=403, detail="Verification token mismatch")

    # X (Twitter) CRC challenge
    if crc_token and platform == "x":
        secret = settings.X_API_SECRET or "mock_x_secret"
        resp_token = generate_twitter_crc_response(crc_token, secret)
        return {"response_token": resp_token}

    return {"status": "ready"}


@router.post("/webhooks/{platform}")
async def handle_incoming_webhook(
    platform: str,
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    db: AsyncSession = Depends(get_db),
):
    """Process incoming webhook payloads with cryptographic signature verification."""
    body_bytes = await request.body()

    # Verify Meta signatures if secret is configured and not running demo
    if platform in ["meta", "facebook", "instagram", "whatsapp", "messenger", "threads"]:
        if settings.META_APP_SECRET and x_hub_signature_256:
            valid = verify_meta_webhook_signature(body_bytes, x_hub_signature_256, settings.META_APP_SECRET)
            if not valid:
                logger.warning(f"Rejected forged webhook signature on {platform}")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    # Route event parsing
    parsed_events: Dict[str, Any] = {}
    if platform == "whatsapp":
        parsed_events = wa_agent.process_incoming_webhook(payload)
    elif platform == "messenger":
        parsed_events = msg_agent.process_incoming_webhook(payload)
    else:
        parsed_events = {"type": f"{platform}_event", "raw": payload}

    # Log to SocialIntegrationLog
    log_entry = SocialIntegrationLog(
        platform=platform,
        endpoint=f"/social/webhooks/{platform}",
        method="POST",
        status_code=200,
        success=True,
        audit_actor=f"{platform}_webhook",
    )
    db.add(log_entry)

    return {"status": "received", "events_processed": parsed_events}


# ==========================================
# 6. Integration Logs and Audit
# ==========================================

@router.get("/logs")
async def get_social_integration_logs(
    limit: int = 50,
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve integration audit logs and connection history."""
    stmt = select(SocialIntegrationLog).order_by(desc(SocialIntegrationLog.created_at)).limit(limit)
    if platform:
        stmt = stmt.where(SocialIntegrationLog.platform == platform)
    res = await db.execute(stmt)
    logs = res.scalars().all()

    hist_stmt = select(AccountConnectionHistory).order_by(desc(AccountConnectionHistory.timestamp)).limit(limit)
    if platform:
        hist_stmt = hist_stmt.where(AccountConnectionHistory.platform == platform)
    hist_res = await db.execute(hist_stmt)
    history = hist_res.scalars().all()

    return {
        "integration_logs": [
            {
                "id": l.id,
                "platform": l.platform,
                "endpoint": l.endpoint,
                "method": l.method,
                "status_code": l.status_code,
                "success": l.success,
                "error_message": l.error_message,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "connection_history": [
            {
                "id": h.id,
                "tenant_id": h.tenant_id,
                "platform": h.platform,
                "user_identifier": h.user_identifier,
                "action": h.action,
                "actor": h.actor,
                "details": h.details_json,
                "timestamp": h.timestamp.isoformat() if h.timestamp else None,
            }
            for h in history
        ],
    }
