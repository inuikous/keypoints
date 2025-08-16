---
description: 'Python コーディング規約 (日本語版)'
applyTo: '**/*.py'
---

# Python コーディング規約（AIコード生成最適化版）

本ドキュメントは **GitHub Copilot 等のコード生成AIが最小曖昧性で正確にコードを生成** できるよう、
人間/AI双方が解釈しやすい「優先順序付きルール + 明示チェックリスト + プロンプトテンプレ」を提供します。

> 目的: 初学者でも「指示の抜け漏れ/再生成リトライの手戻り」を最小化し、品質と一貫性を自動化ツールで確実に担保する。

---

## 🔁 最上位優先順位 (AIへ渡す簡潔サマリ / TL;DR)

1. 可読性 > 短文化 > 早すぎる最適化禁止。
2. すべての公開関数/メソッド/テストに型ヒント + GoogleスタイルDocstring。
3. 設定は環境変数禁止・`resources/ApplicationConfig.xml` に集約。
4. Path操作は `pathlib.Path`、文字列連結禁止。
5. 後方互換ラッパ禁止（rename後は旧名削除）。
6. 例外は握りつぶさない。`raise ... from err` を優先。
7. テストカバレッジ 90% 以上 (pytest + parametrize)。
8. Dead code は即削除（コメントアウト保管禁止）。
9. インポート順: 標準 / サードパーティ / 自プロジェクト（空行で区切る）。
10. 行長 88 / Black / isort(profile=black) / Ruff (or flake8)。

> AIにはまずこの 10 行を読み込ませる。詳細差異が必要になった時のみ下位節を参照。

---

## ✅ 最小チェックリスト (生成前に AI プロンプトへ貼り付け可)

```
【Code Checklist】
[] 目的/入出力/利用者/制約(性能・I/O)を明文化したか
[] 例外ポリシー(何を raise / どこで捕捉)を指定したか
[] 型ヒント & Google Docstring 必須と記したか
[] 路径処理は pathlib / 設定は ApplicationConfig.xml と明示したか
[] ログレベルと禁止(機密値)を指示したか
[] テスト観点(正常/境界/エラー1件以上)を列挙したか
[] 後方互換ラッパ不要 & 旧API削除方針を明示したか
[] 依存追加時の requirements 更新フローを指示したか
[] 完了定義(DoD)を明記したか
```

---

## 🧩 推奨プロンプトテンプレ (AIへ渡す指示例)

```
あなたは本リポジトリのPythonエンジニアです。CODING_STYLE.md の「最上位優先順位」「チェックリスト」に従い、以下を実施してください。

【タスク】<何を実現したいか1行>
【目的】<ユーザ価値 / 上位ユースケース>
【入出力】Input: <型/意味> -> Output: <型/意味>
【制約】性能:<ms or QPS>, メモリ:<MB>, 対応OS:<list>
【例外方針】<主要な raise, どこで捕捉するか>
【ログ】INFO=進行要点, DEBUG=詳細, 機密値マスク
【アルゴリズム案】<簡潔: O記法や根拠>
【テスト観点】正常 / 境界 / エラー / 大量データ / I/O失敗
【非機能】可読性>性能, 早期return, 後方互換ラッパ禁止
【完了定義】型/Docstring/テスト(>=90%)/lint/format全OK
出力: 1) 設計要約 2) 実装コード 3) テストコード 4) 次の改善提案
```

---

## ℹ️ 本文（詳細規約）

この節以下は既存規約の詳細版です。AIへの投入は必要最小限とし、ヒューマンレビュー/参照用に保持します。

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
16. [禁止事項 / 閉域ネットワーク制約](#禁止事項--閉域ネットワーク制約)
17. [付録（実務ガイド）](#付録実務ガイド)

---

## 基本思想

* **可読性第一**：誰が見ても理解しやすいコードを最優先。
* **一貫性**：全体で同一のルールを適用。
* **自動化容易性**：CI／Lint／フォーマッタとの親和性を重視。
* **拡張性**：小規模から大規模までスケール可能な構成。
* **外部環境依存の排除**：環境変数・利用端末固有パス・外部ネットワーク可否に挙動を依存させない（閉域/製造現場での再現性確保）。

---

## ファイル・ディレクトリ構成

```plaintext
ProjectName/
├── ProgramName/
│   ├── main.py
│   ├── common/   # 開発Gr内共通モジュール ※まだ存在しないため不使用
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

* **GoogleスタイルDocstring**（PEP 257準拠）義務。
* すべての公開シンボル: 説明 / Args / Returns / Raises / Examples(必要時) / Notes(逸脱理由)。
* 複雑度閾値超過（行数>50 or 循環的複雑度>10）は Docstring の `Notes:` に理由を記述。
* 可能なら `Examples:` に最小実行例（I/O 1:1）を追加し Copilot の補完精度を高める。

### Docstring最小テンプレ

```python
def connect(host: str, port: int = 5432) -> Connection:
    """DBに接続する。

    Args:
        host (str): ホスト名。
        port (int, optional): ポート番号。デフォルト5432。

    Returns:
        Connection: オープン済み接続。

    Raises:
        ConnectionError: ネットワーク/認証失敗。

    Examples:
        >>> conn = connect("db.internal", 5432)
        >>> conn.is_alive()
        True
    """
    # 実装...
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
* **Path/IO ポリシー**:  パス操作は `pathlib.Path` を第一選択とし、`os.path.*` は互換性/低レベル API が必須の場合のみ。文字列連結でのパス生成禁止。例: `Path(base) / "sub" / filename`。
* **環境差異吸収**: ホームディレクトリやユーザ名を参照しない。必要な一時領域はアプリ自身のワークディレクトリ直下 (`./runtime/` 等) を明示生成。
* **動的設定更新**: ホットリロード対象は ConfigService 経由に限定。直接ファイルを開いて書き換えるユーティリティ関数を追加しない。

```python
from pathlib import Path

cfg_dir = Path("resources")
config_file = cfg_dir / "ApplicationConfig.xml"  # 連結は / 演算子
```

`os.environ.get` や `os.getenv` を用いた分岐や隠しフラグは禁止。実装レビューで検出次第修正。

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

### プロンプト例（廃止対応指示）
```
以下の関数 rename を実施してください:
旧: process_image  新: run_image_pipeline
要件: 旧名の残存禁止 / ラッパ禁止 / すべての呼び出し点を書き換え / テスト名も同期 / Dead code 削除。
出力: 変更差分要約 + 更新コード + 影響範囲一覧 + テスト更新案。
```

---

## 🤖 AI への投入/レビュー時フォーマット推奨

以下を **Issue / PR 説明 / Copilotチャット最初のメッセージ** に貼ると再現性が高まる。

```
【Context】機能概要 / 背景 / 利用者
【Goal】達成後の観測可能な状態
【Non-Goals】今回扱わない範囲
【Constraints】性能 / メモリ / I/O / 外部接続可否
【Interfaces】公開予定関数(シグネチャ草案)
【Data Flow】入力 -> 加工 -> 出力 (簡潔)
【Error Policy】主要例外 / 再試行方針
【Test Plan】正/境界/例外/大規模/スモーク
【Done Definition】lint/format/tests(≥90%)/型/レビュー合意
```

---

## 🧪 DoD (Definition of Done) 再掲
* Black / isort / Ruff 無警告。
* mypy (導入済領域) pass or 許容例外に `# type: ignore` (理由コメント必須)。
* pytest 全緑 / カバレッジ 90%+ (除外は `# pragma: no cover` + 理由)。
* Docstring & README 反映。
* Dead code / 未使用 import / TODO 無し（残す場合は Issue 番号必須）。

---

## 📎 付録: 失敗しやすい曖昧指示と改善例

| NG 指示 | 問題 | 改善例 |
|---------|------|--------|
| 画像を処理する関数作って | 入出力条件不明 | PNG/RGB画像(Path/np.ndarray許容)を読み→リサイズ(長辺=256)→正規化(float32[0,1])→np.ndarray返却 |
| 早くして | 指標不明 | 処理時間 <50ms (100枚バッチ時)、アルゴリズム O(n) を維持 |
| エラー処理ちゃんとして | 例外境界不明 | I/O失敗=Retry3回→ConnectionError、パラメータ不正は ValueError 即raise |

---

## 🗂 機械可読サマリ (スクリプト抽出用 YAML) 
> 自動整形禁止。ツールがこのブロックを抽出可能。

```yaml
style:
    line_length: 88
    formatter: black
    import_sorter: isort
    linter: ruff
    typing: required_public
    docstring: google
tests:
    framework: pytest
    coverage_min: 0.90
    layout: tests/{unit,integration}
    edge_cases: [empty, boundary, large, error, io_failure]
deprecation:
    wrapper_allowed: false
    rename_policy: update_all_refs_same_pr
paths:
    config: resources/ApplicationConfig.xml
    models: ProgramName/models
    results: ProgramName/results
exceptions:
    rethrow_with_cause: true
    mandatory_message: true
```

---

（以上）

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
