import asyncio
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from pyfiglet import Figlet
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
            
            # Extract basic info with defaults
            query_text = job.get('query', 'Advanced Search')
            page = job['page']
            years = job.get('years', {})
            adv_params = job.get('advanced_params', None) # <--- NEW PARAMETER
            
            progress.update(task_id, description=f"[cyan]{name}[/] scraping: {query_text} (Pg {page})")
            
            # Pass advanced_params to browser
            html = await self.browser.fetch_scholar_results(query_text, page, cfg.config, years, adv_params)
            
            # 2. Parse Data
            if html:
                # Use query text or "Advanced Search" as the label
                label = query_text if not adv_params else "Advanced Search"
                papers = self.parser.parse_html(html, label)
                
                # 3. Save to DB
                saved_count = 0
                for paper in papers:
                    if await self.db.save_paper(paper):
                        saved_count += 1
                
                console.print(f"   [green]✔ {name}[/] found {len(papers)} papers ({saved_count} new) on Pg {page}")
            else:
                console.print(f"   [red]✖ {name}[/] failed to fetch Pg {page}")
            
            queue.task_done()

    def advanced_search_input(self):
        """Collects exact Google Scholar Advanced Search parameters."""
        console.clear()
        console.rule("[bold magenta]ADVANCED SEARCH[/bold magenta]")
        console.print("[dim]Leave fields empty to skip them.[/dim]\n")
        
        params = {}
        
        console.print("[bold underline]Find articles:[/bold underline]")
        params['all_words'] = Prompt.ask("With [bold green]ALL[/bold green] of the words", default="")
        params['exact_phrase'] = Prompt.ask("With the [bold green]EXACT PHRASE[/bold green]", default="")
        params['at_least_one'] = Prompt.ask("With [bold green]AT LEAST ONE[/bold green] of the words", default="")
        params['without_words'] = Prompt.ask("[bold red]WITHOUT[/bold red] the words", default="")
        
        console.print("\n[bold underline]Where my words occur:[/bold underline]")
        loc_choice = Prompt.ask("Occurring in", choices=["anywhere", "title"], default="anywhere")
        params['occurrence'] = "any" if loc_choice == "anywhere" else "title"
        
        console.print("\n[bold underline]Filters:[/bold underline]")
        params['author'] = Prompt.ask("Return articles [bold blue]AUTHORED BY[/bold blue] (e.g. 'PJ Hayes')", default="")
        params['pub'] = Prompt.ask("Return articles [bold blue]PUBLISHED IN[/bold blue] (e.g. 'Nature')", default="")
        
        console.print("\n[bold underline]Date Range:[/bold underline]")
        params['date_low'] = Prompt.ask("Dated between [bold yellow]Start Year[/bold yellow]", default="")
        if params['date_low']:
            params['date_high'] = Prompt.ask("...and [bold yellow]End Year[/bold yellow]", default="")
        
        return params

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
           # --- ASCII ART BANNER ---
            f = Figlet(font='slant',width=200, justify='center')
            console.print(f.renderText('SCHOLAR SCRAPPER'), style="bold blue")
            console.rule("[bold white]v2.0 - Automated Scrapping Engine[/bold white]")
            # ------------------------
            console.print("\n[1] Standard Scrap (AI Topics)", style="bold green")
            console.print("[2] Advanced Search (Manual)", style="bold magenta")
            console.print("[3] Search Settings", style="bold blue")
            console.print("[4] Export as CSV", style="bold blue")
            console.print("[0] Exit", style="bold red")
            print("\n")
            
            choice = Prompt.ask("Select Option", choices=["1", "2", "3", "4", "0"], default="1")
            
            if choice == "0":
                console.print("[yellow]Goodbye![/yellow]")
                break

            # --- EXPORT ---
            if choice == "4":
                console.print("\n[bold green]Exporting Data...[/bold green]")
                # Call the export function from check_db.py
                try:
                    from check_db import export_to_csv
                    export_to_csv()
                except ImportError:
                    console.print("[red]Could not import 'export_to_csv' from check_db.py[/red]")
                
                Prompt.ask("\nPress Enter to return to menu...")
                continue
                
            # --- SETTINGS ---
            if choice == "3":
                self.settings_menu()
                continue
            
            # --- ADVANCED SEARCH ---
            if choice == "2":
                await self.db.init_db()
                adv_params = self.advanced_search_input()
                
                if not any(adv_params.values()):
                    console.print("[red]No parameters entered![/red]")
                    asyncio.sleep(1)
                    continue
                
                # Ask depth for advanced search
                pages = int(Prompt.ask("\nHow many pages to scrape?", default="3"))
                
                queue = asyncio.Queue()
                for i in range(1, pages + 1):
                    queue.put_nowait({
                        'query': 'Advanced Search', 
                        'page': i,
                        'years': {}, # Years handled inside params
                        'advanced_params': adv_params
                    })
                
                with Progress() as progress:
                    task_id = progress.add_task("[magenta]Precision Scrapping...[/]", total=queue.qsize())
                    workers = [
                        asyncio.create_task(self.worker(f"Worker-{i+1}", queue, progress, task_id))
                        for i in range(CONCURRENT_TABS)
                    ]
                    await queue.join()
                    for w in workers: w.cancel()
                
                total = await self.db.get_stats()
                console.rule(f"[bold green]Advanced Search Complete. Total DB: {total}[/bold green]")
                Prompt.ask("Press Enter...")
                continue
                
            # --- STANDARD AI SEARCH ---
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