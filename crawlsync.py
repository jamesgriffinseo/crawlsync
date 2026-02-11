import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import gzip
import re
from urllib.parse import urlparse, urljoin
import time

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Sitemap CrawlSync",
    page_icon="🕸️",
    layout="wide"
)

# --- CLASS DEFINITION ---
class SitemapExtractor:
    def __init__(self, target, status_container):
        self.target = target
        self.status_container = status_container
        self.urls = set()
        self.visited_sitemaps = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def log(self, msg):
        """Updates the Streamlit status container."""
        self.status_container.write(f"👉 {msg}")

    def fetch_content(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                self.log(f"Failed: {url} (Status: {response.status_code})")
                return None

            # Handle GZIP
            if url.lower().endswith('.gz') or response.headers.get('Content-Type') == 'application/x-gzip':
                try:
                    return gzip.decompress(response.content)
                except:
                    return response.content
            return response.content
        except Exception as e:
            self.log(f"Error fetching {url}: {e}")
            return None

    def discover(self):
        url = self.target.strip()
        if not url.startswith("http"):
            url = "https://" + url

        # Direct XML check
        if url.lower().endswith(('.xml', '.xml.gz')):
            return url

        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        # Check robots.txt
        robots_url = urljoin(base, "robots.txt")
        self.log(f"Checking {robots_url}...")
        
        content = self.fetch_content(robots_url)
        if content:
            text = content.decode('utf-8', errors='ignore')
            match = re.search(r'Sitemap:\s*(https?://[^\s]+)', text, re.IGNORECASE)
            if match:
                found = match.group(1)
                self.log(f"Found in robots.txt: {found}")
                return found

        fallback = urljoin(base, "sitemap.xml")
        self.log(f"Trying default: {fallback}")
        return fallback

    def parse_recursive(self, url):
        if url in self.visited_sitemaps:
            return
        self.visited_sitemaps.add(url)
        
        self.log(f"Scanning: {url}")
        content = self.fetch_content(url)
        if not content:
            return

        try:
            root = ET.fromstring(content)
            
            # Namespace stripping
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]

            # Check for Nested Sitemaps (Index)
            sitemaps = root.findall(".//sitemap/loc")
            if sitemaps:
                self.log(f"Found Sitemap Index ({len(sitemaps)} sub-sitemaps). Digging deeper...")
                for sm in sitemaps:
                    if sm.text:
                        self.parse_recursive(sm.text.strip())
            else:
                # Extract URLs
                locs = root.findall(".//url/loc")
                imgs = root.findall(".//image/loc")
                
                new_urls = 0
                for node in locs + imgs:
                    if node.text:
                        self.urls.add(node.text.strip())
                        new_urls += 1
                
                # Optional: specific log for large batches
                if new_urls > 0:
                    self.status_container.write(f"✅ Extracted {new_urls} URLs from {url.split('/')[-1]}")

        except ET.ParseError:
            self.log(f"XML Parse Error: {url}")
        except Exception as e:
            self.log(f"Error: {e}")

# --- UI LAYOUT ---

st.title("🕸️ Sitemap CrawlSync")
st.markdown("""
Smarter sitemap discovery. Automatically crawl `robots.txt`, follow **sitemap indexes**, 
and recursively fetch every linked sitemap in one workflow.
""")

# Sidebar for Filters
with st.sidebar:
    st.header("Refine Stack")
    
    filter_include = st.text_input("Must Contain", placeholder="e.g. /products/")
    filter_exclude = st.text_input("Exclude", placeholder="e.g. tag")
    
    st.subheader("Target Extensions")
    type_filter = st.radio(
        "File Type",
        ["All", "Images", "PDFs"],
        index=0
    )

# Main Input Area
col1, col2 = st.columns([3, 1])
with col1:
    target_url = st.text_input("Target Website", placeholder="moneyme.com.au")
with col2:
    st.write("") # Spacer
    st.write("") # Spacer
    start_btn = st.button("Start Deep Extraction", type="primary", use_container_width=True)

# State Management
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = []

# --- EXECUTION LOGIC ---

if start_btn and target_url:
    st.session_state.extracted_data = [] # Reset
    
    with st.status("🕷️ Crawling...", expanded=True) as status:
        extractor = SitemapExtractor(target_url, status)
        
        # 1. Discover
        master_sitemap = extractor.discover()
        
        # 2. Recursive Crawl
        extractor.parse_recursive(master_sitemap)
        
        # 3. Store Results
        st.session_state.extracted_data = list(extractor.urls)
        
        status.update(label="Crawl Complete!", state="complete", expanded=False)

# --- RESULTS & FILTERING ---

if st.session_state.extracted_data:
    df = pd.DataFrame(st.session_state.extracted_data, columns=["URL"])
    
    # Apply Filters
    if filter_include:
        df = df[df['URL'].str.contains(filter_include, case=False, na=False)]
    
    if filter_exclude:
        df = df[~df['URL'].str.contains(filter_exclude, case=False, na=False)]
        
    if type_filter == "Images":
        img_ext = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg', '.bmp', '.tiff')
        df = df[df['URL'].str.lower().str.endswith(img_ext)]
    elif type_filter == "PDFs":
        df = df[df['URL'].str.lower().str.endswith('.pdf')]
    
    # Sort
    df = df.sort_values(by="URL").reset_index(drop=True)

    # --- DISPLAY METRICS ---
    st.divider()
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Total Found", len(st.session_state.extracted_data))
    m_col2.metric("After Filters", len(df))
    
    # --- DOWNLOADS ---
    csv = df.to_csv(index=False).encode('utf-8')
    m_col3.download_button(
        label="Download CSV",
        data=csv,
        file_name='sitemap_export.csv',
        mime='text/csv',
    )

    # --- DATA TABLE ---
    st.write("### Results")
    st.dataframe(
        df, 
        use_container_width=True,
        column_config={
            "URL": st.column_config.LinkColumn("URL")
        },
        height=500
    )
    
elif start_btn:
    st.warning("No URLs found. Check the domain or try a specific sitemap.xml URL.")
