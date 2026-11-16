"""
LinkedIn API Specialist Agent (Role #42).
Handles LinkedIn Member Profile, Organization Page posts, and User Info endpoints.
"""

import time
from typing import Any, Dict, List, Optional
import httpx

from factory.core.logger import logger
from factory.social.base import SocialApiResult


class LinkedInApiAgent:
    """Specialist Agent for LinkedIn Platform API operations."""

    def __init__(self):
        self.base_url = "https://api.linkedin.com/v2"

    async def get_user_profile(self, access_token: str) -> SocialApiResult:
        """
        Retrieve OpenID Connect user profile info.
        Calls GET https://api.linkedin.com/v2/userinfo.
        """
        start = time.time()
        if access_token.startswith("mock_") or access_token.startswith("linkedin_"):
            return SocialApiResult(
                success=True,
                platform="linkedin",
                operation="get_user_profile",
                data={
                    "sub": "urn:li:person:mock12345",
                    "name": "Jane Developer",
                    "email": "jane@example.com",
                    "picture": "https://example.com/jane.jpg",
                },
                latency_ms=int((time.time() - start) * 1000),
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.base_url}/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                latency = int((time.time() - start) * 1000)
                if r.status_code == 200:
                    return SocialApiResult(
                        success=True,
                        platform="linkedin",
                        operation="get_user_profile",
                        data=r.json(),
                        latency_ms=latency,
                    )
                return SocialApiResult(
                    success=False,
                    platform="linkedin",
                    operation="get_user_profile",
                    status_code=r.status_code,
                    error_message=r.text,
                    latency_ms=latency,
                )
        except Exception as e:
            return SocialApiResult(
                success=False,
                platform="linkedin",
                operation="get_user_profile",
                status_code=500,
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
            )

    async def share_content(
        self,
        author_urn: str,
        access_token: str,
        text: str,
    ) -> SocialApiResult:
        """
        Share an update or article on LinkedIn.
        Calls POST /v2/ugcPosts.
        """
        start = time.time()
        if access_token.startswith("mock_") or access_token.startswith("linkedin_"):
            return SocialApiResult(
                success=True,
                platform="linkedin",
                operation="share_content",
                data={
                    "post_id": f"urn:li:share:{int(time.time())}",
                    "status": "published",
                },
                latency_ms=int((time.time() - start) * 1000),
            )

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                r = await client.post(
                    f"{self.base_url}/ugcPosts",
                    headers={"Authorization": f"Bearer {access_token}", "X-Restli-Protocol-Version": "2.0.0"},
                    json=payload,
                )
                latency = int((time.time() - start) * 1000)
                if r.status_code in (200, 201):
                    return SocialApiResult(
                        success=True,
                        platform="linkedin",
                        operation="share_content",
                        data=r.json(),
                        latency_ms=latency,
                    )
                return SocialApiResult(
                    success=False,
                    platform="linkedin",
                    operation="share_content",
                    status_code=r.status_code,
                    error_message=r.text,
                    latency_ms=latency,
                )
        except Exception as e:
            return SocialApiResult(
                success=False,
                platform="linkedin",
                operation="share_content",
                status_code=500,
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
            )
