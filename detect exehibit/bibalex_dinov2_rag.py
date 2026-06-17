"""
bibalex_dinov2_rag.py
─────────────────────────────────────────────────────────────────────────────
DINOv2 exhibit retrieval module — Bibalex Smart Tourist Robot.

Usage
─────
    from bibalex_dinov2_rag import initialise, get_exhibit_for_rag

    initialise("embeddings/DINOv2")          # once at startup

    result = get_exhibit_for_rag(pil_frame)  # per camera frame

Required artefacts
──────────────────
    embeddings.npy   float32  (N, 768)  L2-normalised reference vectors
    keys.json        list[str]           index-aligned exhibit keys
    meta.json        dict                key → {exhibit, section, description}
    config.json      dict                must contain best_threshold

Dependencies
────────────
    torch torchvision pillow numpy
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

_MODEL_NAME       = "DINOv2"
_HUB_REPO         = "facebookresearch/dinov2"
_HUB_MODEL        = "dinov2_vitb14"
_INPUT_SIZE       = 224
_IMAGENET_MEAN    = (0.485, 0.456, 0.406)
_IMAGENET_STD     = (0.229, 0.224, 0.225)
_DEFAULT_THRESHOLD = 0.35

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ─────────────────────────────────────────────────────────────────────────────
# Encoder
# ─────────────────────────────────────────────────────────────────────────────

class _DinoV2Encoder:
    """DINOv2 ViT-B/14 — L2-normalised 768-dim output per image."""

    def __init__(self) -> None:
        self._model = torch.hub.load(_HUB_REPO, _HUB_MODEL, verbose=False)
        self._model.to(DEVICE).eval()
        self._transform = T.Compose([
            T.Resize(_INPUT_SIZE, interpolation=T.InterpolationMode.BICUBIC),
            T.CenterCrop(_INPUT_SIZE),
            T.ToTensor(),
            T.Normalize(_IMAGENET_MEAN, _IMAGENET_STD),
        ])

    def embed(self, image_input: Union[str, Image.Image]) -> np.ndarray | None:
        """Single image → (768,) float32 array. Returns None on failure."""
        try:
            img = (
                Image.open(image_input).convert("RGB")
                if isinstance(image_input, str)
                else image_input.convert("RGB")
            )
            t = self._transform(img).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                f = nn.functional.normalize(self._model(t), dim=1, p=2)
            return f.cpu().numpy().flatten()
        except Exception:
            return None

    def embed_batch(
        self, images: list[Union[str, Image.Image]]
    ) -> np.ndarray | None:
        """
        Batch of images → (B, 768) float32 array in one forward pass.
        Faster than calling embed() in a loop when processing multiple frames.
        Returns None on failure.
        """
        try:
            tensors = []
            for img_input in images:
                img = (
                    Image.open(img_input).convert("RGB")
                    if isinstance(img_input, str)
                    else img_input.convert("RGB")
                )
                tensors.append(self._transform(img))
            batch = torch.stack(tensors).to(DEVICE)
            with torch.no_grad():
                f = nn.functional.normalize(self._model(batch), dim=1, p=2)
            return f.cpu().numpy()
        except Exception:
            return None


# ─────────────────────────────────────────────────────────────────────────────
# Artefact store
# ─────────────────────────────────────────────────────────────────────────────

class _ArtifactStore:
    """Holds pre-built embeddings and metadata loaded once from disk."""

    def __init__(self, embeddings_dir: str) -> None:
        base = Path(embeddings_dir)

        self.embeddings: np.ndarray = np.load(base / "embeddings.npy")

        with open(base / "keys.json", encoding="utf-8") as f:
            self.keys: list[str] = json.load(f)

        with open(base / "meta.json", encoding="utf-8") as f:
            self.meta: dict = json.load(f)

        with open(base / "config.json", encoding="utf-8") as f:
            self.threshold: float = float(
                json.load(f).get("best_threshold", _DEFAULT_THRESHOLD)
            )

        if self.embeddings.shape[0] != len(self.keys):
            raise ValueError(
                f"Artefact mismatch: {self.embeddings.shape[0]} embeddings "
                f"but {len(self.keys)} keys."
            )


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singletons
# ─────────────────────────────────────────────────────────────────────────────

_encoder: _DinoV2Encoder | None = None
_store:   _ArtifactStore | None = None


def _require_init() -> tuple[_DinoV2Encoder, _ArtifactStore]:
    if _encoder is None or _store is None:
        raise RuntimeError(
            "Module not initialised. Call initialise(embeddings_dir) at startup."
        )
    return _encoder, _store


# ─────────────────────────────────────────────────────────────────────────────
# Result builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_result(key: str, score: float, meta: dict, recognized: bool) -> dict:
    if not recognized:
        return {
            "exhibit_id":   "unknown",
            "exhibit_name": "Unknown",
            "section":      "Unknown",
            "description":  "",
            "confidence":   round(score, 4),
            "recognized":   False,
            "model_used":   _MODEL_NAME,
        }
    return {
        "exhibit_id":   key,
        "exhibit_name": meta.get("exhibit",     "Unknown"),
        "section":      meta.get("section",     "Unknown"),
        "description":  meta.get("description", ""),
        "confidence":   round(score, 4),
        "recognized":   True,
        "model_used":   _MODEL_NAME,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def initialise(embeddings_dir: str) -> None:
    """
    Load the DINOv2 model and artefacts once at application startup.

    embeddings_dir is fixed here. Do not pass a path on every inference call.

    Parameters
    ----------
    embeddings_dir : str
        Directory containing embeddings.npy, keys.json, meta.json, config.json.
    """
    global _encoder, _store
    _encoder = _DinoV2Encoder()
    _store   = _ArtifactStore(embeddings_dir)


def get_exhibit_for_rag(image_input: Union[str, Image.Image]) -> dict:
    """
    Single-image inference — designed for real-time camera frames.

    Parameters
    ----------
    image_input : str | PIL.Image.Image
        File path or PIL image (e.g. a frame captured from cv2 / picamera).

    Returns
    -------
    dict
        exhibit_id, exhibit_name, section, description,
        confidence, recognized, model_used
    """
    encoder, store = _require_init()

    vec = encoder.embed(image_input)
    if vec is None:
        return _build_result("unknown", 0.0, {}, False)

    # dot product == cosine similarity for L2-normalised vectors — no sklearn needed
    sims    = store.embeddings @ vec       # (N,)
    top_idx = int(sims.argmax())
    score   = float(sims[top_idx])
    key     = store.keys[top_idx]

    return _build_result(key, score, store.meta.get(key, {}), score >= store.threshold)


def get_exhibits_batch(
    images: list[Union[str, Image.Image]],
) -> list[dict]:
    """
    Batch inference — one GPU forward pass for all images.

    Use this when processing multiple frames at once (e.g. a frame buffer
    or a burst from the camera). More efficient than looping get_exhibit_for_rag().

    Parameters
    ----------
    images : list[str | PIL.Image.Image]

    Returns
    -------
    list[dict]  — one result dict per input image, in order.
    """
    encoder, store = _require_init()

    if not images:
        return []

    matrix = encoder.embed_batch(images)   # (B, 768) or None
    if matrix is None:
        return [_build_result("unknown", 0.0, {}, False) for _ in images]

    # (N, 768) @ (768, B) → (N, B)  — all similarities in one matmul
    sims_matrix = store.embeddings @ matrix.T
    top_indices = sims_matrix.argmax(axis=0)   # (B,)

    results = []
    for i, top_idx in enumerate(top_indices):
        score = float(sims_matrix[top_idx, i])
        key   = store.keys[int(top_idx)]
        results.append(
            _build_result(key, score, store.meta.get(key, {}), score >= store.threshold)
        )
    return results
