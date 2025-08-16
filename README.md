# Hand Gesture Multi-Cam Analyzer

本リポジトリは複数RTSPカメラ映像をOpenVINOで推論しGUI表示・録画・結果エクスポートを行うオフライン解析アプリケーションの設計/実装プロジェクトです。

## ディレクトリ構成 (現行計画)
```
app/
  main.py                  # エントリーポイント
  scripts/
    config/                # 設定ロード/検証
    core/                  # Orchestrator / Workers / Aggregator / Recorder / モデル/例外
    gui/                   # GUI Adapter / (GUI実装後続)
  tools/
    convert_model.py       # PyTorch→OpenVINO IR 変換ツール (予定)
  logs/                    # 実行時ログ (起動時に生成)
  results/                 # 推論結果エクスポート・録画成果物
  models/                  # OpenVINO IR (xml, bin) とメタデータ
  resources/
    ApplicationConfig.xml  # 全設定集約 (env 禁止)
```

## 参照ドキュメント
- `要件.md` : 機能/非機能/制約
- `基本設計.md` : コンポーネント・アーキ概要
- `詳細設計.md` : クラス/関数レベル仕様
- `.github/prompts/CODING_STYLE.md` : コーディング & AI プロンプト規約
- `.github/prompts/STANDARD_DEVELOPMENT_FLOW.md` : 標準開発フロー

## セットアップ (初期案)
1. Python 3.11 仮想環境を作成
2. requirements.txt / requirements-dev.txt をインストール
3. `app/resources/ApplicationConfig.xml` を環境に合わせ編集
4. (必要なら) `app/tools/convert_model.py` でモデルを IR 変換し `app/models/` へ配置
5. 実行: `python -m app.main`

## ログ
- 既定出力ディレクトリ: `app/logs`
- 異常終了: `app/logs/crash_<timestamp>.log`

## ライセンス / 注意
現時点ドラフト。外部配布前にライセンス整理予定。

---
(以上)
