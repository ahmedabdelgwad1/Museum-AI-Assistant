import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image
from typing import Union
import logging

logger = logging.getLogger(__name__)

_HUB_REPO         = "facebookresearch/dinov2"
_HUB_MODEL        = "dinov2_vitb14"
_INPUT_SIZE       = 224
_IMAGENET_MEAN    = (0.485, 0.456, 0.406)
_IMAGENET_STD     = (0.229, 0.224, 0.225)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class DinoV2Encoder:
    """DINOv2 ViT-B/14 — L2-normalised 768-dim output per image."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        logger.info("Initializing DINOv2 model on %s...", DEVICE)
        self._model = torch.hub.load(_HUB_REPO, _HUB_MODEL, verbose=False)
        self._model.to(DEVICE).eval()
        self._transform = T.Compose([
            T.Resize(_INPUT_SIZE, interpolation=T.InterpolationMode.BICUBIC),
            T.CenterCrop(_INPUT_SIZE),
            T.ToTensor(),
            T.Normalize(_IMAGENET_MEAN, _IMAGENET_STD),
        ])
        logger.info("DINOv2 initialized successfully.")

    def embed(self, image_input: Union[str, Image.Image]) -> list[float] | None:
        """Single image → 768-dim float list. Returns None on failure."""
        try:
            img = (
                Image.open(image_input).convert("RGB")
                if isinstance(image_input, str)
                else image_input.convert("RGB")
            )
            t = self._transform(img).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                f = nn.functional.normalize(self._model(t), dim=1, p=2)
            # return as list for supabase pgvector
            return f.cpu().numpy().flatten().tolist()
        except Exception as e:
            logger.error("DINOv2 embedding failed: %s", e)
            return None
