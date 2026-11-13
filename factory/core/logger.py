"""
Structured Factory Logger.
"""

import logging
import sys
from rich.console import Console
from rich.logging import RichHandler

console = Console()


def setup_logger(name: str = "ai_factory") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True
        )
        formatter = logging.Formatter("[%(name)s] %(message)s")
        rich_handler.setFormatter(formatter)
        logger.addHandler(rich_handler)
    return logger


logger = setup_logger()
