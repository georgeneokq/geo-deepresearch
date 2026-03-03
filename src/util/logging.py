import os
import logging

def setup_logging():
    # Get the string and ensure it's uppercase
    level_str = os.getenv("LOGGING_LEVEL", "INFO").upper()
    
    # Fetch the valid mapping
    allowed_levels = logging.getLevelNamesMapping()

    # Validate and fallback if the user provided a typo
    if level_str not in allowed_levels:
        level_str = "INFO"

    logging.basicConfig(
        level=level_str, 
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
