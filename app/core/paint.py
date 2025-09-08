# app/core/paint.py
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

def _clip(img,x,y,w,h):
    H,W=img.shape[:2]; x=max(0,min(x,W-1)); y=max(0,min(y,H-1))
    w=max(1,min(w,W-x)); h=max(1,min(h,H-y)); return x,y,w,h

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

# === 追加: カートゥーン化（完全オフライン） ===
def _cartoonize_crop(roi: np.ndarray,
                     bilateral_passes: int = 2,
                     d: int = 9, sigmaColor: int = 75, sigmaSpace: int = 75,
                     adaptive_block: int = 9, adaptive_C: int = 2) -> np.ndarray:
    """
    BGR ROI をカートゥーン風に。小さすぎる領域は pixelate へフォールバック。
    """
    h, w = roi.shape[:2]
    if h < 24 or w < 24:
        # 小さすぎると破綻しやすいので確実なマスクへ
        return _pixelate_crop_fallback(roi)

    # 1) 色面をならす（塗り絵っぽく）
    color = roi.copy()
    for _ in range(int(max(1, bilateral_passes))):
        color = cv2.bilateralFilter(color, d, sigmaColor, sigmaSpace)

    # 2) 輪郭（白=残す）マスク
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,
        adaptive_block, adaptive_C
    )
    # 3) マスク適用（白のみ残す）で漫画調
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    return cartoon

def _pixelate_crop_fallback(roi: np.ndarray, g: int = 12) -> np.ndarray:
    h, w = roi.shape[:2]
    if h < 2 or w < 2:
        return roi
    sh, sw = max(1, h // g), max(1, w // g)
    small = cv2.resize(roi, (sw, sh), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

def _apply_cartoon(img, b):
    x,y,w,h=_clip(img,*b)
    roi = img[y:y+h, x:x+w]
    try:
        stylized = _cartoonize_crop(roi)
    except Exception:
        # 失敗時は確実なマスクへ
        stylized = _pixelate_crop_fallback(roi)
    img[y:y+h, x:x+w] = stylized
    return img

def apply(img, boxes, style="box"):
    style = (style or "box").lower()
    for b in boxes:
        if style == "pixelate":
            img = pixelate(img, b)
        elif style == "readable":
            img = readable(img, b)
        elif style == "cartoon":            # ← 追加分岐
            img = _apply_cartoon(img, b)
        else:
            img = box(img, b)
    return img
