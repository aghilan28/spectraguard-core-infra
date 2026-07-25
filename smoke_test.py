import sys
import os
import logging
import importlib.util
from dotenv import load_dotenv


def run_smoke_test():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("smoke_test")

    logger.info("Starting Python Environment Smoke Test...")
    logger.info(f"Python Version: {sys.version.split()[0]}")

    if not os.path.exists(".env.example"):
        logger.error(".env.example missing")
        sys.exit(1)

    load_dotenv(".env.example")
    logger.info("Environment variables loaded successfully.")

    # Use standard importlib to explicitly verify dependency presence without raising unused import warnings
    pytest_spec = importlib.util.find_spec("pytest")
    black_spec = importlib.util.find_spec("black")

    if pytest_spec is not None and black_spec is not None:
        logger.info("Core engineering dependencies verified.")
    else:
        logger.error("Dependency validation failed: pytest or black package missing.")
        sys.exit(1)

    logger.info("Smoke test PASSED. Engineering baseline operational.")
    sys.exit(0)


if __name__ == "__main__":
    run_smoke_test()
