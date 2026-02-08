import aiosqlite
from config.settings import DB_NAME
from rich import print as rprint

class ResearchDatabase:
    def __init__(self):
        self.db_path = DB_NAME

    async def init_db(self):
        """Creates the tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE,
                    snippet TEXT,
                    keyword_source TEXT,
                    year TEXT,
                    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()

    async def save_paper(self, paper_data: dict):
        """Saves a single paper, ignoring duplicates (based on URL)."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("""
                    INSERT OR IGNORE INTO papers (title, url, snippet, keyword_source, year)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    paper_data['title'],
                    paper_data['url'],
                    paper_data['snippet'],
                    paper_data['keyword'],
                    paper_data['year']
                ))
                await db.commit()
                return True
            except Exception as e:
                rprint(f"[red]DB Error:[/red] {e}")
                return False

    async def get_stats(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM papers") as cursor:
                count = await cursor.fetchone()
                return count[0]