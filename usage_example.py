
# Example: Using the Updated Instagram Scraper

from clean_scraper import CleanInstagramScraper

# Initialize scraper
scraper = CleanInstagramScraper()

# Scrape a single profile
result = scraper.scrape_profile("champagnepapi")

if "error" not in result:
    print(f"Username: {result['username']}")
    print(f"Followers: {result['follower_count']:,}")
    print(f"Following: {result['following_count']:,}")
    print(f"Posts: {result['post_count']:,}")
    print(f"Biography: {result['biography']}")
else:
    print(f"Error: {result['error']}")

# Scrape multiple profiles
usernames = ["champagnepapi", "instagram", "natgeo"]
results = scraper.scrape_bulk_profiles(usernames)

for username, data in results.items():
    if "error" not in data:
        print(f"{username}: {data['follower_count']:,} followers")
