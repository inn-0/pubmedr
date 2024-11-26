# utils.py

import json
from pathlib import Path
import pubmedr.data_store as data_store
from typing import Any

CACHE_FILE = "custom_cache.json"


def load_cache() -> dict:
    """Load cache from file, including data_store contents if available"""
    if Path(CACHE_FILE).exists():
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)

            # If we have a data store dump, restore it
            if "data_store_dump" in cache:
                for key, value in cache["data_store_dump"].items():
                    if value is not None and key.endswith("_data"):
                        # Get the type annotation directly from data_store
                        model_class = data_store.__annotations__[key].__args__[
                            0
                        ]  # Gets the non-None type from Optional
                        setattr(data_store, key, model_class.model_validate(value))

            return cache
    return {}


def save_cache(cache: dict[str, Any]) -> None:
    """Save cache to file, including current data_store contents"""
    data_store_dump = {}

    # Handle each data model separately
    data_models = [
        "s1_setup_data",
        "s2_settings_data",
        "s3_queries_data",
        "s4_results_data",
        "s5_saved_data",
    ]

    for key in data_models:
        value = getattr(data_store, key)
        if value is not None:
            # Convert each Pydantic model to dict first, using model_dump
            data_store_dump[key] = value.model_dump()
        else:
            data_store_dump[key] = None

    cache["data_store_dump"] = data_store_dump

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)
