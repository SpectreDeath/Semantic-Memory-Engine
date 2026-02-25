import os
import requests
import re

def vendor_faststylometry():
    base_url = "https://raw.githubusercontent.com/fastdatascience/faststylometry/main/src/faststylometry/"
    files = ["corpus.py", "burrows_delta.py", "en.py", "probability.py"]
    target_dir = "D:/SME/src/sme/vendor/faststylometry"
    
    os.makedirs(target_dir, exist_ok=True)
    
    # Create __init__.py files up the tree
    open(os.path.join("D:/SME/src/sme", "__init__.py"), "a").close()
    open(os.path.join("D:/SME/src/sme/vendor", "__init__.py"), "a").close()
    open(os.path.join(target_dir, "__init__.py"), "a").close()
    
    for filename in files:
        url = base_url + filename
        print(f"Downloading {filename}...")
        response = requests.get(url)
        if response.status_code == 200:
            content = response.text
            
            # Patch imports: from faststylometry import ... -> from . import ...
            # Also handle: from faststylometry.something import ... -> from .something import ...
            # Fix double-dot imports (..) to single-dot (.)
            patched_content = re.sub(r'from faststylometry(\..+)? import', r'from .\1 import', content)
            patched_content = re.sub(r'\.\.(\.)?', r'.', patched_content)  # Fix .. to .
            patched_content = re.sub(r'import faststylometry', r'from . import __init__ as faststylometry', patched_content)
            
            with open(os.path.join(target_dir, filename), "w", encoding="utf-8") as f:
                f.write(patched_content)
            print(f"Successfully vendored and patched {filename}")
        else:
            print(f"Failed to download {filename}: {response.status_code}")

if __name__ == "__main__":
    vendor_faststylometry()
