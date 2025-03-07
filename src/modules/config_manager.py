import json
import os
import logging
from typing import Dict

logger = logging.getLogger("ConfigManager")

class ConfigManager:
    def __init__(self, config_path: str = "config.json", keys_path: str = "keys.json"):
        self.config_path = config_path
        self.keys_path = keys_path
        self.config = self._load_config()
        self.keys = self._load_keys()

    def _load_config(self) -> Dict:
        if not os.path.exists(self.config_path):
            default_config = {
                "imap_server": "imap.example.com",
                "email": "your_email@example.com",
                "password": "your_password",
                "check_interval": 3600,
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
        if not os.path.exists(self.keys_path):
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

    def save_keys(self) -> None:
        try:
            with open(self.keys_path, 'w', encoding='utf-8') as f:
                json.dump(self.keys, f, indent=4, ensure_ascii=False)
            logger.info("キーデータを保存しました")
        except Exception as e:
            logger.error(f"キーデータの保存に失敗: {e}")
            raise

    def add_key(self, key: str, description: Optional[str] = None, expected_frequency: Optional[str] = None) -> None:
        if key in self.keys:
            logger.warning(f"キー '{key}' は既に存在します。上書きします。")

        self.keys[key] = {
            "description": description or "",
            "expected_frequency": expected_frequency or "daily",
            "last_received": None,
            "history": []
        }
        self.save_keys()
        logger.info(f"キー '{key}' を追加しました")

    def remove_key(self, key: str) -> bool:
        if key in self.keys:
            del self.keys[key]
            self.save_keys()
            logger.info(f"キー '{key}' を削除しました")
            return True
        logger.warning(f"キー '{key}' は存在しません")
        return False

    def list_keys(self) -> Dict:
        return self.keys
