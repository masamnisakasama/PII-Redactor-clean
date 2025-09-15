# PII-Redactor-clean

**PII-Redactor-clean** は、スパゲッティ化していた旧実装（PII-Redactor）を**壊さず動くこと最優先**で再構成した移送版です。  
目的は **読みやすさ・機能分離・拡張性** の確保（リファクタリング中心）で、オンライン/オフライン処理の切替や将来の検出器差し替えが簡単にできる構成にしています。
非常に重要な事として、機能をちゃんとファイルごとに分離する事と、main.pyを肥大化させないことを重視しています。

---

## 内容
- 基本的には旧版と同じです
- Ragにより入力したデータのPIIを自然言語ベースで指示してリダクトしてくれる機能を予定しています
- 画像の **顔** と **テキストPII**（メール/電話/ID/住所など）をマスク
- **モード**: オフライン　テキスト（OpenCV/Tesseract） 顔検出 (haar|yunet|dnn|yolo） オンライン（Gemini）を切替
- **オンライン顔変換**: スタイル選択（`synthetic/anime/cartoon/emoji/pixel/old/3d/blur`）
- API は **FastAPI**。`/redact/replace` に画像を投げると **PNG をストリーム返却**（サーバ保存しない）

---

## ファイル構成

<!-- FILE TREE START -->
```text
/app
├─ core
│  ├─ config.py                 # 環境変数/モデルパス/閾値
│  ├─ face_cv2.py               # 顔検出 (haar|yunet|dnn|yolo 切替可能に変更)
│  ├─ offline_detectors.py      # 文字検出 (tesseract|EAST)
│  ├─ online_gemini.py          # Gemini 呼び出し (画像編集)
│  ├─ online_prompt.py          # 顔変換/PII 用プロンプト生成
│  ├─ paint.py                  # マスク描画（黒塗り等）
│  ├─ pipeline.py               # online/offline を統括するパイプラインとFB
│  ├─ pipeline_offline.py       # オフライン統合（顔やテキスト→マスク）
│  └─ pipeline_online.py        # オンライン統合（GeminiのNanobanana使用）
├─ routers
│  ├─ redact.py                 # /redact/replace (リダクト用エンドポイント)
│  ├─ health.py                 # /health,/capabilities
│  ├─ diag.py                   # /diag 
│  ├─ rag.py                    # /rag/offline/*（reindex/ask のRAG API）
│  ├─ policy.py                 # /policy/resolve（自然文→CSV 変換）
│  └─ compose.py                # /compose/resolve_then_redact（自然文→即リダクト）
├─ rag
│  ├─ __init__.py
│  ├─ common
│  │  ├─ __init__.py
│  │  └─ textsplit.py           # チャンク分割設定（LangChain TextSplitter）
│  └─ offline
│     ├─ __init__.py
│     ├─ ingest.py              # 索引作成（FAISSに保存）
│     ├─ retriever.py           # 検索（MMRで関連文脈取得）
│     └─ policy.py              # 自然文→ポリシーCSV（辞書ベース）
└─ main.py

/models                           # 事前DLモデル置き場（scriptsで取得）
├─ deploy.prototxt                # DNN (Caffe) prototxt
├─ res10_300x300_ssd_iter_140000.caffemodel    # DNN fp32
├─ face_detection_yunet_2023mar.onnx           # YuNet (ONNX)
├─ frozen_east_text_detection.pb               # EAST (PB)
├─ haarcascade_frontalface_default.xml         # Haar
├─ yolov8n.pt                                   # YOLOv8 (det)
├─ yolov8n-seg.pt                               # YOLOv8 (seg, 任意)
└─ animegan
   ├─ AnimeGANv2_Hayao.onnx     # AnimeGAN（Hayao）
   └─ face_paint_512_v2_0.onnx  # AnimeGAN（face paint）

/scripts
├─ devserve.sh                 # FACE_BACKEND 指定でuvicorn起動
├─ fetch_models.sh             # モデル一括DL（EAST/YOLO/YuNet/DNN）
├─ verify_models.sh            # モデルサイズ検証（しきい値調整済み）
├─ regression.sh               # オフラインでの回帰テスト用bashコマンド
├─ regression_online.sh        # オンラインでの回帰テスト用bashコマンド
├─ fix_pii_redactor.py         # 旧実装からの移送補助スクリプト
└─ patch_ocr_bbox.sh           # OCR矩形の変換/補正パッチ適用

```

# .env例
## === モデルパス ===（fetch_models.shの配置先）<br>
EAST_MODEL_PATH=models/frozen_east_text_detection.pb <br>
YUNET_MODEL_PATH=models/face_detection_yunet_2023mar.onnx <br>
HAAR_MODEL_PATH=models/haarcascade_frontalface_default.xml <br>
YOLO_DET_PATH=models/yolov8n.pt <br>
YOLO_SEG_PATH=models/yolov8n-seg.pt <br>

## === モード ===
MODE=offline   online にしたい時はフォームで mode=online でもOK <br>
ONLINE_FALLBACK_OFFLINE=1 <br>

## === オンライン(Gemini) ===
GEMINI_API_KEY=xxxxx_your_key_xxxxx <br>
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image-preview <br>
GEMINI_API_BASE=https://generativelanguage.googleapis.com/v1beta <br>

## === 顔検出バックエンド（haar | yunet | yolo | dnn）=== 
FACE_BACKEND=haar <br>

## === テキスト検出/認識（tesseract | east）===
TEXT_BACKEND=tesseract <br>
TESS_LANG=eng       日本語OCRするなら jpn+eng（要 tesseract-lang） <br>

## === ローカルモデルパス ===
EAST_MODEL_PATH=models/frozen_east_text_detection.pb <br>
YUNET_MODEL_PATH=models/face_detection_yunet_2023mar.onnx <br>
HAAR_MODEL_PATH=models/haarcascade_frontalface_default.xml <br>
YOLO_DET_PATH=models/yolov8n.pt <br>
DNN_CAFFE_PROTO=models/deploy.prototxt <br>
DNN_CAFFE_MODEL=models/res10_300x300_ssd_iter_140000.caffemodel <br>


## 依存
brew install tesseract   macOS（英語OCR） <br>
## 日本語のOCRしたい場合 
brew install tesseract-lang jpn などの追加辞書 <br>

## 起動
PYTHONPATH="$(pwd)" uvicorn app.main:app \ <br>
  --host 127.0.0.1 --port 8000 --env-file .env --reload

## オフラインのモデル指定用簡単コマンド
scripts/devserve.sh モデル名
