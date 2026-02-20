import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)

logger = logging.getLogger("DarkoGram")

def get_logger():
    return logger
