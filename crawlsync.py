import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import gzip
import re
from urllib.parse import urlparse, urljoin
import time

# --- 1. PAGE CONFIGURATION & CSS STYLING ---
st.set_page_config(
    page_title="Sitemap Extractor",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject Custom CSS to mimic the Tailwind design
st.markdown("""
<style>
    /* Import Inter Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Font & Background */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background-color: #F9FAFB; /* Light Gray Background */
    }

    /* Input Fields Styling */
    .stTextInput input, .stTextArea textarea {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
    }
    
    /* Custom Header Styling */
    h1 {
        color: #111827;
        font-weight: 800;
        letter-spacing: -0.025em;
    }
    
    /* Metrics Styling */
    div[data-testid="stMetricValue"] {
        font-size: 18px;
        font-weight: 600;
    }

    /* Scrollable Log Area */
    .log-box {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        padding: 10px;
        border-radius: 6px;
        height: 150px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 12px;
        color: #6B7280;
    }
    
    /* Hide Default Streamlit Menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 2. BACKEND LOGIC (The Crawler) ---
class SitemapExtractor:
    def __init__(self, target, log_placeholder):
        self.target = target
        self.log_placeholder = log_placeholder
        self.urls = set()
        self.visited_sitemaps = set()
        self.logs = []
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    def update_log(self, msg):
        # We accumulate logs to show them in the UI text box
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] > {msg}")
        # Join logs with newlines and push to UI
        log_content = "\n".join(self.logs)
        self.log_placeholder.code(log_content, language="text")

    def fetch_content(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                self.update_log(f"Failed: {url} ({response.status_code})")
                return None
            
            # Handle GZIP
            if url.lower().endswith('.gz') or response.headers.get('Content-Type') == 'application/x-gzip':
                try:
                    return gzip.decompress(response.content)
                except:
                    return response.content
            return response.content
        except Exception as e:
            self.update_log(f"Error: {str(e)}")
            return None

    def discover(self):
        url = self.target.strip()
        if not url.startswith("http"): url = "https://" + url

        if url.lower().endswith(('.xml', '.xml.gz')):
            return url

        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        self.update_log(f"Checking robots.txt at {base}...")
        robots_url = urljoin(base, "robots.txt")
        content = self.fetch_content(robots_url)
        
        if content:
            text = content.decode('utf-8', errors='ignore')
            match = re.search(r'Sitemap:\s*(https?://[^\s]+)', text, re.IGNORECASE)
            if match:
                self.update_log(f"Found in robots.txt: {match.group(1)}")
                return match.group(1)

        fallback = urljoin(base, "sitemap.xml")
        self.update_log(f"Trying default: {fallback}")
        return fallback

    def parse_recursive(self, url):
        if url in self.visited_sitemaps: return
        self.visited_sitemaps.add(url)
        
        self.update_log(f"Scanning: {url}")
        content = self.fetch_content(url)
        if not content: return

        try:
            root = ET.fromstring(content)
            for elem in root.iter():
                if '}' in elem.tag: elem.tag = elem.tag.split('}', 1)[1]

            sitemaps = root.findall(".//sitemap/loc")
            if sitemaps:
                self.update_log(f"Found Index ({len(sitemaps)} nested). Recursively crawling...")
                for sm in sitemaps:
                    if sm.text: self.parse_recursive(sm.text.strip())
            else:
                locs = root.findall(".//url/loc")
                imgs = root.findall(".//image/loc")
                count = 0
                for node in locs + imgs:
                    if node.text:
                        self.urls.add(node.text.strip())
                        count += 1
                self.update_log(f"Extracted {count} URLs.")

        except ET.ParseError:
            self.update_log(f"XML Parse Error: {url}")
        except Exception as e:
            self.update_log(f"Error: {e}")

# --- 3. UI LAYOUT ---

# Header (Centered)
st.markdown("""
<div style="text-align: center; padding-top: 2rem; padding-bottom: 1.5rem;">
    <h1 style="font-size: 2.5rem; margin-bottom: 0;">Sitemap <span style="color: #9CA3AF;">Crawl</span>Sync</h1>
    <p style="color: #6B7280; margin-top: 0.5rem; font-size: 0.95rem;">
        Smarter sitemap discovery. Crawls robots.txt, follows indexes, and recursively fetches every link.
    </p>
</div>
""", unsafe_allow_html=True)

# Main Grid (Left Control Panel, Right Results Panel)
col_left, col_right = st.columns([1, 1.8], gap="medium")

# --- LEFT COLUMN: INPUTS & FILTERS ---
with col_left:
    
    # CARD 1: TARGET
    with st.container(border=True):
        st.markdown("**TARGET WEBSITE**", help="Enter Domain, robots.txt, or sitemap.xml")
        target_input = st.text_area(
            "Target", 
            height=100, 
            placeholder="moneyme.com.au", 
            label_visibility="collapsed"
        )
        st.caption("Accepts: Domain, robots.txt, or direct sitemap.xml")
        
        start_btn = st.button("Start Deep Extraction", type="primary", use_container_width=True)
        
        # Status Log Area
        st.markdown("**STATUS LOG**")
        log_display = st.empty()

    # CARD 2: FILTERS
    with st.container(border=True):
        st.markdown("**REFINE STACK**")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.caption("Must Contain")
            filter_include = st.text_input("include", label_visibility="collapsed", placeholder="/products/")
        with col_f2:
            st.caption("Exclude")
            filter_exclude = st.text_input("exclude", label_visibility="collapsed", placeholder="tag")
            
        st.markdown("") # Spacer
        st.markdown("**TARGET EXTENSIONS**")
        
        # Using radio as a pill-like selector
        type_filter = st.radio(
            "Extensions",
            ["All", "Images", "PDFs"],
            horizontal=True,
            label_visibility="collapsed"
        )

# --- RIGHT COLUMN: RESULTS ---
with col_right:
    
    # CARD 3: RESULTS
    with st.container(border=True):
        # Header Row inside the card
        head_c1, head_c2, head_c3 = st.columns([2, 2, 2])
        
        with head_c1:
            st.markdown("**RESULTS (A-Z)**")
        
        # Initialize State
        if 'data' not in st.session_state:
            st.session_state.data = []

        # PROCESSING logic
        if start_btn and target_input:
            st.session_state.data = [] # Reset
            # Initialize log with a placeholder text
            log_display.code("Initializing...", language="text")
            
            extractor = SitemapExtractor(target_input, log_display)
            master = extractor.discover()
            if master:
                extractor.parse_recursive(master)
                st.session_state.data = sorted(list(extractor.urls))
                extractor.update_log(f"DONE. Total Unique: {len(st.session_state.data)}")
            else:
                extractor.update_log("Could not identify sitemap.")

        # FILTERING Logic
        df = pd.DataFrame(st.session_state.data, columns=["URL"])
        
        if not df.empty:
            if filter_include:
                df = df[df['URL'].str.contains(filter_include, case=False, na=False)]
            if filter_exclude:
                df = df[~df['URL'].str.contains(filter_exclude, case=False, na=False)]
            
            if type_filter == "Images":
                img_ext = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg')
                df = df[df['URL'].str.lower().str.endswith(img_ext)]
            elif type_filter == "PDFs":
                df = df[df['URL'].str.lower().str.endswith('.pdf')]
            
            # Update Count Badge
            with head_c2:
                st.markdown(f"<span style='background-color:#E5E7EB; color:#374151; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;'>{len(df)}</span>", unsafe_allow_html=True)

            # Export Button
            with head_c3:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download CSV",
                    data=csv,
                    file_name="sitemap_export.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # The Data Display
            st.divider()
            
            # Using data_editor for a copy-paste friendly table
            st.data_editor(
                df,
                column_config={"URL": st.column_config.LinkColumn("URL Found")},
                use_container_width=True,
                height=550,
                hide_index=True,
                disabled=True
            )
            
        else:
            # Empty State
            st.markdown("""
            <div style="height: 550px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #D1D5DB;">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <p style="margin-top: 10px; font-size: 0.9rem;">Enter a domain to begin</p>
            </div>
            """, unsafe_allow_html=True)
