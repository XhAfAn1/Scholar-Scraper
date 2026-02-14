# scraper/browser.py
import asyncio
import random
from urllib.parse import urlencode # <--- ADD THIS IMPORT
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from config.settings import Global_TIMEOUT, Human_DELAY_MIN, Human_DELAY_MAX

class StealthBrowser:
    async def fetch_scholar_results(self, query: str, page_num: int, search_prefs: dict, years: dict, advanced_params: dict = None):
        """
        Fetches results. Supports both Standard (LLM) and Advanced (Manual) modes.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False) 
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            await stealth_async(page) 
            
            # --- URL CONSTRUCTION ---
            base_url = "https://scholar.google.com/scholar"
            start_index = (page_num - 1) * 10
            
            # --- URL CONSTRUCTION ---
            if advanced_params:
                # MODE A: ADVANCED SEARCH (Manual Inputs)
                # Google Scholar Advanced Search Parameters
                params = {
                    "start": start_index,
                    "as_q": advanced_params.get("all_words", ""),       # All words
                    "as_epq": advanced_params.get("exact_phrase", ""),  # Exact phrase
                    "as_oq": advanced_params.get("at_least_one", ""),   # At least one
                    "as_eq": advanced_params.get("without_words", ""),  # Without
                    "as_occt": advanced_params.get("occurrence", "any"),# "any" or "title"
                    "as_sauthors": advanced_params.get("author", ""),   # Author
                    "as_publication": advanced_params.get("pub", ""),   # Publication
                    "as_ylo": advanced_params.get("date_low", ""),      # Year Low
                    "as_yhi": advanced_params.get("date_high", "")      # Year High
                }
                # Filter out empty keys to keep URL clean
                clean_params = {k: v for k, v in params.items() if v}
                final_url = f"{base_url}?{urlencode(clean_params)}"
                
            else:
                # MODE B: STANDARD SEARCH (LLM Keywords)
                params_str = f"?start={start_index}&q={query.replace(' ', '+')}"
                
                # Apply Preferences
                if search_prefs.get("sort_by") == "date": params_str += "&scisbd=1"
                if search_prefs.get("article_type") == "review": params_str += "&as_rr=1"
                
                # Apply Dynamic Years
                if years and years.get("min"): params_str += f"&as_ylo={years['min']}"
                if years and years.get("max"): params_str += f"&as_yhi={years['max']}"
                
                final_url = base_url + params_str
            # ------------------------

            try:
                await page.goto(final_url, timeout=Global_TIMEOUT)
                
                if "gs_captcha" in page.url or "sorry" in page.url:
                    print(f"⚠️ CAPTCHA detected for {query}! Waiting for manual solve...")
                    await page.wait_for_timeout(30000)
                
                # Wait for results to load
                await page.wait_for_selector('#gs_res_ccl_mid', timeout=10000)
                
                # Human jitter (scroll down a bit)
                await page.mouse.wheel(0, random.randint(300, 700))
                await asyncio.sleep(random.uniform(Human_DELAY_MIN, Human_DELAY_MAX))
                
                content = await page.content()
                await browser.close()
                return content
                
            except Exception as e:
                print(f"Browser Error ({query}): {e}")
                await browser.close()
                return None