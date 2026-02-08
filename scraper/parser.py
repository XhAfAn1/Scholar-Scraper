from bs4 import BeautifulSoup
import re

class ScholarParser:
    def parse_html(self, html_content: str, source_keyword: str):
        """
        Extracts a list of paper dictionaries from raw HTML.
        """
        if not html_content:
            return []
            
        soup = BeautifulSoup(html_content, 'html.parser')
        papers = []
        
        # Google Scholar results are usually in div.gs_ri
        results = soup.select('.gs_ri')
        
        for item in results:
            try:
                # Extract Title
                title_tag = item.select_one('.gs_rt')
                title = title_tag.text.replace('[PDF]', '').replace('[HTML]', '').strip() if title_tag else "Unknown"
                
                # Extract Link
                link_tag = item.select_one('.gs_rt a')
                url = link_tag['href'] if link_tag else None
                
                # Extract Snippet (Abstract fragment)
                snippet_tag = item.select_one('.gs_rs')
                snippet = snippet_tag.text.strip() if snippet_tag else ""
                
                # Extract Year (Regex search in the green metadata line)
                meta_tag = item.select_one('.gs_a')
                meta_text = meta_tag.text if meta_tag else ""
                year_match = re.search(r'\b(19|20)\d{2}\b', meta_text)
                year = year_match.group(0) if year_match else "Unknown"

                if url: # Only save if we have a link
                    papers.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                        "keyword": source_keyword,
                        "year": year
                    })
            except Exception:
                continue
                
        return papers