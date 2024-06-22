import logging
import pickle
from pathlib import Path

from .paths import OUTPUT_PATH


def save_pkl(obj, name: str, path: Path = OUTPUT_PATH):
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / f"{name}.pkl"
    with open(filepath, "wb") as f:
        pickle.dump(obj, f)
    logging.info(f"Saved {name} to {filepath}")


def load_pkl(name: str, path: Path = OUTPUT_PATH):
    filepath = path / f"{name}.pkl"
    logging.info(f"Loding {name} from {filepath}")
    with open(filepath, "rb") as f:
        return pickle.load(f)
