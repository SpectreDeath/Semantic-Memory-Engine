from mcp.server.fastmcp import FastMCP
import os

# Initialize FastMCP
mcp = FastMCP("WhitesFileManager")

# The "Jail" directory - only files inside here can be accessed
BASE_DIR = os.path.normpath("D:/mcp_servers/storage")

def get_safe_path(requested_path: str) -> str:
    """Ensures the path is within the allowed BASE_DIR."""
    # Resolve to absolute path
    target_path = os.path.normpath(os.path.join(BASE_DIR, requested_path))
    
    # Check if the target path is actually within the BASE_DIR
    if not target_path.startswith(BASE_DIR):
        raise PermissionError(f"Access denied: {requested_path} is outside the allowed directory.")
    
    return target_path

@mcp.tool()
def read_local_file(file_path: str) -> str:
    """
    Reads the contents of a file at the given path. 
    Paths should be relative to the storage directory.
    """
    try:
        safe_path = get_safe_path(file_path)
        with open(safe_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def list_directory_contents(dir_path: str = ".") -> str:
    """
    Lists all files and folders in a directory. 
    Paths should be relative to the storage directory.
    """
    try:
        safe_path = get_safe_path(dir_path)
        items = os.listdir(safe_path)
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

if __name__ == "__main__":
    mcp.run()