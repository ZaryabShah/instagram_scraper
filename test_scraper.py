#!/usr/bin/env python3
"""
Test script to validate the updated Instagram scraper against the response.html file
"""

import os
import sys
from clean_scraper import CleanInstagramScraper

def test_with_local_html():
    """Test the scraper using the local HTML file"""
    scraper = CleanInstagramScraper()
    
    # Read the local HTML file
    html_file = "response.html"
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found!")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print("Testing updated scraper with local HTML file...")
    print("=" * 50)
    
    # Extract profile data
    username = "champagnepapi"
    profile_data = scraper.extract_profile_data(html_content, username)
    
    # Display results
    print(f"Username: {profile_data['username']}")
    print(f"Full Name: {profile_data['full_name']}")
    print(f"Biography: {profile_data['biography']}")
    print(f"Followers: {profile_data['follower_count']:,}" if profile_data['follower_count'] else "Followers: None")
    print(f"Following: {profile_data['following_count']:,}" if profile_data['following_count'] else "Following: None")
    print(f"Posts: {profile_data['post_count']:,}" if profile_data['post_count'] else "Posts: None")
    print(f"Profile Picture URL: {profile_data['profile_pic_url']}")
    print(f"Verified: {profile_data['is_verified']}")
    print(f"Private: {profile_data['is_private']}")
    print(f"Business: {profile_data['is_business']}")
    print(f"External URL: {profile_data['external_url']}")
    print(f"Scraped at: {profile_data['scraped_at']}")
    
    # Save test results
    filename = scraper.save_profile_data(profile_data, username)
    print(f"\nTest results saved to: {filename}")
    
    return profile_data

if __name__ == "__main__":
    test_with_local_html()
