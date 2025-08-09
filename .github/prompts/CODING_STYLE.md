---
description: 'Python コーディング規約 (日本語版)'
applyTo: '**/*.py'
---

# Python コーディング規約

この文書は、Python初心者にも分かりやすく、チームでの再現性と品質を高めるための実践的な規約です。Copilot/自動化ツールと相性良く運用できるように具体例と数値基準を示します。

## 📘 目次

1. [基本思想](#基本思想)
2. [ファイル・ディレクトリ構成](#ファイルディレクトリ構成)
3. [ネーミング規則](#ネーミング規則)
4. [定数定義](#定数定義)
5. [コードフォーマット](#コードフォーマット)
6. [インポート](#インポート)
7. [型アノテーション](#型アノテーション)
8. [ドキュメンテーション](#ドキュメンテーション)
9. [例外・エラー処理](#例外エラー処理)
10. [テスト](#テスト)
11. [設定管理](#設定管理)
12. [CI／Lint／フォーマッタ](#cilintフォーマッタ)
13. [依存管理＆パッケージング](#依存管理パッケージング)
14. [Git コミット＆ブランチ運用](#gitコミットブランチ運用)
15. [Copilot 連携のヒント](#copilot連携のヒント)
16. [付録（実務ガイド）](#付録実務ガイド)

---

## 基本思想

* **可読性第一**：誰が見ても理解しやすいコードを最優先。
* **一貫性**：全体で同一のルールを適用。
* **自動化容易性**：CI／Lint／フォーマッタとの親和性を重視。
* **拡張性**：小規模から大規模までスケール可能な構成。

---

## ファイル・ディレクトリ構成

```plaintext
ProjectName/
├── ProgramName/
│   ├── main.py
│   ├── common/   # 開発Gr内共通モジュール
│   ├── models/
│   │    ├── openvino_model.xml
│   │    └── openvino_model.bin
│   ├── resources/
│   │    └── ApplicationConfig.xml
│   ├── results/
│   ├── scripts/  # モジュール
│   │    ├── module_a.py
│   │    └── module_b.py
│   └── tests/
│        ├─── unit
│        │    ├── test_module_a.py
│        │    └── test_module_b.py
│        └─── integration
│             └── test_integration.py
├── docs/
├── requirements_dev.txt
├── requirements.txt
├── requirements_result.txt
├── CODING_STYLE.md
└── README.md
```

---

## ネーミング規則

| 種類       | スタイル                       | 例                |
| -------- | -------------------------- | ---------------- |
| モジュール名   | 小文字 + アンダースコア（snake_case） | data_loader.py  |
| パッケージ名   | 小文字（snake_case）           | image_utils     |
| クラス名     | UpperCamelCase             | ImageProcessor   |
| 関数・メソッド名 | 小文字 + アンダースコア              | load_image()    |
| 変数名      | 小文字 + アンダースコア              | file_path       |
| 定数       | 全大文字 + アンダースコア             | MAX_RETRIES = 3 |

補足：
* ブールは is_/has_/can_ を先頭に（例: is_valid）。
* 単位は名前に含める（例: timeout_ms, size_bytes）。
* コレクションは複数形（users, items）。

---

## 定数定義

* モジュール固有の定数はファイル冒頭にまとめる。
* クラス固有の定数はクラス定義内の冒頭に記載する。
* 値の変更を禁止する場合は `typing.Final` を付与する。
* 状態や選択肢の定義には **Enum** を推奨。
* 構造化が必要な場合は dataclass / TypedDict の利用を検討する。

---

## コードフォーマット

* **PEP 8 準拠**。
* インデントはスペース4文字。
* 行長は最大**88**文字（Black デフォルト）に統一。
* 空行：クラス間は2行、関数間は1行。
* 文字列は f-string を優先。ログは遅延評価（`logger.info("x=%s", x)`）。

```python
import math

def compute_area(radius: float) -> float:
    """円の面積を返す。"""
    return math.pi * radius ** 2
```

---

## インポート

1. 標準ライブラリ
2. サードパーティ
3. 自プロジェクト

* 各グループは空行で区切る（isortのprofile=black想定）。
* 原則：モジュール先頭でインポート、ワイルドカード禁止、不要インポート禁止。
* 例外（許容）：
  - 遅延読み込みが明らかに有利（重依存/起動高速化）。
  - 循環依存の回避が必要。
  - オプショナル依存（導入時のみ使用）。
  上記はいずれも「WHY」をコメントで必ず残す。
* 相対よりも絶対インポートを推奨。

```python
import os

import numpy as np

from mypkg.module_a import CONST_A
```

---

## 型アノテーション

* **全パブリック関数／メソッド**に必須。
* 戻り値に `-> None` も明示。
* `from __future__ import annotations` 推奨。
* 可能なら型チェックツール（mypy等）を段階導入。

```python
from typing import List

def parse_items(lines: List[str]) -> List[int]:
    return [int(x) for x in lines]
```

---

## ドキュメンテーション

* **GoogleスタイルのDocstring**を採用（PEP 257の原則に準拠：def/class直後に記述）。
* モジュール、クラス、関数すべてに説明を付与し、引数・戻り値・例外を明示。
* 重要処理は「計算量/前提条件/注意点/Examples」を含める。

### Docstring例

```python
def connect(host: str, port: int = 5432) -> Connection:
    """DBに接続する。

    Args:
        host (str): ホスト名。
        port (int, optional): ポート番号。デフォルトは5432。

    Returns:
        Connection: DB接続オブジェクト。

    Raises:
        ConnectionError: 接続失敗時。
    """
    ...
```

---

## 例外・エラー処理

* 捕捉は必要最小限に留める。握りつぶし禁止。
* 例外メッセージは「行為 + 対象 + 期待 vs 実際 + 次アクション」で具体的に。
* 原因保持のため `raise NewError(...) from err` を推奨。
* 独自例外を定義する場合は `Exception` を直接継承し、必要なら基底例外を用意。
* **テストコード内で`expect`を利用**する際のログ形式：

```python
try:
    expect(some_condition)
except AssertionError as e:
    logger.error("テスト失敗: %s", e, exc_info=True)
    raise
```

> ロガーの生成方法は任意。プロジェクトやモジュール方針に合わせてよい。

```python
# 例1: モジュールレベルで取得
import logging
logger = logging.getLogger(__name__)

# 例2: クラス内で取得
class Processor:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
```

---

## テスト（pytest）

**pytest推奨理由**

1. **記述量が少なく読みやすい**（`assert`がそのまま使える）。
2. **強力なfixture機能**でセットアップ/後処理を簡潔に管理。
3. **パラメータ化**で条件網羅が容易。
4. **豊富なプラグイン**（pytest-cov, pytest-mock等）。
5. unittestコードもそのまま実行可能。

**ルール**

* テストは原則 `if __name__ == "__main__"` で行わない。
* 単体テスト：`tests/unit/test_<module_name>.py`
* 結合テスト：`tests/integration/test_integration.py`
* カバレッジ90%以上（`pytest --cov`で測定）。
* 各テストに短いDocstringで「目的/前提/期待結果」を1〜3行で記載。
* 代表的エッジケース（付録参照）を最低1つは含める。

期待値検証（`expect`）時のログ：

```python
try:
    expect(func() == expected)
except AssertionError as e:
    logger.error("期待値不一致: %s", e, exc_info=True)
    raise
```

実行例：

Windows (cmd.exe):

```cmd
.venv\Scripts\activate
pytest --maxfail=1 --disable-warnings -q
pytest --cov=ProgramName tests
```

macOS/Linux:

```bash
source .venv/bin/activate
pytest --maxfail=1 --disable-warnings -q
pytest --cov=ProgramName tests
```

---

## 設定管理

* 原則：環境変数禁止。設定は `resources/ApplicationConfig.xml` に集約。機密値・CI設定・実行環境識別などはログに出さない。
* 例外：なし。

---

## CI／Lint／フォーマッタ

開発開始時には、仮想環境を作成して `requirements-dev.txt` をインストール。

Windows (cmd.exe):

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

推奨ツール：

* **Black**: コード整形（行長88）。
* **isort**: インポート整列（profile=black）。
* **Ruff（推奨）** または **flake8/pylint**: 静的解析。
* **pytest**: テスト実行。

### GitHub Actions 例（pytestに統一）

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: black --check ProgramName tests
      - run: isort --check-only ProgramName tests
      - run: ruff check ProgramName tests || flake8 ProgramName tests
      - run: pytest --maxfail=1 --disable-warnings -q
      - run: pytest --cov=ProgramName --cov-report=term-missing
```

---

## 依存管理＆パッケージング

1. 開発必須ライブラリを記載した `requirements_dev.txt` をコピーして `requirements.txt` を作成。
2. 必要なライブラリを `requirements.txt` に追記。
3. `pip install -r requirements.txt`。
4. `pip freeze > requirements_result.txt`。
5. `requirements_result.txt` をリポジトリにpush。
6. ライブラリ追加時は①〜⑤を再実施。
7. Dependabot で自動脆弱性チェック。

---

## Git コミット＆ブランチ運用

* **Conventional Commits** 準拠。
* PR は必ずコードレビュー後マージ。
* main ブランチは常にデプロイ可状態。

```plaintext
feat: ユーザ登録機能を追加
fix: ログイン例外処理を修正
```

---

## Copilot 連携のヒント

* リポジトリ直下に本ガイド（`CODING_STYLE.md`）を配置。
* プロンプト先頭にガイドへのリンクを記載。

```plaintext
# Please follow this Python coding style guide:
# https://github.com/your-org/your-repo/blob/main/CODING_STYLE.md
```

* 「WHY/TODO/NOTE/PERF」などのタグをコメントで統一（Copilotが意図を理解しやすい）。

---

## 互換性 / 廃止 (Deprecation) ポリシー

本プロジェクトは「内部サービス / アプリケーション」前提で **長期的な後方互換レイヤを保持しません**。不要コードを温存せず、履歴は Git で追跡します。Copilot へも「ラッパを残さず rename / 削除で即時一本化」を期待します。

原則:
1. 公開 API として明示していないモジュール / 関数はバージョン間互換を保証しない。
2. 名前変更・分割・インターフェース調整時は **同一PRで全利用箇所を更新** し旧シンボルを残さない。
3. "legacy_", "old_", "deprecated_" のような一時ラッパ命名は禁止。Git 履歴で十分。
4. 使われなくなった関数/クラス/設定項目/ファイルは即時削除（コメントアウトでの“仮残し”禁止）。
5. Copilot プロンプトにも「古い関数を残さず置換」「互換ラッパ不要」と明示すること。
6. 例外的に外部利用者が存在する場合のみ短期猶予（最大1スプリント）を設け `# DEPRECATED: <削除予定日>` コメントを付ける。期間経過後は削除。
7. 削除/破壊的変更のコミットメッセージ例:
    - `refactor: rename process_image to run_image_pipeline (no wrapper)`
    - `breaking: remove obsolete parse_legacy_config` (外部影響がある場合)
8. Dead code 判定基準（いずれか該当で削除）:
    - 参照検索で0件
    - テストも含めて import されない
    - コメントアウト状態が1PRを超えて放置
9. テストでのみ使用されていた補助関数は該当テストファイルへ移動（本体から削除）。

プロンプト例（Copilot向け）:
```text
関数Aを関数Bへリネームし、旧Aは残さず全呼び出しを書き換えてください。
互換ラッパ/別名は作成しないでください。CODING_STYLE.mdの廃止ポリシーに従うこと。
```

---

## 付録（実務ガイド）

### A. 関数分割と複雑度の目安
* 1関数の行数：目安 ≤ 50 行。分岐数：目安 ≤ 8。循環的複雑度：目安 ≤ 10。
* 逸脱する場合は Docstring の「Notes」やコメントで理由（WHY）を記述。
* 早期return（ガード節）でネストを浅く保つ。

### B. エッジケース標準セット
* 空/None、境界（最小/最大/負）、巨大データ、重複/順序、タイムアウト、権限、並行、I/O失敗、外部サービス不達。

### C. ログと監視
* ログレベル：DEBUG（開発詳細）/INFO（通常）/WARNING（注意）/ERROR（復旧可能エラー）/CRITICAL（致命）。
* 機密値（トークン/パスワード/個人情報）はログ出力しない（マスク）。
* 例外時は `exc_info=True` を付ける。相関IDがある場合は一緒に出力。

### D. 命名のヒント
* 目的語+動詞の順で読みやすく（load_image, parse_config）。
* 単位/型/フォーマットを名前で伝える（timestamp_utc, id_hex）。

---

上記をベースにプロジェクト固有ルールを追加し、一貫性を保ちながら運用してください。
