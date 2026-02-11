import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Sitemap CrawlSync", layout="wide")

# --- CORE LOGIC (PYTHON) ---
def get_sitemap_urls(url):
    """
    Determines the sitemap URL. Checks robots.txt first, then falls back to /sitemap.xml.
    """
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    
    # If user provided a direct xml link
    if url.endswith(".xml") or url.endswith(".xml.gz"):
        return url

    # Check robots.txt
    domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    robots_url = urljoin(domain, "robots.txt")
    
    try:
        response = requests.get(robots_url, timeout=10)
        if response.status_code == 200:
            for line in response.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass

    # Fallback
    return urljoin(domain, "sitemap.xml")

def parse_sitemap(url, found_urls=None, recursive=True):
    """
    Recursively parses sitemaps to find all URLs.
    """
    if found_urls is None:
        found_urls = set()
    
    # Avoid processing the same sitemap twice
    if url in found_urls: 
        return found_urls
    
    try:
        with st.spinner(f"Fetching {url}..."):
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; SitemapExtractor/1.0)'}
            response = requests.get(url, headers=headers, timeout=10)
            
            # Handle XML parsing
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                
                # 1. Check for Nested Sitemaps (SitemapIndex)
                sitemaps = soup.find_all("sitemap")
                if sitemaps and recursive:
                    for sm in sitemaps:
                        loc = sm.find("loc")
                        if loc:
                            # Recursion
                            parse_sitemap(loc.text.strip(), found_urls, recursive)
                
                # 2. Check for actual URLs (urlset)
                urls = soup.find_all("url")
                for tag in urls:
                    loc = tag.find("loc")
                    if loc:
                        found_urls.add(loc.text.strip())
                        
    except Exception as e:
        st.error(f"Error fetching {url}: {e}")

    return found_urls

# --- UI LAYOUT ---
st.title("Sitemap **Crawl**Sync (Python Native)")
st.markdown("Extracts all URLs from a domain by recursively parsing sitemaps and robots.txt.")

col1, col2 = st.columns([1, 2])

with col1:
    with st.container(border=True):
        st.subheader("Target")
        target_url = st.text_input("Domain or Sitemap URL", placeholder="example.com")
        recursive_mode = st.checkbox("Recursive Search (Follow Sitemap Indexes)", value=True)
        start_btn = st.button("Start Extraction", type="primary", use_container_width=True)

    if 'results' in st.session_state and st.session_state.results:
        with st.container(border=True):
            st.subheader("Filters")
            search_term = st.text_input("Must Contain", placeholder="/products/")
            exclude_term = st.text_input("Exclude", placeholder="tag")
            
            file_type = st.radio("File Type", ["All", "Images", "PDFs"], horizontal=True)

with col2:
    if start_btn and target_url:
        # Reset previous results
        st.session_state.results = set()
        
        # 1. Find the master sitemap
        master_sitemap = get_sitemap_urls(target_url)
        st.info(f"Targeting Sitemap: {master_sitemap}")
        
        # 2. Crawl
        extracted = parse_sitemap(master_sitemap, recursive=recursive_mode)
        st.session_state.results = list(extracted) # Convert to list for display
        st.success(f"Extraction Complete! Found {len(st.session_state.results)} URLs.")

    # --- RESULT DISPLAY ---
    if 'results' in st.session_state and st.session_state.results:
        df = pd.DataFrame(st.session_state.results, columns=["URL"])
        
        # Apply Filters
        if 'search_term' in locals() and search_term:
            df = df[df['URL'].str.contains(search_term, case=False)]
        
        if 'exclude_term' in locals() and exclude_term:
            df = df[~df['URL'].str.contains(exclude_term, case=False)]
            
        if 'file_type' in locals():
            if file_type == "Images":
                df = df[df['URL'].str.contains(r'\.(jpg|jpeg|png|webp|gif|svg)$', case=False, regex=True)]
            elif file_type == "PDFs":
                df = df[df['URL'].str.contains(r'\.pdf$', case=False, regex=True)]

        # Sort
        df = df.sort_values("URL").reset_index(drop=True)

        st.markdown(f"### Results ({len(df)})")
        
        # Download Buttons
        d_col1, d_col2 = st.columns(2)
        csv = df.to_csv(index=False).encode('utf-8')
        d_col1.download_button("Download CSV", csv, "sitemap_links.csv", "text/csv")
        
        # Dataframe Display
        st.dataframe(df, use_container_width=True, height=500)
    
    elif start_btn:
        st.warning("No URLs found. Check if the sitemap exists or is blocked.")
