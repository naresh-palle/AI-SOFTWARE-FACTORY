"""
Tests for Disaster Recovery, Backup Restoration & State Survival.
Verifies backup creation, SHA-256 verification, restore exercises,
and tampered backup detection.
"""

import os
import tempfile
import pytest
from factory.core.disaster_recovery import DisasterRecoveryManager


def test_disaster_recovery_backup_and_restore_exercise():
    """Execute complete backup, checksum verification, and restore cycle."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy db file
        source_db = os.path.join(tmpdir, "primary.db")
        with open(source_db, "w") as f:
            f.write("SAMPLE_FACTORY_DATA_RECORD_001\n")

        # 1. Create Backup
        manifest = DisasterRecoveryManager.create_database_backup(source_db)
        assert manifest["status"] == "COMPLETED"
        assert manifest["verified"] is True
        assert os.path.exists(manifest["backup_path"])

        # 2. Restore to secondary target
        restore_target = os.path.join(tmpdir, "restored_primary.db")
        manifest_file = manifest["backup_path"] + ".json"
        res = DisasterRecoveryManager.restore_database_backup(manifest_file, restore_target)

        assert res["status"] == "SUCCESS"
        assert res["sha256_verified"] is True
        assert os.path.exists(restore_target)

        # Check content matches
        with open(restore_target, "r") as f:
            content = f.read()
        assert "SAMPLE_FACTORY_DATA_RECORD_001" in content


def test_tampered_backup_restoration_rejected():
    """Verify that a corrupted or tampered backup file is rejected during restore."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_db = os.path.join(tmpdir, "primary.db")
        with open(source_db, "w") as f:
            f.write("INITIAL_DATA\n")

        manifest = DisasterRecoveryManager.create_database_backup(source_db)
        backup_file = manifest["backup_path"]

        # Intentionally tamper with backup bytes
        with open(backup_file, "a") as f:
            f.write("MALICIOUS_TAMPERED_APPENDED_BYTES\n")

        restore_target = os.path.join(tmpdir, "should_fail.db")
        manifest_file = backup_file + ".json"

        # Restoration must fail with integrity check error
        with pytest.raises(ValueError, match="Integrity check failed"):
            DisasterRecoveryManager.restore_database_backup(manifest_file, restore_target)
