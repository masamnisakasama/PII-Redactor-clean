import re, pathlib, sys

ROOT = pathlib.Path(".")
f_pipeline = ROOT / "app/core/pipeline_offline.py"
f_det      = ROOT / "app/core/offline_detectors.py"

# ---- 1) pipeline_offline.py を確実に復旧（faceのみならOCRスキップ） ----
src = f_pipeline.read_text(encoding="utf-8")

def replace_function(src:str)->str:
    pattern = re.compile(
        r"(def\s+redact_bytes_offline\s*\([\s\S]*?\):)([\s\S]*?)(?=^\s*def\s+|\Z)",
        re.M
    )
    m = pattern.search(src)
    if not m:
        print("[WARN] redact_bytes_offline() が見つからないためファイル全体を置換します")
        return (
            "# app/core/pipeline_offline.py\n"
            "import io\n"
            "from PIL import Image\n"
            "from .offline_detectors import bgr_from_bytes, detect_faces, tokens, match_pii\n"
            "from .paint import apply\n\n"
            "def redact_bytes_offline(image_bytes: bytes, policy_csv: str, style: str = \"box\"):\n"
            "    img = bgr_from_bytes(image_bytes)\n"
            "    policy = {p.strip() for p in (policy_csv or \"\").split(\",\") if p.strip()}\n\n"
            "    boxes = []\n"
            "    if \"face\" in policy:\n"
            "        try:\n"
            "            boxes += detect_faces(img)\n"
            "        except Exception:\n"
            "            pass\n\n"
            "    TEXT_POLICIES = {\"email\",\"phone\",\"address\",\"id\",\"name\",\"amount\",\"date\",\n"
            "                     \"plate\",\"nationalid\",\"zipcode\",\"creditcard\",\"ssn\"}\n"
            "    if policy & TEXT_POLICIES:\n"
            "        try:\n"
            "            toks = tokens(img)\n"
            "            boxes += match_pii(toks, policy)\n"
            "        except Exception:\n"
            "            pass\n\n"
            "    out = apply(img.copy(), boxes, (style or \"box\"))\n"
            "    bio = io.BytesIO()\n"
            "    from PIL import Image as _I\n"
            "    _I.fromarray(out[:, :, ::-1].copy()).save(bio, format=\"PNG\")\n"
            "    bio.seek(0)\n"
            "    return bio, boxes\n"
        )
    head = m.group(1)
    body_fixed = (
        "\n"
        "    img = bgr_from_bytes(image_bytes)\n"
        "    policy = {p.strip() for p in (policy_csv or \"\").split(\",\") if p.strip()}\n\n"
        "    boxes = []\n"
        "    if \"face\" in policy:\n"
        "        try:\n"
        "            boxes += detect_faces(img)\n"
        "        except Exception:\n"
        "            pass\n\n"
        "    # テキスト系ポリシーがあるときだけ OCR 実行\n"
        "    TEXT_POLICIES = {\"email\",\"phone\",\"address\",\"id\",\"name\",\"amount\",\"date\",\n"
        "                     \"plate\",\"nationalid\",\"zipcode\",\"creditcard\",\"ssn\"}\n"
        "    if policy & TEXT_POLICIES:\n"
        "        try:\n"
        "            toks = tokens(img)\n"
        "            boxes += match_pii(toks, policy)\n"
        "        except Exception:\n"
        "            pass\n\n"
        "    out = apply(img.copy(), boxes, (style or \"box\"))\n"
        "    bio = io.BytesIO()\n"
        "    from PIL import Image as _I\n"
        "    _I.fromarray(out[:, :, ::-1].copy()).save(bio, format=\"PNG\")\n"
        "    bio.seek(0)\n"
        "    return bio, boxes\n"
    )
    return src[:m.start()] + head + body_fixed + src[m.end():]

if "TEXT_POLICIES" not in src or "return bio, boxes" not in src:
    src_new = replace_function(src)
    f_pipeline.write_text(src_new, encoding="utf-8")
    print("[fix] pipeline_offline.py: function restored / OCR gated")
else:
    print("[skip] pipeline_offline.py: already OK")

# ---- 2) offline_detectors.py に bbox 安全キャストを注入 ----
sd = f_det.read_text(encoding="utf-8")

if "_to_int_bb" not in sd:
    sd = sd.replace(
        "import numpy as np",
        "import numpy as np\nfrom typing import Tuple\n\n"
        "# numpy 配列/スカラー混在でも安全に int 化\n"
        "def _scalar_int(v) -> int:\n"
        "    import numpy as _np\n"
        "    if isinstance(v, _np.ndarray):\n"
        "        if v.size == 1:\n"
        "            v = v.reshape(-1)[0]\n"
        "        else:\n"
        "            v = float(v.astype(float).mean())\n"
        "    return int(round(float(v)))\n\n"
        "def _to_int_bb(x, y, w, h) -> Tuple[int, int, int, int]:\n"
        "    xi, yi, wi, hi = _scalar_int(x), _scalar_int(y), _scalar_int(w), _scalar_int(h)\n"
        "    wi = max(1, wi); hi = max(1, hi)\n"
        "    return xi, yi, wi, hi"
    )
    print("[fix] offline_detectors.py: helpers inserted")
else:
    print("[skip] offline_detectors.py: helpers already present")

new_sd = re.sub(
    r'x\s*,\s*y\s*,\s*w\s*,\s*h\s*=\s*map\(\s*int\s*,\s*\(\s*x\s*,\s*y\s*,\s*w\s*,\s*h\s*\)\s*\)',
    'x, y, w, h = _to_int_bb(x, y, w, h)',
    sd
)
if new_sd != sd:
    f_det.write_text(new_sd, encoding="utf-8")
    print("[fix] offline_detectors.py: bbox cast replaced")
else:
    print("[skip] offline_detectors.py: bbox cast already safe or pattern not found")

print("[done] fixes applied")
