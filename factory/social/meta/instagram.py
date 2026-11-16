"""
Instagram Platform API Specialist Agent (Role #35).
Handles Professional account connections, media retrieval, Content Publishing API, and insights.
"""

import time
from typing import Any, Dict, List, Optional
import httpx

from factory.core.logger import logger
from factory.social.base import SocialApiResult


class InstagramApiAgent:
    """Specialist Agent for Instagram Graph API operations."""

    def __init__(self, api_version: str = "v20.0"):
        self.api_version = api_version
        self.graph_base = f"https://graph.facebook.com/{api_version}"

    async def get_instagram_business_account(self, page_id: str, page_access_token: str) -> SocialApiResult:
        """
        Discover linked Instagram Professional/Business Account for a Facebook Page.
        Calls GET /v20.0/{page_id}?fields=instagram_business_account.
        """
        start = time.time()
        if page_access_token.startswith("mock_") or page_access_token.startswith("page_token_") or page_access_token.startswith("facebook_live_token_"):
            return SocialApiResult(
                success=True,
                platform="instagram",
                operation="get_instagram_business_account",
                data={
                    "page_id": page_id,
                    "instagram_business_account": {
                        "id": "ig_business_987654321",
                        "username": "acme_official",
                    },
                },
                latency_ms=int((time.time() - start) * 1000),
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.graph_base}/{page_id}",
                    params={"fields": "instagram_business_account{id,username,name}", "access_token": page_access_token},
                )
                latency = int((time.time() - start) * 1000)
                if r.status_code == 200:
                    payload = r.json()
                    ig_acc = payload.get("instagram_business_account")
                    if not ig_acc:
                        return SocialApiResult(
                            success=False,
                            platform="instagram",
                            operation="get_instagram_business_account",
                            error_message="No Instagram Professional account is connected to this Facebook Page. Personal accounts must be converted to Professional/Creator in Instagram app settings.",
                            latency_ms=latency,
                        )
                    return SocialApiResult(
                        success=True,
                        platform="instagram",
                        operation="get_instagram_business_account",
                        data={"page_id": page_id, "instagram_business_account": ig_acc},
                        latency_ms=latency,
                    )
                return SocialApiResult(
                    success=False,
                    platform="instagram",
                    operation="get_instagram_business_account",
                    status_code=r.status_code,
                    error_message=r.text,
                    latency_ms=latency,
                )
        except Exception as e:
            return SocialApiResult(
                success=False,
                platform="instagram",
                operation="get_instagram_business_account",
                status_code=500,
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
            )

    async def get_account_info(self, ig_user_id: str, access_token: str) -> SocialApiResult:
        """
        Retrieve Instagram professional profile, followers, bio, and media count.
        Calls GET /v20.0/{ig_user_id}.
        """
        start = time.time()
        if access_token.startswith("mock_") or access_token.startswith("facebook_live_token_") or access_token.startswith("page_token_"):
            return SocialApiResult(
                success=True,
                platform="instagram",
                operation="get_account_info",
                data={
                    "id": ig_user_id,
                    "username": "acme_official",
                    "name": "Acme Innovations",
                    "biography": "Official Instagram of Acme Innovations. Leading AI solutions.",
                    "followers_count": 98400,
                    "follows_count": 420,
                    "media_count": 530,
                    "profile_picture_url": "https://example.com/avatar.jpg",
                },
                latency_ms=int((time.time() - start) * 1000),
            )

        try:
            fields = "id,username,name,biography,profile_picture_url,followers_count,follows_count,media_count"
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.graph_base}/{ig_user_id}",
                    params={"fields": fields, "access_token": access_token},
                )
                latency = int((time.time() - start) * 1000)
                if r.status_code == 200:
                    return SocialApiResult(
                        success=True,
                        platform="instagram",
                        operation="get_account_info",
                        data=r.json(),
                        latency_ms=latency,
                    )
                return SocialApiResult(
                    success=False,
                    platform="instagram",
                    operation="get_account_info",
                    status_code=r.status_code,
                    error_message=r.text,
                    latency_ms=latency,
                )
        except Exception as e:
            return SocialApiResult(
                success=False,
                platform="instagram",
                operation="get_account_info",
                status_code=500,
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
            )

    async def get_user_media(self, ig_user_id: str, access_token: str, limit: int = 10) -> SocialApiResult:
        """
        Retrieve published media posts, carousels, and reels.
        Calls GET /v20.0/{ig_user_id}/media.
        """
        start = time.time()
        if access_token.startswith("mock_") or access_token.startswith("facebook_live_token_") or access_token.startswith("page_token_"):
            return SocialApiResult(
                success=True,
                platform="instagram",
                operation="get_user_media",
                data={
                    "media": [
                        {
                            "id": "18012345678901234",
                            "caption": "Announcing Autonomous AI Software Factory v2.0 #AI #Software",
                            "media_type": "IMAGE",
                            "media_url": "https://example.com/post1.jpg",
                            "permalink": "https://instagram.com/p/mock123",
                            "timestamp": "2026-11-01T12:00:00+0000",
                            "like_count": 1420,
                            "comments_count": 89,
                        }
                    ]
                },
                latency_ms=int((time.time() - start) * 1000),
            )

        try:
            fields = "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count"
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.graph_base}/{ig_user_id}/media",
                    params={"fields": fields, "limit": limit, "access_token": access_token},
                )
                latency = int((time.time() - start) * 1000)
                if r.status_code == 200:
                    return SocialApiResult(
                        success=True,
                        platform="instagram",
                        operation="get_user_media",
                        data={"media": r.json().get("data", [])},
                        latency_ms=latency,
                    )
                return SocialApiResult(
                    success=False,
                    platform="instagram",
                    operation="get_user_media",
                    status_code=r.status_code,
                    error_message=r.text,
                    latency_ms=latency,
                )
        except Exception as e:
            return SocialApiResult(
                success=False,
                platform="instagram",
                operation="get_user_media",
                status_code=500,
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
            )

    async def publish_photo(
        self,
        ig_user_id: str,
        access_token: str,
        image_url: str,
        caption: str,
    ) -> SocialApiResult:
        """
        Publish image post using the two-step Instagram Content Publishing API:
        1. Create Media Container (POST /{ig-user-id}/media)
        2. Publish Container (POST /{ig-user-id}/media_publish)
        """
        start = time.time()
        if access_token.startswith("mock_") or access_token.startswith("facebook_live_token_") or access_token.startswith("page_token_"):
            return SocialApiResult(
                success=True,
                platform="instagram",
                operation="publish_photo",
                data={"media_id": f"ig_media_{int(time.time())}", "status": "published"},
                latency_ms=int((time.time() - start) * 1000),
            )

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Step 1: Create Container
                r1 = await client.post(
                    f"{self.graph_base}/{ig_user_id}/media",
                    data={"image_url": image_url, "caption": caption, "access_token": access_token},
                )
                if r1.status_code != 200:
                    return SocialApiResult(
                        success=False,
                        platform="instagram",
                        operation="publish_photo",
                        status_code=r1.status_code,
                        error_message=f"Container creation failed: {r1.text}",
                    )
                creation_id = r1.json().get("id")

                # Step 2: Publish Container
                r2 = await client.post(
                    f"{self.graph_base}/{ig_user_id}/media_publish",
                    data={"creation_id": creation_id, "access_token": access_token},
                )
                latency = int((time.time() - start) * 1000)
                if r2.status_code == 200:
                    return SocialApiResult(
                        success=True,
                        platform="instagram",
                        operation="publish_photo",
                        data={"media_id": r2.json().get("id"), "creation_id": creation_id},
                        latency_ms=latency,
                    )
                return SocialApiResult(
                    success=False,
                    platform="instagram",
                    operation="publish_photo",
                    status_code=r2.status_code,
                    error_message=f"Publish failed: {r2.text}",
                    latency_ms=latency,
                )
        except Exception as e:
            return SocialApiResult(
                success=False,
                platform="instagram",
                operation="publish_photo",
                status_code=500,
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
            )

    async def get_account_insights(
        self,
        ig_user_id: str,
        access_token: str,
        metrics: Optional[List[str]] = None,
    ) -> SocialApiResult:
        """
        Retrieve Instagram professional analytics.
        Calls GET /v20.0/{ig_user_id}/insights.
        """
        start = time.time()
        if access_token.startswith("mock_") or access_token.startswith("facebook_live_token_") or access_token.startswith("page_token_"):
            return SocialApiResult(
                success=True,
                platform="instagram",
                operation="get_account_insights",
                data={
                    "ig_user_id": ig_user_id,
                    "metrics": {
                        "impressions_last_28d": 210000,
                        "reach_last_28d": 165000,
                        "profile_views_last_28d": 12800,
                        "website_clicks_last_28d": 3400,
                    },
                },
                latency_ms=int((time.time() - start) * 1000),
            )

        metric_list = metrics or ["impressions", "reach", "profile_views"]
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.graph_base}/{ig_user_id}/insights",
                    params={"metric": ",".join(metric_list), "period": "day", "access_token": access_token},
                )
                latency = int((time.time() - start) * 1000)
                if r.status_code == 200:
                    return SocialApiResult(
                        success=True,
                        platform="instagram",
                        operation="get_account_insights",
                        data={"insights": r.json().get("data", [])},
                        latency_ms=latency,
                    )
                return SocialApiResult(
                    success=False,
                    platform="instagram",
                    operation="get_account_insights",
                    status_code=r.status_code,
                    error_message=r.text,
                    latency_ms=latency,
                )
        except Exception as e:
            return SocialApiResult(
                success=False,
                platform="instagram",
                operation="get_account_insights",
                status_code=500,
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
            )
