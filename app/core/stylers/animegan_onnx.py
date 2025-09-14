# app/core/stylers/animegan_onnx.py
# animeGANを使うファイル
import os
from pathlib import Path
import numpy as np
import cv2
import onnxruntime as ort


REPO_ROOT = Path(__file__).parents[3]
DEFAULT_DIR = REPO_ROOT / "models" / "animegan"
DEFAULT_MODEL = os.getenv("ANIMEGAN_MODEL", "AnimeGANv2_Hayao.onnx")

def _providers():
    av = set(ort.get_available_providers())
    return ["CUDAExecutionProvider"] if "CUDAExecutionProvider" in av else ["CPUExecutionProvider"]

class _AnimeGAN:
    _inst = None

    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
            cls._inst._init_session()
        return cls._inst

    def _init_session(self):
        model_path = Path(os.getenv("ANIMEGAN_MODEL_PATH", str(DEFAULT_DIR / DEFAULT_MODEL)))
        if not model_path.exists():
            raise FileNotFoundError(f"AnimeGAN ONNX not found: {model_path}")
        self.sess = ort.InferenceSession(str(model_path), providers=_providers())
        inp = self.sess.get_inputs()[0]
        self.input_name = inp.name
        shape = inp.shape  # [1,3,H,W] or [1,H,W,3]
        self.is_nchw = (len(shape) == 4 and shape[1] in (1, 3))

    @staticmethod
    def _pad32(h, w):
        return max(32, h - (h % 32)), max(32, w - (w % 32))

    def _pre(self, bgr: np.ndarray):
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        h32, w32 = self._pad32(h, w)
        x = cv2.resize(rgb, (w32, h32)).astype(np.float32) / 127.5 - 1.0
        if self.is_nchw:
            x = np.transpose(x, (2, 0, 1))  # HWC->CHW
        x = x[None, ...]
        return x, (w, h)

    def _post(self, out: np.ndarray, orig_wh):
        y = out[0]
        if self.is_nchw:
            y = np.transpose(y, (1, 2, 0))
        y = ((y + 1.0) * 127.5).clip(0, 255).astype(np.uint8)
        y = cv2.resize(y, orig_wh)
        return cv2.cvtColor(y, cv2.COLOR_RGB2BGR)

    def stylize(self, bgr: np.ndarray) -> np.ndarray:
        if bgr.size == 0:
            return bgr
        x, wh = self._pre(bgr)
        y = self.sess.run(None, {self.input_name: x})[0]
        return self._post(y, wh)

def animegan_stylize(bgr: np.ndarray) -> np.ndarray:
    return _AnimeGAN().stylize(bgr)
