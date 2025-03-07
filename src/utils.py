import logging

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

