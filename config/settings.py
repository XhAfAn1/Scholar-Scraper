import os

# --- AI CONFIG ---
# Use "llama3.2" for speed or "llama3.1" for better reasoning
MODEL_NAME = "llama3.1" 

# --- SCRAPER CONFIG ---
CONCURRENT_TABS = 2        # How many browser tabs to open at once (Keep low to avoid bans)
Global_TIMEOUT = 30000     # 30 seconds for page loads
Human_DELAY_MIN = 3        # Min seconds to wait between actions
Human_DELAY_MAX = 7        # Max seconds to wait

# --- DATABASE CONFIG ---
DB_NAME = "scholar_data.db"