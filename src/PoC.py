import json
import imaplib
import email
from email.header import decode_header
import datetime
import time
import os
import logging
from typing import Dict, List, Optional

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("email_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EmailMonitor")

class EmailMonitor:
    def __init__(self, config_path: str = "config.json", keys_path: str = "keys.json"):
        """
        メール監視ツールの初期化
        
        Args:
            config_path: 設定ファイルのパス
            keys_path: キー文字列保存用ファイルのパス
        """
        self.config_path = config_path
        self.keys_path = keys_path
        self.config = self._load_config()
        self.keys = self._load_keys()
        self.last_check = {}
        
    def _load_config(self) -> Dict:
        """設定ファイルを読み込む"""
        if not os.path.exists(self.config_path):
            # デフォルト設定を作成
            default_config = {
                "imap_server": "imap.example.com",
                "email": "your_email@example.com",
                "password": "your_password",
                "check_interval": 3600,  # 1時間ごとに確認（秒）
                "folder": "INBOX"
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            logger.info(f"デフォルト設定ファイルを作成しました: {self.config_path}")
            return default_config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("設定を読み込みました")
            return config
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗: {e}")
            raise
        
    def _load_keys(self) -> Dict:
        """キー文字列データを読み込む"""
        if not os.path.exists(self.keys_path):
            # 空のキーファイルを作成
            empty_keys = {}
            with open(self.keys_path, 'w', encoding='utf-8') as f:
                json.dump(empty_keys, f, indent=4)
            logger.info(f"空のキーファイルを作成しました: {self.keys_path}")
            return empty_keys
        
        try:
            with open(self.keys_path, 'r', encoding='utf-8') as f:
                keys = json.load(f)
            logger.info(f"{len(keys)} 個のキーを読み込みました")
            return keys
        except Exception as e:
            logger.error(f"キーファイルの読み込みに失敗: {e}")
            raise
    
    def _save_keys(self) -> None:
        """キー文字列データを保存する"""
        try:
            with open(self.keys_path, 'w', encoding='utf-8') as f:
                json.dump(self.keys, f, indent=4, ensure_ascii=False)
            logger.info("キーデータを保存しました")
        except Exception as e:
            logger.error(f"キーデータの保存に失敗: {e}")
            raise
    
    def add_key(self, key: str, description: Optional[str] = None, expected_frequency: Optional[str] = None) -> None:
        """
        監視するキー文字列を追加
        
        Args:
            key: 監視するキー文字列
            description: キーの説明
            expected_frequency: 予想される頻度 ("daily", "weekly", "monthly" など)
        """
        if key in self.keys:
            logger.warning(f"キー '{key}' は既に存在します。上書きします。")
        
        self.keys[key] = {
            "description": description or "",
            "expected_frequency": expected_frequency or "daily",
            "last_received": None,
            "history": []
        }
        self._save_keys()
        logger.info(f"キー '{key}' を追加しました")
    
    def remove_key(self, key: str) -> bool:
        """キー文字列を削除"""
        if key in self.keys:
            del self.keys[key]
            self._save_keys()
            logger.info(f"キー '{key}' を削除しました")
            return True
        logger.warning(f"キー '{key}' は存在しません")
        return False
    
    def list_keys(self) -> Dict:
        """すべてのキー文字列と状態を表示"""
        return self.keys
    
    def check_emails(self) -> Dict:
        """メールをチェックし、キーが含まれるメールを記録"""
        logger.info("メールチェックを開始")
        
        try:
            # IMAPサーバーに接続
            mail = imaplib.IMAP4_SSL(self.config["imap_server"])
            mail.login(self.config["email"], self.config["password"])
            mail.select(self.config["folder"])
            
            # 前回のチェック以降のメールを検索
            today = datetime.date.today()
            since_date = (today - datetime.timedelta(days=7)).strftime("%d-%b-%Y")
            _, data = mail.search(None, f'(SINCE {since_date})')
            
            results = {}
            for key in self.keys:
                results[key] = False
                
            # メール本文をスキャン
            for num in data[0].split():
                _, msg_data = mail.fetch(num, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # 日付を取得
                date_tuple = email.utils.parsedate_tz(msg['Date'])
                if date_tuple:
                    email_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                else:
                    email_date = datetime.datetime.now()
                
                # 件名を取得
                subject = ""
                if msg['Subject']:
                    subject, encoding = decode_header(msg['Subject'])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or 'utf-8', errors='replace')
                
                # 本文を取得
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        
                        if "attachment" not in content_disposition:
                            if content_type == "text/plain":
                                body_bytes = part.get_payload(decode=True)
                                if body_bytes:
                                    body = body_bytes.decode('utf-8', errors='replace')
                                    break
                else:
                    body_bytes = msg.get_payload(decode=True)
                    if body_bytes:
                        body = body_bytes.decode('utf-8', errors='replace')
                
                # 件名と本文でキーワードを探す
                search_text = subject + " " + body
                for key in self.keys:
                    if key in search_text:
                        # キーが見つかった場合、データを更新
                        self.keys[key]["last_received"] = email_date.isoformat()
                        
                        # 履歴に追加
                        self.keys[key]["history"].append({
                            "date": email_date.isoformat(),
                            "subject": subject
                        })
                        
                        # 最新の10件だけ保持
                        if len(self.keys[key]["history"]) > 10:
                            self.keys[key]["history"] = self.keys[key]["history"][-10:]
                        
                        results[key] = True
                        logger.info(f"キー '{key}' を含むメールを検出: {subject}")
            
            mail.close()
            mail.logout()
            
            self._save_keys()
            logger.info("メールチェック完了")
            return results
            
        except Exception as e:
            logger.error(f"メールチェック中にエラー: {e}")
            raise
    
    def check_missing_emails(self) -> Dict:
        """未着のメールを確認"""
        missing = {}
        now = datetime.datetime.now()
        
        for key, data in self.keys.items():
            if not data["last_received"]:
                missing[key] = "未受信"
                continue
                
            last_received = datetime.datetime.fromisoformat(data["last_received"])
            days_since_last = (now - last_received).days
            
            if data["expected_frequency"] == "daily" and days_since_last > 1:
                missing[key] = f"{days_since_last}日間未受信"
            elif data["expected_frequency"] == "weekly" and days_since_last > 7:
                missing[key] = f"{days_since_last}日間未受信"
            elif data["expected_frequency"] == "monthly" and days_since_last > 30:
                missing[key] = f"{days_since_last}日間未受信"
                
        return missing
    
    def run_scheduled_check(self):
        """定期的にメールをチェック"""
        logger.info("定期チェックを開始")
        
        try:
            while True:
                self.check_emails()
                missing = self.check_missing_emails()
                
                if missing:
                    logger.warning(f"未着メール検出: {missing}")
                    # ここで通知を送るなどの処理を追加できます
                
                # 次のチェックまで待機
                logger.info(f"{self.config['check_interval']}秒後に再チェックします")
                time.sleep(self.config["check_interval"])
                
        except KeyboardInterrupt:
            logger.info("ユーザーによって定期チェックが停止されました")
        except Exception as e:
            logger.error(f"定期チェック中にエラー: {e}")
            raise

# 使用例
if __name__ == "__main__":
    monitor = EmailMonitor()
    
    # コマンドライン引数に基づいて動作を変更することも可能
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "add" and len(sys.argv) >= 3:
            description = sys.argv[3] if len(sys.argv) > 3 else None
            frequency = sys.argv[4] if len(sys.argv) > 4 else "daily"
            monitor.add_key(sys.argv[2], description, frequency)
        elif sys.argv[1] == "remove" and len(sys.argv) >= 3:
            monitor.remove_key(sys.argv[2])
        elif sys.argv[1] == "check":
            results = monitor.check_emails()
            missing = monitor.check_missing_emails()
            print(f"チェック結果: {results}")
            print(f"未着メール: {missing}")
        elif sys.argv[1] == "list":
            keys = monitor.list_keys()
            for key, data in keys.items():
                print(f"キー: {key}")
                print(f"  説明: {data['description']}")
                print(f"  予想頻度: {data['expected_frequency']}")
                print(f"  最終受信: {data['last_received'] or '未受信'}")
                print("")
        else:
            print("使用法: python email_monitor.py [add <key> [description] [frequency]|remove <key>|check|list]")
    else:
        # 引数がない場合は定期チェックを開始
        monitor.run_scheduled_check()
