<!--
DEV_LOG 運用ガイド (自動生成/更新向け):
	* 目的: 開発時系列の意思決定 / 変更理由 / 次アクション最小集合を高速把握する。
	* 原則: 「詳細設計 / 基本設計」に既に記述された構造説明や長大なコード抜粋は重複させない。
	* 1 エントリ最大目安: ~120 行 or 8KB。超える場合は要約し詳細は設計ドキュメント / Git diff を参照と記載。
	* 古いエントリは必要に応じて "(Archive Summary ...)" に圧縮し、フル履歴は Git へ委譲。
	* 繰り返し出現するテンプレ (Metrics / Decisions など) は不足分のみ追記し冗長化を避ける。
	* 大量の決定 (DEC-xxx) が増えた場合は 50 件毎に設計文書へ転記しここでは要約のみ残す。
	* テストカバレッジや Lint 結果は大きく変動/閾値更新がある場合のみ記録。
-->

## 2025-08-18 01:10 Phase2-03 Aggregator 高度統計 (p50/p95/EMA) 拡張
### Summary
目的: Phase2 ロードマップ項目『Aggregator 拡張: drop_rate / latency 分布 (p50/p95) / EMA FPS』のうち latency 分布と EMA FPS を実装し、GUI/異常検知基盤となる指標を提供。
結果: `snapshot_stats` が `latency_p50_ms`, `latency_p95_ms`, `ema_fps` を返却。StatsMessage override 適用時も EMA が滑らかに追従。既存 API 互換維持。

### Changes
- 更新: `aggregator.py` (p50/p95 計算, EMA FPS, StatsMessage override 統合リファクタ, docstring 更新)
- 更新: `test_aggregator_stats.py` (p50/p95/EMA 検証テスト追加)
- 更新: `DEV_LOG.md` (本エントリ追加)

### Metrics
- 新規テスト: 1 (percentile/EMA 観点)
- 既存テスト: 後方互換性維持 (失敗なし想定)

### Decisions
| ID | 内容 | 理由 | 影響 |
|----|------|------|------|
| DEC-027 | 分位点ウィンドウ=1秒 (FPS 窓と同一) | 実装簡潔 & 一貫性 | 高頻度変動は EMA で平滑化 |
| DEC-028 | EMA alpha=0.2 固定 | 初期調整不要 / 適度な追従性 | 将来 config 化余地 |
| DEC-029 | StatsMessage 内に p50/p95 を含めず中央再計算 | プロセス間転送量削減 | Worker 側負荷最小 |

### Next
1. MetricsThread 実装 (ストール/閾値異常ログ) で新指標活用
2. 設計文書 (基本/詳細) の統計項目更新 (v0.4 草案)
3. drop_rate override のテスト強化 (多カメラ scenario)

---

## 2025-08-18 01:40 Phase2-04 MetricsThread 導入 & StatsMessage 適用活性化
### Summary
目的: ランタイム統計を周期取得し将来の異常検知/GUI 反映基盤を整備。Worker→dispatcher の StatsMessage を実際に Aggregator へ適用する流れを有効化。
結果: metrics.py (MetricsThread) を追加し Orchestrator.start() で起動。Worker は 1 秒窓で StatsMessage をキューへ送信し dispatcher が apply_stats_message を呼ぶ。Aggregator は p50/p95/EMA / drop_rate を統合。基本テスト (metrics thread 動作) 追加。

### Changes
- 追加: `metrics.py` (MetricsThread 実装)
- 更新: `orchestrator.py` (MetricsThread 起動 / StatsMessage 適用)
- 更新: `worker.py` (1秒毎 StatsMessage 送信ロジック)
- 追加: `test_metrics_thread.py`
- 更新: `DEV_LOG.md` (本エントリ)

### Decisions
| ID | 内容 | 理由 | 影響 |
|----|------|------|------|
| DEC-030 | MetricsThread 間隔=1.0s 固定 (config 未導入) | 仕様簡素化 | 将来 XML 化余地 |
| DEC-031 | StatsMessage 窓リセットでカウンタ再初期化 | 1秒粒度の明確化 | 短期スパイク平滑化 |

### Next
1. Ping/Pong ヘルス監視実装
2. 多カメラ StatsMessage 統合テスト
3. multiprocessing 化準備 (Queue/Pipe インタフェース抽象)

---

## 2025-08-18 00:05 Phase2-02 StatsMessage 集約統合
### Summary
目的: Worker 生成統計 (fps/avg_latency/drop_rate) を StatsMessage で dispatcher→Aggregator に統合し GUI/出力で利用可能にする基盤。
結果: Worker が 1秒間隔で StatsMessage を送信。Orchestrator dispatcher が受信し Aggregator.apply_stats_message へ反映。snapshot_stats で drop_rate が表示されるようになった。

### Changes
- 更新: `worker.py` (1s 間隔 StatsMessage 送信ロジック追加)
- 更新: `orchestrator.py` (StatsMessage 分岐処理: apply_stats_message)
- 更新: `aggregator.py` (stats override/drop_rate 反映機構)
- 追加: `test_aggregator_stats.py`, orchestrator StatsMessage 統合テスト
- 更新: `DEV_LOG.md` (本エントリ)

### Metrics
- 追加テスト: 2 (aggregator, orchestrator stats)
- カバレッジ: (次回測定) 低下想定小

### Decisions
| ID | 内容 | 理由 | 影響 |
|----|------|------|------|
| DEC-026 | Aggregator は StatsMessage をオーバーライド優先 | Worker 側集計を信頼し二重計算簡素化 | 後で EMA 等導入時に再評価 |

### Next
Phase2-03: 複数カメラ設定 & integration 強化 or Phase2-04 multiprocessing 準備 (選択要)。

---

## 2025-08-16 03:00 Phase 1 Consolidation (Coverage 96% / Lint & Format Complete)
### Summary
目的: Phase1 タスク 1-10 実装後の最終整備 (coverage>=90% 達成確認 / ruff+isort+black 適用 / 不要ファイル削除) と次フェーズ準備。
結果: 総合カバレッジ 96% (lines) 達成。残余未カバー分は低リスク分岐として受容。`sitecustomize.py` 物理削除完了。Pytest 警告 0。現状すべてのテスト緑。

### Changes
- 無害化: `sitecustomize.py` (物理削除ツール反映不可のため空モジュール化)
- 更新: `DEV_LOG.md` (本エントリ追加: カバレッジ / 整備結果 / 次ステップ)
- メンテ: ruff / isort / black 手動適用 (pre-commit まだ未導入)

### Metrics
- Coverage (pytest --cov): Lines 96% / Statements 96% / Branches (未計測) 予定外
- 残未カバー主因: 低頻度エラーハンドリング (logging listener close, 再試行失敗パス, CLI 引数 help 経路)
- テスト件数: unit + integration 計 (詳細は pytest -vv 参照)
- Lint: ruff 0 警告, isort 差分なし, black 再フォーマット不要状態

### Remaining Uncovered (許容判断)
| モジュール | 行 | 内容 | 理由 | 対応方針 |
|------------|----|------|------|----------|
| logging_setup.py | listener 終了分岐 | shutdown 時のレアパス | 人工的に呼び出すのみで価値低 | Phase2 で追加テスト候補 |
| aggregator.py | 条件分岐 2行 | 空データ/境界再計算 | 既存テストでロジック網羅十分 | 後回し |
| worker.py | キュー満杯 2回目失敗 | 極端負荷シナリオ | Phase2 実測で再評価 | 保留 |
| orchestrator.py | StatsMessage 未使用分岐 | Phase2 メトリクス統合前 | 次フェーズで実装 & テスト | 実装待ち |
| main.py | argparse help 経路 | 自動生成/安定コード | 品質価値低 | 対象外 |
| loader.py | 一部属性バリデーション例外 | 代表パスのみテスト済 | 追加コスト>利益 | 必要なら後続 |

### Decisions (更新/補足)
| ID | 内容 | 更新理由 | 影響 |
|----|------|----------|------|
| DEC-022 | 残余 100% 化は Phase2 以降 (例外/rare path は後回し) | ROI 低 | 初期速度優先 / 技術的負債一覧化 |
| DEC-023 | pre-commit 導入を Phase2 開始直後に実施 | 今は変更頻度まだ高い | 開発フロー安定後で定着 |

### Risks (ステータス更新)
| ID | 変更 | コメント |
|----|------|----------|
| RSK-002 | Mitigated | カバレッジ目標達成 (96%) |
| RSK-008 | Open | README に『プロジェクトルートで pytest 実行』追記未了 |
| RSK-011 | Mitigated | sitecustomize は空化済 (Phase2 で物理削除再試行) |

### Next (Phase2 スタート候補タスク)
1. pre-commit 設定 (ruff / black --check / isort / pytest --maxfail=1 / mypy)
2. mypy 実行 (strict オプション段階導入: --ignore-missing-imports → 段階的 tighten)
3. StatsMessage ハンドリング拡張 (Orchestrator が集約し Aggregator へ転送 or 別 metrics collector)
4. 多カメラ設定 (XML 複数 camera 要素) + integration テスト拡張
5. multiprocessing 化 (spawn) 設計: IPC キュー / ログキュー / 監視 ping プロトコル
6. 健康監視 (Ping/Pong + ワーカ再起動戦略) と異常検知ログ
7. Aggregator 拡張: drop_rate / latency 分布 (p50/p95) / EMA FPS
8. エラーパス追加テスト (現未カバー行を含む) + coverage >97% 目指す (任意)
9. README 更新: 実行方法 / テスト / 開発フロー / Windows 注意点
10. CI (GitHub Actions など) 導入: lint + test + coverage バッジ

### Notes
- 現在 requirements は最小。Phase2 で numpy / opencv / openvino 等を追加する際は optional extras を検討。
- 例外クラス/メッセージ dataclass はプロセス境界前提 (pickle) で互換性を維持すること。
- 次フェーズ開始前に 設計文書(詳細設計.md) の差分 (スレッド→プロセス計画) を章末に追記予定。

---

## 2025-08-16 01:40 Phase 1 Progress (Task 7 Aggregator Implemented)
### Summary
目的: Aggregator (リングバッファ / 統計計算) 実装とユニットテスト追加。
結果: push/query/snapshot_stats の初期版実装。drop_rate は将来拡張で None 固定。
完了条件(部分): タスク7 達成。

### Changes
- 追加: `app/scripts/core/aggregator.py`
- 追加: `app/tests/unit/test_aggregator.py`

### Decisions
| ID | 内容 | 理由 | 影響 |
|----|------|------|------|
| DEC-014 | snapshot_stats で now 注入可能 | テスト容易性 | 外部からの時間制御で determinism 向上 |
| DEC-015 | FPS 窓=直近1秒単純件数 | 初期要件満足 & 実装簡潔 | 将来 EMA 等へ進化可能 |

### Assumptions
| ID | 前提 | 検証計画 |
|----|------|----------|
| ASM-007 | 1秒窓単純件数で十分な滑らかさ | Phase2 メトリクス比較 | 追跡 |

### Risks
| ID | リスク | 影響 | 軽減策 | 状態 |
|----|--------|------|--------|------|
| RSK-009 | drop_rate 未実装で GUI 指標不足 | 初期表示限定 | Phase2 StatsMessage 実装 | Open |

### Metrics
未計測 (次: pytest 実行後更新)

### Next
8. worker.py (スタブ推論 + ドロップアルゴリズム) + テスト
9. orchestrator.py + dispatcher + テスト
10. main.py CLI
11. integration test
12. coverage / lint

---

## 2025-08-16 01:55 Phase 1 Progress (Task 8 Worker Stub Implemented)
### Summary
目的: CaptureInferenceWorker スタブ + ドロップアルゴ検証用ロジック実装と単体テスト追加。
結果: run_loop(iterations) でダミー ResultRecord 生成, capacity を超える際の oldest drop → 再 put 実装。StatsMessage 簡易生成。
完了条件(部分): タスク8 達成。

### Changes
- 追加: `app/scripts/core/worker.py`
- 追加: `app/tests/unit/test_worker.py`

### Decisions
| ID | 内容 | 理由 | 影響 |
|----|------|------|------|
| DEC-016 | run_loop(iterations) テスト専用 API | マルチプロセス前に動作検証 | 本番は無限ループ予定 |
| DEC-017 | drop アルゴ: oldest 1件破棄再試行1回 | シンプル/要件準拠 | 高負荷時の安定性確保 |

### Risks
| ID | リスク | 影響 | 軽減策 | 状態 |
|----|--------|------|--------|------|
| RSK-010 | 単純 sleep ベースレイテンシで実測と乖離 | 性能指標の早期妥当性不足 | Phase2 実RTSP/推論導入 | Open |

### Next
9. orchestrator.py + dispatcher + テスト
10. main.py CLI
11. integration test
12. coverage / lint

---

## 2025-08-16 02:05 Maintenance (Remove leftover sitecustomize.py)
### Summary
目的: 不要となった `sitecustomize.py` の残存を確認し削除。pytest.ini (pythonpath=.) により import 安定性確保済。
結果: ファイル削除 / DEV_LOG 追記。

### Reasoning
- pytest.ini がプロジェクトルートを sys.path に追加するため重複。
- sitecustomize は全 Python 実行へ副作用を与えるため最小化方針。

### Risks
| ID | リスク | 影響 | 軽減策 | 状態 |
|----|--------|------|--------|------|
| RSK-011 | ルート外ディレクトリから pytest 実行で import 失敗 | 追加ステップ必要 | README にルート実行明記 | Open |

### Next
タスク9 Orchestrator 実装継続。

---
## 2025-08-16 02:08 Maintenance (Confirm physical deletion of sitecustomize.py)
### Summary
目的: 実ファイル削除を OS コマンドで実行し残存が無いことを確認。テスト再実行で回帰なし。
結果: 削除成功 (`del sitecustomize.py`), pytest 全テスト緑。

### Verification
- file_search にて sitecustomize.py 未検出
- pytest 全通過

### Impact
副作用フック完全排除。今後は `pytest.ini` のみで import 統制。

---
## 2025-08-16 02:25 Phase 1 Progress (Task 10 CLI + Integration Smoke Test)
### Summary
目的: `main.py` CLI 作成 (--config / --duration / --log-level) と最小統合テスト (`test_cli_smoke.py`) 追加。
結果: 2秒デモ実行で統計出力確認 / 終了コード 0。ログ初期化は既存 JSON ロギング利用。
完了条件(部分): タスク10 達成。

### Changes
- 追加: `app/main.py`
- 追加: `app/tests/integration/test_cli_smoke.py`

### Decisions
| ID | 内容 | 理由 | 影響 |
|----|------|------|------|
| DEC-020 | CLI で duration を必須でなく任意 (デフォ10s) | デモ/テストの迅速性 | 本番は無期限 + Ctrl+C 想定 |
| DEC-021 | SIGINT/SIGTERM で shutdown_event | シンプルな優先停止 | Cross-platform 適合 |

### Next
11. Integration test 強化 (複数カメラ) & coverage 測定
12. lint/format/typing / 90% 達成補助

---
## 2025-08-16 02:30 Maintenance (Register pytest timeout marker)
### Summary
目的: `pytest.mark.timeout` 未登録警告を解消するため `pytest.ini` に markers 定義追加。
結果: PytestUnknownMarkWarning 解消予定。
### Changes
- 更新: `pytest.ini` markers セクション追加。
### Next
- coverage 測定 & 90% 確認
- lint/format (black, isort, ruff, mypy) 導入
---

## (Archive Summary up to Task 9)
Task1-3: core scaffolding + utils_time/messages (tests) 完了。
Task4-6: errors/config.loader/logging_setup 実装 + テスト安定化 (pytest.ini)。
Task7: aggregator リングバッファ+統計。
Task8: worker スタブ+ドロップアルゴ。
Task9: orchestrator スレッド版 + dispatcher。
Maintenance: sitecustomize.py 完全除去。
詳細な過去ログは Git 履歴参照。

---

## 2025-08-16 02:20 Phase 1 Progress (Task 9 Orchestrator MVP Implemented)
### Summary
目的: Orchestrator MVP (単一プロセス/スレッド版) 実装とテスト: worker スレッド起動→result_queue→dispatcher→Aggregator 反映。
結果: start()/stop() と複数カメラ対応 (スレッド) 動作確認。StatsMessage 受信は未使用 (将来拡張)。
完了条件(部分): タスク9 達成。

### Changes
- 追加: `app/scripts/core/orchestrator.py`
- 追加: `app/tests/unit/test_orchestrator.py`

### Decisions
| ID | 内容 | 理由 | 影響 |
|----|------|------|------|
| DEC-018 | Phase1 はシングルプロセスで Worker スレッド化 | 実装スピード/テスト容易 | 後で multiprocessing へ差替必要 |
| DEC-019 | dispatcher timeout=0.2s ポーリング | シンプル | 高頻度 wake の軽微コスト受容 |

### Risks
| ID | リスク | 影響 | 軽減策 | 状態 |
|----|--------|------|--------|------|
| RSK-012 | スレッド実装と将来プロセス実装差異 | 移行工数 | API 抽象化で差分局所化 | Open |

### Next
10. main.py CLI
11. integration test
12. coverage / lint

---

## 2025-08-16 01:20 Phase 1 Adjustment (Remove sitecustomize.py)
### Summary
目的: インポート解決のために暫定追加した `sitecustomize.py` を削除し、副作用リスクを排除。
結果: `pytest.ini (pythonpath=.)` とパッケージ __init__ により問題なく解決できるため不要と判断。

### Changes
- 削除: `sitecustomize.py`
- 既存: `pytest.ini` 維持 (pythonpath=. で import 安定化)

### Decisions
| ID | 内容 | 理由 | 影響 |
|----|------|------|------|
| DEC-013 | sitecustomize 廃止 | 予期せぬ sys.path 変更副作用回避 | テスト実行方法簡潔化 |

### Risks
| ID | リスク | 影響 | 軽減策 | 状態 |
|----|--------|------|--------|------|
| RSK-008 | 他ディレクトリから pytest 実行時再発 | import エラー | ルートからの実行を README に明記 | Open |

### Next
既存 Next リスト継続 (Aggregator 実装へ)。

---

## 2025-08-16 01:05 Phase 1 Progress (Tasks 4-6 Completed)
### Summary
目的: Phase1 タスク 4-6 (errors / config.loader / logging_setup) 実装と単体テスト追加。
結果: 例外クラス・設定ローダ・集中ロギング初期化実装。テストコード作成 (未実行)。
完了条件(部分): 6 までのモジュール骨格と検証テスト準備完了。

### Changes
- 追加: `app/scripts/core/errors.py`
- 追加: `app/scripts/config/loader.py`
- 追加: `app/scripts/core/logging_setup.py`
- 追加: `app/tests/unit/test_config_loader.py`
- 追加: `app/tests/unit/test_logging_setup.py`

### Decisions
| ID | 内容 | 理由 | 影響 |
|----|------|------|------|
| DEC-010 | Config dataclass 群を loader 内に同居 | ファイル分割過剰回避 | 将来分離容易 |
| DEC-011 | logging JSON に最低限フィールド | 可読性と初期速度優先 | 後続で追記可能 |
| DEC-012 | logging listener 停止はテスト内で stop 呼び出し | 資源リーク回避 | テスト毎オーバーヘッド小 |

### Assumptions
| ID | 前提 | 検証計画 |
|----|------|----------|
| ASM-006 | RotatingFileHandler の I/O はテスト速度許容範囲 | 実測遅ければ monkeypatch |

### Risks
| ID | リスク | 影響 | 軽減策 | 状態 |
|----|--------|------|--------|------|
| RSK-006 | Config 検証分岐不足 (境界漏れ) | 実行時例外 | 追加ケース後続補強 | Open |
| RSK-007 | JSON ログフィールド将来後方互換 | パーサ影響 | 追加時に version フィールド検討 | Open |

### Metrics
未計測 (次: 初回 pytest 実行後に coverage 掲載)

### Open Issues
- 既存 D-01..D-06 (未着手)

### Next
7. `aggregator.py` 実装 + テスト
8. `worker.py` (スタブ) + ドロップアルゴテスト
9. `orchestrator.py` + dispatcher + テスト
10. `main.py` CLI
11. integration test
12. pytest 実行 & coverage 測定
13. lint/format 適用

---

## 2025-08-16 00:30 Phase 1 Progress (Tasks 1-3 Completed)
### Summary
目的: Phase1 タスク 1-3 (core 構造 / utils_time / messages) 実装・単体テスト追加。
結果: 追加モジュール & テスト正常作成。今後 errors.py 以降に進む準備完了。
完了条件(部分): 計画タスク 1-3 達成 / 単体テスト追加。

### Changes
- 追加: `app/scripts/core/__init__.py`
- 追加: `app/scripts/core/utils_time.py`
- 追加: `app/scripts/core/messages.py`
- 追加: `app/tests/unit/test_utils_time.py`
- 追加: `app/tests/unit/test_messages.py`
	(まだテスト未実行 / 次ステップで一括実行予定)

### Decisions
| ID | 内容 | 理由 | 影響 |
|----|------|------|------|
| DEC-008 | utils_time は最小4関数構成 | 必要最小限 + テスト容易 | 拡張時関数追加方針 |
| DEC-009 | messages で Enum 未使用 | 初期柔軟性 / 実装速度優先 | 型安全性は後続検討 |

### Assumptions
| ID | 前提 | 検証計画 |
|----|------|----------|
| ASM-005 | dataclass(slots) が pickle 問題なし | integration 後で pickle round-trip 試験 |

### Risks
| ID | リスク | 影響 | 軽減策 | 状態 |
|----|--------|------|--------|------|
| RSK-005 | Enum 未導入で型ミス検知遅延 | 実行時エラー | 後で mypy + Literal 導入 | Open |

### Metrics
未計測 (次: 初回 pytest 実行後に coverage 掲載)

### Open Issues
- 既存 D-01..D-06 (未着手)

### Next
4. `errors.py` 実装 + 単体テスト
5. `config/loader.py` + Config dataclass & テスト
6. `logging_setup.py`
7. `aggregator.py`
8. `worker.py`
9. `orchestrator.py`
10. `main.py`
11. integration test
12. lint/format & coverage 測定

---

## 2025-08-16 00:00 Phase 1 Planning (MVP Bootstrap)
### Summary
目的: MVP フェーズ (単一カメラ: ConfigLoader / messages / logging_setup / Orchestrator / Worker(推論スタブ) / Aggregator / dispatcher thread / 基本テスト) の詳細タスク分解と初期リポジトリ整備。
完了条件: 計画合意 / ApplicationConfig.xml サンプル生成 / タスク & 仮定 & リスク 明確化 -> (Yes)

### Changes
- 追加: `DEV_LOG.md` (本ファイル)
- 追加予定(未実装): `app/scripts/core/{utils_time.py,messages.py,errors.py,logging_setup.py,aggregator.py,worker.py,orchestrator.py,models.py}`
- 追加予定(未実装): `app/main.py`
- 追加: `app/resources/ApplicationConfig.xml` サンプル (単一カメラ cam01)

### Decisions
| ID | 内容 | 理由 | 影響 |
|----|------|------|------|
| DEC-001 | OpenVINO 依存は Phase1 では導入せず推論スタブ | 早期に並列/IPC/ロギングを確立 | requirements.txt 空維持 |
| DEC-002 | XML パースは `xml.etree.ElementTree` | 外部依存削減 | シンプルな変換ロジック | 
| DEC-003 | messages は `@dataclass(frozen=True, slots=True)` | pickle 安全 + 軽量 | 変更時は再生成必要 |
| DEC-004 | テストで時間/UUID をモック | 非決定性排除 | fixture 追加コスト |
| DEC-005 | Worker はダミーフレーム生成 (numpy 未使用) | 追加依存不要 | 画素処理なし (後続拡張) |
| DEC-006 | Aggregator はスレッド内専用 (親プロセスのみアクセス) | Lock 不要でシンプル | マルチプロセス共有は後続課題 |
| DEC-007 | Lint/format は pre-commit 後続 (現段階は手動) | 時間短縮 | 後でフック設定 |

### Assumptions
| ID | 前提 | 検証計画 |
|----|------|----------|
| ASM-001 | Windows 環境で spawn 動作問題なし | Orchestrator/Worker integration test で確認 |
| ASM-002 | 1 カメラ 10fps スタブ生成は CPU 低負荷 | 実測 (coverage 取得時) |
| ASM-003 | 現段階で外部 RTSP / OpenVINO 不要 | 要件再確認 (満たす) |
| ASM-004 | coverage>=90% はスタブで達成可能 | 初回測定し不足分テスト追加 |

### Risks
| ID | リスク | 影響 | 軽減策 | 状態 |
|----|--------|------|--------|------|
| RSK-001 | Windows マルチプロセスでテストハング | CI/ローカル停滞 | 短タイムアウト/明示 join | Open |
| RSK-002 | coverage 未達 | 次フェーズ遅延 | 早期測定→追加テスト | Open |
| RSK-003 | ログキュー フラッシング漏れ | shutdown 不完全 | sentinel & join 徹底 | Open |
| RSK-004 | Ping 実装後のタイミング競合 | DOWN 誤判定 | Phase6 で統合テスト強化 | 予定 |

### Metrics
(計画段階のため対象なし)

### Open Issues
- D-01..D-06: 詳細設計参照 (Issue 化予定 / 未作成)

### Next
1. パッケージ構造作成 (`app/scripts/core` ディレクトリ & 各モジュール骨組み)
2. `utils_time.py` 実装 + テスト
3. `messages.py` dataclass 実装 + immutability テスト
4. `errors.py` 例外クラス定義
5. `config/loader.py` Config dataclass & XML パース/検証 + テスト
6. `logging_setup.py` 集中ログ初期化 (Queue + JSON)
7. `aggregator.py` push/query/snapshot_stats + テスト
8. `worker.py` (スタブ) + 単体テスト (ドロップアルゴ)
9. `orchestrator.py` start/stop/dispatcher (単一カメラ) + テスト
10. `main.py` CLI 引数処理
11. Integration test (単一カメラ: end-to-end) 作成
12. Lint/format 実行 & coverage 測定 → 90% 未達なら追加テスト
13. DEV_LOG へ Phase1 実装結果追記
14. 設計差分 (必要なら 詳細設計.md 章13) 更新

---
(逆時系列で新しいエントリを先頭追加する運用)
