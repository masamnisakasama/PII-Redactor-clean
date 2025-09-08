# app/core/paint.py
import cv2, numpy as np, os
from PIL import Image, ImageDraw, ImageFont

def _clip(img,x,y,w,h):
    H,W=img.shape[:2]; x=max(0,min(x,W-1)); y=max(0,min(y,H-1))
    w=max(1,min(w,W-x)); h=max(1,min(h,H-y)); return x,y,w,h

def _pad_clip(img,x,y,w,h,pad=0.2):
    """ボックスを左右上下に pad してから画像内にクリップ"""
    if pad <= 0: return _clip(img,x,y,w,h)
    H,W=img.shape[:2]
    px, py = int(round(w*pad)), int(round(h*pad))
    x, y = x - px, y - py
    w, h = w + 2*px, h + 2*py
    return _clip(img,x,y,w,h)

def box(img, b):
    x,y,w,h=_clip(img,*b); cv2.rectangle(img,(x,y),(x+w,y+h),(0,0,0),-1); return img

def pixelate(img,b,g=12):
    x,y,w,h=_clip(img,*b); roi=img[y:y+h,x:x+w]
    if roi.size==0: return img
    small=cv2.resize(roi,(max(1,w//g),max(1,h//g)))
    img[y:y+h,x:x+w]=cv2.resize(small,(w,h),interpolation=cv2.INTER_NEAREST); return img

def readable(img,b,text="REDACTED"):
    x,y,w,h=_clip(img,*b); img[y:y+h,x:x+w]=(255,255,255)
    im=Image.fromarray(img[:,:,::-1].copy()); dr=ImageDraw.Draw(im)
    font=ImageFont.load_default(); tw,th=dr.textbbox((0,0),text,font=font)[2:]
    dr.text((x+(w-tw)//2,y+(h-th)//2), text, fill=(0,0,0), font=font)
    return np.array(im)[:,:,::-1].copy()

# --- cartoon 用の簡易スタイライズ（完全オフライン）---
def _pixelate_crop_fallback(roi: np.ndarray, g: int = 12) -> np.ndarray:
    h, w = roi.shape[:2]
    if h < 2 or w < 2: return roi
    sh, sw = max(1, h//g), max(1, w//g)
    small = cv2.resize(roi, (sw, sh), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

def _cartoonize_crop(roi: np.ndarray) -> np.ndarray:
    h, w = roi.shape[:2]
    if h < 24 or w < 24:
        return _pixelate_crop_fallback(roi)   # 小さすぎる領域は確実にマスク
    color = roi.copy()
    # 色面を均す
    for _ in range(2):  # 必要なら 1 に
        color = cv2.bilateralFilter(color, 9, 75, 75)
    # エッジ抽出（白=残す）
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(gray, 255,
                                  cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,
                                  9, 2)
    return cv2.bitwise_and(color, color, mask=edges)

def _apply_cartoon(img, b, pad_ratio: float):
    x,y,w,h=_pad_clip(img,*b,pad=pad_ratio)
    roi = img[y:y+h, x:x+w]
    try:
        stylized = _cartoonize_crop(roi)
    except Exception:
        stylized = _pixelate_crop_fallback(roi)
    img[y:y+h, x:x+w] = stylized
    return img

def apply(img, boxes, style="box"):
    style = (style or "box").lower()
    pad_ratio = float(os.getenv("PAD_RATIO", "0.2"))  # ← 既定20%だけ広げる
    for b in boxes:
        if style == "pixelate":
            img = pixelate(img, b)
        elif style == "readable":
            img = readable(img, b)
        elif style == "cartoon":                 
            img = _apply_cartoon(img, b, pad_ratio)
        else:
            img = box(img, b)
    return img
