import requests
import re
import argparse
import gzip
import io
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin
import sys

class SitemapExtractor:
    def __init__(self, target, include=None, exclude=None, file_type='all', verbose=True):
        self.target = target
        self.include = include.lower() if include else None
        self.exclude = exclude.lower() if exclude else None
        self.file_type = file_type
        self.verbose = verbose
        
        # Set to track unique URLs
        self.urls = set()
        self.visited_sitemaps = set()
        
        # Mock browser headers to avoid 403 blocks
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def log(self, message):
        if self.verbose:
            print(f"[LOG] {message}")

    def fetch_text(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                self.log(f"Failed to fetch {url} (Status: {response.status_code})")
                return None

            # Handle .gz files explicitly if content-type headers fail
            if url.endswith('.gz') or response.headers.get('content-type') == 'application/x-gzip':
                try:
                    return gzip.decompress(response.content).decode('utf-8')
                except Exception:
                    # Requests might have already decoded it
                    return response.text
            
            return response.text
        except Exception as e:
            self.log(f"Error fetching {url}: {e}")
            return None

    def discover_sitemap(self):
        url = self.target
        if not url.startswith("http"):
            url = "https://" + url

        # 1. If user provided a direct XML file
        if url.lower().endswith('.xml') or url.lower().endswith('.xml.gz'):
            return url

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # 2. Check robots.txt
        robots_url = urljoin(base_url, "robots.txt")
        self.log(f"Checking {robots_url}...")
        content = self.fetch_text(robots_url)

        if content:
            # Regex to find "Sitemap: <url>"
            match = re.search(r'Sitemap:\s*(https?://[^\s]+)', content, re.IGNORECASE)
            if match:
                found_map = match.group(1)
                self.log(f"Found Sitemap in robots.txt: {found_map}")
                return found_map

        # 3. Fallback
        fallback = urljoin(base_url, "sitemap.xml")
        self.log(f"No Sitemap directive found. Trying default: {fallback}")
        return fallback

    def parse_sitemap_recursive(self, url):
        if url in self.visited_sitemaps:
            return
        self.visited_sitemaps.add(url)
        
        self.log(f"Scanning: {url}")
        content = self.fetch_text(url)
        
        if not content:
            return

        try:
            # XML parsing (ignoring namespaces for simplicity)
            root = ET.fromstring(content)
            
            # Remove namespaces to make tag finding easier
            # (e.g., {http://www.sitemaps.org/schemas/sitemap/0.9}loc -> loc)
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]

            # Check if this is a Sitemap Index (contains other sitemaps)
            sitemaps = root.findall(".//sitemap/loc")
            
            if sitemaps:
                self.log(f"Found Index with {len(sitemaps)} sub-sitemaps. Digging deeper...")
                for sitemap in sitemaps:
                    if sitemap.text:
                        self.parse_sitemap_recursive(sitemap.text.strip())
            else:
                # Regular sitemap containing URLs
                urls = root.findall(".//url/loc")
                
                # Check for image sitemaps specifically
                images = root.findall(".//image/loc")
                
                count = 0
                for loc in urls + images:
                    if loc.text:
                        self.urls.add(loc.text.strip())
                        count += 1
                
                self.log(f"Extracted {count} URLs from {url}")

        except ET.ParseError:
            self.log(f"Failed to parse XML from {url}")
        except Exception as e:
            self.log(f"Unexpected error parsing {url}: {e}")

    def apply_filters(self):
        filtered_results = []
        
        img_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg', '.bmp', '.tiff')
        
        results_list = sorted(list(self.urls))

        for url in results_list:
            lower_url = url.lower()

            # Include Filter
            if self.include and self.include not in lower_url:
                continue
            
            # Exclude Filter
            if self.exclude and self.exclude in lower_url:
                continue

            # Type Filter
            if self.file_type == 'image':
                if not lower_url.endswith(img_extensions):
                    continue
            elif self.file_type == 'pdf':
                if not lower_url.endswith('.pdf'):
                    continue

            filtered_results.append(url)
        
        return filtered_results

    def run(self):
        master_sitemap = self.discover_sitemap()
        self.parse_sitemap_recursive(master_sitemap)
        
        final_list = self.apply_filters()
        
        print("\n" + "="*30)
        print(f"EXTRACTION COMPLETE")
        print(f"Total Unique URLs found: {len(self.urls)}")
        print(f"After Filters: {len(final_list)}")
        print("="*30 + "\n")
        
        return final_list

def save_to_csv(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("URL\n")
            for url in data:
                f.write(f"{url}\n")
        print(f"Successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python Sitemap Extractor")
    parser.add_argument("domain", help="Target domain or sitemap URL (e.g., example.com)")
    parser.add_argument("--include", help="Only keep URLs containing this string", default=None)
    parser.add_argument("--exclude", help="Drop URLs containing this string", default=None)
    parser.add_argument("--type", choices=['all', 'image', 'pdf'], default='all', help="Filter by content type")
    parser.add_argument("--output", help="Save results to a CSV file", default=None)
    parser.add_argument("--quiet", action="store_true", help="Suppress logs")

    args = parser.parse_args()

    extractor = SitemapExtractor(
        target=args.domain,
        include=args.include,
        exclude=args.exclude,
        file_type=args.type,
        verbose=not args.quiet
    )

    results = extractor.run()

    if args.output:
        save_to_csv(results, args.output)
    else:
        # Print to console if no file specified
        for url in results:
            print(url)
