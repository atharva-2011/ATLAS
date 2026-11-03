"""Unit and integration tests for ATLAS Backup & Disaster Recovery tool."""

import json
from pathlib import Path

import pytest

from infrastructure.scripts.backup_restore import BackupManager


@pytest.fixture
def temp_environment(tmp_path: Path) -> tuple[Path, Path, Path]:
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "backups"
    restore_dir = tmp_path / "restored"

    source_dir.mkdir()
    output_dir.mkdir()
    restore_dir.mkdir()

    # Create dummy database and storage
    db_file = source_dir / "test_orchestrator.db"
    db_file.write_text("DUMMY_SQLITE_HEADER_CONTENT_12345", encoding="utf-8")

    storage_dir = source_dir / ".atlas_storage" / "documents"
    storage_dir.mkdir(parents=True)
    (storage_dir / "doc1.txt").write_text("Document 1 content", encoding="utf-8")

    return source_dir, output_dir, restore_dir


def test_create_and_verify_backup(temp_environment: tuple[Path, Path, Path]) -> None:
    source_dir, output_dir, _ = temp_environment
    mgr = BackupManager(root_dir=source_dir)

    archive = mgr.create_backup(output_dir=output_dir)
    assert archive.exists()
    assert archive.name.endswith(".tar.gz")

    valid, msg = mgr.verify_backup(archive)
    assert valid is True
    assert "Valid ATLAS snapshot" in msg


def test_restore_backup(temp_environment: tuple[Path, Path, Path]) -> None:
    source_dir, output_dir, restore_dir = temp_environment
    mgr = BackupManager(root_dir=source_dir)

    archive = mgr.create_backup(output_dir=output_dir)
    success = mgr.restore_backup(archive_path=archive, target_dir=restore_dir)
    assert success is True

    # Validate restored files
    snapshot_dir = restore_dir / "atlas_snapshot"
    assert (snapshot_dir / "test_orchestrator.db").exists()
    assert (snapshot_dir / "storage" / "documents" / "doc1.txt").exists()
    assert (snapshot_dir / "backup_manifest.json").exists()

    with open(snapshot_dir / "backup_manifest.json", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["atlas_version"] == "0.1.0"
    assert len(manifest["files"]) == 2


def test_verify_corrupted_archive(tmp_path: Path) -> None:
    corrupt_file = tmp_path / "corrupt.tar.gz"
    corrupt_file.write_text("NOT_A_VALID_TAR_FILE", encoding="utf-8")

    mgr = BackupManager(root_dir=tmp_path)
    valid, msg = mgr.verify_backup(corrupt_file)
    assert valid is False
    assert "Verification failed" in msg
