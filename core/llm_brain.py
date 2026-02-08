import ollama
import json
from config.settings import MODEL_NAME
from rich import print as rprint

class ResearchBrain:
    def generate_search_plan(self, topic: str) -> list:
        """
        Uses Local LLM to break the topic into distinct search queries.
        Returns a list of strings.
        """
        rprint(f"[magenta]🧠 Consulting {MODEL_NAME} for strategy...[/magenta]")
        
        prompt = f"""
        Act as a Senior Research Librarian.
        Topic: "{topic}"
        
        Task: Generate 6 distinct Google Scholar search queries to cover this topic comprehensively.
        Include:
        1. 2 Broad queries (core concepts).
        2. 2 Specific/Technical queries (methodologies, specific algorithms).
        3. 2 Related field queries.

        OUTPUT JSON FORMAT ONLY:
        {{
            "queries": ["query 1", "query 2", "query 3", ...]
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
            return [topic] # Fallback