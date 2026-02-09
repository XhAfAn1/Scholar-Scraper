import ollama
import json
from config.settings import MODEL_NAME, LLM_KEYWORD_LIMIT
from rich import print as rprint

class ResearchBrain:
    def generate_search_plan(self, topic: str) -> list:
        rprint(f"[magenta]Consulting {MODEL_NAME} for strategy...[/magenta]")
        
        prompt = f"""
        Act as a Research Librarian.
        Topic: "{topic}"
        
        Task: Generate exactly {LLM_KEYWORD_LIMIT} distinct Google Scholar search queries.
        Include a mix of broad concepts and specific technical terms.

        OUTPUT JSON FORMAT ONLY:
        {{
            "queries": ["query 1", "query 2", ...]
        }}
        """

        try:
            response = ollama.chat(model=MODEL_NAME, messages=[
                {'role': 'user', 'content': prompt}
            ], format='json')
            
            data = json.loads(response['message']['content'])
            return data.get('queries', [topic])
            
        except Exception as e:
            rprint(f"[red]LLM Error:[/red] {e}")
            return [topic]