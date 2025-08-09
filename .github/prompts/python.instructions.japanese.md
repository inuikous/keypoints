---
description: 'Python コーディング規約 (日本語版)'
applyTo: '**/*.py'
---

# Python コーディング規約 (日本語版簡易指針)

本ファイルは Copilot / 自動生成支援が最小限参照すべき“強制力の高いコア原則”を短くまとめたものです。詳細は `CODING_STYLE.md` を参照してください。

## 基本方針
- 可読性と一貫性を最優先。
- 可能な限り **副作用は小さく/関数は短く (目安 ≤50行)**。
- 設計判断はコメントに WHY を付与。

## コメント / Docstring
- すべての公開関数・クラスに **Googleスタイル Docstring**。
- 目的 / 引数(型) / 戻り値 / 例外 / 必要なら計算量・前提条件・Examples を記載。
- 1行目は概要。詳細は空行後に追記。

## 型アノテーション
- 公開APIは引数・戻り値に必須。戻り値なしでも `-> None`。
- `from __future__ import annotations` 推奨。

## 命名
- snake_case（関数/変数）、UpperCamelCase（クラス）、ALL_CAPS（定数）。
- ブールは is_/has_/can_。コレクションは複数形。単位は末尾に (timeout_ms)。

## インポート
1. 標準
2. サードパーティ
3. 自プロジェクト
- グループ間は空行。ワイルドカード禁止。不要インポート削除。
- 遅延読み込みや循環回避の特例は WHY コメント必須。

## フォーマット
- Black 行長 88。isort(profile=black)。
- 文字列は f-string 優先。ロギングは遅延フォーマット (`logger.info("x=%s", x)`)。

## 例外
- 広域 except: 禁止。必要十分に絞る。
- メッセージ形式: 行為 + 対象 + 期待 vs 実際 + 次アクション。
- 原因継承: `raise NewError(...) from err`。

## テスト (pytest)
- testpaths: ProgramName/tests
- 単体 tests/unit, 結合 tests/integration。
- カバレッジ目標 ≥90%。
- 各テスト Docstring: 目的/期待。
- 代表エッジ: 空/None/境界/巨大/重複/例外/並行/I/O。

## エッジケース
- 事前条件検証を行い、失敗時は ValidationError または ValueError。
- 非常に重いテストはマーカー (# slow) を付け分離可能。

## 廃止ポリシー
- 後方互換ラッパを残さず **即時置換 & 古いシンボル削除**。
- legacy_/deprecated_ 命名禁止。履歴は Git で参照。
- 例外的猶予は # DEPRECATED: <削除予定日> コメントとともに 1 スプリント以内。

## 依存
- 必要最小のライブラリのみ。理由 (WHY) を PR かコメントに。
- 新規追加はセキュリティ/保守性を考慮 (更新頻度・メンテ状況)。

## ログ
- グローバル print 禁止。logging 使用。
- 機密値は出力しない (マスク)。

## 生成コードへの要求 (Copilot への明示例)
```
以下を満たすコードを生成:
- CODING_STYLE.md 準拠 (Google Docstring, 型, 行長88)
- 不要互換ラッパ禁止 / 旧API残さない
- エッジケース: 空/None/境界/例外
- テスト (正常+失敗1例) も生成
```

## サンプル Docstring
```python
def parse_scores(line: str) -> list[int]:
    """CSV行から整数スコア配列を抽出。

    Args:
        line (str): "1,2,3" のようなカンマ区切り文字列。

    Returns:
        list[int]: 変換済み整数リスト。

    Raises:
        ValueError: 空行/数値変換失敗時。
    """
    ...
```

## 禁止事項
- ワイルドカード import
- 使われないコードの温存/コメントアウト遺骸
- グローバル可変状態の乱用
- print デバッグ (logging を使う)

---
この instructions ファイルは機械支援向け “短縮版”。詳細な規約差異があれば CODING_STYLE.md を正とする。
