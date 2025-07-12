import requests
import json
import re
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
from datetime import datetime

class CleanInstagramScraper:
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
            "Connection": "keep-alive",
        }
        
    def validate_username(self, username):
        """Extract clean username from input"""
        if username.startswith('http'):
            parsed = urlparse(username)
            path_parts = parsed.path.strip('/').split('/')
            if path_parts:
                return path_parts[0]
            return None
        
        username = username.strip('@').strip()
        if re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
            return username
        return None
    
    def get_page_content(self, username):
        """Fetch Instagram profile page"""
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
                return None
                
        except requests.exceptions.RequestException:
            return None
    
    def parse_count(self, count_str):
        """Parse follower/following/post counts from Instagram format (e.g., 142M, 3.5K)"""
        if not count_str:
            return None
        
        count_str = count_str.replace(',', '').strip()
        
        if count_str.endswith('M'):
            return int(float(count_str[:-1]) * 1000000)
        elif count_str.endswith('K'):
            return int(float(count_str[:-1]) * 1000)
        elif count_str.endswith('B'):
            return int(float(count_str[:-1]) * 1000000000)
        else:
            try:
                return int(count_str)
            except ValueError:
                return None
    
    def extract_profile_data(self, html_content, username):
        """Extract only essential profile data"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize clean profile data structure
        profile_data = {
            "username": username,
            "full_name": None,
            "biography": None,
            "follower_count": None,
            "following_count": None,
            "post_count": None,
            "profile_pic_url": None,
            "external_url": None,
            "is_verified": None,
            "is_private": None,
            "is_business": None,
            "scraped_at": datetime.now().isoformat()
        }
        
        # First try to extract from meta tags (primary method for current Instagram)
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            content = meta.get('content', '')
            property_name = meta.get('property', '')
            name = meta.get('name', '')
            
            # Extract profile picture from og:image
            if property_name == 'og:image' and content:
                profile_data["profile_pic_url"] = content
            
            # Extract data from og:description or description meta tag
            elif (property_name == 'og:description' or name == 'description') and content:
                # Parse follower/following/posts from description
                # Format: "142M Followers, 3,512 Following, 582 Posts - ..."
                followers_match = re.search(r'([\d,]+[KMB]?)\s+Followers?', content, re.IGNORECASE)
                following_match = re.search(r'([\d,]+[KMB]?)\s+Following', content, re.IGNORECASE)
                posts_match = re.search(r'([\d,]+[KMB]?)\s+Posts?', content, re.IGNORECASE)
                
                if followers_match:
                    profile_data["follower_count"] = self.parse_count(followers_match.group(1))
                if following_match:
                    profile_data["following_count"] = self.parse_count(following_match.group(1))
                if posts_match:
                    profile_data["post_count"] = self.parse_count(posts_match.group(1))
                
                # Extract biography from description after the stats
                bio_match = re.search(r'@\w+ on Instagram: "(.*?)"', content)
                if bio_match:
                    bio_text = bio_match.group(1)
                    # Clean up HTML entities
                    bio_text = bio_text.replace('&#064;', '@').replace('&quot;', '"')
                    profile_data["biography"] = bio_text
        
        # Extract from JSON data in scripts (fallback method)
        if not profile_data["follower_count"]:
            scripts = soup.find_all('script', type='text/javascript')
            for script in scripts:
                if script.string and ('window._sharedData' in script.string or '"ProfilePage"' in script.string):
                    try:
                        # Try to extract JSON data
                        json_match = re.search(r'window\._sharedData\s*=\s*({.*?});', script.string)
                        if json_match:
                            json_data = json.loads(json_match.group(1))
                            profile_data.update(self.parse_json_data(json_data, username))
                            break
                    except:
                        continue
        
        # Try to detect account status from various indicators
        page_text = soup.get_text().lower()
        
        # Check if account is private
        if 'this account is private' in page_text or 'user is private' in page_text:
            profile_data["is_private"] = True
        else:
            profile_data["is_private"] = False
            
        # Check for verified badge indicators
        if 'verified' in page_text or '✓' in soup.get_text():
            profile_data["is_verified"] = True
            
        # Clean up full name - extract from title if not found
        if not profile_data["full_name"]:
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                title = title_tag.string
                # Remove "• Instagram photos and videos" and username
                if "•" in title:
                    potential_name = title.split("•")[0].strip()
                    if potential_name != username:
                        profile_data["full_name"] = potential_name
        
        return profile_data
    
    def parse_json_data(self, json_data, username):
        """Parse profile data from JSON (fallback method for older Instagram structure)"""
        data = {}
        
        try:
            # Navigate through possible JSON structures
            user_data = None
            
            # Try old _sharedData structure
            if "entry_data" in json_data and "ProfilePage" in json_data["entry_data"]:
                if json_data["entry_data"]["ProfilePage"]:
                    page_data = json_data["entry_data"]["ProfilePage"][0]
                    if "graphql" in page_data and "user" in page_data["graphql"]:
                        user_data = page_data["graphql"]["user"]
            
            # Try other possible structures
            elif "user" in json_data:
                user_data = json_data["user"]
            elif "data" in json_data and "user" in json_data["data"]:
                user_data = json_data["data"]["user"]
            
            if user_data:
                data["full_name"] = user_data.get("full_name")
                data["biography"] = user_data.get("biography")
                data["external_url"] = user_data.get("external_url")
                data["profile_pic_url"] = user_data.get("profile_pic_url_hd") or user_data.get("profile_pic_url")
                data["is_verified"] = user_data.get("is_verified")
                data["is_private"] = user_data.get("is_private")
                data["is_business"] = user_data.get("is_business_account") or user_data.get("is_business")
                
                # Extract counts from various possible structures
                if "edge_followed_by" in user_data:
                    data["follower_count"] = user_data["edge_followed_by"].get("count")
                elif "follower_count" in user_data:
                    data["follower_count"] = user_data["follower_count"]
                    
                if "edge_follow" in user_data:
                    data["following_count"] = user_data["edge_follow"].get("count")
                elif "following_count" in user_data:
                    data["following_count"] = user_data["following_count"]
                    
                if "edge_owner_to_timeline_media" in user_data:
                    data["post_count"] = user_data["edge_owner_to_timeline_media"].get("count")
                elif "media_count" in user_data:
                    data["post_count"] = user_data["media_count"]
        
        except Exception as e:
            # Silently ignore JSON parsing errors
            pass
        
        return data
    
    def save_profile_data(self, data, username):
        """Save clean profile data to JSON"""
        if not os.path.exists("profiles"):
            os.makedirs("profiles")
        
        filename = f"profiles/{username}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def scrape_profile(self, username_input):
        """Scrape a single profile and return clean data"""
        username = self.validate_username(username_input)
        if not username:
            return {"error": f"Invalid username: {username_input}"}
        
        html_content = self.get_page_content(username)
        if not html_content:
            return {"error": f"Failed to fetch profile: {username}"}
        
        profile_data = self.extract_profile_data(html_content, username)
        filename = self.save_profile_data(profile_data, username)
        
        return profile_data
    
    def scrape_bulk_profiles(self, usernames):
        """Scrape multiple profiles"""
        results = {}
        
        for username_input in usernames:
            username = self.validate_username(username_input)
            if username:
                print(f"Scraping: {username}")
                result = self.scrape_profile(username_input)
                results[username] = result
                
                # Add delay between requests
                time.sleep(random.uniform(2, 4))
            else:
                print(f"Invalid username: {username_input}")
        
        # Save bulk results
        if results:
            bulk_filename = f"profiles/bulk_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(bulk_filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Bulk results saved to: {bulk_filename}")
        
        return results

def main():
    scraper = CleanInstagramScraper()
    
    print("Instagram Profile Data Scraper")
    print("1. Single username")
    print("2. Bulk usernames (comma-separated)")
    print("3. Load from file")
    
    choice = input("Choose option (1-3): ").strip()
    
    if choice == "1":
        username = input("Enter username or URL: ").strip()
        result = scraper.scrape_profile(username)
        
        if "error" not in result:
            print("\nProfile Data:")
            print(f"Username: {result['username']}")
            print(f"Full Name: {result['full_name']}")
            print(f"Biography: {result['biography']}")
            print(f"Followers: {result['follower_count']}")
            print(f"Following: {result['following_count']}")
            print(f"Posts: {result['post_count']}")
            print(f"Verified: {result['is_verified']}")
            print(f"Private: {result['is_private']}")
            print(f"Business: {result['is_business']}")
        else:
            print(f"Error: {result['error']}")
            
    elif choice == "2":
        usernames_input = input("Enter usernames (comma-separated): ").strip()
        usernames = [u.strip() for u in usernames_input.split(",") if u.strip()]
        results = scraper.scrape_bulk_profiles(usernames)
        
        print(f"\nScraped {len(results)} profiles")
        for username, data in results.items():
            if "error" not in data:
                print(f"{username}: {data['full_name']} - {data['follower_count']} followers")
            else:
                print(f"{username}: {data['error']}")
                
    elif choice == "3":
        filename = input("Enter filename: ").strip()
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                usernames = [line.strip() for line in f if line.strip()]
            results = scraper.scrape_bulk_profiles(usernames)
            print(f"Processed {len(results)} profiles from file")
        except FileNotFoundError:
            print(f"File not found: {filename}")

if __name__ == "__main__":
    main()
