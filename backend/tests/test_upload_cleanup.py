import logging

from app.services.upload_cleanup import cleanup_orphaned_uploads


def test_cleanup_removes_only_unreferenced_top_level_files(tmp_path):
    referenced = tmp_path / "active.txt"
    orphaned = tmp_path / "orphan.txt"
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    nested_orphan = nested_dir / "nested-orphan.txt"
    referenced.write_text("active", encoding="utf-8")
    orphaned.write_text("orphan", encoding="utf-8")
    nested_orphan.write_text("nested", encoding="utf-8")

    removed, failures = cleanup_orphaned_uploads(tmp_path, [str(referenced)])

    assert (removed, failures) == (1, 0)
    assert referenced.exists()
    assert not orphaned.exists()
    assert nested_orphan.exists()


def test_cleanup_preserves_protected_demo_pdfs(tmp_path):
    protected_files = [
        tmp_path / f"{index}_01_CBC_Blood_Report.pdf"
        for index in ("first", "second")
    ]
    protected_files.extend(
        [
            tmp_path / "third_02_Prescription_Demo.pdf",
            tmp_path / "fourth_03_Followup_Lipid_Report.pdf",
        ]
    )
    for path in protected_files:
        path.write_bytes(b"fixture")

    removed, failures = cleanup_orphaned_uploads(tmp_path, [])

    assert (removed, failures) == (0, 0)
    assert all(path.exists() for path in protected_files)


def test_cleanup_logs_and_counts_unlink_failures(tmp_path, monkeypatch, caplog):
    orphaned = tmp_path / "orphan.txt"
    orphaned.write_text("orphan", encoding="utf-8")
    real_unlink = type(orphaned).unlink

    def fail_unlink(path, *args, **kwargs):
        if path == orphaned:
            raise OSError("permission denied")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(type(orphaned), "unlink", fail_unlink)
    with caplog.at_level(logging.ERROR):
        removed, failures = cleanup_orphaned_uploads(tmp_path, [])

    assert (removed, failures) == (0, 1)
    assert orphaned.exists()
    assert "Could not remove orphaned upload file" in caplog.text