import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("❌ Error: TAVILY_API_KEY not found in .env")

client = TavilyClient(api_key=tavily_api_key)

# 🚫 BLACKLIST: Urls containing these patterns are usually lists, not jobs.
AGGREGATOR_PATTERNS = [
    "search", "page=", "jobs/field", "browse", "results", 
    "category", "job-function", "locations", "all-jobs"
]

def is_valid_job_url(url):
    """
    Returns False if the URL looks like a generic search result page.
    """
    url_lower = url.lower()
    for pattern in AGGREGATOR_PATTERNS:
        if pattern in url_lower:
            return False
    return True

def search_jobs(query, max_results=5):
    """
    Searches the web for specific job postings.
    Filters out aggregator lists to find direct links.
    """
    print(f"🕵️‍♀️ Mikasa is scouting for: '{query}'...")
    
    try:
        # 1. Fetch MORE results than we need (buffer for filtering)
        response = client.search(
            query=query,
            search_depth="advanced", 
            max_results=15, # Fetch 15, we will filter down to 5
            # We REMOVED the 'include_domains' restriction. 
            # Now she searches University sites directly.
            exclude_domains=["pinterest.com", "facebook.com", "instagram.com"]
        )
        
        valid_results = []
        seen_urls = set()
        
        for res in response.get('results', []):
            url = res['url']
            
            # 2. Apply The Sniper Filter
            if url in seen_urls: continue
            if not is_valid_job_url(url): 
                continue
            
            # 3. Check Content Quality
            # If content is too short, it's likely a navigation wrapper, not a job desc.
            if len(res['content']) < 200:
                continue
                
            seen_urls.add(url)
            valid_results.append({
                "title": res['title'],
                "url": url,
                "content": res['content']
            })
            
            if len(valid_results) >= max_results:
                break
            
        print(f"✅ Filtered down to {len(valid_results)} high-quality targets.")
        return valid_results

    except Exception as e:
        print(f"⚠️ Search Error: {e}")
        return []

if __name__ == "__main__":
    # Test Run
    test_query = "PhD position Physics Informed Neural Networks Germany"
    jobs = search_jobs(test_query)
    
    for i, job in enumerate(jobs):
        print(f"\n{i+1}. {job['title']}")
        print(f"   🔗 {job['url']}")