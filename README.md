# Keypoints Project Scaffold

`CODING_STYLE.md` に基づく Python プロジェクト初期構成サンプルです。Copilot と自動化が最大限活きる標準ツールセットを含みます。

## クイックスタート (Windows cmd)

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pre-commit install
pytest -q
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
pytest -q
```

## 主なツール

| 分類 | ツール | 用途 |
| ---- | ------ | ---- |
| フォーマッタ | black | 行長88/自動整形 |
| import整列 | isort | インポート順序統一 |
| Lint | ruff (fallback: flake8/pylint) | 静的解析高速化 |
| 型 | mypy | 型チェック (段階導入) |
| テスト | pytest / pytest-cov | 単体/結合/カバレッジ測定 |
| Commit hooks | pre-commit | 失敗を早期検知 |

## 代表的コマンド

| タスク | コマンド例 |
| ------ | ---------- |
| フォーマット | black ProgramName tests |
| import整列 | isort ProgramName tests |
| Lint | ruff check ProgramName tests |
| 型チェック | mypy ProgramName |
| テスト | pytest -q |
| カバレッジ | pytest --cov=ProgramName tests |

## ディレクトリ概要

```
ProgramName/
	main.py
	common/        # 共通ユーティリティ（例外/ログ等）
	scripts/       # 業務ロジックモジュール
	models/        # モデル資産
	resources/     # 設定 (ApplicationConfig.xml 等)
	results/       # 出力
	tests/
		unit/        # 単体テスト
		integration/ # 結合テスト
docs/            # ドキュメント
CODING_STYLE.md  # コーディング規約
PROMPT_GUIDE.md  # プロンプトテンプレ
```

詳細は `CODING_STYLE.md` を参照してください。