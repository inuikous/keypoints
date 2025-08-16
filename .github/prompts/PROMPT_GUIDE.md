# Unified Prompt Guide (ALWAYS LOADED)

本ファイルは以下3ガイドを統合: 旧 `PROMPT_GUIDE.md` (一般テンプレ) + `AGENT_PROMPT_GUIDE.md` (内部フェーズ/スコアリング) + `AMBIGUOUS_PROMPT_GUIDE.md` (曖昧→精緻化)。
全プロンプト生成時に自動ロードされる唯一の参照ガイド。追加参照不要。

常時前提ロードセット: `CODING_STYLE.md`, `python.instructions.japanese.md`, (本ファイル)。

---
## 0. フロー全体像 (Phase Map)
```
Phase 0 (必要時): Ambiguity Detect → Refine (PROMPT_REFINEMENT)
Phase 1: Analyze (要求理解 + 不明点 ≤2 + 仮定宣言)
Phase 2: Alternatives (3案 + スコア表)
Phase 3: TestPlan (正常/失敗/境界/エッジ)
Phase 4: Implement (最小で緑)
Phase 5: Enhance (任意最適化/リファクタ)
Phase 6: QualityGate (lint/type/test 要約)
Phase 7: Next (後続提案)
```
曖昧判定で Phase 0 へ。確定プロンプト (# MODE: FINAL_PROMPT) 出力後 Phase 1 へ移行。

---
## 1. 曖昧判定 (自動)
発火条件 ANY:
- 曖昧語: 「適当」「いい感じ」「なんか」「よしなに」「ざっくり」「整理して」「最適化して」
- 文字数 <15 且つ 技術トークン <2
- 動詞のみ/対象欠落 (例: "高速化して")
- `/^(.+して)$/` 的単文で成果物形式不明

発火時: コード生成禁止 → PROMPT_REFINEMENT テンプレ出力。

### 1.1 PROMPT_REFINEMENT テンプレ
```
# MODE: PROMPT_REFINEMENT
## Assumptions
Goal: <推定1行> (conf=0.xx)
TaskType: <feature|refactor|bugfix|test|removal|investigation|doc> (conf=...)
Scope: <推定ファイル/関数> (conf=...)
EdgeCases: <最大4件>
Constraints: <推定 or 既定>

## Gaps (<=3)
1. <質問1>
2. <質問2>
3. <質問3>

## Candidates
### A Minimal
<候補本文>
### B Balanced
<候補本文>
### C Rich
<候補本文>

Scores (1-5)
| Plan | Speed | Robustness | Maintainability | Risk | Total |
|------|-------|-----------|-----------------|------|-------|
| A    |       |           |                 |      |       |
| B    |       |           |                 |      |       |
| C    |       |           |                 |      |       |

## Recommended
<候補ID + 理由≤4行>

## Next Actions (User)
- OK: <候補ID>
- 回答: Q1=..., Q2=...
- 修正: Goal/Scope/EdgeCases 差し替え ↓
```

### 1.2 生成ルール
- Constraints 既定: 型必須 / Google Docstring / 行長88 / カバレッジ≥90% / ValueError or ValidationError / rename語→互換ラッパ禁止
- EdgeCases 選択 (Minimal=2, Balanced=3, Rich=4) from [空/None, 境界, 巨大, 重複, 例外, 並行, I/O]
- Gaps: conf<0.6 属性上位 ≤3 (超過は “他は後続で検証”)
- Candidate 差異: Minimal=最小必須, Balanced=標準, Rich=Unknowns+NonGoals+性能
- Total=(Speed+Robustness+Maintainability)-Risk

### 1.3 確定
ユーザが候補選択 or 回答提供 → 1件の最終プロンプト (# MODE: FINAL_PROMPT) 再出力 → Phase 1.
応答無 2ターン → Minimal 仮定明示で進行。

---
## 2. 基本原則
1. 1タスク=明確成果物 (コード / テスト / 差分 / 分析)
2. 先にゴール&制約 → 簡潔設計 → 出力形式
3. 常に: 代替案比較 → 最適案選択理由 → 実装 → 品質ゲート
4. 後方互換ラッパ禁止 (deprecation policy)
5. WHY コメントで意思決定を最小残量で可視化

---
## 3. スコア指標 (1-5)
| 指標 | 5 | 3 | 1 |
|------|---|---|---|
| Speed | 即実行 | 中 | 重準備 |
| Robustness | 主要+エッジ | 主要のみ | 脆弱 |
| Maintainability | 明瞭/分離 | 標準 | 密結合 |
| Risk | 影響極小 | 中 | 破壊的 |
推奨 Total=(Speed+Robustness+Maintainability)-Risk。

---
## 4. 最小設計ブリーフ テンプレ (50〜80行推奨)
```
# Goal
<機能1行>

# Context
<関係モジュール / 現状課題>

# Interfaces
Input: <型/例>
Output: <型/例>

# Constraints
- 性能: <O(n) 等>
- 例外: <ValueError on ...>
- スタイル: CODING_STYLE.md / 行長88

# EdgeCases
- 空/None/境界/巨大/重複...

# SuccessCriteria
- テストX件 / カバレッジ>90% / mypy pass

# NonGoals
- <触れない領域>

# Unknowns (≤2)
- 不明点1 (回答なければ仮定A)
```

---
## 5. 指示テンプレ (通常フェーズ開始用)
```
タスク: <機能/修正/調査>
設計: <最小設計ブリーフ or 差分のみ>
要求:
- 代替アプローチ 3件 (Baseline / Optimized / Minimal)
- Speed / Robustness / Maintainability / Risk スコア (1-5)
- 最適案選択理由 ≤5行
- テスト方針 (ケース列挙)
- 実装 (差分) + テスト
- 品質ゲート要約 (lint/type/test)
出力形式: 1) Plan 2) Chosen 3) Diff 4) Quality 5) NextSteps
参照: CODING_STYLE.md / 廃止ポリシー / 本ガイド
```

---
## 6. 典型ショートカット
| 目的 | ショート指示例 |
|------|----------------|
| 新機能 | `タスク: 画像前処理関数追加。<短ブリーフ> 上記テンプレで。` |
| リファクタ | `タスク: 関数X循環的複雑度15→≤8。代替案比較付き。` |
| バグ調査 | `タスク: 例外Y再現と原因特定→修正案3→最適案実装。` |
| テスト強化 | `タスク: validators.parse エッジ網羅 (既存仕様保持)。` |
| 廃止 | `タスク: old_func rename new_func。互換ラッパ禁止。全呼び出し置換。` |

---
## 7. アンチパターン
- 「適当に」「いい感じに」等の曖昧語 (自動Refine対象)
- 実装手段詳細を過剰固定
- 大型変更一括 (分割不足)
- legacy_ / deprecated_ ラッパ提案

---
## 8. チェックリスト (最終プロンプト提出前)
[ ] Goal / Output 明確  
[ ] Constraints (性能/例外/スタイル)  
[ ] EdgeCases (≥2)  
[ ] SuccessCriteria (テスト/カバレッジ/型)  
[ ] NonGoals or 明示的無し  
[ ] Unknowns or 仮定  
[ ] 代替案比較要求  
[ ] 後方互換ラッパ禁止明示(該当時)  

---
## 9. 1行ショート版
```
タスク:<要約>/目的:<1行>/制約:<主要3>/Edge:<2>/成功:<指標>/代替案比較して実装。
```

---
## 10. 代表エッジケースセット
- 空/None
- 境界(最小/最大/負など)
- 巨大データ量
- 重複/順序
- 並行/競合
- I/O 失敗
- 例外経路 (外部サービス不達 等)

---
## 11. 例: 関数実装
```
目的: CSV行を辞書へ変換。
背景: services/data_loader.py へ追加。列 id(int), name(str), score(float)
要件:
- 無効列数=ValueError
- 空白trim / 数値変換失敗 raise from
- 型+Google Docstring+計算量
- テスト(正常/欠損/型不正)
出力: 関数コード + tests/unit/test_data_loader.py
```

---
## 12. 例: リファクタ
```
目的: heavy_calc.compute_all の複雑度低減。
背景: 150行, CC>15
要件: ガード節化, 重複抽出, 既存シグネチャ維持, 内部関数Docstring
出力: 差分パッチ
```

---
## 13. 例: テスト生成
```
目的: validate_user 網羅テスト。
要件: 正常境界 / 空 / None / 型不正 / 権限例外 / pytest parametrize
出力: tests/unit/test_validators.py
```

---
## 14. 例: 例外改善
```
目的: db.connect() の広域 except を細分化。
要件: 捕捉対象提案 / メッセージ形式統一 / raise from 適用箇所
出力: 改善案 + パッチ
```

---
## 15. Before→Refine デモ
User: `画像前処理いい感じに高速化して`
Refine抜粋:
```
Goal: 画像前処理パイプライン高速化 (conf=0.78)
TaskType: refactor
Scope: services/image_preprocess.py (conf=0.72)
EdgeCases: 空画像, 超高解像度, 異常チャネル
Constraints: 行長88 / 型必須 / Google Docstring / 精度劣化なし(画素差<1e-3)
Gaps: 1. 目標ms? 2. 並列(CPU/GPU)? 3. 現行平均?
```

---
## 16. Quality Gate 期待
- Lint (ruff/black/isort) PASS
- Type (mypy) PASS
- Tests PASS (失敗 0)
- Coverage ≥90% (必要ファイル)
- 破壊的変更時: 全呼出更新 / ラッパ不在

---
## 17. 出力形式ガイド
| モード | 用途 | 必須セクション |
|--------|------|----------------|
| PROMPT_REFINEMENT | 曖昧入力時 | Assumptions / Gaps / Candidates / Scores / Recommended / Next |
| FINAL_PROMPT | 確定後 | Goal / Constraints / EdgeCases / SuccessCriteria / (Optional NonGoals) |
| IMPLEMENT_RESULT | 実装完了 | Plan要約 / Diff / Tests / QualityGate / Next |

---
## 18. FAQ
Q. どこまで詳細に書くべき?  
A. 不変契約(入出力/例外/性能)は明示。内部アルゴリズムは最小。  
Q. 曖昧か自信がない時?  
A. Refine を強制発火 (手動で “曖昧扱い” と明記)。  
Q. 進行中に追加要件?  
A. NextSteps で再チケット化しスコープ肥大防止。  

---
## 19. 成功定義 (内部メトリクス)
- 曖昧→1往復以内確定率 ≥80%
- 自動補完採用率 ≥60%
- 追加質問平均 ≤1
- ラッパ提案 0件

---
## 20. 1行ショート例
```
タスク: CSVパーサ追加 / 制約: 型+ValueError+O(n) / Edge: 空行,数値不正 / 成功: >=90%cov / 代替案比較して実装。
```

---
この統合ガイドを唯一ソースとし、他ガイドの重複版は順次削除/リンク化すること（DRY維持）。改善提案は別PRで最小差分。
