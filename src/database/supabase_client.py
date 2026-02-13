import os
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

try:
    from supabase import create_client, Client
    if not url or not key:
        print("⚠️ Warning: Supabase credentials not found in .env file.")
        supabase: Client = None
    else:
        supabase: Client = create_client(url, key)
except Exception as e:
    # Handle both ImportError (missing package) and initialization errors
    print(f"⚠️ Warning: Supabase client failed to initialize due to environmental incompatibility: {e}")
    supabase = None

def sync_osint_results_to_supabase(scan_results):
    """Sync a single OSINT scan result to Supabase."""
    if not supabase:
        return None
    
    username = scan_results.get("username")
    timestamp = scan_results.get("timestamp")
    
    try:
        # 1. Upsert Actor
        actor_res = supabase.table("actors").upsert({
            "username": username,
            "last_scanned": timestamp,
            "metadata": {"last_scan_summary": scan_results}
        }, on_conflict="username").execute()
        
        if not actor_res.data:
            return None
        
        actor_id = actor_res.data[0]["id"]
        
        # 2. Upsert Footprints
        footprints = []
        for p in scan_results.get("platforms", []):
            footprints.append({
                "actor_id": actor_id,
                "platform_name": p["name"],
                "url": p.get("url"),
                "status": p["status"],
                "discovered_at": timestamp
            })
        
        if footprints:
            supabase.table("footprints").upsert(footprints, on_conflict="actor_id,platform_name").execute()
            
        return actor_id
    except Exception as e:
        print(f"❌ Supabase OSINT Sync Error: {e}")
        return None

def sync_news_to_supabase(news_list):
    """Sync a list of news articles to Supabase."""
    if not supabase or not news_list:
        return
    try:
        supabase.table("news_articles").upsert([{
            "title": n.get("title"),
            "summary": n.get("summary"),
            "source_feed": n.get("source_feed"),
            "url": n.get("link") or n.get("url"),
            "published_at": n.get("published"),
            "sentiment_polarity": n.get("sentiment_polarity")
        } for n in news_list], on_conflict="url").execute()
    except Exception as e:
        print(f"❌ Supabase News Sync Error: {e}")

def sync_research_to_supabase(research_list):
    """Sync a list of research papers to Supabase."""
    if not supabase or not research_list:
        return
    try:
        supabase.table("research_papers").upsert([{
            "paper_id": p.get("paperId"),
            "title": p.get("title"),
            "abstract": p.get("abstract"),
            "authors": p.get("authors"),
            "year": p.get("year"),
            "url": p.get("url"),
            "ingested_at": p.get("ingested_at")
        } for p in research_list], on_conflict="paper_id").execute()
    except Exception as e:
        print(f"❌ Supabase Research Sync Error: {e}")

def test_connection():
    """Verify the connection to Supabase."""
    if not supabase:
        return False
    try:
        # A simple query to check connectivity
        supabase.table("actors").select("*", count="exact").limit(1).execute()
        return True
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return False

def get_threat_leads():
    """Fetch all records from the threat_leads table."""
    if not supabase:
        return []
    try:
        response = supabase.table("threat_leads").select("*").execute()
        return response.data
    except Exception as e:
        print(f"❌ Supabase Query Error (threat_leads): {e}")
        return []
