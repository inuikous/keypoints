# 標準開発フロー（GitHub Copilot 活用ガイド）

本ドキュメントは **Copilot 初心者が曖昧さ/手戻りを最小化** し、設計〜実装〜テスト〜レビューを一貫して高速に進めるための標準的手順を示します。`CODING_STYLE.md` の AI 最適化版と併用してください。

---
## 0. ゴール定義フェーズ
1. 課題/要求を 1 行で要約（誰が何のために）。
2. 完了後に観測できる状態 (Success Criteria) を列挙。
3. スコープ外 (Non-Goals) を 2〜3 行で明示。
4. 制約 (性能/遅延/メモリ/外部接続/OS) を具体値で書く。

テンプレ:
```
【Task】ユーザが結果画像をPNGでダウンロードできるAPI追加
【Goal】/export が 200 (<500ms, 画像<2MB) で PNG を返す
【Non-Goals】PDF出力, 認証方式変更
【Constraints】同時50req, メモリ<256MB, 外部HTTP禁止
```

---
## 1. 最小設計（Copilot へ渡す前）
以下を埋めてからプロンプトへ貼る。抜けがあると再生成率が上がる。
```
【Interfaces】
- def export_image(record_id: str, fmt: str = "png") -> Path
【Data Flow】DB読み出し -> Pillow変換 -> 正規化 -> 一時保存 -> Path返却
【Errors】存在しないID=NotFoundError, 変換失敗=ImageConvertError
【Logging】INFO=開始/完了, WARNING=再試行, ERROR=失敗詳細
【Test Cases】正常/存在しないID/不正fmt/巨大画像/並列10件
【Performance】1画像処理<80ms, バッチ(10) < 1s
【Deprecation】旧 export_png() は本PRで削除
【Done Definition】型/Docstring/pytest>=90%/Black/isort/Ruff OK
```

---
## 2. Copilot への標準プロンプト
```
CODING_STYLE.md の最上位優先順位とチェックリストに従って以下を実装してください。
<上記 0,1 で記述したブロック貼り付け>
出力: 
1) 設計要約 (データフロー図テキスト + 例外一覧) 
2) 実装コード (必要ファイルすべて) 
3) テストコード (pytest, 正常/境界/エラー) 
4) 実行/テスト手順 (Windows cmd) 
5) 改善候補 (性能/保守/拡張)
禁止: 旧APIラッパ, 環境変数, 文字列でのパス連結, 未使用import
```

---
## 3. 生成結果レビュー手順 (手戻り防止)
| チェック | 具体観点 | OK条件 |
|----------|----------|--------|
| 構造 | ファイル配置 | `ProgramName/` 配下 & 既存構造順守 |
| 型 | すべて公開関数 | 引数/戻り値に型ヒントあり |
| Docstring | Google形式 | Args/Returns/Raises/Examples 必要時 |
| 例外 | 握り潰し無 | `except Exception:` で空処理なし |
| ログ | 過不足 | ERRORで `exc_info=True` |
| 設定 | 禁止事項 | 環境変数未使用, ApplicationConfig.xml 不整備なら TODO化し Issue番号 |
| テスト | 網羅 | 正常/境界/エラー/大ケース 少なくとも1つずつ |
| カバレッジ | pytest-cov | 90% 以上 (除外理由明示) |
| 依存 | requirements | 新規ライブラリ追加時フロー遵守 |
| Dead code | 未使用 | 未参照シンボル無し (`grep`, IDE) |

---
## 4. テスト & 品質自動化
1. 仮想環境起動
```
.venv\Scripts\activate
```
2. Lint & Format (失敗したら自動修正→再実行)
```
black ProgramName tests
isort ProgramName tests
ruff check ProgramName tests
```
3. テスト
```
pytest --maxfail=1 -q
pytest --cov=ProgramName --cov-report=term-missing
```
4. カバレッジ閾値不足時: 追加テスト (エラー経路/境界) を最優先補完。

---
## 5. 依存追加フロー
1. `requirements.txt` に追記
2. `pip install -r requirements.txt`
3. `pip freeze > requirements_result.txt`
4. 差分レビュー (不要transitive削除検討)
5. PR に "依存追加理由 + 代替検討" を明記

---
## 6. リファクタ / Rename 手順
1. 目的 (性能改善/重複削減/命名整合) を 1 行で。
2. 影響範囲 grep + テスト一覧化。
3. Copilot 指示 (旧→新, ラッパ禁止, テスト更新)。
4. 生成差分レビュー後 一括置換。
5. Dead code/旧名消滅を confirm。

テンプレ:
```
関数 rename: old_name -> new_name
根拠: 責務再定義/曖昧命名改善
要求: 旧シンボル完全削除, 参照全更新, テスト関数名同期
```

---
## 7. 失敗パターンと回避
| 失敗 | 症状 | 回避策テンプレ |
|------|------|---------------|
| 要件曖昧 | 再生成連発 | 入出力/制約/DoD ブロック化して貼る |
| 例外抜け | 実行時Unhandled | 主要例外と再試行方針 明示 |
| テスト漏れ | カバレッジ不足 | チェックリストの Edge Case 行を先に列挙 |
| 依存過多 | ビルド遅延 | 目的と軽量代替案をPR記述 |
| ラッパ残骸 | 二重API | Deprecation原則テンプレ使用 |

---
## 8. PR テンプレート（コピーして使用推奨）
```
### 概要
<機能/修正概要>

### 目的 (ユーザ/運用価値)

### 実装ポイント / 代替案

### 例外 & ログ方針

### テスト結果
- 正常: <要約>
- 境界: <要約>
- エラー: <要約>
- カバレッジ: xx%

### 破壊的変更
有 / 無 （有の場合: 影響 & 移行手順）

### チェックリスト
- [ ] Black/isort/Ruff Pass
- [ ] 型 & Docstring 完備
- [ ] カバレッジ >= 90%
- [ ] Dead code 無し
- [ ] 依存追加/変更理由明記
```

---
## 9. スモールスタートガイド (初回学習用)
1. 100行未満の小タスクを選ぶ
2. 上記 0/1 のテンプレを埋める
3. Copilot へテンプレ貼付→生成
4. チェックリストで差分検証
5. 不足のみ再生成（全文指示し直さない）
6. テスト/品質ゲート通過→PR

---
## 10. Quick Reference (最頻コマンド)
```
# 生成後品質
black ProgramName tests
isort ProgramName tests
ruff check ProgramName tests
pytest -q
pytest --cov=ProgramName
```

---
## 11. FAQ
Q: プロンプトが長いと遅くなる?  
A: 重要ブロック(チェックリスト/要件)は短文化し箇条書き化。冗長説明は省く。  
Q: 途中修正はどう指示?  
A: 変更点のみ "差分指示" (例: 【変更】性能制約 80ms→60ms) を最初に列挙して再生成。  
Q: カバレッジ到達が難しい?  
A: 例外経路 / 入力検証 / 境界長さ / 異常I/O を優先追加。

---
（以上）
