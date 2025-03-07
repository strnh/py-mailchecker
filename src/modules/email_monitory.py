import imaplib
import email
from email.header import decode_header
import datetime
import logging
from typing import Dict

from config_manager import ConfigManager

logger = logging.getLogger("EmailMonitor")

class EmailMonitor:
    def __init__(self, config: ConfigManager):
        self.config_manager = config

    def check_emails(self) -> Dict:
        logger.info("メールチェックを開始")
        config = self.config_manager.config
        keys = self.config_manager.keys

        try:
            mail = imaplib.IMAP4_SSL(config["imap_server"])
            mail.login(config["email"], config["password"])
            mail.select(config["folder"])

            today = datetime.date.today()
            since_date = (today - datetime.timedelta(days=7)).strftime("%d-%b-%Y")
            _, data = mail.search(None, f'(SINCE {since_date})')

            results = {key: False for key in keys}

            for num in data[0].split():
                _, msg_data = mail.fetch(num, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                date_tuple = email.utils.parsedate_tz(msg['Date'])
                email_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple)) if date_tuple else datetime.datetime.now()

                subject, body = self._get_email_content(msg)

                search_text = subject + " " + body
                for key in keys:
                    if key in search_text:
                        keys[key]["last_received"] = email_date.isoformat()
                        keys[key]["history"].append({
                            "date": email_date.isoformat(),
                            "subject": subject
                        })
                        if len(keys[key]["history"]) > 10:
                            keys[key]["history"] = keys[key]["history"][-10:]
                        results[key] = True
                        logger.info(f"キー '{key}' を含むメールを検出: {subject}")

            mail.close()
            mail.logout()

            self.config_manager.save_keys()
            logger.info("メールチェック完了")
            return results

        except Exception as e:
            logger.error(f"メールチェック中にエラー: {e}")
            raise

    def _get_email_content(self, msg) -> (str, str):
        subject = msg['Subject']
        if subject:
            subject, encoding = decode_header(subject)[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or 'utf-8', errors='replace')

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body_bytes = part.get_payload(decode=True)
                    if body_bytes:
                        return subject, body_bytes.decode('utf-8', errors='replace')
        else:
            body_bytes = msg.get_payload(decode=True)
            if body_bytes:
                return subject, body_bytes.decode('utf-8', errors='replace')

        return subject, ""

    def check_missing_emails(self) -> Dict:
        missing = {}
        now = datetime.datetime.now()
        keys = self.config_manager.keys

        for key, data in keys.items():
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
        logger.info("定期チェックを開始")
        config = self.config_manager.config

        try:
            while True:
                self.check_emails()
                missing = self.check_missing_emails()

                if missing:
                    logger.warning(f"未着メール検出: {missing}")
                    # 通知処理などをここに追加

                logger.info(f"{config['check_interval']}秒後に再チェックします")
                time.sleep(config["check_interval"])

        except KeyboardInterrupt:
            logger.info("ユーザーによって定期チェックが停止されました")
        except Exception as e:
            logger.error(f"定期チェック中にエラー: {e}")
            raise

