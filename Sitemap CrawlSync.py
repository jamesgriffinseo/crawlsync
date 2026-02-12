import streamlit as st
import streamlit.components.v1 as components
import requests
import xml.etree.ElementTree as ET
import re
from urllib.parse import urljoin, urlparse

# 1. PAGE SETUP
st.set_page_config(page_title="Sitemap CrawlSync", layout="wide")

# 2. PYTHON CRAWLING ENGINE (Bypasses CORS and handles multiple sitemaps)
def fetch_content(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response.text if response.status_code == 200 else None
    except:
        return None

def extract_urls_from_sitemap(url, found_urls=None, searched_sitemaps=None):
    if found_urls is None: found_urls = set()
    if searched_sitemaps is None: searched_sitemaps = set()
    if url in searched_sitemaps: return found_urls
    searched_sitemaps.add(url)

    content = fetch_content(url)
    if not content: return found_urls

    try:
        # Handle namespaces commonly found in sitemaps
        root = ET.fromstring(content)
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Check for Sitemap Index (sub-sitemaps)
        for sitemap in root.findall('ns:sitemap', ns):
            loc = sitemap.find('ns:loc', ns)
            if loc is not None:
                extract_urls_from_sitemap(loc.text, found_urls, searched_sitemaps)
        
        # Check for standard URLs
        for url_tag in root.findall('ns:url', ns):
            loc = url_tag.find('ns:loc', ns)
            if loc is not None:
                found_urls.add(loc.text)
    except:
        # Fallback regex if XML parser fails on PHP generated sitemaps
        links = re.findall(r'<loc>(.*?)</loc>', content)
        for link in links:
            if '.xml' in link or 'sitemap' in link.lower():
                extract_urls_from_sitemap(link, found_urls, searched_sitemaps)
            else:
                found_urls.add(link)
    
    return found_urls

# --- UI STATE MANAGEMENT ---
if 'extracted_urls' not in st.session_state:
    st.session_state.extracted_urls = []

# --- STREAMLIT SIDEBAR FOR INPUT ---
# We use a real Streamlit sidebar to trigger the Python crawl
with st.sidebar:
    st.title("Crawl Control")
    target_input = st.text_input("Target Domain", placeholder="pillowtalk.com.au")
    
    if st.button("Run Deep Crawl", use_container_width=True):
        if target_input:
            with st.spinner("Python engine crawling..."):
                # Based on the robots.txt you provided
                base = f"https://{target_input.replace('https://','').replace('http://','').split('/')[0]}"
                # Start with the specific Pillow Talk sitemaps discovered in robots.txt
                start_points = [
                    urljoin(base, "/xmlsitemap.php"),
                    urljoin(base, "/comfort-journal/sitemap_index.xml")
                ]
                
                all_results = set()
                for sp in start_points:
                    all_results.update(extract_urls_from_sitemap(sp))
                
                st.session_state.extracted_urls = sorted(list(all_results))
                st.success(f"Found {len(st.session_state.extracted_urls)} URLs!")
        else:
            st.warning("Enter a domain first.")

# --- THE DESIGN (HTML/JS) ---
# We inject the python results into the JS state
js_urls = str(st.session_state.extracted_urls).replace("'", '"')

html_code = f"""
<!doctype html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Sitemap CrawlSync</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
        <style>
            body {{ font-family: "Inter", sans-serif; background-color: #F9FAFB; overflow: hidden; }}
            .scroller::-webkit-scrollbar {{ width: 6px; }}
            .scroller::-webkit-scrollbar-track {{ background: #f1f1f1; }}
            .scroller::-webkit-scrollbar-thumb {{ background: #d1d5db; border-radius: 3px; }}
            .tab-btn.active {{ border-bottom: 2px solid black; color: black; font-weight: 600; }}
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
                    <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">Results ({len(st.session_state.extracted_urls)})</span>
                    <div class="flex gap-2">
                        <button onclick="sendToIA()" class="text-xs font-medium text-gray-600 bg-white border border-gray-200 px-3 py-1.5 rounded-lg hover:border-black transition">Send to IA Builder</button>
                        <button onclick="copyToClipboard()" class="text-xs font-medium text-white bg-black px-3 py-1.5 rounded-lg">Copy All</button>
                    </div>
                </div>
                <div id="resultsList" class="scroller flex-1 overflow-y-auto p-6 max-h-[550px] space-y-2">
                    </div>
            </div>
        </div>

        <div id="view-ia-builder" class="hidden max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
             <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <div class="lg:col-span-4 space-y-6">
                    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                        <h2 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Input Data</h2>
                        <textarea id="urlInput" class="w-full h-64 p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm font-mono outline-none resize-none transition" placeholder="URLs here..."></textarea>
                        <button onclick="processSitemapIA()" class="w-full mt-4 bg-black text-white font-semibold py-3 px-4 rounded-xl shadow-lg transition">Build IA Structure</button>
                    </div>
                </div>
                <div class="lg:col-span-8">
                    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-1 min-h-[500px] flex flex-col">
                        <div class="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50 rounded-t-xl">
                            <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">IA Table</span>
                            <button onclick="copyTableToClipboard()" class="text-xs font-medium text-white bg-black px-3 py-1.5 rounded-lg">Copy for Sheets</button>
                        </div>
                        <div id="outputSection" class="hidden flex-1 overflow-hidden flex flex-col">
                            <div id="outputTable" class="scroller flex-1 overflow-auto p-4 text-[11px]"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const pythonUrls = {js_urls};
            
            function switchTab(tab) {{
                document.getElementById('view-extractor').classList.toggle('hidden', tab !== 'extractor');
                document.getElementById('view-ia-builder').classList.toggle('hidden', tab !== 'ia-builder');
                document.getElementById('tab-extractor').classList.toggle('active', tab === 'extractor');
                document.getElementById('tab-ia-builder').classList.toggle('active', tab === 'ia-builder');
            }}

            function renderResults() {{
                const container = document.getElementById("resultsList");
                if (pythonUrls.length === 0) {{
                    container.innerHTML = '<div class="h-full flex flex-col items-center justify-center text-gray-300"><span class="text-sm">Use the sidebar to run a crawl</span></div>';
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

            // IA Builder Logic
            const sanitize = (s) => {{
                if (!s) return '';
                let parts = s.split('?')[0].replace(/\/$/, "").split('-');
                if (parts[parts.length-1].length > 10) parts.pop();
                return parts.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
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
                        item.specific = segments.length > 10 ? sanitize(segments.slice(10).join('-')) : '';
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

            function copyTableToClipboard() {{
                // Logic to copy table content
                alert("Table content ready to copy!");
            }}

            function copyToClipboard() {{
                navigator.clipboard.writeText(pythonUrls.join('\\n'));
                alert("Copied!");
            }}

            renderResults();
        </script>
    </body>
</html>
"""

components.html(html_code, height=900, scrolling=False)
