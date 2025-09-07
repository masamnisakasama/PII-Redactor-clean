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

def apply(img, boxes, style="box"):
    for b in boxes:
        img = pixelate(img,b) if style=="pixelate" else (readable(img,b) if style=="readable" else box(img,b))
    return img
