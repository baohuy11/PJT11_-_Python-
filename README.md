# Python提出課題のアドバイス生成システム

プロジェクトの詳細は、所定のドキュメントを確認すること。

## 実装された機能

### 管理者機能
- ✅ 問題の作成・編集・削除
- ✅ テストケースとの評価基準の設定（JSON形式）
- ✅ 提出されたコードの確認と管理
- ✅ 評価結果とアドバイスの閲覧

### 受講生機能
- ✅ 問題一覧の表示と選択
- ✅ 問題詳細の確認
- ✅ Webフォームでのコード提出
- ✅ リアルタイムでの評価結果待機
- ✅ 改善アドバイスの表示

### 評価・アドバイス機能
- ✅ Dockerサンドボックス環境での安全なコード実行
- ✅ テストケースによる自動評価
- ✅ Google Gemini APIによる建設的なアドバイス生成
- ✅ 具体的な改善提案とヒントの提供
- ✅ チート行為の自動検出機能
- ✅ LLM使用コストの計算と表示

### セキュリティ機能
- ✅ 提出コードの安全性チェック
- ✅ 危険な関数・モジュールの検出
- ✅ サンドボックス環境での隔離実行
- ✅ 適切なエラーハンドリング

## 技術仕様

### バックエンド
- **Python 3.12** - メイン言語
- **FastAPI 0.104+** - Web APIフレームワーク
- **SQLAlchemy 2.0+** - データベースORM
- **SQLite** - データベース
- **Google Gemini API** - AI アドバイス生成
- **Docker** - サンドボックス環境
- **uvicorn** - ASGIサーバー

### フロントエンド
- **HTML5/CSS3/JavaScript** - UI実装
- **Bootstrap 5** - レスポンシブデザイン
- **Jinja2** - テンプレートエンジン

### 開発環境
- **uv** - 高速パッケージマネージャー
- **pyproject.toml** - プロジェクト設定

## システム構成

```
python-advice-system/
├── app/
│   ├── main.py                  # FastAPIメインアプリケーション
│   ├── models/
│   │   ├── models.py           # SQLAlchemyデータモデル
│   │   └── schemas.py          # Pydanticスキーマ
│   ├── routers/
│   │   ├── problems.py         # 問題管理API
│   │   └── submissions.py      # 提出管理API
│   ├── services/
│   │   ├── code_evaluator.py   # コード評価サービス
│   │   └── gemini_service.py   # Gemini API統合
│   ├── database/
│   │   └── database.py         # データベース設定
│   └── utils/                  # ユーティリティ関数
├── frontend/
│   ├── static/
│   │   ├── style.css          # カスタムスタイル
│   │   ├── main.js            # 受講生ページJS
│   │   └── admin.js           # 管理者ページJS
│   └── templates/
│       ├── index.html         # 受講生メインページ
│       └── admin.html         # 管理者ページ
├── sandbox/                    # コード実行環境
├── tests/                      # テストファイル
├── pyproject.toml             # プロジェクト設定
├── requirements.txt           # 依存関係（参考用）
└── .env                       # 環境変数
```

## インストールと実行

### 前提条件
- Python 3.9以上（3.13未満推奨）
- Docker Desktop（コード実行用）
- Google Gemini APIキー

### 1. 仮想環境の作成
```bash
# uvを使用（推奨）
uv venv --python 3.12
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# または標準のvenv
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. 依存関係のインストール
```bash
# uvを使用（推奨）
uv sync

# または pip
pip install -r requirements.txt
```

### 3. 環境変数の設定
`.env`ファイルを作成し、以下を設定：
```bash
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./advice_system.db
SECRET_KEY=your_secret_key_here
SANDBOX_TIMEOUT=30
```

### 4. アプリケーションの実行
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### 5. アクセス
- **メインページ（受講生用）**: http://localhost:8080
- **管理者ページ**: http://localhost:8080/admin
- **API仕様書**: http://localhost:8080/docs
- **ヘルスチェック**: http://localhost:8080/health

## API仕様

### 問題管理
- `POST /api/problems/` - 問題登録（管理者用）
- `GET /api/problems/` - 問題一覧取得
- `GET /api/problems/{problem_id}` - 特定問題取得
- `PUT /api/problems/{problem_id}` - 問題更新（管理者用）
- `DELETE /api/problems/{problem_id}` - 問題削除（管理者用）

### 提出管理
- `POST /api/submissions/` - コード提出
- `GET /api/submissions/{submission_id}` - 提出詳細取得
- `GET /api/submissions/{submission_id}/advice` - アドバイス取得
- `GET /api/submissions/` - 提出一覧取得（フィルター対応）

## 使用方法

### 管理者向け

1. **問題の作成**
   - 管理者ページにアクセス
   - 問題タイトル、説明、テストケース（JSON形式）を入力
   - 期待される出力と難易度を設定

2. **テストケース例**
```json
[
    {"input": [1, 2], "expected": 3},
    {"input": [5, 10], "expected": 15},
    {"input": [0, 0], "expected": 0}
]
```

### 受講生向け

1. **問題の選択**
   - メインページで問題を選択
   - 問題の詳細を確認

2. **コードの提出**
   - 名前とPythonコードを入力
   - 提出ボタンをクリック

3. **結果の確認**
   - テスト結果の確認
   - AIからのアドバイスを読む
   - 改善提案を参考に修正

## セキュリティ機能

### コード実行の安全性
- Dockerコンテナによる完全な隔離
- 危険な関数・モジュールの事前検出
- 実行時間制限（デフォルト30秒）
- リソース使用量の制限

### チート検出
- コード中の直接的な答えの検出
- 外部からのコピーの可能性判定
- 不適切なコードパターンの識別

## トラブルシューティング

### よくある問題

1. **Docker関連エラー**
   - Docker Desktopが起動していることを確認
   - Docker APIへのアクセス権限を確認

2. **Gemini API エラー**
   - APIキーが正しく設定されているか確認
   - API使用量制限に達していないか確認

3. **依存関係エラー**
   - Python 3.12の使用を推奨
   - 仮想環境が正しく有効化されているか確認

### デバッグ情報
```bash
# ログの確認
uvicorn app.main:app --log-level debug

# データベースの状態確認
sqlite3 advice_system.db ".tables"
```

## 開発・カスタマイズ

### 新しい評価方法の追加
`app/services/code_evaluator.py`を編集してカスタム評価ロジックを追加

### UIのカスタマイズ
`frontend/static/style.css`でスタイルを調整

### 新しいアドバイスパターンの追加
`app/services/gemini_service.py`でプロンプトを調整

## 今後の拡張可能性

- 複数プログラミング言語への対応
- より高度なチート検出アルゴリズム
- 学習進捗の可視化機能
- 自動問題生成機能
- チーム開発演習への対応# PJT11_-_Python-
