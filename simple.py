import requests
import json
import re
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
from datetime import datetime

class InstagramScraper:
    def __init__(self):
        self.session = requests.Session()
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
            "raw_data": {}
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
        filename = f"{username}_profile_data.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")
        
        # Also save HTML for debugging
        if "raw_html" in data:
            html_filename = f"{username}_raw.html"
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(data["raw_html"])
            print(f"Raw HTML saved to {html_filename}")
    
    def scrape_profile(self, username_input):
        """Main scraping function for a single profile"""
        username = self.validate_username(username_input)
        if not username:
            print(f"Invalid username format: {username_input}")
            return None
        
        print(f"Scraping profile: {username}")
        
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        html_content = self.get_page_content(username)
        if not html_content:
            return None
        
        # Extract all data
        profile_data = self.extract_profile_data(html_content, username)
        profile_data["raw_html"] = html_content
        
        # Save results
        self.save_results(profile_data, username)
        
        return profile_data
    
    def scrape_bulk_profiles(self, usernames):
        """Scrape multiple profiles"""
        results = {}
        
        for username_input in usernames:
            try:
                result = self.scrape_profile(username_input)
                if result:
                    results[result["username"]] = result
                    print(f"✓ Successfully scraped: {result['username']}")
                else:
                    print(f"✗ Failed to scrape: {username_input}")
                    
                # Add delay between requests
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                print(f"Error scraping {username_input}: {str(e)}")
                continue
        
        # Save bulk results
        if results:
            bulk_filename = f"bulk_scrape_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(bulk_filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Bulk results saved to {bulk_filename}")
        
        return results

def main():
    scraper = InstagramScraper()
    
    print("Instagram Profile Scraper")
    print("=" * 40)
    print("Options:")
    print("1. Single username")
    print("2. Bulk usernames (comma-separated)")
    print("3. Load usernames from file")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        username = input("Enter username or URL: ").strip()
        scraper.scrape_profile(username)
        
    elif choice == "2":
        usernames_input = input("Enter usernames separated by commas: ").strip()
        usernames = [u.strip() for u in usernames_input.split(",") if u.strip()]
        scraper.scrape_bulk_profiles(usernames)
        
    elif choice == "3":
        filename = input("Enter filename containing usernames (one per line): ").strip()
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                usernames = [line.strip() for line in f if line.strip()]
            scraper.scrape_bulk_profiles(usernames)
        except FileNotFoundError:
            print(f"File not found: {filename}")
        except Exception as e:
            print(f"Error reading file: {str(e)}")
    
    else:
        print("Invalid option selected.")

if __name__ == "__main__":
    main()