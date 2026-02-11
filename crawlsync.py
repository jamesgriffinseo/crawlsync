from flask import Flask, Response

app = Flask(__name__)

HTML_CONTENT = """<!doctype html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Sitemap Extractor</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link
            href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
            rel="stylesheet"
        />
        <style>
            body {
                font-family: "Inter", sans-serif;
            }
            .scroller::-webkit-scrollbar { width: 6px; }
            .scroller::-webkit-scrollbar-track { background: #f1f1f1; }
            .scroller::-webkit-scrollbar-thumb {
                background: #d1d5db;
                border-radius: 3px;
            }
            .scroller::-webkit-scrollbar-thumb:hover {
                background: #9ca3af;
            }
            .type-btn.active {
                background-color: black;
                color: white;
                border-color: black;
            }
        </style>
    </head>
    <body class="bg-[#F9FAFB] text-gray-800 min-h-screen">
       <!doctype html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Sitemap Extractor</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link
            href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
            rel="stylesheet"
        />
        <style>
            body {
                font-family: "Inter", sans-serif;
            }
            /* Custom Scrollbar */
            .scroller::-webkit-scrollbar {
                width: 6px;
            }
            .scroller::-webkit-scrollbar-track {
                background: #f1f1f1;
            }
            .scroller::-webkit-scrollbar-thumb {
                background: #d1d5db;
                border-radius: 3px;
            }
            .scroller::-webkit-scrollbar-thumb:hover {
                background: #9ca3af;
            }

            .type-btn.active {
                background-color: black;
                color: white;
                border-color: black;
            }
        </style>
    </head>
    <body class="bg-[#F9FAFB] text-gray-800 min-h-screen">
        <div class="text-center pt-10 pb-6">
            <h1 class="text-4xl font-extrabold tracking-tight text-gray-900">
                Sitemap <span class="text-gray-400">Crawl</span>Sync
            </h1>
            <p class="text-gray-500 mt-2 text-sm">
                Smarter sitemap discovery. Automatically crawl robots.txt,
                follow sitemap indexes, and recursively fetch every linked
                sitemap in one seamless workflow.
            </p>
        </div>

        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <div class="lg:col-span-4 space-y-6">
                    <div
                        class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6"
                    >
                        <h2
                            class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4"
                        >
                            Target Website
                        </h2>
                        <textarea
                            id="sitemapInput"
                            class="w-full h-24 p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-black focus:border-transparent outline-none resize-none placeholder-gray-400 transition"
                            placeholder="moneyme.com.au"
                        ></textarea>
                        <p class="text-xs text-gray-400 mt-2 mb-4">
                            Accepts: Domain, robots.txt, or direct sitemap.xml
                        </p>

                        <button
                            onclick="startDeepExtraction()"
                            id="extractBtn"
                            class="w-full bg-black hover:bg-gray-800 text-white font-semibold py-3 px-4 rounded-xl shadow-lg transform transition hover:-translate-y-0.5 active:translate-y-0"
                        >
                            Start Deep Extraction
                        </button>

                        <div
                            id="statusLog"
                            class="hidden mt-4 text-xs font-mono text-gray-500 bg-gray-50 p-3 rounded border border-gray-200 h-24 overflow-y-auto scroller"
                        ></div>
                    </div>

                    <div
                        class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6"
                    >
                        <h2
                            class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4"
                        >
                            Refine Stack
                        </h2>

                        <div class="space-y-4">
                            <div>
                                <label
                                    class="block text-xs font-medium text-gray-700 mb-1"
                                    >Must Contain</label
                                >
                                <input
                                    type="text"
                                    id="filterInclude"
                                    oninput="applyFilters()"
                                    class="w-full p-2 pl-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-1 focus:ring-black outline-none"
                                    placeholder="e.g. /products/"
                                />
                            </div>
                            <div>
                                <label
                                    class="block text-xs font-medium text-gray-700 mb-1"
                                    >Exclude</label
                                >
                                <input
                                    type="text"
                                    id="filterExclude"
                                    oninput="applyFilters()"
                                    class="w-full p-2 pl-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-1 focus:ring-black outline-none"
                                    placeholder="e.g. tag"
                                />
                            </div>
                        </div>

                        <div class="mt-6">
                            <label
                                class="block text-xs font-medium text-gray-700 mb-2"
                                >Target Extensions</label
                            >
                            <div class="flex flex-wrap gap-2">
                                <button
                                    onclick="toggleType('all')"
                                    id="btn-all"
                                    class="type-btn active px-4 py-1.5 text-xs font-medium rounded-full border border-black bg-black text-white transition"
                                >
                                    All
                                </button>
                                <button
                                    onclick="toggleType('image')"
                                    id="btn-image"
                                    class="type-btn px-4 py-1.5 text-xs font-medium rounded-full border border-gray-200 text-gray-600 hover:border-gray-400 transition"
                                >
                                    Images
                                </button>
                                <button
                                    onclick="toggleType('pdf')"
                                    id="btn-pdf"
                                    class="type-btn px-4 py-1.5 text-xs font-medium rounded-full border border-gray-200 text-gray-600 hover:border-gray-400 transition"
                                >
                                    PDFs
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="lg:col-span-8 space-y-6">
                    <div
                        class="bg-white rounded-2xl shadow-sm border border-gray-200 p-1 min-h-[600px] flex flex-col"
                    >
                        <div
                            class="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50 rounded-t-xl"
                        >
                            <div class="flex items-center gap-2">
                                <span
                                    class="text-xs font-bold text-gray-400 uppercase tracking-wider"
                                    >Results (A-Z)</span
                                >
                                <span
                                    id="resultCount"
                                    class="bg-gray-200 text-gray-700 text-[10px] font-bold px-2 py-0.5 rounded-full"
                                    >0</span
                                >
                            </div>
                            <div class="flex gap-2">
                                <button
                                    onclick="copyForSheets()"
                                    class="flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 border border-green-200 hover:bg-green-100 px-3 py-1.5 rounded-lg shadow-sm transition"
                                >
                                    <svg
                                        class="w-3 h-3"
                                        fill="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14H5v-4h5v4zm0-6H5V7h5v4zm9 6h-5v-4h5v4zm0-6h-5V7h5v4z"
                                        />
                                    </svg>
                                    Copy for Sheets
                                </button>
                                <button
                                    onclick="downloadCSV()"
                                    class="text-xs font-medium text-gray-600 hover:text-black bg-white border border-gray-200 px-3 py-1.5 rounded-lg shadow-sm transition"
                                >
                                    CSV
                                </button>
                                <button
                                    onclick="copyToClipboard()"
                                    class="text-xs font-medium text-white bg-black px-3 py-1.5 rounded-lg shadow-sm transition"
                                >
                                    Copy
                                </button>
                            </div>
                        </div>

                        <div
                            id="resultsList"
                            class="scroller flex-1 overflow-y-auto p-6 max-h-[600px] space-y-2"
                        >
                            <div
                                class="h-full flex flex-col items-center justify-center text-gray-300"
                            >
                                <svg
                                    class="w-12 h-12 mb-3 text-gray-200"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                                    ></path>
                                </svg>
                                <span class="text-sm"
                                    >Enter a domain to begin</span
                                >
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // --- CONFIG ---
            const CORS_PROXY = "https://corsproxy.io/?";

            // --- STATE ---
            let allExtractedUrls = [];
            let displayedUrls = [];
            let currentTypeFilter = "all";

            // --- UTILS ---
            function log(msg) {
                const el = document.getElementById("statusLog");
                el.classList.remove("hidden");
                const line = document.createElement("div");
                line.className = "mb-1";
                line.textContent = "> " + msg;
                el.appendChild(line);
                el.scrollTop = el.scrollHeight;
            }

            async function fetchText(url) {
                try {
                    // Use proxy to bypass CORS
                    const res = await fetch(
                        CORS_PROXY + encodeURIComponent(url),
                    );
                    if (!res.ok) throw new Error(res.status);
                    return await res.text();
                } catch (e) {
                    log(`Failed to fetch ${url} (Error: ${e.message})`);
                    return null;
                }
            }

            // --- CORE LOGIC ---

            async function discoverSitemap(input) {
                let url = input.trim();
                if (!url.startsWith("http")) url = "https://" + url;

                if (
                    url.toLowerCase().endsWith(".xml") ||
                    url.toLowerCase().endsWith(".xml.gz")
                ) {
                    return url;
                }

                let robotsUrl = url;
                if (!robotsUrl.toLowerCase().endsWith("robots.txt")) {
                    robotsUrl = robotsUrl.replace(/\/$/, "") + "/robots.txt";
                }

                log(`Checking ${robotsUrl}...`);
                const robotsContent = await fetchText(robotsUrl);

                if (robotsContent) {
                    const match = robotsContent.match(
                        /Sitemap:\s*(https?:\/\/[^\s]+)/i,
                    );
                    if (match && match[1]) {
                        log(`Found Sitemap in robots.txt: ${match[1]}`);
                        return match[1];
                    }
                }

                const fallback =
                    url.replace(/\/robots\.txt$/i, "").replace(/\/$/, "") +
                    "/sitemap.xml";
                log(
                    `No Sitemap found in robots.txt. Trying default: ${fallback}`,
                );
                return fallback;
            }

            async function fetchSitemapRecursive(url) {
                log(`Scanning: ${url}`);
                const text = await fetchText(url);
                if (!text) return;

                const parser = new DOMParser();
                const xml = parser.parseFromString(text, "text/xml");

                const sitemaps = xml.getElementsByTagName("sitemap");
                if (sitemaps.length > 0) {
                    log(
                        `Found Index with ${sitemaps.length} sub-sitemaps. Digging deeper...`,
                    );
                    for (let i = 0; i < sitemaps.length; i++) {
                        const loc =
                            sitemaps[i].getElementsByTagName("loc")[0]
                                ?.textContent;
                        if (loc) await fetchSitemapRecursive(loc);
                    }
                } else {
                    const urls = xml.getElementsByTagName("loc");
                    log(`Extracted ${urls.length} URLs from ${url}`);
                    for (let i = 0; i < urls.length; i++) {
                        allExtractedUrls.push(urls[i].textContent);
                    }
                }
            }

            async function startDeepExtraction() {
                const input = document.getElementById("sitemapInput").value;
                if (!input) return alert("Please enter a domain or URL");

                document.getElementById("statusLog").innerHTML = "";
                const btn = document.getElementById("extractBtn");
                btn.disabled = true;
                btn.textContent = "Crawling...";
                btn.classList.add("opacity-75", "cursor-not-allowed");
                allExtractedUrls = [];

                try {
                    const masterSitemap = await discoverSitemap(input);
                    await fetchSitemapRecursive(masterSitemap);

                    allExtractedUrls = [...new Set(allExtractedUrls)];
                    log(`DONE. Total unique URLs: ${allExtractedUrls.length}`);

                    applyFilters();
                } catch (error) {
                    log(`CRITICAL ERROR: ${error.message}`);
                } finally {
                    btn.disabled = false;
                    btn.textContent = "Start Deep Extraction";
                    btn.classList.remove("opacity-75", "cursor-not-allowed");
                }
            }

            // --- FILTERING & UI ---

            function applyFilters() {
                const includeTxt = document
                    .getElementById("filterInclude")
                    .value.toLowerCase();
                const excludeTxt = document
                    .getElementById("filterExclude")
                    .value.toLowerCase();

                displayedUrls = allExtractedUrls.filter((url) => {
                    const lowerUrl = url.toLowerCase();
                    if (includeTxt && !lowerUrl.includes(includeTxt))
                        return false;
                    if (excludeTxt && lowerUrl.includes(excludeTxt))
                        return false;

                    if (currentTypeFilter === "image")
                        return /\.(jpg|jpeg|png|webp|gif|svg|bmp|tiff)$/i.test(
                            url,
                        );
                    if (currentTypeFilter === "pdf") return /\.pdf$/i.test(url);

                    return true;
                });

                // --- NEW: A-Z SORTING ---
                displayedUrls.sort();

                renderResults();
            }

            function renderResults() {
                const container = document.getElementById("resultsList");
                const countLabel = document.getElementById("resultCount");

                container.innerHTML = "";
                countLabel.textContent = displayedUrls.length;

                if (displayedUrls.length === 0) {
                    if (allExtractedUrls.length > 0) {
                        container.innerHTML = `<div class="h-full flex flex-col items-center justify-center text-gray-300"><span class="text-sm">No URLs match your filters</span></div>`;
                    } else {
                        container.innerHTML = `<div class="h-full flex flex-col items-center justify-center text-gray-300"><span class="text-sm">No URLs found yet</span></div>`;
                    }
                    return;
                }

                const LIMIT = 2000;
                const subset = displayedUrls.slice(0, LIMIT);

                subset.forEach((url) => {
                    const item = document.createElement("div");
                    item.className =
                        "group flex items-center justify-between p-2 bg-gray-50 border border-transparent hover:bg-white hover:border-gray-200 rounded text-xs transition-all cursor-pointer";
                    item.onclick = () => {
                        navigator.clipboard.writeText(url);
                        item.classList.add("bg-blue-50");
                        setTimeout(
                            () => item.classList.remove("bg-blue-50"),
                            200,
                        );
                    };
                    item.innerHTML = `
                    <span class="truncate mr-4 font-mono text-gray-600">${url}</span>
                    <span class="opacity-0 group-hover:opacity-100 text-[10px] text-blue-500 font-bold">COPY</span>
                `;
                    container.appendChild(item);
                });

                if (displayedUrls.length > LIMIT) {
                    const warning = document.createElement("div");
                    warning.className = "text-center text-xs text-red-400 p-2";
                    warning.textContent = `Showing first ${LIMIT} of ${displayedUrls.length} results. Use filters to narrow down.`;
                    container.appendChild(warning);
                }
            }

            function toggleType(type) {
                currentTypeFilter = type;
                document.querySelectorAll(".type-btn").forEach((btn) => {
                    btn.classList.remove("active", "bg-black", "text-white");
                    btn.classList.add("text-gray-600", "border-gray-200");
                });
                const activeBtn = document.getElementById("btn-" + type);
                activeBtn.classList.add("active", "bg-black", "text-white");
                activeBtn.classList.remove("text-gray-600", "border-gray-200");

                applyFilters();
            }

            // --- EXPORT ---

            function downloadCSV() {
                if (displayedUrls.length === 0) return;
                const csvContent =
                    "data:text/csv;charset=utf-8," + displayedUrls.join("\n");
                const encodedUri = encodeURI(csvContent);
                const link = document.createElement("a");
                link.setAttribute("href", encodedUri);
                link.setAttribute("download", "sitemap_export.csv");
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }

            function copyToClipboard() {
                if (displayedUrls.length === 0) return;
                navigator.clipboard
                    .writeText(displayedUrls.join("\n"))
                    .then(() => alert("Copied all URLs to clipboard!"));
            }

            function copyForSheets() {
                if (displayedUrls.length === 0) return;
                const data = displayedUrls.join("\n");
                navigator.clipboard.writeText(data).then(() => {
                    alert("Copied! Ready to paste into Google Sheets.");
                });
            }
        </script>
    </body>
</html>
"""

@app.route("/")
def home():
    return Response(HTML_CONTENT, mimetype="text/html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
