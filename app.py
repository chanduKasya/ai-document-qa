from pathlib import Path
import sys
import os

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"

print("project setup check")
print("-------------------")
print(f"python version: {sys.version.split()[0]}")
print(f"project root: {PROJECT_ROOT}")
print(f"env file: {ENV_FILE.exists()}")

if not ENV_FILE.exists():
    raise FileNotFoundError(
        "Missing .env file. Create it in the project root."
        )
   

print("Milestone 1 setup check passed.")