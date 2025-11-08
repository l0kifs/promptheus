#!/usr/bin/env python3
"""Manual test script for logging configuration."""

import os
import json
from pathlib import Path
from loguru import logger

# Set environment
os.environ["ENVIRONMENT"] = "development"

from src.promptheus.main import configure_logging

# Configure logging
configure_logging()

# Test logging
logger.info("Test info message in development", user_id=123, action="login")
logger.debug("Test debug message in development", lesson_id=456)
logger.warning("Test warning message in development")

# Check the log file
log_file = Path("logs/promptheus_$(date +%Y-%m-%d).log")
if log_file.exists():
    print(f"
Log file contents ({log_file}):")
    with open(log_file, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                print(f"Level: {entry["record"]["level"]["name"]}")
                print(f"Message: {entry["record"]["message"]}")
                print(f"Extra: {entry["record"]["extra"]}")
                print("---")
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {line.strip()} - {e}")
else:
    print(f"Log file {log_file} does not exist")
