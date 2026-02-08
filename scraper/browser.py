import asyncio
import random
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from config.settings import Global_TIMEOUT, Human_DELAY_MIN, Human_DELAY_MAX

class StealthBrowser:
    async def fetch_scholar_results(self, query: str, page_num: int = 1):
        """
        Launches a stealth browser, searches Google Scholar, and returns HTML.
        """
        async with async_playwright() as p:
            # Launch typical browser
            browser = await p.chromium.launch(headless=False) # Headless=False helps avoid CAPTCHA
            
            # Create a context that mimics a real user
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            await stealth_async(page) # Apply stealth patches
            
            # Calculate start parameter (0 for pg1, 10 for pg2)
            start_index = (page_num - 1) * 10
            url = f"https://scholar.google.com/scholar?start={start_index}&q={query.replace(' ', '+')}"
            
            try:
                # Go to page
                await page.goto(url, timeout=Global_TIMEOUT)
                
                # Check for CAPTCHA
                if "gs_captcha" in page.url or "sorry" in page.url:
                    print(f"⚠️ CAPTCHA detected for {query}! Waiting for manual solve...")
                    await page.wait_for_timeout(30000) # Give user 30s to solve it
                
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