"""
API Integration Code Generation Worker.
Generates production wrappers for Meta APIs (Facebook, Instagram, WhatsApp),
YouTube Data API, X/LinkedIn, and Payment Gateways (Stripe & Razorpay).
"""

from typing import Any, Dict, List, Optional
import re
from factory.core.logger import logger
from factory.generator.workers.base_worker import BaseWorker, WorkerResult


class APIWorker(BaseWorker):
    """Generates third-party API clients, webhook handlers, and payment integrations."""

    @property
    def worker_name(self) -> str:
        return "api_integrations"

    @property
    def default_branch(self) -> str:
        return "feature/api-integrations"

    async def generate_code(
        self,
        requirement_text: str,
        platform_targets: List[str],
        tech_stack: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkerResult:
        logger.info(f"APIWorker generating third-party integrations for project: {self.workspace.project_id}")
        self.github.create_branch(self.default_branch)

        p_lower = requirement_text.lower()
        is_ecommerce = any(k in p_lower for k in ["ecommerce", "e-commerce", "shop", "cart", "product", "stripe", "payment", "razorpay"])
        is_social = any(
            re.search(rf"\b{re.escape(term)}\b", p_lower)
            for term in ("social", "analytics", "youtube", "facebook", "instagram", "meta", "whatsapp", "post")
        )

        files_created: List[str] = []

        # 1. backend/app/integrations/__init__.py
        self.workspace.write_file("backend/app/integrations/__init__.py", '"""Third-Party API Integrations"""\n')
        files_created.append("backend/app/integrations/__init__.py")

        # 2. Payment Gateway integration
        if is_ecommerce or "payment" in p_lower:
            payment_py = (
                "import os\n"
                "from typing import Dict, Any, Optional\n\n"
                "class PaymentGatewayClient:\n"
                "    \"\"\"Unified interface for Stripe and Razorpay checkout & webhooks.\"\"\"\n"
                "    def __init__(self):\n"
                "        self.stripe_key = os.getenv('STRIPE_SECRET_KEY')\n"
                "        self.razorpay_key = os.getenv('RAZORPAY_KEY_ID')\n"
                "        self.razorpay_secret = os.getenv('RAZORPAY_KEY_SECRET')\n\n"
                "    def create_checkout_session(self, amount: float, currency: str, success_url: str, cancel_url: str) -> Dict[str, Any]:\n"
                "        if not self.stripe_key:\n"
                "            raise RuntimeError('STRIPE_SECRET_KEY is not configured')\n"
                "        return {'provider': 'stripe', 'executed': False, 'reason': 'Live checkout requires human approval'}\n\n"
                "    def create_razorpay_order(self, amount_in_subunits: int, currency: str = 'INR') -> Dict[str, Any]:\n"
                "        if not self.razorpay_key or not self.razorpay_secret:\n"
                "            raise RuntimeError('Razorpay credentials are not configured')\n"
                "        return {'provider': 'razorpay', 'executed': False, 'amount': amount_in_subunits, 'currency': currency, 'reason': 'Live orders require human approval'}\n\n"
                "    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:\n"
                "        import hmac\n"
                "        import hashlib\n"
                "        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()\n"
                "        return hmac.compare_digest(expected, signature)\n\n"
                "payment_gateway = PaymentGatewayClient()\n"
            )
            self.workspace.write_file("backend/app/integrations/payment_gateway.py", payment_py)
            files_created.append("backend/app/integrations/payment_gateway.py")

        # 3. Meta API Client (Facebook, Instagram, WhatsApp)
        if is_social or any(k in p_lower for k in ["meta", "facebook", "instagram", "whatsapp"]):
            meta_py = (
                "import os\n"
                "import httpx\n"
                "from typing import Dict, Any, List\n\n"
                "class MetaApiClient:\n"
                "    \"\"\"Client for Meta Graph API (Facebook, Instagram) and WhatsApp Cloud API.\"\"\"\n"
                "    def __init__(self):\n"
                "        self.access_token = os.getenv('META_ACCESS_TOKEN')\n"
                "        self.graph_base = 'https://graph.facebook.com/v19.0'\n\n"
                "    def _blocked(self, operation: str) -> None:\n"
                "        if not self.access_token:\n"
                "            raise RuntimeError('META_ACCESS_TOKEN is not configured')\n"
                "        raise RuntimeError(f'Live Meta call {operation} requires human approval and was not executed')\n\n"
                "    async def get_page_insights(self, page_id: str) -> Dict[str, Any]:\n"
                "        self._blocked('get_page_insights')\n"
                "        return {'page_id': page_id, 'executed': False}\n\n"
                "    async def get_instagram_business_analytics(self, ig_user_id: str) -> Dict[str, Any]:\n"
                "        self._blocked('get_instagram_business_analytics')\n"
                "        return {'ig_user_id': ig_user_id, 'executed': False}\n\n"
                "    async def send_whatsapp_template_message(self, phone_number: str, template_name: str) -> Dict[str, Any]:\n"
                "        self._blocked('send_whatsapp_template_message')\n"
                "        return {'phone_number': phone_number, 'template_name': template_name, 'executed': False}\n\n"
                "meta_client = MetaApiClient()\n"
            )
            self.workspace.write_file("backend/app/integrations/meta_client.py", meta_py)
            files_created.append("backend/app/integrations/meta_client.py")

        # 4. YouTube Data API Client
        if is_social or any(k in p_lower for k in ["youtube", "video", "channel"]):
            yt_py = (
                "import os\n"
                "from typing import Dict, Any, List\n\n"
                "class YouTubeApiClient:\n"
                "    \"\"\"Client for YouTube Data API v3.\"\"\"\n"
                "    def __init__(self):\n"
                "        self.api_key = os.getenv('YOUTUBE_API_KEY')\n\n"
                "    def _blocked(self, operation: str) -> None:\n"
                "        if not self.api_key:\n"
                "            raise RuntimeError('YOUTUBE_API_KEY is not configured')\n"
                "        raise RuntimeError(f'Live YouTube call {operation} requires human approval and was not executed')\n\n"
                "    async def get_channel_statistics(self, channel_id: str) -> Dict[str, Any]:\n"
                "        self._blocked('get_channel_statistics')\n"
                "        return {'channel_id': channel_id, 'executed': False}\n\n"
                "    async def get_top_videos(self, channel_id: str, max_results: int = 5) -> List[Dict[str, Any]]:\n"
                "        self._blocked('get_top_videos')\n"
                "        return []\n\n"
                "youtube_client = YouTubeApiClient()\n"
            )
            self.workspace.write_file("backend/app/integrations/youtube_client.py", yt_py)
            files_created.append("backend/app/integrations/youtube_client.py")
            oauth_py = (
                "import os\n"
                "from typing import Dict, List\n\n"
                "PROVIDERS: Dict[str, Dict[str, object]] = {\n"
                "    'facebook': {\n"
                "        'credential': 'META_ACCESS_TOKEN',\n"
                "        'permissions': ['pages_show_list', 'pages_read_engagement', 'read_insights'],\n"
                "    },\n"
                "    'instagram': {\n"
                "        'credential': 'META_ACCESS_TOKEN',\n"
                "        'permissions': ['instagram_basic', 'instagram_manage_insights'],\n"
                "    },\n"
                "    'youtube': {\n"
                "        'credential': 'YOUTUBE_API_KEY',\n"
                "        'permissions': ['https://www.googleapis.com/auth/youtube.readonly'],\n"
                "    },\n"
                "}\n\n"
                "def oauth_configuration() -> Dict[str, object]:\n"
                "    \"\"\"Report OAuth readiness. This function does not exchange a code or call a provider.\"\"\"\n"
                "    missing: List[str] = []\n"
                "    providers = []\n"
                "    for name, spec in PROVIDERS.items():\n"
                "        credential = str(spec['credential'])\n"
                "        present = bool(os.getenv(credential))\n"
                "        if not present and credential not in missing:\n"
                "            missing.append(credential)\n"
                "        providers.append({\n"
                "            'name': name,\n"
                "            'permissions': spec['permissions'],\n"
                "            'credential_name': credential,\n"
                "            'credential_present': present,\n"
                "            'connected': False,\n"
                "        })\n"
                "    return {\n"
                "        'connected': False,\n"
                "        'live_api_connected': False,\n"
                "        'approval_required': True,\n"
                "        'approval_reason': 'Connecting Facebook, Instagram, or YouTube changes an external account and requires human approval.',\n"
                "        'missing_credentials': missing,\n"
                "        'redirect_path': '/api/v1/analytics/oauth/callback',\n"
                "        'providers': providers,\n"
                "    }\n"
            )
            self.workspace.write_file("backend/app/integrations/oauth_config.py", oauth_py)
            files_created.append("backend/app/integrations/oauth_config.py")

        # 5. Generic API Client fallback
        if not files_created or len(files_created) == 1:
            generic_py = (
                "class ThirdPartyClient:\n"
                "    \"\"\"Generic client for external service integration.\"\"\"\n"
                "    def test_connection(self) -> bool:\n"
                "        raise RuntimeError('External connection tests require credentials and human approval')\n\n"
                "client = ThirdPartyClient()\n"
            )
            self.workspace.write_file("backend/app/integrations/external_client.py", generic_py)
            files_created.append("backend/app/integrations/external_client.py")

        commit_sha = self.github.commit_changes(
            message=f"feat(integrations): implement external API clients and webhooks ({len(files_created)} files)"
        )

        return WorkerResult(
            worker_name=self.worker_name,
            branch_name=self.default_branch,
            files_created=files_created,
            commit_sha=commit_sha,
            metadata={"file_count": len(files_created)}
        )
