"""
TikTok Developer Platform Specialist Agent (Role #43).
Handles TikTok Login Kit, user profile query, Content Posting API, and video listing.
"""

import time
from typing import Any, Dict, List, Optional
import httpx

from factory.core.logger import logger
from factory.social.base import SocialApiResult


class TikTokApiAgent:
    """Specialist Agent for TikTok Developer API operations."""

    def __init__(self):
        self.base_url = "https://open.tiktokapis.com/v2"

    async def get_user_info(self, access_token: str) -> SocialApiResult:
        """
        Query basic user profile (display_name, avatar_url, follower_count).
        Calls GET /v2/user/info/.
        """
        start = time.time()
        if access_token.startswith("mock_") or access_token.startswith("tiktok_"):
            return SocialApiResult(
                success=True,
                platform="tiktok",
                operation="get_user_info",
                data={
                    "open_id": "mock_tiktok_open_id_101",
                    "union_id": "mock_union_id_101",
                    "avatar_url": "https://example.com/tiktok_avatar.jpg",
                    "display_name": "Acme Creator",
                    "follower_count": 54200,
                    "likes_count": 890000,
                },
                latency_ms=int((time.time() - start) * 1000),
            )

        fields = "open_id,union_id,avatar_url,display_name,follower_count,likes_count"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.base_url}/user/info/",
                    params={"fields": fields},
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                latency = int((time.time() - start) * 1000)
                if r.status_code == 200:
                    payload = r.json().get("data", {}).get("user", {})
                    return SocialApiResult(
                        success=True,
                        platform="tiktok",
                        operation="get_user_info",
                        data=payload,
                        latency_ms=latency,
                    )
                return SocialApiResult(
                    success=False,
                    platform="tiktok",
                    operation="get_user_info",
                    status_code=r.status_code,
                    error_message=r.text,
                    latency_ms=latency,
                )
        except Exception as e:
            return SocialApiResult(
                success=False,
                platform="tiktok",
                operation="get_user_info",
                status_code=500,
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
            )

    async def query_video_list(self, access_token: str, max_count: int = 10) -> SocialApiResult:
        """
        List public creator videos.
        Calls POST /v2/video/list/.
        """
        start = time.time()
        if access_token.startswith("mock_") or access_token.startswith("tiktok_"):
            return SocialApiResult(
                success=True,
                platform="tiktok",
                operation="query_video_list",
                data={
                    "videos": [
                        {
                            "id": "7123456789012345678",
                            "title": "Autonomous AI Engineering Demo",
                            "view_count": 42000,
                            "like_count": 3100,
                            "comment_count": 140,
                            "share_count": 480,
                        }
                    ]
                },
                latency_ms=int((time.time() - start) * 1000),
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{self.base_url}/video/list/",
                    headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                    json={"max_count": max_count},
                )
                latency = int((time.time() - start) * 1000)
                if r.status_code == 200:
                    return SocialApiResult(
                        success=True,
                        platform="tiktok",
                        operation="query_video_list",
                        data=r.json().get("data", {}),
                        latency_ms=latency,
                    )
                return SocialApiResult(
                    success=False,
                    platform="tiktok",
                    operation="query_video_list",
                    status_code=r.status_code,
                    error_message=r.text,
                    latency_ms=latency,
                )
        except Exception as e:
            return SocialApiResult(
                success=False,
                platform="tiktok",
                operation="query_video_list",
                status_code=500,
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
            )
