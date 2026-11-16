"""
Database Architecture and Code Generation Worker.
Generates SQLAlchemy / Alembic migrations, MongoDB Motor schemas, Redis cache layers,
and database backup configurations.
"""

import json
import re
from typing import Any, Dict, List, Optional
from factory.core.logger import logger
from factory.generator.workers.base_worker import BaseWorker, WorkerResult


class DatabaseWorker(BaseWorker):
    """Generates database schema definitions, migrations, and cache configurations."""

    @property
    def worker_name(self) -> str:
        return "database"

    @property
    def default_branch(self) -> str:
        return "feature/database-schemas"

    async def generate_code(
        self,
        requirement_text: str,
        platform_targets: List[str],
        tech_stack: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkerResult:
        logger.info(f"DatabaseWorker generating database schemas for project: {self.workspace.project_id}")
        self.github.create_branch(self.default_branch)

        p_lower = requirement_text.lower()
        db_type = tech_stack.get("database", "PostgreSQL")
        is_mongo = "mongo" in db_type.lower() or "mongo" in p_lower
        is_ecommerce = any(k in p_lower for k in ["ecommerce", "e-commerce", "shop", "cart", "product", "stripe", "payment"])
        is_social = any(
            re.search(rf"\b{re.escape(term)}\b", p_lower)
            for term in ("social", "analytics", "youtube", "facebook", "instagram", "meta", "post", "follower")
        )
        is_employee = any(re.search(rf"\b{term}\b", p_lower) for term in ("employee", "employees", "staff", "payroll"))

        files_created: List[str] = []

        # 1. Database models
        if not is_mongo:
            # PostgreSQL SQLAlchemy Declarative Models
            models_py = (
                "from datetime import datetime\n"
                "from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index, Text\n"
                "from sqlalchemy.orm import declarative_base, relationship\n\n"
                "Base = declarative_base()\n\n"
                "class UserModel(Base):\n"
                "    __tablename__ = 'users'\n"
                "    id = Column(String(36), primary_key=True, index=True)\n"
                "    email = Column(String(255), unique=True, nullable=False, index=True)\n"
                "    hashed_password = Column(String(255), nullable=False)\n"
                "    full_name = Column(String(255), nullable=False)\n"
                "    created_at = Column(DateTime, default=datetime.utcnow)\n"
                "    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)\n"
            )
            if is_ecommerce:
                models_py += (
                    "\nclass ProductModel(Base):\n"
                    "    __tablename__ = 'products'\n"
                    "    id = Column(String(36), primary_key=True, index=True)\n"
                    "    title = Column(String(255), nullable=False)\n"
                    "    description = Column(Text, nullable=True)\n"
                    "    price = Column(Float, nullable=False)\n"
                    "    currency = Column(String(10), default='USD')\n"
                    "    inventory = Column(Integer, default=0)\n"
                    "    category = Column(String(100), index=True)\n"
                    "    created_at = Column(DateTime, default=datetime.utcnow)\n\n"
                    "    __table_args__ = (Index('ix_product_cat_price', 'category', 'price'),)\n\n"
                    "class OrderModel(Base):\n"
                    "    __tablename__ = 'orders'\n"
                    "    id = Column(String(36), primary_key=True, index=True)\n"
                    "    user_id = Column(String(36), ForeignKey('users.id'), index=True)\n"
                    "    product_id = Column(String(36), ForeignKey('products.id'), index=True)\n"
                    "    quantity = Column(Integer, nullable=False)\n"
                    "    total_amount = Column(Float, nullable=False)\n"
                    "    status = Column(String(50), default='pending', index=True)\n"
                    "    created_at = Column(DateTime, default=datetime.utcnow)\n"
                )
            elif is_employee:
                models_py += (
                    "\n    role = Column(String(50), nullable=False, default='employee', index=True)\n\n"
                    "class EmployeeModel(Base):\n"
                    "    __tablename__ = 'employees'\n"
                    "    id = Column(String(36), primary_key=True, index=True)\n"
                    "    full_name = Column(String(255), nullable=False)\n"
                    "    email = Column(String(255), unique=True, nullable=False, index=True)\n"
                    "    title = Column(String(255), nullable=False)\n"
                    "    department = Column(String(100), nullable=False, index=True)\n"
                    "    user_id = Column(String(36), ForeignKey('users.id'), nullable=True, index=True)\n"
                    "    created_at = Column(DateTime, default=datetime.utcnow)\n"
                )
            elif is_social:
                models_py += (
                    "\nclass SocialChannelModel(Base):\n"
                    "    __tablename__ = 'social_channels'\n"
                    "    id = Column(String(36), primary_key=True, index=True)\n"
                    "    platform = Column(String(50), nullable=False, index=True)\n"
                    "    channel_id = Column(String(100), nullable=False)\n"
                    "    channel_name = Column(String(255), nullable=False)\n"
                    "    followers = Column(Integer, default=0)\n"
                    "    views_total = Column(Integer, default=0)\n"
                    "    updated_at = Column(DateTime, default=datetime.utcnow)\n"
                )
            self.workspace.write_file("backend/app/models/entities.py", models_py)
            files_created.append("backend/app/models/entities.py")

            # Database session manager
            db_session_py = (
                "import os\n"
                "from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession\n"
                "from sqlalchemy.orm import sessionmaker\n\n"
                "DATABASE_URL = os.getenv('DATABASE_URL', '')\n\n"
                "def create_engine():\n"
                "    if not DATABASE_URL:\n"
                "        raise RuntimeError('DATABASE_URL is not configured')\n"
                "    return create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)\n\n"
                "def session_factory():\n"
                "    return sessionmaker(create_engine(), class_=AsyncSession, expire_on_commit=False)\n\n"
                "async def get_db():\n"
                "    Session = session_factory()\n"
                "    async with Session() as session:\n"
                "        yield session\n"
            )
            self.workspace.write_file("backend/app/db/session.py", db_session_py)
            files_created.append("backend/app/db/session.py")

            # Alembic migration configuration
            alembic_ini = (
                "[alembic]\n"
                "script_location = migrations\n"
                "sqlalchemy.url = postgresql://localhost/app_db\n\n"
                "[loggers]\nkeys = root,sqlalchemy,alembic\n"
                "[handlers]\nkeys = console\n"
                "[formatters]\nkeys = generic\n"
                "[logger_root]\nlevel = WARN\nhandlers = console\nqualname =\n"
                "[logger_sqlalchemy]\nlevel = WARN\nhandlers =\nqualname = sqlalchemy.engine\n"
                "[logger_alembic]\nlevel = INFO\nhandlers =\nqualname = alembic\n"
                "[handler_console]\nclass = StreamHandler\nargs = (sys.stderr,)\nlevel = NOTSET\nformatter = generic\n"
                "[formatter_generic]\nformat = %(levelname)-5.5s [%(name)s] %(message)s\n"
            )
            self.workspace.write_file("backend/alembic.ini", alembic_ini)
            files_created.append("backend/alembic.ini")

            env_py = (
                "import os\n"
                "from alembic import context\n"
                "from sqlalchemy import engine_from_config, pool\n\n"
                "config = context.config\n"
                "url = os.getenv('DATABASE_URL', '')\n"
                "if not url:\n"
                "    raise RuntimeError('DATABASE_URL is not configured')\n"
                "if url.startswith('postgresql+asyncpg'):\n"
                "    url = 'postgresql+psycopg2' + url[len('postgresql+asyncpg'):]\n"
                "config.set_main_option('sqlalchemy.url', url)\n\n"
                "def run_migrations_online() -> None:\n"
                "    connectable = engine_from_config(\n"
                "        config.get_section(config.config_ini_section) or {},\n"
                "        prefix='sqlalchemy.',\n"
                "        poolclass=pool.NullPool,\n"
                "    )\n"
                "    with connectable.connect() as connection:\n"
                "        context.configure(connection=connection, target_metadata=None)\n"
                "        with context.begin_transaction():\n"
                "            context.run_migrations()\n\n"
                "run_migrations_online()\n"
            )
            self.workspace.write_file("backend/migrations/env.py", env_py)
            files_created.append("backend/migrations/env.py")

            if is_employee:
                upgrade_body = (
                    "    op.create_table(\n"
                    "        'users',\n"
                    "        sa.Column('id', sa.String(length=36), primary_key=True),\n"
                    "        sa.Column('email', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('hashed_password', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('full_name', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('role', sa.String(length=50), nullable=False),\n"
                    "        sa.Column('created_at', sa.DateTime(), nullable=True),\n"
                    "    )\n"
                    "    op.create_index('ix_users_email', 'users', ['email'], unique=True)\n"
                    "    op.create_table(\n"
                    "        'employees',\n"
                    "        sa.Column('id', sa.String(length=36), primary_key=True),\n"
                    "        sa.Column('full_name', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('email', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('title', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('department', sa.String(length=100), nullable=False),\n"
                    "        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id'), nullable=True),\n"
                    "        sa.Column('created_at', sa.DateTime(), nullable=True),\n"
                    "    )\n"
                    "    op.create_index('ix_employees_email', 'employees', ['email'], unique=True)\n"
                )
            elif is_ecommerce:
                upgrade_body = (
                    "    op.create_table(\n"
                    "        'users',\n"
                    "        sa.Column('id', sa.String(length=36), primary_key=True),\n"
                    "        sa.Column('email', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('hashed_password', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('full_name', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('created_at', sa.DateTime(), nullable=True),\n"
                    "    )\n"
                    "    op.create_table(\n"
                    "        'products',\n"
                    "        sa.Column('id', sa.String(length=36), primary_key=True),\n"
                    "        sa.Column('title', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('price', sa.Float(), nullable=False),\n"
                    "        sa.Column('inventory', sa.Integer(), nullable=False),\n"
                    "        sa.Column('category', sa.String(length=100), nullable=True),\n"
                    "    )\n"
                    "    op.create_table(\n"
                    "        'orders',\n"
                    "        sa.Column('id', sa.String(length=36), primary_key=True),\n"
                    "        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id')),\n"
                    "        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id')),\n"
                    "        sa.Column('quantity', sa.Integer(), nullable=False),\n"
                    "        sa.Column('total_amount', sa.Float(), nullable=False),\n"
                    "        sa.Column('status', sa.String(length=50), nullable=False),\n"
                    "    )\n"
                )
            else:
                upgrade_body = (
                    "    op.create_table(\n"
                    "        'users',\n"
                    "        sa.Column('id', sa.String(length=36), primary_key=True),\n"
                    "        sa.Column('email', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('hashed_password', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('full_name', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('created_at', sa.DateTime(), nullable=True),\n"
                    "    )\n"
                    "    op.create_table(\n"
                    "        'inquiries',\n"
                    "        sa.Column('id', sa.String(length=36), primary_key=True),\n"
                    "        sa.Column('name', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('email', sa.String(length=255), nullable=False),\n"
                    "        sa.Column('message', sa.Text(), nullable=False),\n"
                    "        sa.Column('status', sa.String(length=50), nullable=False),\n"
                    "    )\n"
                )
            alembic_migration = (
                '"""initial schema\n\nRevision ID: 001_initial\nRevises:\nCreate Date: 2026-01-01\n"""\n'
                "from alembic import op\n"
                "import sqlalchemy as sa\n\n"
                "revision = '001_initial'\n"
                "down_revision = None\n"
                "branch_labels = None\n"
                "depends_on = None\n\n"
                "def upgrade() -> None:\n"
                + upgrade_body
                + "\ndef downgrade() -> None:\n"
                "    pass\n"
            )
            self.workspace.write_file("backend/migrations/versions/001_initial_schema.py", alembic_migration)
            files_created.append("backend/migrations/versions/001_initial_schema.py")

        else:
            # MongoDB Motor client and documents
            mongo_py = (
                "import os\n"
                "from motor.motor_asyncio import AsyncIOMotorClient\n\n"
                "MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')\n"
                "DB_NAME = os.getenv('MONGO_DB', 'app_data')\n\n"
                "client = AsyncIOMotorClient(MONGO_URI)\n"
                "db = client[DB_NAME]\n\n"
                "async def ensure_indexes():\n"
                "    await db.users.create_index('email', unique=True)\n"
                "    await db.analytics.create_index([('platform', 1), ('timestamp', -1)])\n"
            )
            self.workspace.write_file("backend/app/db/mongodb.py", mongo_py)
            files_created.append("backend/app/db/mongodb.py")

        # 2. Redis Cache Layer
        redis_py = (
            "import os\n"
            "import json\n"
            "from typing import Optional, Any\n\n"
            "REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')\n\n"
            "class CacheService:\n"
            "    def __init__(self):\n"
            "        self._in_memory = {}\n\n"
            "    async def get(self, key: str) -> Optional[Any]:\n"
            "        return self._in_memory.get(key)\n\n"
            "    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:\n"
            "        self._in_memory[key] = value\n\n"
            "    async def delete(self, key: str) -> None:\n"
            "        self._in_memory.pop(key, None)\n\n"
            "cache = CacheService()\n"
        )
        self.workspace.write_file("backend/app/db/redis_cache.py", redis_py)
        files_created.append("backend/app/db/redis_cache.py")

        # 3. Database backup script
        backup_sh = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n\n"
            "BACKUP_DIR=\"./backups/$(date +%Y%m%d_%H%M%S)\"\n"
            "mkdir -p \"$BACKUP_DIR\"\n\n"
            "echo \"[BACKUP] Starting automated database backup into $BACKUP_DIR...\"\n"
            "if [ \"${DB_TYPE:-postgres}\" = \"postgres\" ]; then\n"
            "  pg_dump -h \"${DB_HOST:-localhost}\" -U \"${DB_USER:-postgres}\" \"${DB_NAME:-app_db}\" | gzip > \"$BACKUP_DIR/postgres_dump.sql.gz\"\n"
            "else\n"
            "  mongodump --uri=\"${MONGO_URI:-mongodb://localhost:27017}\" --out=\"$BACKUP_DIR/mongo_dump\"\n"
            "fi\n\n"
            "echo \"[BACKUP] Backup file written to $BACKUP_DIR.\"\n"
        )
        self.workspace.write_file("scripts/backup_database.sh", backup_sh)
        files_created.append("scripts/backup_database.sh")

        commit_sha = self.github.commit_changes(
            message=f"feat(database): configure schemas, migrations, redis cache, and backup scripts ({len(files_created)} files)"
        )

        return WorkerResult(
            worker_name=self.worker_name,
            branch_name=self.default_branch,
            files_created=files_created,
            commit_sha=commit_sha,
            metadata={"db_type": db_type, "file_count": len(files_created)}
        )
