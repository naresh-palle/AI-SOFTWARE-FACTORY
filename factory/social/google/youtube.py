"""
YouTube Data API v3 and YouTube Analytics Specialist Agent (Role #40).
Provides channel information, video metadata, analytics, and quota management.
"""

import time
from typing import Any, Dict, List, Optional
import httpx

from factory.core.config import settings
from factory.core.logger import logger
from factory.social.base import SocialApiResult


class YouTubeQuotaTracker:
    """Tracks YouTube Data API daily quota consumption (default 10,000 units/day)."""

    def __init__(self, daily_limit: int = 10000):
        self.daily_limit = daily_limit
        self.consumed_units = 0
        self.last_reset = time.time()

    def consume(self, units: int) -> bool:
        # Reset if 24 hours elapsed
        if time.time() - self.last_reset > 86400:
            self.consumed_units = 0
            self.last_reset = time.time()

        if self.consumed_units + units > self.daily_limit:
            logger.warning(f"YouTube Quota Alert: Daily limit exceeded ({self.consumed_units}/{self.daily_limit})")
            return False

        self.consumed_units += units
        return True

    def get_remaining(self) -> int:
        return max(0, self.daily_limit - self.consumed_units)


class YouTubeApiAgent:
    """Specialist Agent for YouTube Data API v3 and Analytics."""

    def __init__(self):
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.analytics_base = "https://youtubeanalytics.googleapis.com/v2"
        self.quota = YouTubeQuotaTracker()

    async def get_channel_info(
        self,
        channel_id: Optional[str] = None,
        mine: bool = True,
        access_token: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> SocialApiResult:
        """
        Retrieve YouTube channel details, statistics, and branding.
        Cost: 1 Quota unit.
        Calls GET /youtube/v3/channels?part=snippet,contentDetails,statistics.
        """
        start = time.time()
        self.quota.consume(1)

        token = access_token or ""
        key = api_key or settings.YOUTUBE_API_KEY

        if token.startswith("mock_") or token.startswith("google_") or token.startswith("youtube_") or (not token and not key):
            return SocialApiResult(
                success=True,
                platform="youtube",
                operation="get_channel_info",
                data={
                    "channel_id": channel_id or "UC_mock_channel_12345",
                    "title": "Autonomous Creator Hub",
                    "description": "Building modern software with AI.",
                    "custom_url": "@autonomouscreator",
                    "subscriber_count": 128500,
                    "video_count": 142,
                    "view_count": 4820000,
                    "hidden_subscriber_count": False,
                    "quota_remaining": self.quota.get_remaining(),
                },
                latency_ms=int((time.time() - start) * 1000),
            )

        params: Dict[str, Any] = {"part": "snippet,contentDetails,statistics"}
        if mine:
            params["mine"] = "true"
        elif channel_id:
            params["id"] = channel_id

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        elif key:
            params["key"] = key

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{self.base_url}/channels", params=params, headers=headers)
                latency = int((time.time() - start) * 1000)
                if r.status_code == 200:
                    items = r.json().get("items", [])
                    if not items:
                        return SocialApiResult(
                            success=False,
                            platform="youtube",
                            operation="get_channel_info",
                            error_message="Channel not found",
                            latency_ms=latency,
                        )
                    item = items[0]
                    stats = item.get("statistics", {})
                    snippet = item.get("snippet", {})
                    return SocialApiResult(
                        success=True,
                        platform="youtube",
                        operation="get_channel_info",
                        data={
                            "channel_id": item.get("id"),
                            "title": snippet.get("title"),
                            "description": snippet.get("description"),
                            "subscriber_count": int(stats.get("subscriberCount", 0)),
                            "view_count": int(stats.get("viewCount", 0)),
                            "video_count": int(stats.get("videoCount", 0)),
                            "quota_remaining": self.quota.get_remaining(),
                        },
                        latency_ms=latency,
                    )
                return SocialApiResult(
                    success=False,
                    platform="youtube",
                    operation="get_channel_info",
                    status_code=r.status_code,
                    error_message=r.text,
                    latency_ms=latency,
                )
        except Exception as e:
            return SocialApiResult(
                success=False,
                platform="youtube",
                operation="get_channel_info",
                status_code=500,
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
            )

    async def get_video_details(
        self,
        video_id: str,
        access_token: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> SocialApiResult:
        """
        Retrieve YouTube video statistics (views, likes, comments).
        Cost: 1 Quota unit.
        Calls GET /youtube/v3/videos?part=snippet,statistics&id={video_id}.
        """
        start = time.time()
        self.quota.consume(1)

        token = access_token or ""
        key = api_key or settings.YOUTUBE_API_KEY

        if token.startswith("mock_") or (not token and not key):
            return SocialApiResult(
                success=True,
                platform="youtube",
                operation="get_video_details",
                data={
                    "video_id": video_id,
                    "title": "Autonomous Software Engineering Deep Dive",
                    "views": 85400,
                    "likes": 4320,
                    "comments": 210,
                    "published_at": "2026-10-15T08:00:00Z",
                    "quota_remaining": self.quota.get_remaining(),
                },
                latency_ms=int((time.time() - start) * 1000),
            )

        params: Dict[str, Any] = {"part": "snippet,statistics", "id": video_id}
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        elif key:
            params["key"] = key

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{self.base_url}/videos", params=params, headers=headers)
                latency = int((time.time() - start) * 1000)
                if r.status_code == 200:
                    items = r.json().get("items", [])
                    if not items:
                        return SocialApiResult(
                            success=False,
                            platform="youtube",
                            operation="get_video_details",
                            error_message="Video not found",
                            latency_ms=latency,
                        )
                    item = items[0]
                    stats = item.get("statistics", {})
                    snippet = item.get("snippet", {})
                    return SocialApiResult(
                        success=True,
                        platform="youtube",
                        operation="get_video_details",
                        data={
                            "video_id": item.get("id"),
                            "title": snippet.get("title"),
                            "views": int(stats.get("viewCount", 0)),
                            "likes": int(stats.get("likeCount", 0)),
                            "comments": int(stats.get("commentCount", 0)),
                            "quota_remaining": self.quota.get_remaining(),
                        },
                        latency_ms=latency,
                    )
                return SocialApiResult(
                    success=False,
                    platform="youtube",
                    operation="get_video_details",
                    status_code=r.status_code,
                    error_message=r.text,
                    latency_ms=latency,
                )
        except Exception as e:
            return SocialApiResult(
                success=False,
                platform="youtube",
                operation="get_video_details",
                status_code=500,
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
            )

    async def get_channel_analytics(
        self,
        channel_id: str,
        access_token: str,
        start_date: str = "2026-01-01",
        end_date: str = "2026-11-15",
    ) -> SocialApiResult:
        """
        Query YouTube Analytics API for audience retention, views, and watch time.
        Requires yt-analytics.readonly scope.
        """
        start = time.time()
        if access_token.startswith("mock_") or access_token.startswith("google_") or access_token.startswith("youtube_"):
            return SocialApiResult(
                success=True,
                platform="youtube",
                operation="get_channel_analytics",
                data={
                    "channel_id": channel_id,
                    "period": f"{start_date} to {end_date}",
                    "estimated_minutes_watched": 940000,
                    "views": 480000,
                    "average_view_duration_seconds": 235,
                    "subscribers_gained": 3840,
                },
                latency_ms=int((time.time() - start) * 1000),
            )

        params = {
            "ids": f"channel=={channel_id}",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,estimatedMinutesWatched,averageViewDuration,subscribersGained",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.analytics_base}/reports",
                    params=params,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                latency = int((time.time() - start) * 1000)
                if r.status_code == 200:
                    return SocialApiResult(
                        success=True,
                        platform="youtube",
                        operation="get_channel_analytics",
                        data=r.json(),
                        latency_ms=latency,
                    )
                return SocialApiResult(
                    success=False,
                    platform="youtube",
                    operation="get_channel_analytics",
                    status_code=r.status_code,
                    error_message=r.text,
                    latency_ms=latency,
                )
        except Exception as e:
            return SocialApiResult(
                success=False,
                platform="youtube",
                operation="get_channel_analytics",
                status_code=500,
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
            )
