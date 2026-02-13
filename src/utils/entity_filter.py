#!/usr/bin/env python3
"""
Entity Filter - SME Core Utility
Filters and validates potential usernames extracted from various sources.
Prevents "junk" entities from flooding the OSINT pipeline.
"""

import re

def is_valid_username(username: str) -> bool:
    """
    Check if a string looks like a valid username/alias.
    
    Criteria:
    - Length between 3 and 32 characters.
    - Contains only alphanumeric characters, underscores, or hyphens.
    - Does not contain common academic "junk" (e.g., 'Vol.', 'pp.', 'No.', years).
    - Is not a very common English word or citation fragment.
    """
    if not username or not isinstance(username, str):
        return False
        
    # Remove whitespace
    username = username.strip()
    
    # 1. Length check
    if not (3 <= len(username) <= 32):
        return False
        
    # 2. Character set check
    if not re.match(r'^[a-zA-Z0-9_\-]+$', username):
        return False
        
    # 3. Junk word blacklist (academic/citation common words)
    blacklist = {
        "Volume", "Vol", "Page", "Pages", "pp", "Issue", "No", "Number",
        "Edition", "Ed", "University", "Dept", "Institute", "Dept.", "Inst.",
        "Journal", "Proc", "Conf", "International", "Research", "Studies",
        "Science", "Tech", "Technologies", "State", "Public", "Service"
    }
    if username.lower().capitalize() in blacklist or username.upper() in blacklist:
        return False
        
    # 4. Pattern check for common citation junk (e.g., "pp.32-45", "1990-202X")
    if re.search(r'\d{1,2}-\d{1,2}', username) or re.search(r'[0-9]{4}', username):
        return False

    return True

def filter_targets(targets: list) -> list:
    """Filter a list of potential targets for OSINT pivoting."""
    unique_targets = sorted(list(set(targets)))
    valid_targets = [t for t in unique_targets if is_valid_username(t)]
    return valid_targets

if __name__ == "__main__":
    # Test cases
    test_names = [
        "SpectreDeath", "ForensicAnalyst_88", "Vol.42", "pp.12-14", 
        "University", "short", "VeryLongUsernameThatIsActuallyAJunkString",
        "valid-user", "invalid user", "1994", "JSmith"
    ]
    
    filtered = filter_targets(test_names)
    print(f"Original list: {test_names}")
    print(f"Filtered list: {filtered}")
