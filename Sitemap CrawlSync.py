import streamlit as st
import streamlit.components.v1 as components
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
import re
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="Sitemap CrawlSync", layout="wide")

# --- SESSION STATE ---
if 'all_urls' not in st.session_state:
    st.session_state.all_urls = []
if 'ia_data' not in st.session_state:
    st.session_state.ia_data = []

# --- CORE LOGIC (PYTHON NATIVE) ---
def get_sitemap_urls(url):
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    if url.endswith(".xml") or url.endswith(".xml.gz"):
        return [url]

    domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    robots_url = urljoin(domain, "robots.txt")
    sitemaps = []
    
    try:
        response = requests.get(robots_url, timeout=10)
        if response.status_code == 200:
            for line in response.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    sitemaps.append(line.split(":", 1)[1].strip())
    except:
        pass

    return sitemaps if sitemaps else [urljoin(domain, "sitemap.xml")]

def parse_sitemap(url, found_urls=None, searched_sitemaps=None):
    if found_urls is None: found_urls = set()
    if searched_sitemaps is None: searched_sitemaps = set()
    if url in searched_sitemaps: return found_urls
    searched_sitemaps.add(url)
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            
            # 1. Sitemap Indexes
            sitemaps = soup.find_all("sitemap")
            for sm in sitemaps:
                loc = sm.find("loc")
                if loc:
                    parse_sitemap(loc.text.strip(), found_urls, searched_sitemaps)
            
            # 2. Page URLs
            urls = soup.find_all("url")
            for tag in urls:
                loc = tag.find("loc")
                if loc:
                    found_urls.add(loc.text.strip())
    except:
        pass
    return found_urls

# --- UI LOGIC ---
st.markdown("""
    <style>
    .stApp { background-color: #F9FAFB; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    /* Hide default Streamlit tab borders */
    div[data-testid="stTabs"] { border-bottom: none !important; }
    button[data-baseweb="tab"] { font-family: 'Inter', sans-serif; font-weight: 500; color: #9CA3AF; }
    button[data-baseweb="tab"][aria-selected="true"] { color: black; border-bottom-color: black !important; }
    </style>
""", unsafe_allow_html=True)

# Original Design Header
st.markdown("""
    <div style="text-align:center; padding: 30px 0;">
        <h1 style="font-size: 40px; font-weight: 800; color: #111827; letter-spacing: -0.025em; margin-bottom: 0;">
            Sitemap <span style="color: #9CA3AF;">Crawl</span>Sync
        </h1>
        <p style="color: #6B7280; font-size: 14px; margin-top: 8px;">Smarter, recursive sitemap discovery via Python Native engine.</p>
    </div>
""", unsafe_allow_html=True)

tab_extractor, tab_ia = st.tabs(["Extractor", "IA Builder"])

with tab_extractor:
    col_in, col_out = st.columns([1, 2], gap="large")
    
    with col_in:
        with st.container(border=True):
            st.markdown("<p style='font-size: 12px; font-weight: 700; color: #9CA3AF; text-transform: uppercase;'>Target Website</p>", unsafe_allow_html=True)
            target_url = st.text_input("Domain", placeholder="pillowtalk.com.au", label_visibility="collapsed")
            start_btn = st.button("Start Deep Extraction", use_container_width=True, type="primary")
            
        with st.container(border=True):
            st.markdown("<p style='font-size: 12px; font-weight: 700; color: #9CA3AF; text-transform: uppercase;'>Refine Stack</p>", unsafe_allow_html=True)
            inc = st.text_input("Must Contain", placeholder="/products/")
            exc = st.text_input("Exclude", placeholder="tag")

    with col_out:
        if start_btn and target_url:
            with st.status("Crawling Sitemaps...", expanded=True) as status:
                st.write("Searching robots.txt...")
                master_sitemaps = get_sitemap_urls(target_url)
                all_found = set()
                for ms in master_sitemaps:
                    st.write(f"Scanning branch: {ms}")
                    all_found.update(parse_sitemap(ms))
                st.session_state.all_urls = sorted(list(all_found))
                status.update(label="Extraction Complete!", state="complete", expanded=False)

        # Filtering Logic
        urls_to_show = [u for u in st.session_state.all_urls if 
                        (not inc or inc.lower() in u.lower()) and 
                        (not exc or exc.lower() not in u.lower())]

        with st.container(border=True):
            res_col1, res_col2 = st.columns([1, 1])
            res_col1.markdown(f"**Results ({len(urls_to_show)})**")
            
            if urls_to_show:
                if res_col2.button("Send to IA Builder", use_container_width=True):
                    st.session_state.ia_input = "\n".join(urls_to_show)
                    st.toast("Data transferred to IA Builder!")

                # Result List Box (Aesthetic match)
                st.code("\n".join(urls_to_show), language="text")
                st.download_button("Download CSV", pd.DataFrame(urls_to_show, columns=["URL"]).to_csv(index=False), "sitemap_export.csv", use_container_width=True)
            else:
                st.info("No URLs found yet.")

with tab_ia:
    st.markdown("<p style='font-size: 12px; font-weight: 700; color: #9CA3AF; text-transform: uppercase; margin-bottom: 20px;'>Sitemap to IA Builder</p>", unsafe_allow_html=True)
    
    col_ia_in, col_ia_out = st.columns([1, 2.5], gap="large")
    
    with col_ia_in:
        ia_text = st.text_area("Input URLs", value=st.session_state.get('ia_input', ''), height=400, placeholder="Paste URLs here...")
        build_ia = st.button("Build IA Structure", use_container_width=True, type="primary")

    with col_ia_out:
        if build_ia and ia_text:
            raw_urls = ia_text.split('\n')
            ia_list = []
            
            for u in raw_urls:
                u = u.strip()
                if not u: continue
                try:
                    path = urlparse(u).path
                    segs = [s for s in path.split('/') if s]
                    
                    def clean(s):
                        p = s.split('-')
                        if len(p[-1]) > 10: p.pop() # Remove ID slugs
                        return " ".join([word.capitalize() for word in p])
                    
                    row = {
                        "Main": clean(segs[0]) if len(segs) > 0 else "Home",
                        "Sub 1": clean(segs[1]) if len(segs) > 1 else "",
                        "Sub 2": clean(segs[2]) if len(segs) > 2 else "",
                        "Sub 3": clean(segs[3]) if len(segs) > 3 else "",
                        "Item": clean(segs[-1]) if len(segs) > 0 else "",
                        "URL": u
                    }
                    ia_list.append(row)
                except: continue
            
            st.session_state.ia_data = pd.DataFrame(ia_list)
        
        if not st.session_state.ia_data.empty:
            st.dataframe(st.session_state.ia_data, use_container_width=True, height=500)
            csv_ia = st.session_state.ia_data.to_csv(index=False).encode('utf-8')
            st.download_button("Copy for Sheets (CSV)", csv_ia, "ia_structure.csv", use_container_width=True)
        else:
            st.info("Paste URLs or send them from the Extractor to build the IA table.")
