# Scholar Scrapper 

A local research tool that automates Google Scholar scraping. It uses **Ollama (Llama 3)** to generate search strategies and **Playwright** to harvest papers without getting blocked.

### Key Features
- **Local AI:** Uses Llama 3.1 to generate synonyms and boolean logic (no API keys).
- **Stealth Scraping:** Runs a headless Chromium browser with `playwright-stealth` to bypass bot detection.
- **Async:** Scrapes multiple search pages in parallel.
- **SQLite Storage:** Automatically saves unique papers to `scholar_data.db`.

### Requirements
- **Python 3.12** (Strict requirement for `greenlet` compatibility).
- **Ollama** installed and running (`ollama serve`).

### Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
playwright install chromium
```
2. **Pull the AI Model**

  ```Bash
  ollama pull llama3.1
  ```
(Note: You can switch to llama3.2 in config/settings.py for faster, lower-memory performance)
Usage
Make sure Ollama is running.

3. **Run the engine:**

  ```Bash
  python main.py
  ```
Enter your topic. The tool will plan the search, scrape Page 1 & 2 for each query, and save results to the database.
```bash
Project Structure
Plaintext
scholar_engine/
├── config/       # Settings & Model selection
├── core/         # Database & LLM logic
├── scraper/      # Playwright browser & HTML parsing
└── main.py       # Entry point
```
Disclaimer
For educational purposes only. Respect Google Scholar's rate limits to avoid IP bans.
