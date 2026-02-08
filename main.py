import asyncio
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import Progress

from core.database import ResearchDatabase
from core.llm_brain import ResearchBrain
from scraper.browser import StealthBrowser
from scraper.parser import ScholarParser
from config.settings import CONCURRENT_TABS

console = Console()

class ScholarEngine:
    def __init__(self):
        self.db = ResearchDatabase()
        self.brain = ResearchBrain()
        self.browser = StealthBrowser()
        self.parser = ScholarParser()

    async def worker(self, name, queue, progress, task_id):
        """Async worker that pulls queries from queue and processes them."""
        while not queue.empty():
            query_item = await queue.get()
            query_text = query_item['query']
            page = query_item['page']
            
            # Update progress
            progress.update(task_id, description=f"[cyan]{name}[/] scraping: {query_text} (Pg {page})")
            
            # 1. Fetch HTML
            html = await self.browser.fetch_scholar_results(query_text, page)
            
            # 2. Parse Data
            if html:
                papers = self.parser.parse_html(html, query_text)
                
                # 3. Save to DB
                saved_count = 0
                for paper in papers:
                    if await self.db.save_paper(paper):
                        saved_count += 1
                
                console.print(f"   [green]✔ {name}[/] found {len(papers)} papers ({saved_count} new) for '{query_text}'")
            else:
                console.print(f"   [red]✖ {name}[/] failed to fetch '{query_text}'")
            
            queue.task_done()

    async def run(self):
        console.clear()
        console.rule("[bold cyan]SCHOLAR ENGINE v3.0 (Async/Stealth)[/bold cyan]")
        
        # 1. Initialize DB
        await self.db.init_db()
        
        # 2. Get Topic
        topic = Prompt.ask("\n[bold green]Enter Research Topic[/bold green]")
        
        # 3. Generate Plan
        queries = self.brain.generate_search_plan(topic)
        
        # Show Plan
        table = Table(title="Search Strategy")
        table.add_column("Query", style="magenta")
        for q in queries:
            table.add_row(q)
        console.print(table)
        
        if Prompt.ask("\nProceed with scraping?", choices=["y", "n"]) == "n":
            return

        # 4. Fill Queue (Page 1 and 2 for each query)
        queue = asyncio.Queue()
        for q in queries:
            queue.put_nowait({'query': q, 'page': 1})
            queue.put_nowait({'query': q, 'page': 2})

        # 5. Launch Workers
        total_tasks = queue.qsize()
        with Progress() as progress:
            task_id = progress.add_task("[green]Processing...[/]", total=total_tasks)
            
            # Create workers based on CONCURRENT_TABS setting
            workers = []
            for i in range(CONCURRENT_TABS):
                w = asyncio.create_task(self.worker(f"Worker-{i+1}", queue, progress, task_id))
                workers.append(w)
            
            # Wait for queue to empty
            await queue.join()
            
            # Cancel workers
            for w in workers:
                w.cancel()

        # 6. Final Report
        total_papers = await self.db.get_stats()
        console.rule(f"[bold green]Mission Complete. Total Papers in DB: {total_papers}[/bold green]")
        console.print(f"[dim]Data saved to {self.db.db_path}[/dim]")

if __name__ == "__main__":
    asyncio.run(ScholarEngine().run())