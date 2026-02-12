async function fetchSitemapRecursive(url, visited = new Set()) {
                if (visited.has(url)) return;
                visited.add(url);
                
                log("Scanning: " + url);
                const text = await fetchText(url);
                if (!text) return;
                
                const xml = new DOMParser().parseFromString(text, "text/xml");
                const sitemaps = xml.getElementsByTagName("sitemap");
                
                if (sitemaps.length > 0) {
                    // PERFORMANCE FIX: Use Promise.all to fetch sub-sitemaps in parallel
                    const sitemapLocs = Array.from(sitemaps)
                        .map(s => s.getElementsByTagName("loc")[0]?.textContent)
                        .filter(loc => loc);
                    
                    await Promise.all(sitemapLocs.map(loc => fetchSitemapRecursive(loc, visited)));
                } else {
                    const urls = xml.getElementsByTagName("loc");
                    const batch = [];
                    for (let i = 0; i < urls.length; i++) {
                        batch.push(urls[i].textContent);
                    }
                    allExtractedUrls.push(...batch);
                    log("Collected " + urls.length + " URLs.");
                }
            }
