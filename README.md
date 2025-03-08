主な機能

キー文字列の管理：

JSONファイルでキー文字列と関連情報を保存
キーの追加、削除、一覧表示機能


メール監視：

IMAP接続によるメールチェック
指定されたキー文字列を含むメールの検出
検出履歴の記録


定期チェック：

指定した間隔で自動的にメールをチェック
予想される頻度に基づく未着メールの検出



使用方法

設定：

初回実行時にconfig.jsonとkeys.jsonが自動生成されます
config.jsonにIMAPサーバー情報やチェック間隔を設定します


コマンド例：

---

# キー追加（キー文字列、説明、頻度を指定）
python email_monitor.py add "請求書" "月次請求書" "monthly"

# キー削除
python email_monitor.py remove "請求書"

# 手動チェック実行
python email_monitor.py check

# キー一覧表示
python email_monitor.py list

# 引数なしで実行すると定期チェックモードに
python email_monitor.py

---
## 構造化

py-mailchecker/
├── src/
│   ├── email_monitor/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── keys.py
│   │   ├── mail_check.py
│   │   └── scheduler.py
│   └── email_monitor.py
