import asyncio
import random
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from config.settings import Global_TIMEOUT, Human_DELAY_MIN, Human_DELAY_MAX

class StealthBrowser:
    async def fetch_scholar_results(self, query: str, page_num: int, search_prefs: dict, years: dict):
        """
        Fetches results using user preferences + Dynamic Year Range.
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
            
            # 1. Base Query
            params = f"?start={start_index}&q={query.replace(' ', '+')}"
            
            # 2. Sort By Date
            if search_prefs.get("sort_by") == "date":
                params += "&scisbd=1"
            
            # 3. Article Type (Review)
            if search_prefs.get("article_type") == "review":
                params += "&as_rr=1"
                
            # 4. Dynamic Year Filters (Passed from Main)
            if years.get("min"):
                params += f"&as_ylo={years['min']}"
            if years.get("max"):
                params += f"&as_yhi={years['max']}"
            
            final_url = base_url + params
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