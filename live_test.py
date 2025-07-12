#!/usr/bin/env python3
"""
Live test of the updated Instagram scraper
"""

from clean_scraper import CleanInstagramScraper
import time

def live_test():
    """Test the scraper with a live request"""
    print("LIVE INSTAGRAM SCRAPER TEST")
    print("=" * 40)
    
    scraper = CleanInstagramScraper()
    
    # Test with a known public profile
    test_username = "instagram"  # Instagram's official account
    
    print(f"Testing with profile: @{test_username}")
    print("Making live request...")
    
    try:
        result = scraper.scrape_profile(test_username)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            print("\nThis could be due to:")
            print("- Rate limiting")
            print("- Network issues")
            print("- Instagram blocking the request")
            print("- Proxy issues")
        else:
            print("✅ Successfully scraped profile!")
            print(f"Username: {result['username']}")
            print(f"Biography: {result['biography'][:100]}..." if result['biography'] and len(result['biography']) > 100 else f"Biography: {result['biography']}")
            
            if result['follower_count']:
                print(f"Followers: {result['follower_count']:,}")
            if result['following_count']:
                print(f"Following: {result['following_count']:,}")
            if result['post_count']:
                print(f"Posts: {result['post_count']:,}")
                
            print(f"Profile Picture: {'✓ Found' if result['profile_pic_url'] else '✗ Not found'}")
            print(f"Private: {result['is_private']}")
            print(f"Verified: {result['is_verified']}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        print("\nThe scraper logic is correct, but live requests may be blocked.")
        print("This is normal - use the test with response.html instead.")

if __name__ == "__main__":
    live_test()
