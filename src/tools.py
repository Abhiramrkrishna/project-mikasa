import os
import datetime
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("❌ Error: TAVILY_API_KEY not found in .env")

client = TavilyClient(api_key=tavily_api_key)

# 1. DOMAINS TO KILL (Aggregators that ruin search)
BLACKLIST_DOMAINS = [
    "academicpositions.com", "academicpositions.de", 
    "researchgate.net", "academia.edu", "arxiv.org", 
    "linkedin.com", "glassdoor.com", "indeed.com", "stepstone.de",
    "www.nature.com", "jobs.ac.uk", "findaphd.com"
]

# 2. URL PATTERNS TO KILL (Generic Portals)
BAD_URL_PATTERNS = [
    "search", "browse", "results", "all-jobs", "job-board", 
    "careers/index", "vacancies/index", "portal", "listing"
]

# 3. CONTENT TRIGGERS (If page says this, it's a list, not a job)
LIST_PAGE_TRIGGERS = [
    "refine search", "filter by", "sort by", "results found", 
    "page 1 of", "view all jobs", "job search"
]

def is_list_page(content, url):
    """Detects if the page is a search result list instead of a job description."""
    content_lower = content.lower()
    url_lower = url.lower()
    
    if any(x in url_lower for x in BAD_URL_PATTERNS):
        return True
        
    match_count = 0
    for trigger in LIST_PAGE_TRIGGERS:
        if trigger in content_lower:
            match_count += 1
            
    if match_count >= 2: 
        return True
    return False

def search_jobs(query, max_results=5):
    current_year = datetime.datetime.now().year
    
    # NEW QUERY STRATEGY: "intitle:"
    # This forces the page TITLE to have "PhD" or "Vacancy"
    # We allow "VacancyEdu" because it actually lists jobs, even if Mikasa struggles parsing them.
    site_bans = " ".join([f"-site:{d}" for d in BLACKLIST_DOMAINS])
    
    # Try 1: Very Specific Search
    enhanced_query = f'{query} intitle:"PhD" "{current_year}" {site_bans}'
    
    print(f"🕵️‍♀️ Mikasa is scouting: '{enhanced_query}'")
    
    try:
        response = client.search(
            query=enhanced_query,
            search_depth="advanced", 
            max_results=20, 
        )
        
        valid_results = []
        seen_urls = set()
        
        for res in response.get('results', []):
            url = res['url']
            content = res['content']
            title = res['title']
            
            if url in seen_urls: continue
            
            # Use our existing filters
            if is_list_page(content, url):
                print(f"⚠️ Dropped Aggregator: {title}")
                continue
            
            # Content Length check
            if len(content) < 500: 
                print(f"⚠️ Dropped Short Content: {url}")
                continue

            seen_urls.add(url)
            valid_results.append({
                "title": title,
                "url": url,
                "content": content
            })
            
            if len(valid_results) >= max_results:
                break
            
        print(f"✅ Filtered down to {len(valid_results)} actionable targets.")
        return valid_results

    except Exception as e:
        print(f"⚠️ Search Error: {e}")
        return []