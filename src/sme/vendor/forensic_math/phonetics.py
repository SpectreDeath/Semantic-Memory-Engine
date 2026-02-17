import re

class DoubleMetaphone:
    """
    Pure-Python implementation of the Double Metaphone phonetic algorithm.
    Optimized for memory with __slots__.
    """
    __slots__ = ('primary', 'secondary', 'original', 'length', 'last')

    def __init__(self, text: str):
        self.primary = ""
        self.secondary = ""
        self.original = text.upper().strip()
        self.length = len(self.original)
        self.last = self.length - 1
        self._calculate()

    def _calculate(self):
        """Simplified Double Metaphone logic for core phonetic hashing."""
        if not self.original:
            return

        # Replace non-alpha and handle common prefixes
        text = re.sub(r'[^A-Z]', '', self.original)
        if not text:
            return

        pos = 0
        # This is a highly truncated version for demonstration/forensic match
        # Real Double Metaphone is ~800 lines of rules. 
        # We implement the 'Forensic Minimal' variant.
        while len(self.primary) < 4 and pos < len(text):
            char = text[pos]
            
            if char in 'AEIOUY':
                if pos == 0:
                    self.primary += 'A'
                    self.secondary += 'A'
                pos += 1
            elif char == 'B':
                self.primary += 'P'
                self.secondary += 'P'
                pos = pos + 2 if (pos + 1 < len(text) and text[pos+1] == 'B') else pos + 1
            elif char == 'C':
                # Simplified C rules
                self.primary += 'K'
                self.secondary += 'K'
                pos += 1
            elif char == 'D':
                self.primary += 'T'
                self.secondary += 'T'
                pos += 1
            elif char == 'F':
                self.primary += 'F'
                self.secondary += 'F'
                pos += 1
            elif char == 'G':
                self.primary += 'K'
                self.secondary += 'K'
                pos += 1
            elif char == 'H':
                pos += 1
            elif char in 'JKLMNPQR':
                self.primary += char
                self.secondary += char
                pos += 1
            elif char == 'S':
                self.primary += 'S'
                self.secondary += 'S'
                pos += 1
            elif char == 'T':
                self.primary += 'T'
                self.secondary += 'T'
                pos += 1
            elif char == 'V':
                self.primary += 'F'
                self.secondary += 'F'
                pos += 1
            elif char == 'W':
                self.primary += 'W'
                self.secondary += 'W'
                pos += 1
            elif char == 'X':
                self.primary += 'KS'
                self.secondary += 'KS'
                pos += 1
            elif char == 'Z':
                self.primary += 'S'
                self.secondary += 'S'
                pos += 1
            else:
                pos += 1

def calculate_phonetic_hash(word: str) -> dict:
    """
    Calculates the Double Metaphone phonetic hash for a word.
    Useful for identifying same-sounding names or handles in aliases.
    """
    dm = DoubleMetaphone(word)
    return {
        "primary": dm.primary,
        "secondary": dm.secondary,
        "original": word,
        "status": "Success"
    }
