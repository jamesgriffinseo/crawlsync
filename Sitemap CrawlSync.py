import streamlit as st
import streamlit.components.v1 as components

# Set page config to wide mode to accommodate the 12-column grid
st.set_page_config(page_title="Sitemap CrawlSync", layout="wide")

# The original HTML/JS/CSS logic
# Note: Using triple quotes and f-string if you need to pass python variables
html_code = """
<!doctype html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Sitemap CrawlSync & IA Builder</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
        <style>
            body { font-family: "Inter", sans-serif; background-color: #F9FAFB; }
            .scroller::-webkit-scrollbar { width: 6px; }
            .scroller::-webkit-scrollbar-track { background: #f1f1f1; }
            .scroller::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
            .scroller::-webkit-scrollbar-thumb:hover { background: #9ca3af; }
            .tab-btn.active { border-bottom: 2px solid black; color: black; font-weight: 600; }
            #outputTable { max-width: 100%; overflow-x: auto; }
            th { white-space: nowrap; }
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

        <div id="view-extractor" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <div class="lg:col-span-4 space-y-6">
                    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                        <h2 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Target Website</h2>
                        <textarea id="sitemapInput" class="w-full h-24 p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-black outline-none resize-none placeholder-gray-400 transition" placeholder="domain.com"></textarea>
                        <button onclick="startDeepExtraction()" id="extractBtn" class="w-full mt-4 bg-black hover:bg-gray-800 text-white font-semibold py-3 px-4 rounded-xl shadow-lg transition">Start Deep Extraction</button>
                        <div id="statusLog" class="hidden mt-4 text-xs font-mono text-gray-500 bg-gray-50 p-3 rounded border border-gray-200 h-32 overflow-y-auto scroller"></div>
                    </div>
                </div>
                <div class="lg:col-span-8">
                    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-1 min-h-[500px] flex flex-col">
                        <div class="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50 rounded-t-xl">
                            <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">Results</span>
                            <div class="flex gap-2">
                                <button onclick="sendToIA()" class="text-xs font-medium text-gray-600 bg-white border border-gray-200 px-3 py-1.5 rounded-lg hover:border-black transition">Send to IA Builder</button>
                                <button onclick="copyToClipboard()" class="text-xs font-medium text-white bg-black px-3 py-1.5 rounded-lg">Copy All</button>
                            </div>
                        </div>
                        <div id="resultsList" class="scroller flex-1 overflow-y-auto p-6 max-h-[500px] space-y-2"></div>
                    </div>
                </div>
            </div>
        </div>

        <div id="view-ia-builder" class="hidden max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
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
            // --- SAME LOGIC AS PREVIOUS VERSION ---
            const CORS_PROXY = "https://corsproxy.io/?";
            let allExtractedUrls = [];
            let displayedUrls = [];
            let processedIAData = [];

            function switchTab(tab) {
                document.getElementById('view-extractor').classList.toggle('hidden', tab !== 'extractor');
                document.getElementById('view-ia-builder').classList.toggle('hidden', tab !== 'ia-builder');
                document.getElementById('tab-extractor').classList.toggle('active', tab === 'extractor');
                document.getElementById('tab-ia-builder').classList.toggle('active', tab === 'ia-builder');
            }

            function log(msg) {
                const el = document.getElementById("statusLog");
                el.classList.remove("hidden");
                const line = document.createElement("div");
                line.textContent = "> " + msg;
                el.appendChild(line);
                el.scrollTop = el.scrollHeight;
            }

            async function fetchText(url) {
                try {
                    const res = await fetch(CORS_PROXY + encodeURIComponent(url));
                    return res.ok ? await res.text() : null;
                } catch (e) { return null; }
            }

            async function discoverSitemap(input) {
                let url = input.trim();
                if (!url.startsWith("http")) url = "https://" + url;
                if (url.toLowerCase().endsWith(".xml") || url.toLowerCase().endsWith(".xml.gz")) return url;
                let robotsUrl = url.replace(/\/$/, "") + "/robots.txt";
                log(`Checking robots.txt...`);
                const robots = await fetchText(robotsUrl);
                if (robots) {
                    const match = robots.match(/Sitemap:\\s*(https?:\/\/[^\\s]+)/i);
                    if (match) return match[1];
                }
                return url.replace(/\/$/, "") + "/sitemap.xml";
            }

            async function fetchSitemapRecursive(url) {
                log(`Scanning: \${url}`);
                const text = await fetchText(url);
                if (!text) return;
                const xml = new DOMParser().parseFromString(text, "text/xml");
                const sitemaps = xml.getElementsByTagName("sitemap");
                if (sitemaps.length > 0) {
                    for (let i = 0; i < sitemaps.length; i++) {
                        const loc = sitemaps[i].getElementsByTagName("loc")[0]?.textContent;
                        if (loc) await fetchSitemapRecursive(loc);
                    }
                } else {
                    const urls = xml.getElementsByTagName("loc");
                    for (let i = 0; i < urls.length; i++) allExtractedUrls.push(urls[i].textContent);
                }
            }

            async function startDeepExtraction() {
                const input = document.getElementById("sitemapInput").value;
                if (!input) return;
                const btn = document.getElementById("extractBtn");
                btn.disabled = true; btn.textContent = "Crawling...";
                document.getElementById("statusLog").innerHTML = "";
                allExtractedUrls = [];
                try {
                    const master = await discoverSitemap(input);
                    await fetchSitemapRecursive(master);
                    allExtractedUrls = [...new Set(allExtractedUrls)];
                    displayedUrls = allExtractedUrls.sort();
                    renderResults();
                } catch (e) { log(`Error: \${e.message}`); }
                finally { btn.disabled = false; btn.textContent = "Start Deep Extraction"; }
            }

            function renderResults() {
                const container = document.getElementById("resultsList");
                container.innerHTML = displayedUrls.slice(0, 1000).map(u => `
                    <div class="p-2 bg-gray-50 border border-transparent hover:border-gray-200 hover:bg-white rounded text-xs font-mono truncate transition">\${u}</div>
                `).join('');
            }

            function sendToIA() {
                document.getElementById('urlInput').value = displayedUrls.join('\\n');
                switchTab('ia-builder');
                processSitemapIA();
            }

            const sanitize = (s) => {
                if (!s) return '';
                let parts = s.split('?')[0].replace(/\/$/, "").split('-');
                if (parts[parts.length-1].length > 10) parts.pop();
                return parts.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            };

            function processSitemapIA() {
                const input = document.getElementById('urlInput').value.trim();
                const urls = input.split('\\n').filter(l => l.trim().startsWith('http'));
                processedIAData = urls.map(u => {
                    try {
                        const path = new URL(u).pathname;
                        const segments = path.split('/').filter(s => s !== '');
                        let item = { url: u, main: segments[0] ? sanitize(segments[0]) : 'Home' };
                        for (let i = 1; i <= 9; i++) item['sub'+i] = segments[i] ? sanitize(segments[i]) : '';
                        item.specific = segments.length > 10 ? sanitize(segments.slice(10).join('-')) : '';
                        return item;
                    } catch(e) { return null; }
                }).filter(x => x);
                renderIATable();
                document.getElementById('outputSection').classList.remove('hidden');
            }

            function renderIATable() {
                let html = `<table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50 text-[10px] uppercase font-bold">
                        <tr><th class="p-2">Main</th>\${[1,2,3,4,5,6,7,8,9].map(i => `<th class="p-2">Sub-\${i}</th>`).join('')}<th class="p-2">Item</th><th class="p-2">URL</th></tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">`;
                processedIAData.forEach(item => {
                    html += `<tr><td class="p-2 font-medium">\${item.main}</td>` + 
                    [1,2,3,4,5,6,7,8,9].map(i => `<td class="p-2 text-gray-500">\${item['sub'+i]}</td>`).join('') + 
                    `<td class="p-2 text-gray-500">\${item.specific}</td><td class="p-2 text-blue-500 truncate max-w-[120px] font-mono">\${item.url}</td></tr>`;
                });
                document.getElementById('outputTable').innerHTML = html + `</tbody></table>`;
            }

            function copyTableToClipboard() {
                const headers = ['Main', 'Sub 1', 'Sub 2', 'Sub 3', 'Sub 4', 'Sub 5', 'Sub 6', 'Sub 7', 'Sub 8', 'Sub 9', 'Item', 'URL'];
                let tsv = headers.join('\\t') + '\\n';
                processedIAData.forEach(item => {
                    const row = [item.main, item.sub1, item.sub2, item.sub3, item.sub4, item.sub5, item.sub6, item.sub7, item.sub8, item.sub9, item.specific, item.url];
                    tsv += row.join('\\t') + '\\n';
                });
                navigator.clipboard.writeText(tsv);
            }

            function copyToClipboard() {
                navigator.clipboard.writeText(displayedUrls.join('\\n'));
            }
        </script>
    </body>
</html>
"""

# Render the HTML in Streamlit
components.html(html_code, height=1000, scrolling=True)
