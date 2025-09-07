# app/core/face_cv2.py  （全面置換）
import os, cv2, numpy as np

def _try_path(base, name):
    p = os.path.join(base, name)
    return p if os.path.exists(p) else None

def _cascade_paths():
    paths = []
    # 1) OpenCV 内蔵
    data = getattr(cv2.data, "haarcascades", None)
    if data:
        for n in ("haarcascade_frontalface_default.xml",
                  "haarcascade_frontalface_alt2.xml",
                  "haarcascade_profileface.xml"):
            p = _try_path(data, n)
            if p: paths.append(p)
    # 2) プロジェクト同梱（models/）
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models"))
    for n in ("haarcascade_frontalface_default.xml",
              "haarcascade_frontalface_alt2.xml",
              "haarcascade_profileface.xml"):
        p = _try_path(here, n)
        if p and p not in paths: paths.append(p)
    # 3) 環境変数（カンマ区切りで複数OK）
    extra = os.getenv("OPENCV_HAAR_PATHS", "")
    for p in [s.strip() for s in extra.split(",") if s.strip()]:
        if os.path.exists(p) and p not in paths: paths.append(p)
    if not paths:
        raise FileNotFoundError("haar cascades not found")
    return paths

def _load_cascades():
    cs=[]
    for p in _cascade_paths():
        c = cv2.CascadeClassifier(p)
        if not c.empty():
            cs.append((os.path.basename(p), c))
    if not cs:
        raise RuntimeError("Failed to load any Haar cascade")
    return cs

def _detect_with(cas: cv2.CascadeClassifier, gray, min_size, sf, mn):
    rects = cas.detectMultiScale(gray, scaleFactor=sf, minNeighbors=mn,
                                 minSize=(min_size, min_size),
                                 flags=cv2.CASCADE_SCALE_IMAGE)
    return [(int(x),int(y),int(w),int(h)) for (x,y,w,h) in rects]

def _iou(a, b):
    ax,ay,aw,ah = a; bx,by,bw,bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax+aw, bx+bw), min(ay+ah, by+bh)
    iw, ih = max(0, x2-x1), max(0, y2-y1)
    inter = iw*ih
    if inter == 0: return 0.0
    ua = aw*ah + bw*bh - inter
    return inter/ua if ua>0 else 0.0

def _dedup(boxes, thr=0.4):
    out=[]
    for b in boxes:
        if all(_iou(b, o) < thr for o in out):
            out.append(b)
    return out

def detect_faces_bgr(img_bgr: np.ndarray):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    H, W = gray.shape[:2]
    min_size = int(os.getenv("FACE_MIN_SIZE_PX", "20"))
    scaleFactor = float(os.getenv("FACE_CASCADE_SCALE_FACTOR", "1.05"))
    minNeighbors = int(os.getenv("FACE_CASCADE_MIN_NEIGHBORS", "2"))

    # 小さい画像はアップサンプリング、大きい画像は軽くダウンサンプリングで速度を確保
    scale = 1.0
    short = min(H, W)
    if short < 320:
        scale = 320.0 / short
    elif short > 1600:
        scale = 1600.0 / short
    if scale != 1.0:
        gray_scaled = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    else:
        gray_scaled = gray

    cascades = _load_cascades()
    boxes = []

    # 1) 正面想定（default/alt2） on scaled
    for name, cas in cascades:
        if "frontalface" in name:
            for (x,y,w,h) in _detect_with(cas, gray_scaled, min_size, scaleFactor, minNeighbors):
                if scale != 1.0:
                    x,y,w,h = int(x/scale), int(y/scale), int(w/scale), int(h/scale)
                boxes.append((x,y,w,h))

    # 2) 横顔（profile） on scaled と、左右裏返し
    for name, cas in cascades:
        if "profileface" in name:
            # 通常
            for (x,y,w,h) in _detect_with(cas, gray_scaled, min_size, scaleFactor, minNeighbors):
                if scale != 1.0:
                    x,y,w,h = int(x/scale), int(y/scale), int(w/scale), int(h/scale)
                boxes.append((x,y,w,h))
            # 左右反転
            flipped = cv2.flip(gray_scaled, 1)
            Wf = flipped.shape[1]
            for (x,y,w,h) in _detect_with(cas, flipped, min_size, scaleFactor, minNeighbors):
                # 反転座標を元に戻す
                x = Wf - (x + w)
                if scale != 1.0:
                    x,y,w,h = int(x/scale), int(y/scale), int(w/scale), int(h/scale)
                boxes.append((x,y,w,h))

    # サイズ/比率の軽いフィルタ
    out=[]
    for (x,y,w,h) in _dedup(boxes, thr=0.4):
        if w>=min_size and h>=min_size and 0.4 <= (w/max(h,1)) <= 2.5:
            out.append((x,y,w,h))
    return out
