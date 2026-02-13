import json
import logging
import os


def configure_logging(log_path: str) -> logging.Logger:
    logger = logging.getLogger("aggregator")
    if logger.handlers:
        return logger

    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def load_feeds_config(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as handle:
        feeds = json.load(handle)

    normalized = []
    for feed in feeds:
        if feed.get("enabled", True) is False:
            continue
        normalized.append(feed)
    return normalized
