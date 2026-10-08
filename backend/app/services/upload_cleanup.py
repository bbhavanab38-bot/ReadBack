import logging
from pathlib import Path
from typing import Iterable, Optional, Union

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]

PROTECTED_DEMO_PDFS = {
    "01_CBC_Blood_Report.pdf",
    "02_Prescription_Demo.pdf",
    "03_Followup_Lipid_Report.pdf",
}


def cleanup_orphaned_uploads(
    upload_dir: PathLike,
    referenced_paths: Iterable[Optional[PathLike]],
) -> tuple[int, int]:
    """Delete only unreferenced regular files directly inside the upload directory."""
    root = Path(upload_dir).resolve()
    if not root.is_dir():
        logger.warning("Upload cleanup skipped; directory does not exist: %s", root)
        return 0, 1

    referenced = set()
    for file_path in referenced_paths:
        if file_path:
            try:
                referenced.add(Path(file_path).resolve())
            except OSError:
                logger.exception("Could not resolve active upload reference: %s", file_path)
                return 0, 1

    removed = 0
    failures = 0
    try:
        entries = list(root.iterdir())
    except OSError:
        logger.exception("Could not list upload directory during cleanup: %s", root)
        return 0, 1

    for entry in entries:
        if entry.is_symlink() or not entry.is_file():
            continue
        if entry.name in PROTECTED_DEMO_PDFS or any(
            entry.name.endswith(f"_{filename}") for filename in PROTECTED_DEMO_PDFS
        ):
            continue

        try:
            if entry.resolve() in referenced:
                continue
            entry.unlink()
            removed += 1
            logger.info("Removed orphaned upload file: %s", entry.name)
        except OSError:
            failures += 1
            logger.exception("Could not remove orphaned upload file: %s", entry)

    return removed, failures