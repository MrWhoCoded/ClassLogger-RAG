import os
from pathlib import Path
from dotenv import load_dotenv

# Force Python to find the .env file relative to this script's location
script_dir = Path(__file__).resolve().parent
env_path = script_dir / '.env'
load_dotenv(dotenv_path=env_path)

# Retrieve variables
astra_key = os.getenv("ASTRADB_API_KEY")
astra_endpoint = os.getenv("ASTRADB_ENDPOINT")

if not astra_key or not astra_endpoint:
    raise ValueError("ASTRADB_API_KEY and ASTRADB_ENDPOINT must be set in .env file")
