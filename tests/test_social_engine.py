"""
Comprehensive Test Suite for Social Platform Developer Automation Engine.
Tests OAuth flows, PKCE, state validation, token encryption, Meta Developer Agent,
Facebook, Instagram, WhatsApp, Messenger, Threads, YouTube, X, LinkedIn, TikTok, and Webhook verification.
"""

import time
import pytest
from factory.core.database import init_db
from factory.core.security import decrypt_secret, encrypt_secret
from factory.social.google.youtube import YouTubeApiAgent, YouTubeQuotaTracker
from factory.social.meta.developer_agent import MetaDeveloperAgent
from factory.social.meta.facebook import FacebookApiAgent
from factory.social.meta.instagram import InstagramApiAgent
from factory.social.meta.messenger import MessengerApiAgent
from factory.social.meta.threads import ThreadsApiAgent
from factory.social.meta.whatsapp import WhatsAppBusinessApiAgent
from factory.social.oauth import CommonOAuthEngine, generate_pkce_pair, generate_state, verify_state
from factory.social.platforms.linkedin_agent import LinkedInApiAgent
from factory.social.platforms.tiktok_agent import TikTokApiAgent
from factory.social.platforms.x_agent import XApiAgent
from factory.social.security import (
    generate_twitter_crc_response,
    sanitize_payload,
    verify_meta_webhook_challenge,
    verify_meta_webhook_signature,
)


@pytest.mark.asyncio
async def test_oauth_state_and_pkce():
    await init_db()
    # 1. State generation and verification
    state = generate_state(tenant_id="tenant_123", platform="facebook")
    assert state is not None
    verified_tenant = verify_state(state, expected_platform="facebook")
    assert verified_tenant == "tenant_123"

    # Verify tampering rejection
    tampered_state = state.replace("tenant_123", "tenant_hacker")
    assert verify_state(tampered_state, "facebook") is None

    # Verify wrong platform rejection
    assert verify_state(state, "google") is None

    # 2. PKCE generation
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) >= 43
    assert len(challenge) > 20
    assert "=" not in challenge  # Unpadded URL-safe base64


@pytest.mark.asyncio
async def test_oauth_engine_full_lifecycle():
    await init_db()
    engine = CommonOAuthEngine()

    # 1. Generate Auth URL for Google (requires PKCE)
    auth_data = engine.get_authorization_url(platform="google", tenant_id="tenant_alpha")
    assert "accounts.google.com" in auth_data["auth_url"]
    assert "code_challenge=" in auth_data["auth_url"]
    assert auth_data["pkce_enabled"] is True

    # 2. Exchange code for token
    token_resp = await engine.exchange_code_for_tokens(
        platform="google",
        code="auth_code_12345",
        state=auth_data["state"],
        account_type="customer",
    )
    assert token_resp.access_token is not None
    assert token_resp.refresh_token is not None

    # 3. List connections with masked secrets
    conns = await engine.list_connections(tenant_id="tenant_alpha")
    assert len(conns) >= 1
    target_conn = next(c for c in conns if c["platform"] == "google")
    assert target_conn["status"] == "active"
    assert "encrypted" not in target_conn  # Never leaks raw cipher or secret

    # 4. Decrypt token internally for agent usage
    decrypted_token = await engine.get_decrypted_token(target_conn["id"])
    assert decrypted_token == token_resp.access_token

    # 5. Refresh token
    refreshed = await engine.refresh_access_token(target_conn["id"])
    assert refreshed.access_token is not None

    # 6. Revoke connection
    revoked = await engine.revoke_connection(target_conn["id"])
    assert revoked is True
    conns_after = await engine.list_connections(tenant_id="tenant_alpha")
    revoked_conn = next(c for c in conns_after if c["id"] == target_conn["id"])
    assert revoked_conn["status"] == "revoked"


@pytest.mark.asyncio
async def test_meta_developer_agent():
    await init_db()
    agent = MetaDeveloperAgent()

    # 1. Register application
    app_id = "test_meta_app_999"
    reg_res = await agent.register_or_update_application(
        app_id=app_id,
        app_name="Acme Social App",
        client_secret="test_secret_123",
        redirect_uris=["https://example.com/callback"],
        enabled_products=["facebook_login", "instagram_graph", "whatsapp_business"],
    )
    assert reg_res.success is True
    assert reg_res.data["app_id"] == app_id

    # 2. Configure compliance URLs (Privacy Policy & Data Deletion)
    comp_res = await agent.configure_compliance_urls(
        app_id=app_id,
        privacy_policy_url="https://example.com/privacy",
        data_deletion_url="https://example.com/data-deletion",
    )
    assert comp_res.success is True

    # 3. Inspect application configuration
    inspect_res = await agent.inspect_application_configuration(app_id=app_id)
    assert inspect_res.success is True
    assert inspect_res.data["privacy_policy_url"] == "https://example.com/privacy"

    # 4. Prepare App Review Submission
    review_res = await agent.prepare_app_review_submission(
        app_id=app_id,
        requested_permissions=["pages_show_list", "instagram_basic"],
        use_case_description="Providing unified marketing analytics to creator clients.",
        screencast_url="https://example.com/screencast.mp4",
    )
    assert review_res.success is True
    assert review_res.data["status"] == "submitted"

    # 5. Validate Graph API Connectivity
    conn_res = await agent.validate_graph_api_connectivity("mock_facebook_token")
    assert conn_res.success is True
    assert conn_res.data["is_valid"] is True


@pytest.mark.asyncio
async def test_facebook_api_agent():
    agent = FacebookApiAgent()
    token = "mock_facebook_token"

    # Pages
    pages_res = await agent.get_user_pages(token)
    assert pages_res.success is True
    assert len(pages_res.data["pages"]) >= 1

    page_id = pages_res.data["pages"][0]["id"]
    page_token = pages_res.data["pages"][0]["access_token"]

    # Details
    det_res = await agent.get_page_details(page_id, page_token)
    assert det_res.success is True
    assert det_res.data["fan_count"] > 0

    # Publish
    pub_res = await agent.publish_page_post(page_id, page_token, "Hello from Autonomous Factory!")
    assert pub_res.success is True
    assert "post_id" in pub_res.data

    # Insights
    ins_res = await agent.get_page_insights(page_id, page_token)
    assert ins_res.success is True
    assert "page_impressions_last_28d" in ins_res.data["metrics"]

    # Permissions
    perm_res = await agent.validate_permissions(token, ["pages_show_list", "pages_read_engagement"])
    assert perm_res.success is True
    assert perm_res.data["all_granted"] is True


@pytest.mark.asyncio
async def test_instagram_api_agent():
    agent = InstagramApiAgent()
    token = "mock_instagram_token"
    ig_id = "ig_business_987654321"

    # Professional account info
    acc_res = await agent.get_account_info(ig_id, token)
    assert acc_res.success is True
    assert acc_res.data["followers_count"] > 0

    # Media retrieval
    media_res = await agent.get_user_media(ig_id, token)
    assert media_res.success is True
    assert len(media_res.data["media"]) >= 1

    # Two-step Content Publishing API
    pub_res = await agent.publish_photo(ig_id, token, "https://example.com/photo.jpg", "Autonomous post")
    assert pub_res.success is True
    assert "media_id" in pub_res.data

    # Insights
    ins_res = await agent.get_account_insights(ig_id, token)
    assert ins_res.success is True
    assert ins_res.data["metrics"]["reach_last_28d"] > 0


@pytest.mark.asyncio
async def test_whatsapp_business_agent():
    agent = WhatsAppBusinessApiAgent()
    token = "mock_whatsapp_token"

    # Phone numbers
    phone_res = await agent.get_business_phone_numbers("waba_101", token)
    assert phone_res.success is True
    assert len(phone_res.data["phone_numbers"]) >= 1

    # Templates
    tpl_res = await agent.list_message_templates("waba_101", token)
    assert tpl_res.success is True
    assert len(tpl_res.data["templates"]) >= 1

    # Send template WITHOUT opt-in should FAIL (Anti-Spam Policy)
    fail_res = await agent.send_template_message(
        phone_number_id="phone_waba_101",
        access_token=token,
        recipient_phone="+15550199",
        template_name="order_confirmation_v1",
        customer_opt_in_verified=False,
    )
    assert fail_res.success is False
    assert fail_res.error_code == "OPT_IN_REQUIRED"

    # Send template WITH opt-in should SUCCEED
    success_res = await agent.send_template_message(
        phone_number_id="phone_waba_101",
        access_token=token,
        recipient_phone="+15550199",
        template_name="order_confirmation_v1",
        customer_opt_in_verified=True,
    )
    assert success_res.success is True
    assert success_res.data["status"] == "accepted"

    # Webhook parsing
    mock_webhook = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "statuses": [{"id": "wamid.123", "status": "delivered", "recipient_id": "15550199"}],
                            "messages": [{"id": "wamid.456", "from": "15550199", "type": "text", "text": {"body": "Yes"}}],
                        }
                    }
                ]
            }
        ]
    }
    parsed = agent.process_incoming_webhook(mock_webhook)
    assert len(parsed["events"]) == 2
    assert parsed["events"][0]["status"] == "delivered"
    assert parsed["events"][1]["text"] == "Yes"


@pytest.mark.asyncio
async def test_messenger_and_threads_agents():
    # Messenger
    msg_agent = MessengerApiAgent()
    send_res = await msg_agent.send_message("psid_101", "mock_page_token", "Hello customer!")
    assert send_res.success is True
    assert "message_id" in send_res.data

    # Threads
    th_agent = ThreadsApiAgent()
    th_token = "mock_threads_token"
    prof_res = await th_agent.get_user_profile(th_token)
    assert prof_res.success is True
    assert "threads_biography" in prof_res.data

    pub_res = await th_agent.publish_thread("th_user_12345678", th_token, "First thread from AI Factory!")
    assert pub_res.success is True
    assert "thread_id" in pub_res.data


@pytest.mark.asyncio
async def test_youtube_api_agent_and_quota():
    agent = YouTubeApiAgent()

    # Channel info
    ch_res = await agent.get_channel_info(channel_id="UC_123")
    assert ch_res.success is True
    assert ch_res.data["subscriber_count"] > 0

    # Video details
    vid_res = await agent.get_video_details(video_id="v_101")
    assert vid_res.success is True
    assert vid_res.data["views"] > 0

    # Analytics
    an_res = await agent.get_channel_analytics(channel_id="UC_123", access_token="google_mock_token")
    assert an_res.success is True
    assert an_res.data["views"] > 0

    # Quota tracker
    tracker = YouTubeQuotaTracker(daily_limit=10)
    assert tracker.consume(4) is True
    assert tracker.get_remaining() == 6
    assert tracker.consume(7) is False  # Exceeds 10


@pytest.mark.asyncio
async def test_x_linkedin_tiktok_agents():
    # X
    x = XApiAgent()
    me_res = await x.get_me("x_mock_token")
    assert me_res.success is True
    tweet_res = await x.post_tweet("x_mock_token", "Building the AI Software Factory #AI")
    assert tweet_res.success is True
    pricing = x.get_tier_limits_and_pricing("basic")
    assert pricing["monthly_cost_usd"] == 100.0

    # LinkedIn
    li = LinkedInApiAgent()
    prof_res = await li.get_user_profile("linkedin_mock_token")
    assert prof_res.success is True
    share_res = await li.share_content("urn:li:person:123", "linkedin_mock_token", "Proud to announce our launch.")
    assert share_res.success is True

    # TikTok
    tt = TikTokApiAgent()
    tt_me = await tt.get_user_info("tiktok_mock_token")
    assert tt_me.success is True
    tt_vid = await tt.query_video_list("tiktok_mock_token")
    assert tt_vid.success is True
    assert len(tt_vid.data["videos"]) >= 1


def test_webhook_security_and_sanitization():
    app_secret = "my_super_secret_app_key"
    payload = b'{"object":"page","entry":[]}'

    import hashlib
    import hmac
    expected_sig = "sha256=" + hmac.new(app_secret.encode(), payload, hashlib.sha256).hexdigest()

    # Valid signature
    assert verify_meta_webhook_signature(payload, expected_sig, app_secret) is True

    # Forged signature
    assert verify_meta_webhook_signature(payload, "sha256=fake_signature_hex", app_secret) is False

    # Challenge verification
    assert verify_meta_webhook_challenge("subscribe", "valid_token", "challenge_12345", "valid_token") == "challenge_12345"
    assert verify_meta_webhook_challenge("subscribe", "wrong_token", "challenge_12345", "valid_token") is None

    # Twitter CRC response
    crc_resp = generate_twitter_crc_response("crc_nonce_123", "consumer_secret_xyz")
    assert crc_resp.startswith("sha256=")

    # Sanitization
    raw = {
        "user": "developer",
        "access_token": "EAAX1234secret",
        "nested": {"client_secret": "super_secret_val", "public": "visible"},
    }
    sanitized = sanitize_payload(raw)
    assert sanitized["access_token"] == "********"
    assert sanitized["nested"]["client_secret"] == "********"
    assert sanitized["nested"]["public"] == "visible"
