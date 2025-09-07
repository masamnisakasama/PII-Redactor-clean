# PII-Redactor-clean

**PII-Redactor-clean** は、スパゲッティ化していた旧実装（PII-Redactor）を**壊さず動くこと最優先**で再構成した移送版です。  
目的は **読みやすさ・機能分離・拡張性** の確保（リファクタリング中心）で、オンライン/オフライン処理の切替や将来の検出器差し替えが簡単にできる構成にしています。

---

## 内容
- 基本的には旧版と同じです
- 画像の **顔** と **テキストPII**（メール/電話/ID/住所など）をマスク
- **モード**: オフライン（OpenCV/Tesseract） / オンライン（Gemini）を切替
- **オンライン顔変換**: スタイル選択（`synthetic/anime/cartoon/emoji/pixel/old/3d/blur`）
- API は **FastAPI**。`/redact/replace` に画像を投げると **PNG をストリーム返却**（サーバ保存しない）

---

## ファイル構成
/app
├── core
│ ├── pipeline.py # online/offline 切替の統括
│ ├── pipeline_offline.py # オフライン統合（顔/テキスト検出→マスク）
│ ├── pipeline_online.py # オンライン統合（Geminiへ編集依頼）
│ ├── online_gemini.py # Gemini呼び出し（画像+プロンプト→編集画像）
│ ├── online_prompt.py # オンライン顔変換・PII用プロンプト生成（★追加）
│ ├── offline_detectors.py # 既存のオフライン検出（Tesseract/EAST等）
│ ├── face_cv2.py # 顔検出のOpenCV実装
│ └── paint.py # マスク描画
├── routers
│ ├── redact.py # /redact/replace（★face_style/face_spec対応）
│ ├── health.py # /health, /v1/health, /capabilities
│ └── diag.py # 診断（キー末尾など）
└── main.py
/models
└── （EAST等のモデル置き場。自動DL試行にはなっているが、ローカルファイルで使用可にする予定）
/scripts
├── regression.sh
└── regression_online.sh

# 依存
brew install tesseract            # macOS（英語OCR）
# 日本語のOCRしたい場合
brew install tesseract-lang       # jpn などの追加辞書

## .env例
# 既定は offline。オンラインにしたい時はフォーム側で mode=online を渡してもOK
MODE=offline　<br>
ONLINE_FALLBACK_OFFLINE=1

# オンライン（Gemini）
GEMINI_API_KEY=xxxxx_your_key_xxxxx <br>
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image-preview <br>
GEMINI_API_BASE=https://generativelanguage.googleapis.com/v1beta

# オフラインOCR
OCR_BACKEND=tesseract        <br>
TESS_LANG=eng                # 日本語OCRするなら jpn+eng に

# 起動
PYTHONPATH="$(pwd)" uvicorn app.main:app \ <br>
  --host 127.0.0.1 --port 8000 --env-file .env --reload
