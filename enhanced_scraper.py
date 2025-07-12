import requests
import json
import re
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
from datetime import datetime

class InstagramScraperEnhanced:
    def __init__(self, config_file="config.json"):
        self.load_config(config_file)
        self.session = requests.Session()
        
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Setup proxy
            if config["proxy"]["enabled"]:
                proxy_url = f"http://{config['proxy']['username']}:{config['proxy']['password']}@{config['proxy']['host']}:{config['proxy']['port']}"
                self.proxy_config = {
                    "http": proxy_url,
                    "https": proxy_url
                }
            else:
                self.proxy_config = None
            
            self.headers = config["headers"]
            self.delays = config["delays"]
            
        except FileNotFoundError:
            print("Config file not found, using default settings")
            self.setup_default_config()
        except Exception as e:
            print(f"Error loading config: {e}, using default settings")
            self.setup_default_config()
    
    def setup_default_config(self):
        """Setup default configuration"""
        self.proxy_config = {
            "http": "http://250621Ev04e-resi-any:5PjDM1IoS0JSr2c@proxy-jet.io:1010",
            "https": "http://250621Ev04e-resi-any:5PjDM1IoS0JSr2c@proxy-jet.io:1010"
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.delays = {
            "single_request": [1, 3],
            "bulk_request": [2, 5]
        }
        
    def validate_username(self, username):
        """Validate Instagram username format"""
        if username.startswith('http'):
            # Extract username from URL
            parsed = urlparse(username)
            path_parts = parsed.path.strip('/').split('/')
            if path_parts:
                return path_parts[0]
            return None
        
        # Clean username
        username = username.strip('@').strip()
        if re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
            return username
        return None
    
    def get_page_content(self, username):
        """Fetch Instagram profile page with rotating proxy"""
        url = f"https://www.instagram.com/{username}/"
        
        try:
            response = self.session.get(
                url, 
                headers=self.headers, 
                proxies=self.proxy_config,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"Failed to fetch {username}: Status code {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {username}: {str(e)}")
            return None
    
    def extract_json_data(self, html_content):
        """Extract JSON data from Instagram page scripts"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find script tags containing JSON data
        scripts = soup.find_all('script', type='text/javascript')
        
        for script in scripts:
            if script.string and 'window._sharedData' in script.string:
                # Extract shared data
                match = re.search(r'window\._sharedData\s*=\s*({.*?});', script.string)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError:
                        continue
                        
            elif script.string and '"ProfilePage"' in script.string:
                # Extract profile page data
                try:
                    json_text = script.string.strip()
                    if json_text.startswith('window._sharedData'):
                        json_text = json_text.split('=', 1)[1].rstrip(';')
                    return json.loads(json_text)
                except:
                    continue
        
        return None
    
    def extract_profile_data(self, html_content, username):
        """Extract all possible profile data from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        profile_data = {
            "username": username,
            "scraped_at": datetime.now().isoformat(),
            "profile_info": {},
            "meta_data": {},
            "post_data": [],
            "raw_data": {},
            "status": "success"
        }
        
        # Extract JSON data first
        json_data = self.extract_json_data(html_content)
        if json_data:
            profile_data["raw_data"]["json_data"] = json_data
            
            # Try to extract user data from various JSON structures
            try:
                if "entry_data" in json_data and "ProfilePage" in json_data["entry_data"]:
                    user_data = json_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
                    profile_data["profile_info"] = self.parse_user_data(user_data)
            except:
                pass
        
        # Extract meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            if meta.get('property'):
                profile_data["meta_data"][meta.get('property')] = meta.get('content')
            elif meta.get('name'):
                profile_data["meta_data"][meta.get('name')] = meta.get('content')
        
        # Extract title
        title = soup.find('title')
        if title:
            profile_data["meta_data"]["page_title"] = title.text.strip()
        
        # Extract any visible text data
        profile_data["extracted_text"] = self.extract_text_data(soup)
        
        # Look for specific Instagram elements
        profile_data["instagram_elements"] = self.extract_instagram_elements(soup)
        
        # Try to extract profile info from meta tags if JSON failed
        if not profile_data["profile_info"]:
            profile_data["profile_info"] = self.extract_from_meta_tags(profile_data["meta_data"])
        
        return profile_data
    
    def parse_user_data(self, user_data):
        """Parse user data from JSON"""
        return {
            "id": user_data.get("id"),
            "username": user_data.get("username"),
            "full_name": user_data.get("full_name"),
            "biography": user_data.get("biography"),
            "external_url": user_data.get("external_url"),
            "follower_count": user_data.get("edge_followed_by", {}).get("count"),
            "following_count": user_data.get("edge_follow", {}).get("count"),
            "post_count": user_data.get("edge_owner_to_timeline_media", {}).get("count"),
            "profile_pic_url": user_data.get("profile_pic_url_hd"),
            "is_verified": user_data.get("is_verified"),
            "is_private": user_data.get("is_private"),
            "is_business_account": user_data.get("is_business_account"),
            "business_category": user_data.get("business_category_name"),
            "category": user_data.get("category_name"),
            "connected_fb_page": user_data.get("connected_fb_page"),
        }
    
    def extract_from_meta_tags(self, meta_data):
        """Extract profile info from meta tags"""
        profile_info = {}
        
        # Extract from OpenGraph tags
        if "og:title" in meta_data:
            title = meta_data["og:title"]
            # Try to extract username and full name
            if "(@" in title:
                parts = title.split("(@")
                if len(parts) == 2:
                    profile_info["full_name"] = parts[0].strip()
                    profile_info["username"] = parts[1].rstrip(")").strip()
        
        if "og:description" in meta_data:
            profile_info["biography"] = meta_data["og:description"]
        
        if "og:image" in meta_data:
            profile_info["profile_pic_url"] = meta_data["og:image"]
        
        return profile_info
    
    def extract_text_data(self, soup):
        """Extract all relevant text data from the page"""
        text_data = {}
        
        # Extract from specific selectors commonly used by Instagram
        selectors = [
            'h1', 'h2', 'span', 'div[class*="count"]', 
            'div[class*="bio"]', 'div[class*="name"]',
            'a[href*="followers"]', 'a[href*="following"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                text_data[selector] = [elem.get_text(strip=True) for elem in elements if elem.get_text(strip=True)]
        
        return text_data
    
    def extract_instagram_elements(self, soup):
        """Extract Instagram-specific elements and attributes"""
        instagram_data = {}
        
        # Look for data attributes
        elements_with_data = soup.find_all(attrs={"data-testid": True})
        for elem in elements_with_data:
            testid = elem.get("data-testid")
            instagram_data[f"testid_{testid}"] = {
                "tag": elem.name,
                "text": elem.get_text(strip=True),
                "attributes": dict(elem.attrs)
            }
        
        # Look for role attributes
        elements_with_roles = soup.find_all(attrs={"role": True})
        for elem in elements_with_roles:
            role = elem.get("role")
            if role not in instagram_data:
                instagram_data[f"role_{role}"] = []
            instagram_data[f"role_{role}"].append({
                "tag": elem.name,
                "text": elem.get_text(strip=True)[:200],  # Limit text length
                "attributes": dict(elem.attrs)
            })
        
        return instagram_data
    
    def save_results(self, data, username):
        """Save results to JSON file"""
        # Create results directory if it doesn't exist
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        
        filename = os.path.join(results_dir, f"{username}_profile_data.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✓ Data saved to {filename}")
        
        # Also save HTML for debugging if requested
        if "raw_html" in data:
            html_filename = os.path.join(results_dir, f"{username}_raw.html")
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(data["raw_html"])
            print(f"✓ Raw HTML saved to {html_filename}")
    
    def scrape_profile(self, username_input, save_html=True):
        """Main scraping function for a single profile"""
        username = self.validate_username(username_input)
        if not username:
            print(f"✗ Invalid username format: {username_input}")
            return None
        
        print(f"🔍 Scraping profile: {username}")
        
        # Add random delay to avoid rate limiting
        delay = random.uniform(*self.delays["single_request"])
        time.sleep(delay)
        
        html_content = self.get_page_content(username)
        if not html_content:
            return None
        
        # Extract all data
        profile_data = self.extract_profile_data(html_content, username)
        
        if save_html:
            profile_data["raw_html"] = html_content
        
        # Save results
        self.save_results(profile_data, username)
        
        return profile_data
    
    def scrape_bulk_profiles(self, usernames, save_html=False):
        """Scrape multiple profiles"""
        results = {}
        total = len(usernames)
        
        print(f"🚀 Starting bulk scrape of {total} profiles...")
        
        for i, username_input in enumerate(usernames, 1):
            try:
                print(f"\n[{i}/{total}] Processing: {username_input}")
                result = self.scrape_profile(username_input, save_html)
                if result:
                    results[result["username"]] = result
                    print(f"✓ Successfully scraped: {result['username']}")
                else:
                    print(f"✗ Failed to scrape: {username_input}")
                    
                # Add delay between requests for bulk operations
                if i < total:  # Don't delay after the last request
                    delay = random.uniform(*self.delays["bulk_request"])
                    print(f"⏳ Waiting {delay:.1f}s before next request...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"✗ Error scraping {username_input}: {str(e)}")
                continue
        
        # Save bulk results
        if results:
            results_dir = "results"
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
                
            bulk_filename = os.path.join(results_dir, f"bulk_scrape_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(bulk_filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n🎉 Bulk results saved to {bulk_filename}")
            print(f"📊 Successfully scraped {len(results)}/{total} profiles")
        
        return results

def main():
    print("=" * 60)
    print("🔥 INSTAGRAM PROFILE SCRAPER WITH ROTATING PROXY 🔥")
    print("=" * 60)
    
    scraper = InstagramScraperEnhanced()
    
    print("\nSelect an option:")
    print("1️⃣  Single username")
    print("2️⃣  Bulk usernames (comma-separated)")
    print("3️⃣  Load usernames from file")
    print("4️⃣  Test sample usernames")
    
    choice = input("\n👉 Enter your choice (1-4): ").strip()
    
    if choice == "1":
        username = input("\n📝 Enter username or URL: ").strip()
        save_html = input("💾 Save raw HTML? (y/n): ").lower().startswith('y')
        scraper.scrape_profile(username, save_html)
        
    elif choice == "2":
        usernames_input = input("\n📝 Enter usernames separated by commas: ").strip()
        usernames = [u.strip() for u in usernames_input.split(",") if u.strip()]
        save_html = input("💾 Save raw HTML for each profile? (y/n): ").lower().startswith('y')
        scraper.scrape_bulk_profiles(usernames, save_html)
        
    elif choice == "3":
        filename = input("\n📁 Enter filename containing usernames (one per line): ").strip()
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                usernames = [line.strip() for line in f if line.strip()]
            save_html = input("💾 Save raw HTML for each profile? (y/n): ").lower().startswith('y')
            scraper.scrape_bulk_profiles(usernames, save_html)
        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
        except Exception as e:
            print(f"❌ Error reading file: {str(e)}")
    
    elif choice == "4":
        print("\n🧪 Testing with sample usernames...")
        sample_usernames = ["champagnepapi", "instagram", "cristiano"]
        scraper.scrape_bulk_profiles(sample_usernames, False)
    
    else:
        print("❌ Invalid option selected.")

if __name__ == "__main__":
    main()
