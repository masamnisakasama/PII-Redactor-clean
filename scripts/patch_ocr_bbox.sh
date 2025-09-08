#!/usr/bin/env bash
set -euo pipefail
f1="app/core/pipeline_offline.py"
f2="app/core/offline_detectors.py"

# 0) バックアップ（初回のみ残す）
cp -n "$f1" "$f1.bak" 2>/dev/null || true
cp -n "$f2" "$f2.bak" 2>/dev/null || true

# 1) pipeline_offline.py: faceのみならOCRを回さない
python3 - <<'PY'
import re, io, sys
p="app/core/pipeline_offline.py"
s=open(p,'r',encoding='utf-8').read()
# すでにTEXT_POLICIESがあれば何もしない
if 'TEXT_POLICIES' not in s:
    # toks/match_piiの2行を条件ブロックで置き換え
    pat=r'(\btoks\s*=\s*tokens\(img\)\s*\n\s*boxes\s*\+=\s*match_pii\(toks,\s*policy\))'
    if re.search(pat,s):
        repl=('''# テキスト系ポリシーが指定された場合のみ OCR を実行
TEXT_POLICIES = {
    "email","phone","address","id","name","amount","date",
    "plate","nationalid","zipcode","creditcard","ssn"
}
if policy & TEXT_POLICIES:
    toks = tokens(img)
    boxes += match_pii(toks, policy)''')
        s=re.sub(pat,repl,s, count=1)
        open(p,'w',encoding='utf-8').write(s)
        print("patched:", p)
    else:
        print("WARN: pattern not found in", p, "- nothing changed")
else:
    print("skip (already patched):", p)
PY

# 2) offline_detectors.py: EASTのbboxを安全キャストに
python3 - <<'PY'
import re
p="app/core/offline_detectors.py"
s=open(p,'r',encoding='utf-8').read()
added=False
if '_to_int_bb' not in s:
    s=s.replace('import numpy as np',
                'import numpy as np\nfrom typing import Tuple\n\n'
                '# numpy 配列/スカラー混在でも安全に int 化\n'
                'def _scalar_int(v) -> int:\n'
                '    import numpy as _np\n'
                '    if isinstance(v, _np.ndarray):\n'
                '        if v.size == 1:\n'
                '            v = v.reshape(-1)[0]\n'
                '        else:\n'
                '            v = float(v.astype(float).mean())\n'
                '    return int(round(float(v)))\n\n'
                'def _to_int_bb(x, y, w, h) -> Tuple[int, int, int, int]:\n'
                '    xi, yi, wi, hi = _scalar_int(x), _scalar_int(y), _scalar_int(w), _scalar_int(h)\n'
                '    wi = max(1, wi); hi = max(1, hi)\n'
                '    return xi, yi, wi, hi')
    added=True
new=re.sub(r'x\s*,\s*y\s*,\s*w\s*,\s*h\s*=\s*map\(\s*int\s*,\s*\(\s*x\s*,\s*y\s*,\s*w\s*,\s*h\s*\)\s*\)',
           'x, y, w, h = _to_int_bb(x, y, w, h)', s)
if new!=s or added:
    open(p,'w',encoding='utf-8').write(new)
    print("patched:", p)
else:
    print("skip (already patched):", p)
PY
