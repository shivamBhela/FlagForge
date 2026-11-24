import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("flagforge-worker")

def main():
    logger.info("FlagForge Background Worker started. Listening for release evaluations & scan jobs...")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Worker shutting down cleanly.")

if __name__ == "__main__":
    main()
