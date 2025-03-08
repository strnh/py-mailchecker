import logging
from email_monitor.config import load_config
from email_monitor.keys import load_keys, save_keys
from email_monitor.mail_check import check_emails
from email_monitor.scheduler import run_scheduled_check

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
        self.config_path = config_path
        self.keys_path = keys_path
        self.config = load_config(config_path)
        self.keys = load_keys(keys_path)
        self.last_check = {}

    def add_key(self, key: str, description: Optional[str] = None, expected_frequency: Optional[str] = None) -> None:
        if key in self.keys:
            logger.warning(f"キー '{key}' は既に存在します。上書きします。")

        self.keys[key] = {
            "description": description or "",
            "expected_frequency": expected_frequency or "daily",
            "last_received": None,
            "history": []
        }
        save_keys(self.keys_path, self.keys)
        logger.info(f"キー '{key}' を追加しました")

    def remove_key(self, key: str) -> bool:
        if key in self.keys:
            del self.keys[key]
            save_keys(self.keys_path, self.keys)
            logger.info(f"キー '{key}' を削除しました")
            return True
        logger.warning(f"キー '{key}' は存在しません")
        return False

    def list_keys(self) -> Dict:
        return self.keys

    def check_emails(self) -> Dict:
        results = check_emails(self.config, self.keys)
        save_keys(self.keys_path, self.keys)
        return results

    def check_missing_emails(self) -> Dict:
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
        run_scheduled_check(self.config, self.keys_path)

if __name__ == "__main__":
    monitor = EmailMonitor()

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
        monitor.run_scheduled_check()

