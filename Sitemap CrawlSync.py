import streamlit as st
import streamlit.components.v1 as components
import requests
import xml.etree.ElementTree as ET
import re
from urllib.parse import urljoin, urlparse

# 1. PAGE SETUP
st.set_page_config(page_title="Sitemap CrawlSync", layout="wide")

# 2. ADVANCED PYTHON CRAWLER (Mimics a real human browser)
def fetch_content_resilient(url):
    # These headers are essential for Pillow Talk/Cloudflare sites
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    try:
        # Use a session to handle cookies/persistence if the site requires it
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20)
        return response.text if response.status_code == 200 else None
    except Exception as e:
        return None

def extract_urls_deep(url, found_urls=None, searched_sitemaps=None):
    if found_urls is None: found_urls = set()
    if searched_sitemaps is None: searched_sitemaps = set()
    if url in searched_sitemaps or len(found_urls) > 10000: return found_urls
    searched_sitemaps.add(url)

    content = fetch_content_resilient(url)
    if not content: return found_urls

    # Robust regex extraction (works even if XML is malformed or PHP-generated)
    # This finds both <loc> tags for URLs and potential sub-sitemaps
    locs = re.findall(r'<loc>(.*?)</loc>', content, re.IGNORECASE)
    
    for loc in locs:
        # If the loc ends in .xml, .php, or contains sitemap, treat as sub-sitemap
        if any(ext in loc.lower() for ext in ['.xml', '.php', 'sitemap']):
            if loc not in searched_sitemaps:
                extract_urls_deep(loc, found_urls, searched_sitemaps)
        else:
            found_urls.add(loc)
    
    return found_urls

# --- SESSION STATE ---
if 'extracted_urls' not in st.session_state:
    st.session_state.extracted_urls = []

# --- SIDEBAR CONTROL ---
with st.sidebar:
    st.title("Crawler Control")
    target_domain = st.text_input("Domain (e.g. pillowtalk.com.au)", value="pillowtalk.com.au")
    
    if st.button("🚀 Start Deep Extraction", use_container_width=True):
        if target_domain:
            with st.spinner(f"Bypassing firewalls for {target_domain}..."):
                # Clean the domain
                clean_domain = target_domain.replace('https://','').replace('http://','').split('/')[0]
                base_url = f"https://{clean_domain}"
                
                # Check the specific Pillow Talk sitemaps from your robots.txt
                start_urls = [
                    urljoin(base_url, "/xmlsitemap.php"),
                    urljoin(base_url, "/comfort-journal/sitemap_index.xml"),
                    urljoin(base_url, "/sitemap.xml") # Global fallback
                ]
                
                final_results = set()
                for start_url in start_urls:
                    final_results.update(extract_urls_deep(start_url))
                
                st.session_state.extracted_urls = sorted(list(final_results))
                
                if not st.session_state.extracted_urls:
                    st.error("Still 0 URLs. The site might be blocking Streamlit's IP. Try a different domain to confirm.")
                else:
                    st.success(f"Found {len(st.session_state.extracted_urls)} URLs!")

# --- ORIGINAL DESIGN (HTML/JS) ---
js_url_list = str(st.session_state.extracted_urls).replace("'", '"')

html_content = f"""
<!doctype html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Sitemap CrawlSync</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
        <style>
            body {{ font-family: "Inter", sans-serif; background-color: #F9FAFB; overflow-x: hidden; }}
            .scroller::-webkit-scrollbar {{ width: 6px; }}
            .scroller::-webkit-scrollbar-track {{ background: #f1f1f1; }}
            .scroller::-webkit-scrollbar-thumb {{ background: #d1d5db; border-radius: 3px; }}
            .tab-btn.active {{ border-bottom: 2px solid black; color: black; font-weight: 600; }}
            #outputTable {{ max-width: 100%; overflow-x: auto; }}
        </style>
    </head>
    <body class="text-gray-800">
        <div class="text-center pt-6 pb-6">
            <h1 class="text-4xl font-extrabold tracking-tight text-gray-900">
                Sitemap <span class="text-gray-400">Crawl</span>Sync
            </h1>
            <div class="flex justify-center mt-6 border-b border-gray-200 max-w-xs mx-auto">
                <button onclick="switchTab('extractor')" id="tab-extractor" class="tab-btn active px-4 py-2 text-sm text-gray-500 hover:text-black transition">Extractor</button>
                <button onclick="switchTab('ia-builder')" id="tab-ia-builder" class="tab-btn px-4 py-2 text-sm text-gray-500 hover:text-black transition">IA Builder</button>
            </div>
        </div>

        <div id="view-extractor" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-1 min-h-[600px] flex flex-col">
                <div class="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50 rounded-t-xl">
                    <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">URL Inventory ({len(st.session_state.extracted_urls)})</span>
                    <div class="flex gap-2">
                        <button onclick="sendToIA()" class="text-xs font-medium text-gray-600 bg-white border border-gray-200 px-3 py-1.5 rounded-lg hover:border-black transition">Send to IA Builder</button>
                        <button onclick="copyToClipboard()" class="text-xs font-medium text-white bg-black px-3 py-1.5 rounded-lg shadow-sm">Copy List</button>
                    </div>
                </div>
                <div id="resultsList" class="scroller flex-1 overflow-y-auto p-6 max-h-[550px] space-y-2">
                    </div>
            </div>
        </div>

        <div id="view-ia-builder" class="hidden max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <div class="lg:col-span-4 space-y-6">
                    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                        <h2 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Manual Import</h2>
                        <textarea id="urlInput" class="w-full h-64 p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm font-mono outline-none resize-none transition" placeholder="Paste URLs here..."></textarea>
                        <button onclick="processSitemapIA()" class="w-full mt-4 bg-black text-white font-semibold py-3 px-4 rounded-xl shadow-lg transition">Generate IA</button>
                    </div>
                </div>
                <div class="lg:col-span-8">
                    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-1 min-h-[500px] flex flex-col">
                        <div class="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50 rounded-t-xl">
                            <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">IA Mapping</span>
                            <button onclick="copyTableToClipboard()" class="text-xs font-medium text-white bg-black px-3 py-1.5 rounded-lg">Copy Table</button>
                        </div>
                        <div id="outputSection" class="hidden flex-1 overflow-hidden flex flex-col">
                            <div id="outputTable" class="scroller flex-1 overflow-auto p-4 text-[11px]"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const pythonUrls = {js_url_list};

            function switchTab(tab) {{
                document.getElementById('view-extractor').classList.toggle('hidden', tab !== 'extractor');
                document.getElementById('view-ia-builder').classList.toggle('hidden', tab !== 'ia-builder');
                document.getElementById('tab-extractor').classList.toggle('active', tab === 'extractor');
                document.getElementById('tab-ia-builder').classList.toggle('active', tab === 'ia-builder');
            }}

            function renderResults() {{
                const container = document.getElementById("resultsList");
                if (pythonUrls.length === 0) {{
                    container.innerHTML = '<div class="h-full flex flex-col items-center justify-center text-gray-300"><span class="text-sm">Click Start Deep Extraction in the sidebar</span></div>';
                    return;
                }}
                container.innerHTML = pythonUrls.map(u => 
                    '<div class="p-2 bg-gray-50 border border-transparent hover:border-gray-200 hover:bg-white rounded text-xs font-mono truncate transition">' + u + '</div>'
                ).join('');
            }}

            function sendToIA() {{
                document.getElementById('urlInput').value = pythonUrls.join('\\n');
                switchTab('ia-builder');
                processSitemapIA();
            }}

            const sanitize = (s) => {{
                if (!s) return '';
                let parts = s.split('?')[0].replace(/\/$/, "").split('/');
                let slug = parts[parts.length - 1];
                let slugParts = slug.split('-');
                if (slugParts[slugParts.length-1].length > 10) slugParts.pop();
                return slugParts.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            }};

            function processSitemapIA() {{
                const input = document.getElementById('urlInput').value.trim();
                const urls = input.split('\\n').filter(l => l.trim().startsWith('http'));
                const data = urls.map(u => {{
                    try {{
                        const urlObj = new URL(u);
                        const segments = urlObj.pathname.split('/').filter(s => s !== '');
                        let item = {{ url: u, main: segments[0] ? sanitize(segments[0]) : 'Home' }};
                        for (let i = 1; i <= 9; i++) item['sub'+i] = segments[i] ? sanitize(segments[i]) : '';
                        item.specific = segments.length > 0 ? sanitize(u) : '';
                        return item;
                    }} catch(e) {{ return null; }}
                }}).filter(x => x);

                let html = '<table class="min-w-full divide-y divide-gray-200"><thead class="bg-gray-50 text-[10px] uppercase font-bold text-left"><tr><th class="p-2">Main</th>';
                for(let i=1; i<=9; i++) html += '<th class="p-2">Sub-' + i + '</th>';
                html += '<th class="p-2">Item</th><th class="p-2">URL</th></tr></thead><tbody class="divide-y divide-gray-100">';
                
                data.forEach(item => {{
                    html += '<tr><td class="p-2 font-medium">' + item.main + '</td>';
                    for(let i=1; i<=9; i++) html += '<td class="p-2 text-gray-500">' + item['sub'+i] + '</td>';
                    html += '<td class="p-2 text-gray-500">' + item.specific + '</td><td class="p-2 text-blue-500 truncate max-w-[120px] font-mono">' + item.url + '</td></tr>';
                }});
                document.getElementById('outputTable').innerHTML = html + '</tbody></table>';
                document.getElementById('outputSection').classList.remove('hidden');
            }}

            function copyToClipboard() {{
                navigator.clipboard.writeText(pythonUrls.join('\\n'));
                alert("All URLs copied!");
            }}

            renderResults();
        </script>
    </body>
</html>
"""

components.html(html_content, height=950, scrolling=True)
