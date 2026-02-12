import streamlit as st
import requests
import xml.etree.ElementTree as ET
import re
from urllib.parse import urljoin, urlparse

st.set_page_config(page_title="Sitemap CrawlSync", layout="wide")

# --- PYTHON BACKEND LOGIC (Bypasses CORS) ---

def fetch_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        return response.text if response.status_code == 200 else None
    except Exception:
        return None

def get_sitemaps_from_robots(url):
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    robots_url = urljoin(base_url, "/robots.txt")
    content = fetch_url(robots_url)
    if content:
        return re.findall(r"Sitemap:\s*(https?://[^\s]+)", content, re.IGNORECASE)
    return []

def crawl_sitemaps(url, found_urls=None, searched_sitemaps=None):
    if found_urls is None: found_urls = set()
    if searched_sitemaps is None: searched_sitemaps = set()
    
    if url in searched_sitemaps: return found_urls
    searched_sitemaps.add(url)
    
    content = fetch_url(url)
    if not content: return found_urls

    try:
        root = ET.fromstring(content)
        # Handle namespaces
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Check if it's a Sitemap Index
        for sitemap in root.findall('ns:sitemap', ns):
            loc = sitemap.find('ns:loc', ns)
            if loc is not None:
                crawl_sitemaps(loc.text, found_urls, searched_sitemaps)
        
        # Check for standard URLs
        for url_tag in root.findall('ns:url', ns):
            loc = url_tag.find('ns:loc', ns)
            if loc is not None:
                found_urls.add(loc.text)
    except Exception:
        pass
    
    return found_urls

# --- STREAMLIT UI ---

st.markdown("""
    <style>
    .stApp { background-color: #F9FAFB; }
    .main-title { font-size: 40px; font-weight: 800; text-align: center; color: #111827; margin-bottom: 0px; }
    .sub-title { color: #9CA3AF; font-weight: 400; }
    </style>
    <div style="text-align:center; padding: 20px 0;">
        <h1 class="main-title">Sitemap <span class="sub-title">Crawl</span>Sync</h1>
    </div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Extractor", "IA Builder"])

if 'all_urls' not in st.session_state:
    st.session_state.all_urls = []

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Target Website")
        domain = st.text_input("Enter Domain or Sitemap URL", placeholder="pillowtalk.com.au")
        
        if st.button("Start Deep Extraction", use_container_width=True):
            if domain:
                with st.spinner("Crawling sitemaps via Python (Bypassing CORS)..."):
                    # 1. Try Robots.txt
                    sitemaps = get_sitemaps_from_robots(domain)
                    if not sitemaps:
                        # 2. Fallback to default sitemap.xml
                        base = f"https://{domain.replace('https://', '').replace('http://', '').split('/')[0]}"
                        sitemaps = [urljoin(base, "/sitemap.xml")]
                    
                    all_found = set()
                    for sm in sitemaps:
                        all_found.update(crawl_sitemaps(sm))
                    
                    st.session_state.all_urls = sorted(list(all_found))
                    st.success(f"Extracted {len(st.session_state.all_urls)} URLs!")
            else:
                st.error("Please enter a domain.")

        st.divider()
        st.subheader("Refine Stack")
        include = st.text_input("Must Contain")
        exclude = st.text_input("Exclude")

    with col2:
        # Filter Logic
        filtered_urls = [u for u in st.session_state.all_urls if 
                         (not include or include.lower() in u.lower()) and 
                         (not exclude or exclude.lower() not in u.lower())]
        
        st.subheader(f"Results ({len(filtered_urls)})")
        
        if filtered_urls:
            st.code("\n".join(filtered_urls), language="text")
            if st.button("Send to IA Builder", use_container_width=True):
                st.session_state.ia_input = "\n".join(filtered_urls)
                st.info("Data sent! Switch to the IA Builder tab.")
        else:
            st.info("No URLs found yet. Enter a domain and start extraction.")

with tab2:
    st.subheader("Sitemap to IA Builder")
    ia_val = st.session_state.get('ia_input', '')
    ia_text = st.text_area("Input URLs", value=ia_val, height=300)
    
    if st.button("Build IA Structure", use_container_width=True):
        if ia_text:
            urls = ia_text.split('\n')
            data = []
            for u in urls:
                if not u.strip(): continue
                try:
                    path = urlparse(u.strip()).path
                    segments = [s for s in path.split('/') if s]
                    
                    # Sanitize function
                    def clean(s):
                        parts = s.split('-')
                        if len(parts[-1]) > 10: parts.pop() # Remove IDs
                        return " ".join([p.capitalize() for p in parts])

                    row = {
                        "Main": clean(segments[0]) if len(segments) > 0 else "Home",
                        "Sub 1": clean(segments[1]) if len(segments) > 1 else "",
                        "Sub 2": clean(segments[2]) if len(segments) > 2 else "",
                        "Sub 3": clean(segments[3]) if len(segments) > 3 else "",
                        "Item": clean(segments[-1]) if len(segments) > 1 else "",
                        "URL": u.strip()
                    }
                    data.append(row)
                except: continue
            
            st.dataframe(data, use_container_width=True)
            st.download_button("Download CSV", "Main,Sub 1,Sub 2,Sub 3,Item,URL\n" + "\n".join([f"{r['Main']},{r['Sub 1']},{r['Sub 2']},{r['Sub 3']},{r['Item']},{r['URL']}" for r in data]), "ia_structure.csv")
