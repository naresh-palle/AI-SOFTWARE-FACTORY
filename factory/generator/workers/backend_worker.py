"""
Backend Code Generation Worker.
Generates complete Python FastAPI backends with JWT authentication,
business logic, Pydantic v2 schemas, REST endpoints, and pytest suites.
"""

from typing import Any, Dict, List, Optional
from factory.core.logger import logger
from factory.generator.workers.base_worker import BaseWorker, WorkerResult


class BackendWorker(BaseWorker):
    """Generates production-grade FastAPI applications."""

    @property
    def worker_name(self) -> str:
        return "backend"

    @property
    def default_branch(self) -> str:
        return "feature/backend-fastapi"

    async def generate_code(
        self,
        requirement_text: str,
        platform_targets: List[str],
        tech_stack: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkerResult:
        logger.info(f"BackendWorker generating code for project: {self.workspace.project_id}")
        self.github.create_branch(self.default_branch)

        p_lower = requirement_text.lower()
        is_ecommerce = any(k in p_lower for k in ["ecommerce", "e-commerce", "shop", "cart", "product", "stripe", "payment"])
        is_social = any(k in p_lower for k in ["social", "analytics", "youtube", "facebook", "instagram", "meta", "post", "follower"])

        files_created: List[str] = []

        # 1. requirements.txt
        reqs = (
            "fastapi>=0.110.0\n"
            "uvicorn[standard]>=0.29.0\n"
            "pydantic>=2.6.0\n"
            "pydantic-settings>=2.2.0\n"
            "pytest>=8.0.0\n"
            "httpx>=0.27.0\n"
            "python-multipart>=0.0.9\n"
        )
        self.workspace.write_file("backend/requirements.txt", reqs)
        files_created.append("backend/requirements.txt")

        # 2. app/__init__.py
        self.workspace.write_file("backend/app/__init__.py", '"""Backend Application Package"""\n')
        files_created.append("backend/app/__init__.py")

        # 3. app/core/config.py (Clean Pydantic v2 Settings)
        config_py = (
            "import os\n"
            "from typing import List\n"
            "from pydantic_settings import BaseSettings, SettingsConfigDict\n\n"
            "class Settings(BaseSettings):\n"
            "    model_config = SettingsConfigDict(case_sensitive=True)\n\n"
            "    PROJECT_NAME: str = 'Autonomous Generated Backend'\n"
            "    API_V1_STR: str = '/api/v1'\n"
            "    SECRET_KEY: str = os.getenv('SECRET_KEY', 'development-secret-key-32-chars-long-min')\n"
            "    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24\n"
            "    ALGORITHM: str = 'HS256'\n"
            "    ALLOWED_ORIGINS: List[str] = ['*']\n\n"
            "settings = Settings()\n"
        )
        self.workspace.write_file("backend/app/core/config.py", config_py)
        files_created.append("backend/app/core/config.py")

        # 4. app/core/security.py (Zero external binary dependency, robust standard library HMAC/SHA256)
        sec_py = (
            "import base64\n"
            "import hashlib\n"
            "import hmac\n"
            "import json\n"
            "import time\n"
            "from typing import Any, Dict, Optional\n"
            "from app.core.config import settings\n\n"
            "def _b64encode(data: bytes) -> str:\n"
            "    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')\n\n"
            "def _b64decode(s: str) -> bytes:\n"
            "    padding = '=' * (-len(s) % 4)\n"
            "    return base64.urlsafe_b64decode(s + padding)\n\n"
            "def get_password_hash(password: str) -> str:\n"
            "    salt = 'factory_salt_v1'\n"
            "    h = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)\n"
            "    return h.hex()\n\n"
            "def verify_password(plain_password: str, hashed_password: str) -> bool:\n"
            "    return hmac.compare_digest(get_password_hash(plain_password), hashed_password)\n\n"
            "def create_access_token(subject: str, expires_delta_seconds: Optional[int] = None) -> str:\n"
            "    header = {'alg': 'HS256', 'typ': 'JWT'}\n"
            "    exp = int(time.time()) + (expires_delta_seconds or settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)\n"
            "    payload = {'sub': str(subject), 'exp': exp}\n"
            "    h_b64 = _b64encode(json.dumps(header).encode('utf-8'))\n"
            "    p_b64 = _b64encode(json.dumps(payload).encode('utf-8'))\n"
            "    msg = f'{h_b64}.{p_b64}'.encode('utf-8')\n"
            "    sig = hmac.new(settings.SECRET_KEY.encode('utf-8'), msg, hashlib.sha256).digest()\n"
            "    sig_b64 = _b64encode(sig)\n"
            "    return f'{h_b64}.{p_b64}.{sig_b64}'\n\n"
            "def decode_access_token(token: str) -> Dict[str, Any]:\n"
            "    parts = token.split('.')\n"
            "    if len(parts) != 3:\n"
            "        raise ValueError('Invalid token format')\n"
            "    h_b64, p_b64, sig_b64 = parts\n"
            "    msg = f'{h_b64}.{p_b64}'.encode('utf-8')\n"
            "    expected_sig = _b64encode(hmac.new(settings.SECRET_KEY.encode('utf-8'), msg, hashlib.sha256).digest())\n"
            "    if not hmac.compare_digest(expected_sig, sig_b64):\n"
            "        raise ValueError('Invalid token signature')\n"
            "    payload = json.loads(_b64decode(p_b64).decode('utf-8'))\n"
            "    if payload.get('exp', 0) < time.time():\n"
            "        raise ValueError('Token has expired')\n"
            "    return payload\n"
        )
        self.workspace.write_file("backend/app/core/security.py", sec_py)
        files_created.append("backend/app/core/security.py")

        # 5. app/schemas/domain.py
        if is_ecommerce:
            schemas_py = (
                "from pydantic import BaseModel, Field\n"
                "from typing import Optional, List\n\n"
                "class UserCreate(BaseModel):\n"
                "    email: str\n"
                "    password: str\n"
                "    full_name: str\n\n"
                "class UserResponse(BaseModel):\n"
                "    id: str\n"
                "    email: str\n"
                "    full_name: str\n\n"
                "class Token(BaseModel):\n"
                "    access_token: str\n"
                "    token_type: str = 'bearer'\n\n"
                "class ProductItem(BaseModel):\n"
                "    id: str\n"
                "    title: str\n"
                "    price: float\n"
                "    inventory: int\n"
                "    category: str\n\n"
                "class OrderCreate(BaseModel):\n"
                "    product_id: str\n"
                "    quantity: int = Field(gt=0)\n"
                "    shipping_address: str\n\n"
                "class OrderResponse(BaseModel):\n"
                "    order_id: str\n"
                "    product_id: str\n"
                "    quantity: int\n"
                "    total_amount: float\n"
                "    status: str\n"
            )
        elif is_social:
            schemas_py = (
                "from pydantic import BaseModel\n"
                "from typing import Optional, List\n\n"
                "class UserCreate(BaseModel):\n"
                "    email: str\n"
                "    password: str\n"
                "    full_name: str\n\n"
                "class UserResponse(BaseModel):\n"
                "    id: str\n"
                "    email: str\n"
                "    full_name: str\n\n"
                "class Token(BaseModel):\n"
                "    access_token: str\n"
                "    token_type: str = 'bearer'\n\n"
                "class SocialMetricRecord(BaseModel):\n"
                "    platform: str\n"
                "    followers: int\n"
                "    engagement_rate: float\n"
                "    views_last_30d: int\n"
                "    posts_count: int\n\n"
                "class AnalyticsSummary(BaseModel):\n"
                "    total_audience: int\n"
                "    average_engagement: float\n"
                "    channels: List[SocialMetricRecord]\n"
            )
        else:
            schemas_py = (
                "from pydantic import BaseModel\n"
                "from typing import Optional, List\n\n"
                "class UserCreate(BaseModel):\n"
                "    email: str\n"
                "    password: str\n"
                "    full_name: str\n\n"
                "class UserResponse(BaseModel):\n"
                "    id: str\n"
                "    email: str\n"
                "    full_name: str\n\n"
                "class Token(BaseModel):\n"
                "    access_token: str\n"
                "    token_type: str = 'bearer'\n\n"
                "class ServiceInquiry(BaseModel):\n"
                "    name: str\n"
                "    email: str\n"
                "    message: str\n\n"
                "class InquiryResponse(BaseModel):\n"
                "    id: str\n"
                "    status: str\n"
                "    message: str\n"
            )
        self.workspace.write_file("backend/app/schemas/domain.py", schemas_py)
        files_created.append("backend/app/schemas/domain.py")

        # 6. app/api/auth.py
        auth_py = (
            "from fastapi import APIRouter, HTTPException, status, Depends\n"
            "from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm\n"
            "from app.schemas.domain import UserCreate, UserResponse, Token\n"
            "from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token\n\n"
            "router = APIRouter(prefix='/auth', tags=['Authentication'])\n"
            "oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')\n\n"
            "DB_USERS = {}\n\n"
            "@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)\n"
            "def register(user_in: UserCreate):\n"
            "    if user_in.email in DB_USERS:\n"
            "        raise HTTPException(status_code=400, detail='Email already registered')\n"
            "    user_id = f'usr_{len(DB_USERS) + 1}'\n"
            "    hashed = get_password_hash(user_in.password)\n"
            "    DB_USERS[user_in.email] = {\n"
            "        'id': user_id, 'email': user_in.email, 'hashed_password': hashed, 'full_name': user_in.full_name\n"
            "    }\n"
            "    return {'id': user_id, 'email': user_in.email, 'full_name': user_in.full_name}\n\n"
            "@router.post('/login', response_model=Token)\n"
            "def login(form_data: OAuth2PasswordRequestForm = Depends()):\n"
            "    user = DB_USERS.get(form_data.username)\n"
            "    if not user or not verify_password(form_data.password, user['hashed_password']):\n"
            "        raise HTTPException(status_code=401, detail='Incorrect email or password')\n"
            "    token = create_access_token(subject=user['email'])\n"
            "    return {'access_token': token, 'token_type': 'bearer'}\n\n"
            "@router.get('/me', response_model=UserResponse)\n"
            "def get_me(token: str = Depends(oauth2_scheme)):\n"
            "    try:\n"
            "        payload = decode_access_token(token)\n"
            "        email = payload.get('sub')\n"
            "        if not email or email not in DB_USERS:\n"
            "            raise HTTPException(status_code=401, detail='User not found')\n"
            "        u = DB_USERS[email]\n"
            "        return {'id': u['id'], 'email': u['email'], 'full_name': u['full_name']}\n"
            "    except Exception:\n"
            "        raise HTTPException(status_code=401, detail='Invalid token')\n"
        )
        self.workspace.write_file("backend/app/api/auth.py", auth_py)
        files_created.append("backend/app/api/auth.py")

        # 7. app/api/v1/endpoints.py
        if is_ecommerce:
            endpoints_py = (
                "from fastapi import APIRouter, HTTPException\n"
                "from typing import List\n"
                "from app.schemas.domain import ProductItem, OrderCreate, OrderResponse\n\n"
                "router = APIRouter(prefix='/store', tags=['Store & Checkout'])\n\n"
                "CATALOG: List[ProductItem] = [\n"
                "    ProductItem(id='p1', title='Wireless Pro Headphones', price=199.99, inventory=45, category='Electronics'),\n"
                "    ProductItem(id='p2', title='Ergonomic Desk Chair', price=349.00, inventory=12, category='Furniture'),\n"
                "    ProductItem(id='p3', title='Mechanical Keyboard RGB', price=129.50, inventory=80, category='Accessories'),\n"
                "]\n\n"
                "@router.get('/products', response_model=List[ProductItem])\n"
                "def list_products():\n"
                "    return CATALOG\n\n"
                "@router.post('/orders', response_model=OrderResponse)\n"
                "def create_order(order: OrderCreate):\n"
                "    prod = next((p for p in CATALOG if p.id == order.product_id), None)\n"
                "    if not prod:\n"
                "        raise HTTPException(status_code=404, detail='Product not found')\n"
                "    if prod.inventory < order.quantity:\n"
                "        raise HTTPException(status_code=400, detail='Insufficient stock')\n"
                "    prod.inventory -= order.quantity\n"
                "    return OrderResponse(\n"
                "        order_id=f'ord_{order.product_id}_1',\n"
                "        product_id=order.product_id,\n"
                "        quantity=order.quantity,\n"
                "        total_amount=round(prod.price * order.quantity, 2),\n"
                "        status='confirmed'\n"
                "    )\n"
            )
        elif is_social:
            endpoints_py = (
                "from fastapi import APIRouter\n"
                "from typing import List\n"
                "from app.schemas.domain import SocialMetricRecord, AnalyticsSummary\n\n"
                "router = APIRouter(prefix='/analytics', tags=['Social Analytics'])\n\n"
                "@router.get('/summary', response_model=AnalyticsSummary)\n"
                "def get_analytics_summary():\n"
                "    channels = [\n"
                "        SocialMetricRecord(platform='youtube', followers=125000, engagement_rate=6.8, views_last_30d=480000, posts_count=142),\n"
                "        SocialMetricRecord(platform='instagram', followers=98000, engagement_rate=4.2, views_last_30d=210000, posts_count=530),\n"
                "        SocialMetricRecord(platform='facebook', followers=64000, engagement_rate=2.1, views_last_30d=95000, posts_count=890),\n"
                "    ]\n"
                "    total = sum(c.followers for c in channels)\n"
                "    avg_eng = round(sum(c.engagement_rate for c in channels) / len(channels), 2)\n"
                "    return AnalyticsSummary(total_audience=total, average_engagement=avg_eng, channels=channels)\n"
            )
        else:
            endpoints_py = (
                "from fastapi import APIRouter\n"
                "from app.schemas.domain import ServiceInquiry, InquiryResponse\n\n"
                "router = APIRouter(prefix='/services', tags=['Services & Inquiries'])\n\n"
                "@router.post('/inquiry', response_model=InquiryResponse)\n"
                "def submit_inquiry(inquiry: ServiceInquiry):\n"
                "    return InquiryResponse(\n"
                "        id='inq_001',\n"
                "        status='received',\n"
                "        message=f'Thank you {inquiry.name}, we will respond to {inquiry.email}.'\n"
                "    )\n"
            )
        self.workspace.write_file("backend/app/api/v1/endpoints.py", endpoints_py)
        files_created.append("backend/app/api/v1/endpoints.py")

        # 8. app/main.py
        main_py = (
            "from fastapi import FastAPI\n"
            "from fastapi.middleware.cors import CORSMiddleware\n"
            "from app.core.config import settings\n"
            "from app.api.auth import router as auth_router\n"
            "from app.api.v1.endpoints import router as domain_router\n\n"
            "app = FastAPI(\n"
            "    title=settings.PROJECT_NAME,\n"
            "    openapi_url=f'{settings.API_V1_STR}/openapi.json',\n"
            "    docs_url=f'{settings.API_V1_STR}/docs'\n"
            ")\n\n"
            "app.add_middleware(\n"
            "    CORSMiddleware,\n"
            "    allow_origins=settings.ALLOWED_ORIGINS,\n"
            "    allow_credentials=True,\n"
            "    allow_methods=['*'],\n"
            "    allow_headers=['*'],\n"
            ")\n\n"
            "app.include_router(auth_router, prefix=settings.API_V1_STR)\n"
            "app.include_router(domain_router, prefix=settings.API_V1_STR)\n\n"
            "@app.get('/health', tags=['Health'])\n"
            "def health_check():\n"
            "    return {'status': 'healthy', 'service': settings.PROJECT_NAME}\n"
        )
        self.workspace.write_file("backend/app/main.py", main_py)
        files_created.append("backend/app/main.py")

        # 9. tests/test_api.py (Self-contained, verifiable test suite)
        test_py = (
            "import pytest\n"
            "from starlette.testclient import TestClient\n"
            "from app.main import app\n\n"
            "client = TestClient(app)\n\n"
            "def test_health_check():\n"
            "    response = client.get('/health')\n"
            "    assert response.status_code == 200\n"
            "    data = response.json()\n"
            "    assert data['status'] == 'healthy'\n\n"
            "def test_user_registration_and_login():\n"
            "    reg_res = client.post(\n"
            "        '/api/v1/auth/register',\n"
            "        json={'email': 'test@example.com', 'password': 'SecurePassword123!', 'full_name': 'Test User'}\n"
            "    )\n"
            "    assert reg_res.status_code == 201\n"
            "    data = reg_res.json()\n"
            "    assert data['email'] == 'test@example.com'\n\n"
            "    login_res = client.post(\n"
            "        '/api/v1/auth/login',\n"
            "        data={'username': 'test@example.com', 'password': 'SecurePassword123!'}\n"
            "    )\n"
            "    assert login_res.status_code == 200\n"
            "    token_data = login_res.json()\n"
            "    assert 'access_token' in token_data\n"
        )
        if is_ecommerce:
            test_py += (
                "\ndef test_ecommerce_flow():\n"
                "    products = client.get('/api/v1/store/products')\n"
                "    assert products.status_code == 200\n"
                "    items = products.json()\n"
                "    assert len(items) >= 1\n\n"
                "    order_res = client.post(\n"
                "        '/api/v1/store/orders',\n"
                "        json={'product_id': 'p1', 'quantity': 2, 'shipping_address': '123 Market St'}\n"
                "    )\n"
                "    assert order_res.status_code == 200\n"
                "    assert order_res.json()['status'] == 'confirmed'\n"
            )
        elif is_social:
            test_py += (
                "\ndef test_social_analytics_summary():\n"
                "    summary = client.get('/api/v1/analytics/summary')\n"
                "    assert summary.status_code == 200\n"
                "    data = summary.json()\n"
                "    assert data['total_audience'] > 0\n"
                "    assert len(data['channels']) == 3\n"
            )

        self.workspace.write_file("backend/tests/test_api.py", test_py)
        files_created.append("backend/tests/test_api.py")

        # Commit to feature branch
        commit_sha = self.github.commit_changes(
            message=f"feat(backend): implement FastAPI application with auth and domain routes ({len(files_created)} files)"
        )

        return WorkerResult(
            worker_name=self.worker_name,
            branch_name=self.default_branch,
            files_created=files_created,
            commit_sha=commit_sha,
            metadata={"file_count": len(files_created)}
        )
