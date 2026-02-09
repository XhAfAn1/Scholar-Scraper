import os

# --- AI CONFIG ---
MODEL_NAME = "llama3.1" 
LLM_KEYWORD_LIMIT = 6      # <--- How many keywords the AI should generate
MAX_PAGES_PER_QUERY = 2    # <--- How many pages to scrape per keyword (1 page = 10 results)

# --- SCRAPER CONFIG ---
CONCURRENT_TABS = 2        # How many browser tabs to open at once
Global_TIMEOUT = 30000     # 30 seconds for page loads
Human_DELAY_MIN = 2        # Min seconds to wait between actions
Human_DELAY_MAX = 5        # Max seconds to wait

# --- DATABASE CONFIG ---
DB_NAME = "scholar_data.db"