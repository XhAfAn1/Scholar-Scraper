import asyncio
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

from core.database import ResearchDatabase
from core.llm_brain import ResearchBrain
from core.config_manager import ConfigManager
from scraper.browser import StealthBrowser
from scraper.parser import ScholarParser
from config.settings import CONCURRENT_TABS, MAX_PAGES_PER_QUERY

console = Console()
cfg = ConfigManager()

class ScholarEngine:
    def __init__(self):
        self.db = ResearchDatabase()
        self.brain = ResearchBrain()
        self.browser = StealthBrowser()
        self.parser = ScholarParser()

    async def worker(self, name, queue, progress, task_id):
        """Async worker that pulls queries from queue."""
        while not queue.empty():
            job = await queue.get()
            query_text = job['query']
            page = job['page']
            years = job['years'] # Get years from job
            
            progress.update(task_id, description=f"[cyan]{name}[/] scraping: {query_text} (Pg {page})")
            
            # Pass user config AND the manual years to browser
            html = await self.browser.fetch_scholar_results(query_text, page, cfg.config, years)
            
            # 2. Parse Data
            if html:
                papers = self.parser.parse_html(html, query_text)
                
                # 3. Save to DB
                saved_count = 0
                for paper in papers:
                    if await self.db.save_paper(paper):
                        saved_count += 1
                
                console.print(f"   [green]✔ {name}[/] found {len(papers)} papers ({saved_count} new) on Pg {page}")
            else:
                console.print(f"   [red]✖ {name}[/] failed to fetch Pg {page}")
            
            queue.task_done()

    def settings_menu(self):
        """Interactive Settings Menu"""
        while True:
            console.clear()
            console.rule("[bold cyan]SEARCH PREFERENCES[/bold cyan]")
            
            table = Table(show_header=False, box=None)
            table.add_row("1. Sort By", f"[yellow]{cfg.get('sort_by')}[/yellow]")
            table.add_row("2. Article Type", f"[yellow]{cfg.get('article_type')}[/yellow]")
            
            console.print(Panel(table, title="Current Configuration"))
            console.print("[dim]Note: 'Sort By Date' may reduce relevance.[/dim]\n")
            
            choice = Prompt.ask("Select Option", choices=["1", "2", "0"], default="0")
            
            if choice == "0": break
            elif choice == "1":
                cfg.set("sort_by", Prompt.ask("Sort Order", choices=["relevance", "date"], default="relevance"))
            elif choice == "2":
                cfg.set("article_type", Prompt.ask("Type", choices=["any", "review"], default="any"))

    async def run(self):
        while True:
            console.clear()
            console.rule("[bold cyan]SCHOLAR SCRAPPER v1.1[/bold cyan]")
            
            console.print("\n[1]  Start New Scrap", style="bold green")
            console.print("[2]  Search Settings", style="bold blue")
            console.print("[3]  Exit", style="bold red")
            print("\n")
            
            choice = Prompt.ask("Select Option", choices=["1", "2", "3"])
            
            if choice == "3":
                console.print("[yellow]Goodbye![/yellow]")
                break
                
            if choice == "2":
                self.settings_menu()
                continue
                
            if choice == "1":
                await self.db.init_db()
                topic = Prompt.ask("\n[bold green]Enter Research Topic[/bold green]")
                
                # 1. Generate Plan First
                queries = self.brain.generate_search_plan(topic)
                
                # Show the Keywords
                table = Table(title="Generated Keywords")
                table.add_column("Query", style="magenta")
                for q in queries: table.add_row(q)
                console.print(table)
                
                # 2. ASK FOR DATE HERE
                console.print("\n[bold yellow]Time Filter[/bold yellow]")
                min_y = Prompt.ask("Start Year (e.g. 2020) [Leave empty for ALL]", default="")
                max_y = ""
                if min_y:
                    max_y = Prompt.ask("End Year [Leave empty for NOW]", default="")
                
                year_data = {"min": min_y, "max": max_y}

                if Prompt.ask("\nProceed with these settings?", choices=["y", "n"], default="y") == "n":
                    continue

                # Fill Queue based on MAX_PAGES_PER_QUERY
                queue = asyncio.Queue()
                for q in queries:
                    for i in range(1, MAX_PAGES_PER_QUERY + 1):
                        # Pass the year_data into every job
                        queue.put_nowait({'query': q, 'page': i, 'years': year_data})

                # Launch Workers
                with Progress() as progress:
                    task_id = progress.add_task("[green]Scrapping...[/]", total=queue.qsize())
                    workers = [
                        asyncio.create_task(self.worker(f"Worker-{i+1}", queue, progress, task_id))
                        for i in range(CONCURRENT_TABS)
                    ]
                    await queue.join()
                    for w in workers: w.cancel()

                total_papers = await self.db.get_stats()
                console.rule(f"[bold green]Scrapping Complete. Total Papers: {total_papers}[/bold green]")
                Prompt.ask("\nPress Enter to return to menu...")

if __name__ == "__main__":
    try:
        asyncio.run(ScholarEngine().run())
    except KeyboardInterrupt:
        print("\nExiting...")