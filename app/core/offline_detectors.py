import os, io, re, urllib.request, pathlib, cv2, numpy as np
from typing import List, Tuple, Dict
from PIL import Image, ImageOps

# ---------- 共通 ----------
def bgr_from_bytes(b:bytes):
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(b))).convert("RGB")
    return np.array(im)[:,:,::-1].copy()

# ---------- 顔: haar or dnn ----------
# Haar (cv2同梱 or models/)
def _haar_paths():
    paths=[]
    d=getattr(cv2.data,"haarcascades",None)
    if d:
        for n in ("haarcascade_frontalface_default.xml","haarcascade_frontalface_alt2.xml","haarcascade_profileface.xml"):
            p=os.path.join(d,n); 
            if os.path.exists(p): paths.append(p)
    here=os.path.abspath(os.path.join(os.path.dirname(__file__),"../../models"))
    for n in ("haarcascade_frontalface_default.xml","haarcascade_frontalface_alt2.xml","haarcascade_profileface.xml"):
        p=os.path.join(here,n); 
        if os.path.exists(p) and p not in paths: paths.append(p)
    return paths

def detect_faces_haar(img_bgr: np.ndarray) -> List[Tuple[int,int,int,int]]:
    gray=cv2.cvtColor(img_bgr,cv2.COLOR_BGR2GRAY); gray=cv2.equalizeHist(gray)
    H,W=gray.shape[:2]; ms=int(os.getenv("FACE_MIN_SIZE_PX","24"))
    sf=float(os.getenv("FACE_CASCADE_SCALE_FACTOR","1.05")); mn=int(os.getenv("FACE_CASCADE_MIN_NEIGHBORS","3"))
    scale=1.0; short=min(H,W)
    if short<320: scale=320/short
    elif short>1600: scale=1600/short
    g = cv2.resize(gray,None,fx=scale,fy=scale) if scale!=1.0 else gray
    boxes=[]
    for p in _haar_paths():
        cas=cv2.CascadeClassifier(p)
        if cas.empty(): continue
        rects=cas.detectMultiScale(g,scaleFactor=sf,minNeighbors=mn,minSize=(ms,ms))
        for (x,y,w,h) in rects:
            if scale!=1.0: x,y,w,h=int(x/scale),int(y/scale),int(w/scale),int(h/scale)
            if w>=ms and h>=ms: boxes.append((x,y,w,h))
    # 重複除去
    def iou(a,b):
        ax,ay,aw,ah=a; bx,by,bw,bh=b
        x1,y1=max(ax,bx),max(ay,by); x2,y2=min(ax+aw,bx+bw),min(ay+ah,by+bh)
        iw,ih=max(0,x2-x1),max(0,y2-y1); inter=iw*ih; ua=aw*ah+bw*bh-inter
        return inter/ua if ua>0 else 0.0
    out=[]
    for b in boxes:
        if all(iou(b,o)<0.4 for o in out): out.append(b)
    return out

# DNN (res10 SSD) — 初回自動DL
_MODEL_DIR = pathlib.Path(__file__).resolve().parents[2] / "models"
_PROTO = _MODEL_DIR / "deploy.prototxt"
_WEIGHTS = _MODEL_DIR / "res10_300x300_ssd_iter_140000.caffemodel"
_URL_PROTO   = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
_URL_WEIGHTS = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_models_202005/face_detector/res10_300x300_ssd_iter_140000.caffemodel"

def _ensure_dnn():
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if not _PROTO.exists(): urllib.request.urlretrieve(_URL_PROTO, _PROTO.as_posix())
    if not _WEIGHTS.exists(): urllib.request.urlretrieve(_URL_WEIGHTS, _WEIGHTS.as_posix())

def detect_faces_dnn(img_bgr: np.ndarray) -> List[Tuple[int,int,int,int]]:
    _ensure_dnn()
    net=cv2.dnn.readNetFromCaffe(_PROTO.as_posix(), _WEIGHTS.as_posix())
    H,W=img_bgr.shape[:2]
    blob=cv2.dnn.blobFromImage(img_bgr, 1.0, (300,300), (104.0,177.0,123.0), False, False)
    net.setInput(blob); det=net.forward()
    thr=float(os.getenv("FACE_DNN_CONF","0.6"))
    boxes=[]
    for i in range(det.shape[2]):
        conf=float(det[0,0,i,2])
        if conf<thr: continue
        x1=int(det[0,0,i,3]*W); y1=int(det[0,0,i,4]*H)
        x2=int(det[0,0,i,5]*W); y2=int(det[0,0,i,6]*H)
        boxes.append((max(0,x1),max(0,y1),max(1,x2-x1),max(1,y2-y1)))
    return boxes

def detect_faces(img_bgr):
    return detect_faces_dnn(img_bgr) if os.getenv("FACE_BACKEND","haar")=="dnn" else detect_faces_haar(img_bgr)

# ---------- テキスト: tesseract or east+tesseract ----------
def tokens_tesseract(img_bgr):
    try:
        import pytesseract
        from pytesseract import Output
    except Exception:
        return []
    lang=os.getenv("TESS_LANG","jpn+eng")
    data=pytesseract.image_to_data(img_bgr, lang=lang, output_type=Output.DICT)
    H,W=img_bgr.shape[:2]; toks=[]
    for i in range(len(data["text"])):
        t=(data["text"][i] or "").strip()
        if not t: continue
        x,y,w,h=data["left"][i],data["top"][i],data["width"][i],data["height"][i]
        if 0<=x<W and 0<=y<H and w>3 and h>8: toks.append({"text":t,"box":(x,y,w,h)})
    return toks

_EAST = _MODEL_DIR / "frozen_east_text_detection.pb"
_URL_EAST = "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/frozen_east_text_detection.pb"
def _ensure_east():
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if not _EAST.exists(): urllib.request.urlretrieve(_URL_EAST, _EAST.as_posix())

def tokens_east_tess(img_bgr):
    _ensure_east()
    model=cv2.dnn_TextDetectionModel_EAST(_EAST.as_posix())
    size=os.getenv("OCR_EAST_INPUT","640x640"); iw,ih=[int(x) for x in size.lower().split("x")]
    model.setInputParams(scale=1.0, size=(iw,ih), mean=(123.68,116.78,103.94), swapRB=True)
    model.setNMSThreshold(float(os.getenv("OCR_EAST_NMS","0.4")))
    model.setConfidenceThreshold(float(os.getenv("OCR_EAST_SCORE","0.5")))
    rects,_=model.detect(img_bgr)
    toks=[]
    for (x,y,w,h) in rects:
        x,y,w,h=map(int,(x,y,w,h))
        roi=img_bgr[max(0,y-2):y+h+2, max(0,x-2):x+w+2]
        try:
            import pytesseract
            txt = pytesseract.image_to_string(roi, lang=os.getenv("TESS_LANG","jpn+eng"), config="--psm 7").strip()
        except Exception:
            txt=""
        if txt: toks.append({"text":txt, "box":(x,y,w,h)})
    # EASTで拾えなかった時は全画面Tesseract
    return toks or tokens_tesseract(img_bgr)

def tokens(img_bgr):
    return tokens_east_tess(img_bgr) if os.getenv("OCR_BACKEND","tesseract")=="east" else tokens_tesseract(img_bgr)

# ---------- PII ルール ----------
RE_EMAIL=re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_PHONE=re.compile(r"(?:0\d{1,4}-\d{1,4}-\d{3,4})|(?:\d{2,4}-\d{2,4}-\d{3,4})")
RE_ID   =re.compile(r"\b(?:ORD|ACC|ID|USR)-?\d{3,8}\b", re.IGNORECASE)

def match_pii(tokens:List[Dict], policy:set) -> List[Tuple[int,int,int,int]]:
    boxes=[]
    for t in tokens:
        s=t["text"]
        if "email" in policy and RE_EMAIL.search(s): boxes.append(t["box"]); continue
        if "phone" in policy and RE_PHONE.search(s): boxes.append(t["box"]); continue
        if "id"    in policy and RE_ID.search(s):   boxes.append(t["box"]); continue
        if "address" in policy and any(k in s for k in ["丁目","番地","区","市","町"]):
            boxes.append(t["box"]); continue
    return boxes
