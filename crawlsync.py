import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import gzip
import re
from urllib.parse import urlparse, urljoin
import time

# --- 1. PAGE CONFIG & CSS OVERRIDES ---
st.set_page_config(
    page_title="Sitemap CrawlSync",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# This CSS block forces Streamlit to look like your Tailwind design
st.markdown("""
<style>
    /* IMPORT FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    /* GLOBAL RESET */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F9FAFB; /* Tailwind bg-gray-50 */
        color: #1F2937;
    }
    
    /* HIDE STREAMLIT HEADER */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* BACKGROUND */
    .stApp {
        background-color: #F9FAFB;
    }

    /* CARDS (Containers with border) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 16px; /* rounded-2xl */
        border: 1px solid #E5E7EB; /* border-gray-200 */
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); /* shadow-sm */
        padding: 24px;
        margin-bottom: 24px;
    }

    /* INPUTS (Text Area & Text Input) */
    .stTextArea textarea, .stTextInput input {
        background-color: #F9FAFB; /* bg-gray-50 */
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        color: #111827;
        font-family: 'Inter', monospace; /* font-mono for URL */
        font-size: 14px;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #000000;
        box-shadow: none;
    }

    /* BUTTONS (Primary) */
    div.stButton > button {
        background-color: #000000 !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 600 !important;
        border: none !important;
        width: 100%;
        transition: transform 0.1s;
    }
    div.stButton > button:hover {
        background-color: #1F2937 !important; /* gray-800 */
        transform: translateY(-2px);
    }
    div.stButton > button:active {
        transform: translateY(0);
    }

    /* CUSTOM HEADERS (Uppercase gray labels) */
    .custom-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #9CA3AF; /* text-gray-400 */
        margin-bottom: 8px;
    }

    /* METRICS & BADGES */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 800;
        color: #111827;
    }
    
    /* SCROLLBARS */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1; 
    }
    ::-webkit-scrollbar-thumb {
        background: #d1d5db; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #9ca3af; 
    }

</style>
""", unsafe_allow_html=True)

# --- 2. LOGIC CLASS (The Crawler) ---
class SitemapExtractor:
    def __init__(self, target, log_container):
        self.target = target
        self.log_container = log_container
        self.urls = set()
        self.visited_sitemaps = set()
        self.log_messages = []
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    def log(self, msg):
        self.log_messages.append(f"> {msg}")
        # Update the log UI immediately
        self.log_container.code("\n".join(self.log_messages), language="bash")

    def fetch(self, url):
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code != 200:
                self.log(f"Failed: {url} ({res.status_code})")
                return None
            if url.endswith('.gz'):
                try: return gzip.decompress(res.content)
                except: return res.content
            return res.content
        except Exception as e:
            self.log(f"Error: {e}")
            return None

    def discover(self):
        url = self.target.strip()
        if not url.startswith("http"): url = "https://" + url
        if url.endswith(('.xml', '.gz')): return url
        
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        self.log(f"Checking {base}/robots.txt...")
        
        # Check robots.txt
        robots = self.fetch(urljoin(base, "robots.txt"))
        if robots:
            match = re.search(r'Sitemap:\s*(https?://[^\s]+)', robots.decode('utf-8', 'ignore'), re.I)
            if match:
                self.log(f"Found in robots: {match.group(1)}")
                return match.group(1)
        
        fallback = urljoin(base, "sitemap.xml")
        self.log(f"Trying default: {fallback}")
        return fallback

    def crawl(self, url):
        if url in self.visited_sitemaps: return
        self.visited_sitemaps.add(url)
        self.log(f"Scanning: {url}")
        
        content = self.fetch(url)
        if not content: return

        try:
            root = ET.fromstring(content)
            # Remove namespaces
            for elem in root.iter():
                if '}' in elem.tag: elem.tag = elem.tag.split('}', 1)[1]
            
            # Index check
            sitemaps = root.findall(".//sitemap/loc")
            if sitemaps:
                self.log(f"Found Index ({len(sitemaps)} nested). Digging...")
                for sm in sitemaps:
                    if sm.text: self.crawl(sm.text.strip())
            else:
                # URL check
                locs = root.findall(".//url/loc")
                imgs = root.findall(".//image/loc")
                count = 0
                for node in locs + imgs:
                    if node.text:
                        self.urls.add(node.text.strip())
                        count += 1
                self.log(f"Extracted {count} URLs.")
        except:
            self.log(f"Parse Error: {url}")

# --- 3. UI LAYOUT ---

# Header Section (Pure HTML for perfect match)
st.markdown("""
<div style="text-align: center; padding-top: 2rem; padding-bottom: 2rem;">
    <h1 style="font-size: 3rem; font-weight: 800; color: #111827; letter-spacing: -0.05em; margin-bottom: 0;">
        Sitemap <span style="color: #9CA3AF;">Crawl</span>Sync
    </h1>
    <p style="color: #6B7280; margin-top: 0.5rem; max-width: 600px; margin-left: auto; margin-right: auto;">
        Smarter sitemap discovery. Automatically crawl robots.txt, follow sitemap indexes, and recursively fetch every linked sitemap.
    </p>
</div>
""", unsafe_allow_html=True)

# Main Grid: Left (Inputs) | Right (Results)
col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    # --- CARD 1: TARGET ---
    with st.container(border=True):
        st.markdown('<div class="custom-label">Target Website</div>', unsafe_allow_html=True)
        target = st.text_area("Target", placeholder="moneyme.com.au", height=100, label_visibility="collapsed")
        st.caption("Accepts: Domain, robots.txt, or sitemap.xml")
        
        start_btn = st.button("Start Deep Extraction")
        
        st.markdown('<div class="custom-label" style="margin-top: 1rem;">Status Log</div>', unsafe_allow_html=True)
        log_placeholder = st.empty()
        # Initial empty state for log
        log_placeholder.code("", language="bash")

    # --- CARD 2: REFINE ---
    with st.container(border=True):
        st.markdown('<div class="custom-label">Refine Stack</div>', unsafe_allow_html=True)
        
        f_inc = st.text_input("Include", placeholder="Must contain (e.g., /products/)", label_visibility="collapsed")
        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
        f_exc = st.text_input("Exclude", placeholder="Exclude (e.g., tag)", label_visibility="collapsed")
        
        st.markdown('<div class="custom-label" style="margin-top: 1.5rem;">Target Extensions</div>', unsafe_allow_html=True)
        
        # Custom HTML pill buttons are hard in Streamlit, using Radio as closest functional equivalent
        ftype = st.radio("Type", ["All", "Images", "PDFs"], horizontal=True, label_visibility="collapsed")

with col_right:
    # --- CARD 3: RESULTS ---
    with st.container(border=True):
        
        # Header Row
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.markdown('<div class="custom-label">Results (A-Z)</div>', unsafe_allow_html=True)
        
        # Logic State
        if 'results' not in st.session_state:
            st.session_state.results = []
        
        # Processing
        if start_btn and target:
            st.session_state.results = []
            log_placeholder.code("Initializing...", language="bash")
            
            crawler = SitemapExtractor(target, log_placeholder)
            master = crawler.discover()
            if master:
                crawler.crawl(master)
                st.session_state.results = sorted(list(crawler.urls))
                crawler.log(f"DONE. Found {len(st.session_state.results)} unique URLs.")
            else:
                crawler.log("Could not find sitemap.")

        # Filtering
        df = pd.DataFrame(st.session_state.results, columns=["URL"])
        
        if not df.empty:
            if f_inc: df = df[df['URL'].str.contains(f_inc, case=False, na=False)]
            if f_exc: df = df[~df['URL'].str.contains(f_exc, case=False, na=False)]
            
            if ftype == "Images":
                df = df[df['URL'].str.lower().str.endswith(('.jpg','.png','.webp','.svg'))]
            elif ftype == "PDFs":
                df = df[df['URL'].str.lower().str.endswith('.pdf')]
            
            # Count Badge
            with c1:
                 st.caption(f"Showing {len(df)} URLs")

            # Actions
            with c2:
                # Copy logic isn't natively supported in Streamlit without plugins, 
                # so we rely on the download button.
                pass 
            with c3:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", data=csv, file_name="sitemap.csv", mime="text/csv", use_container_width=True)

            # Table
            st.dataframe(
                df,
                use_container_width=True,
                height=600,
                hide_index=True,
                column_config={"URL": st.column_config.LinkColumn("URL")}
            )
        else:
            # Empty State (Matching your HTML)
            st.markdown("""
            <div style="height: 600px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #D1D5DB;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                    <line x1="8" y1="21" x2="16" y2="21"></line>
                    <line x1="12" y1="17" x2="12" y2="21"></line>
                </svg>
                <p style="margin-top: 1rem; font-weight: 500;">Enter a domain to begin</p>
            </div>
            """, unsafe_allow_html=True)
