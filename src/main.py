import sys
from config_manager import ConfigManager
from email_monitor import EmailMonitor

def main():
    config_manager = ConfigManager()
    email_monitor = EmailMonitor(config_manager)

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "add" and len(sys.argv) >= 3:
            description = sys.argv[3] if len(sys.argv) > 3 else None
            frequency = sys.argv[4] if len(sys.argv) > 4 else "daily"
            config_manager.add_key(sys.argv[2], description, frequency)
        elif command == "remove" and len(sys.argv) >= 3:
            config_manager.remove_key(sys.argv[2])
        elif command == "check":
            results = email_monitor.check_emails()
            missing = email_monitor.check_missing_emails()
            print(f"チェック結果: {results}")
            print(f"未着メール: {missing}")
        elif command == "list":
            keys = config_manager.list_keys()
            for key, data in keys.items():
                print(f"キー: {key}")
                print(f"  説明: {data['description']}")
                print(f"  予想頻度: {data['expected_frequency']}")
                print(f"  最終受信: {data['last_received'] or '未受信'}")
                print("")
        else:
            print("使用法: python main.py [add <key> [description] [frequency]|remove <key>|check|list]")
    else:
        email_monitor.run_scheduled_check()

if __name__ == "__main__":
    main()

