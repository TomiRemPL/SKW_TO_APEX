"""Moduł logowania aplikacji — konfiguruje zapis logów do pliku.

Wszystkie komunikaty logging.info/warning/error trafiają do stałego pliku
_out/apex_export.log (append mode) z timestampem.
"""
from __future__ import annotations
import logging
from pathlib import Path

_file_handler: logging.FileHandler | None = None


def setup_file_logging(output_dir: str) -> None:
    """Dodaj FileHandler zapisujący logi do pliku apex_export.log.

    Args:
        output_dir: Katalog wyjściowy (np. '_out')
    """
    global _file_handler
    if _file_handler is not None:
        return  # Już skonfigurowany

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    log_file = out_path / "apex_export.log"

    _file_handler = logging.FileHandler(str(log_file), mode="a", encoding="utf-8")
    _file_handler.setLevel(logging.INFO)
    _file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    root_logger = logging.getLogger()
    root_logger.addHandler(_file_handler)
    logging.info("--- Nowa sesja eksportu ---")
