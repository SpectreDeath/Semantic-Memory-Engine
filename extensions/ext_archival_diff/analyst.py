from bs4 import BeautifulSoup
import difflib
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("LawnmowerMan.ArchivalDiff.Analyst")

class ForensicAnalyst:
    """
    Strips boilerplate and performs semantic diffs on HTML snapshots.
    """
    
    BOILERPLATE_TAGS = ['nav', 'footer', 'script', 'style', 'header', 'aside', 'iframe', 'noscript']
    BOILERPLATE_CLASSES_IDS = ['navbar', 'footer', 'sidebar', 'menu', 'ad', 'cookie', 'banner']

    def strip_boilerplate(self, html: str) -> str:
        """
        Removes navigation, footers, and scripts to reveal core content.
        """
        if not html:
            return ""
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove tags
        for tag in soup.find_all(self.BOILERPLATE_TAGS):
            tag.decompose()
            
        # Remove common boilerplate classes/ids
        for element in soup.find_all(True):
            attrs = element.attrs
            for attr in ['id', 'class']:
                if attr in attrs:
                    val = str(attrs[attr]).lower()
                    if any(target in val for target in self.BOILERPLATE_CLASSES_IDS):
                        element.decompose()
                        break
        
        # Extract text blocks (paragraphs, headers, list items)
        content_blocks = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
            text = tag.get_text(strip=True)
            if not text:
                continue
            
            # Keep headers regardless of length (headers are short but critical),
            # but filter very short paragraphs/list fragments
            if tag.name.startswith('h') or len(text) > 20: 
                content_blocks.append(text)
                
        return "\n\n".join(content_blocks)

    def semantic_diff(self, old_html: str, new_html: str) -> Dict[str, Any]:
        """
        Compares two HTML snapshots and detects added/deleted paragraphs.
        """
        old_text = self.strip_boilerplate(old_html)
        new_text = self.strip_boilerplate(new_html)
        
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()
        
        added = []
        deleted = []
        
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                deleted.extend([line for line in old_lines[i1:i2] if line.strip()])
                added.extend([line for line in new_lines[j1:j2] if line.strip()])
            elif tag == 'delete':
                deleted.extend([line for line in old_lines[i1:i2] if line.strip()])
            elif tag == 'insert':
                added.extend([line for line in new_lines[j1:j2] if line.strip()])
                
        return {
            "added_content": added,
            "deleted_content": deleted,
            "summary": {
                "total_added": len(added),
                "total_deleted": len(deleted)
            }
        }
