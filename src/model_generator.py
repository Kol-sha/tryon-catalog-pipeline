import logging
from typing import Optional

import torch
from PIL import Image
from diffusers import (
    StableDiffusionPipeline,
    DPMSolverMultistepScheduler,
    AutoencoderKL,
)

from config import config
from src.model_storage import ModelStorage

logger = logging.getLogger(__name__)


class ModelGenerator:

    MODEL_ID = "SG161222/Realistic_Vision_V5.1_noVAE"
    VAE_ID   = "stabilityai/sd-vae-ft-mse"

    def __init__(self, device: Optional[str] = None):
        self.device = device or config.DEVICE

        if self.device == "cuda" and not torch.cuda.is_available():
            self.device = "mps" if torch.backends.mps.is_available() else "cpu"

        self.pipe = None
        logger.info(f"ModelGenerator — device: {self.device}")
        self._load_model()

    def _get_dtype(self) -> torch.dtype:
        """MPS must use float32 — float16 causes NaN/black images."""
        if self.device == "cuda":
            return torch.float16
        return torch.float32  # MPS and CPU

    def _load_model(self) -> None:
        logger.info(f"Loading: {self.MODEL_ID}  (~2 GB)")

        dtype = self._get_dtype()
        logger.info(f"Using dtype: {dtype}")

        vae = None
        try:
            vae = AutoencoderKL.from_pretrained(self.VAE_ID, torch_dtype=dtype)
            logger.info("Custom VAE loaded.")
        except Exception as e:
            logger.warning(f"Custom VAE failed ({e}), using default.")

        self.pipe = StableDiffusionPipeline.from_pretrained(
            self.MODEL_ID,
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
            vae=vae,
        )

        self.pipe.scheduler = DPMSolverMultistepScheduler(
            beta_start=0.00085,
            beta_end=0.012,
            beta_schedule="scaled_linear",
            num_train_timesteps=1000,
            algorithm_type="dpmsolver++",
            use_karras_sigmas=True,
            final_sigmas_type="sigma_min",
        )

        self.pipe = self.pipe.to(self.device)
        self.pipe.enable_attention_slicing()

        logger.info(f"ModelGenerator ready on {self.device} ({dtype}).")

    def generate_model_image(
        self,
        gender: str,
        angle: str,
        seed: Optional[int] = None,
        save_model: bool = True,
    ) -> Image.Image:
        """Генерирует изображение модели и опционально сохраняет в хранилище."""
        
        prompt = config.MODEL_PROMPTS[gender][angle]
        negative_prompt = config.NEGATIVE_PROMPT
        
        generator = None
        if seed is not None:
            gen_device = "cpu" if self.device == "mps" else self.device
            generator = torch.Generator(device=gen_device).manual_seed(seed)
        
        logger.info(f"Generating {gender} / {angle} ...")
        
        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=512,
            height=768,
            num_inference_steps=config.NUM_INFERENCE_STEPS,
            guidance_scale=config.GUIDANCE_SCALE,
            generator=generator,
        )
        
        image = result.images[0]
        image = self._validate_image(image)
        image = image.resize(config.IMAGE_SIZE, Image.LANCZOS)
        
        # Сохраняем модель в хранилище
        if save_model:
            storage = ModelStorage()
            storage.save_model(gender, angle, image)
            logger.info(f"Saved model for {gender}/{angle}")
        
        return image

    def _validate_image(self, image: Image.Image) -> Image.Image:
        """Detect black/NaN images and retry with CPU fallback."""
        import numpy as np
        arr = np.array(image)

        if arr.mean() < 5:
            logger.warning(
                "Black image detected (mean=%0.1f). "
                "MPS float16 NaN bug — retrying on CPU...",
                arr.mean(),
            )
            # Re-run on CPU as fallback
            self.pipe = self.pipe.to("cpu")
            generator = torch.Generator(device="cpu").manual_seed(config.SEED)

            result = self.pipe(
                prompt=config.MODEL_PROMPTS["male"]["front"],
                negative_prompt=config.NEGATIVE_PROMPT,
                width=512,
                height=768,
                num_inference_steps=config.NUM_INFERENCE_STEPS,
                guidance_scale=config.GUIDANCE_SCALE,
                generator=generator,
            )
            self.pipe = self.pipe.to(self.device)
            return result.images[0]

        return image

    def unload(self) -> None:
        del self.pipe
        self.pipe = None
        if self.device == "cuda":
            torch.cuda.empty_cache()
        elif self.device == "mps":
            torch.mps.empty_cache()
        logger.info("ModelGenerator unloaded.")