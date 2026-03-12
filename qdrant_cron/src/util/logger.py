import os
import logging

default_logger_name = "qdrant_cron"
default_logger = logging.getLogger(default_logger_name)

def setup_logging(app_name=default_logger_name):
    # Get the desired level for specified app
    level_str = os.getenv("LOGGING_LEVEL", "INFO").upper()
    allowed_levels = logging.getLevelNamesMapping()
    
    if level_str not in allowed_levels:
        level_str = "INFO"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True
    )

    # Explicitly set your application's logger level
    # This ensures only loggers starting with 'app_name' use the env var level
    app_logger = logging.getLogger(app_name)
    app_logger.setLevel(level_str)
    
    return app_logger

def get_logger(logger_name=default_logger_name):
    if logger_name == default_logger_name:
        return default_logger
    return logging.getLogger(logger_name)
