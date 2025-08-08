# Python 至高のコーディング規約 (改訂版)

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
│   └── scripts/  # モジュール
│        ├── module_a.py
│        └── module_b.py
├── resources/
│   └── ApplicationConfig.xml
├── tests/
│   ├── unit/
│        ├── test_module_a.py
│        └── test_module_b.py
│   └── integration/
│        └── test_integration.py
├── models/
│        ├── openvino_model.xml
│        └── openvino_model.bin
├── results/
├── docs/
├── requirements_dev.txt
├── requirements.txt
├── requirements_result.txt
├── CODE_STYLE.md
└── README.md
```

---

## ネーミング規則

| 種類       | スタイル                       | 例                |
| -------- | -------------------------- | ---------------- |
| モジュール名   | 小文字 + アンダースコア（snake\_case） | data\_loader.py  |
| パッケージ名   | 小文字（snake\_case）           | image\_utils     |
| クラス名     | UpperCamelCase             | ImageProcessor   |
| 関数・メソッド名 | 小文字 + アンダースコア              | load\_image()    |
| 変数名      | 小文字 + アンダースコア              | file\_path       |
| 定数       | 全大文字 + アンダースコア             | MAX\_RETRIES = 3 |

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
* 行長は最大88文字（Black デフォルト）。
* 空行：クラス間は2行、関数間は1行。

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

* 各グループは空行で区切る。
* ローカル（関数内）インポート禁止：すべてモジュール先頭で。
* 相対インポートは最上位から短く。

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

```python
from typing import List

def parse_items(lines: List[str]) -> List[int]:
    return [int(x) for x in lines]
```

---

## ドキュメンテーション

* **GoogleスタイルのDocstring**を採用。
* モジュール、クラス、関数すべてに説明を付与し、引数・戻り値・例外を明示。

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
    pass
```

---

## 例外・エラー処理

* 捕捉は必要最小限に留める。
* 捕捉時は必ずログ出力または再送出を行う。
* 独自例外を定義する場合は `Exception` を直接継承し、プロジェクト固有の基底例外クラスを用意してもよい。
* **テストコード内で`expect`を利用する際**、例外情報を詳細に記録するために必ず以下の形式でログ出力を行うこと：

```python
try:
    expect(some_condition)
except AssertionError as e:
    logger.error("テスト失敗: %s", e, exc_info=True)
    raise
```

> **ロガーの生成方法に制限はありません**。プロジェクトやモジュールの方針に合わせて自由に実装してください。

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
2. **強力なfixture機能**でテストデータや環境のセットアップを簡潔に管理可能。
3. **パラメータ化テスト**で同一関数の複数条件テストが容易。
4. **豊富なプラグイン**（pytest-cov, pytest-mockなど）で拡張性が高い。
5. unittestコードもそのまま実行可能な互換性。

**ルール**

* テストは原則`if __name__ == "__main__"`では行わず下記テスト用コードで行う。
* 単体テスト：`tests/unit/test_<module_name>.py`
* 結合テスト：`tests/integration/test_integration.py`
* カバレッジ90%以上（`pytest --cov`で測定）。
* **期待値検証(`expect`)時**には必ず詳細ログを残すため以下を実施：

  ```python
  try:
      expect(func() == expected)
  except AssertionError as e:
      logger.error("期待値不一致: %s", e, exc_info=True)
      raise
  ```

  ロガーの取得方法は自由。

実行例：

```bash
pytest --maxfail=1 --disable-warnings -q
pytest --cov=src tests/
```

---

## 設定管理

* 環境変数禁止：外部依存を排除。
* 設定ファイルは `resources/ApplicationConfig.xml` のみ。
* シークレット情報は含めず、暗号化または別途管理。

---

## CI／Lint／フォーマッタ

開発開始時には、仮想環境を有効化のうえ `requirements-dev.txt` を使って以下をインストールしてください。

```bash
python -m venv .venv
. .venv\Scripts\activate
pip install -r requirements-dev.txt
```

* **Black**: コード整形。
* **isort**: インポート整列。
* **flake8** or **pylint**: 静的解析。
* **unittest**: テスト実行。

### GitHub Actions 例

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
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: black --check src tests
      - run: isort --check-only src tests
      - run: flake8 src tests
      - run: python -m unittest discover tests
```

---

## 依存管理＆パッケージング

1. 開発必須ライブラリを記載した `requirements_dev.txt` をコピーして `requirements.txt` を作成。
2. 必要なライブラリを `requirements.txt` に追記。
3. `pip install -r requirements.txt`。
4. `pip freeze > requirements_results.txt`。
5. `requirements_results.txt` をリポジトリにpush。
6. ライブラリ追加時は①〜⑤を再実施。
7. GitHub Dependabotで自動脆弱性チェック。

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

* リポジトリ直下に `CODE_STYLE.md` を配置。
* プロンプト先頭にガイドへのリンクを記載。

```plaintext
# Please follow this Python coding style guide:
# https://github.com/your-org/your-repo/blob/main/CODE_STYLE.md
```

---

上記をベースにプロジェクト固有ルールを追加し、一貫性を保ちながら運用してください。
