# Instagram Profile Scraper - Updated for 2024

## Overview

This Instagram profile scraper has been updated to work with Instagram's current page structure (as of 2024). Instagram has moved away from the `window._sharedData` JavaScript object and now primarily uses meta tags for profile information.

## ✅ What's Working

The updated scraper can successfully extract:

- **Username**: Account username
- **Biography**: Profile description/bio text
- **Follower Count**: Number of followers (supports M/K formatting)
- **Following Count**: Number of accounts followed
- **Post Count**: Number of posts
- **Profile Picture URL**: High-resolution profile picture
- **Account Status**: Private/public detection
- **Profile URL**: Instagram profile link

## 🔄 Key Changes Made

### 1. **Meta Tag Extraction (Primary Method)**
- Switched from JSON parsing to meta tag extraction
- Uses `og:description` and `description` meta tags
- Parses formatted numbers (142M → 142,000,000)

### 2. **Improved Number Parsing**
```python
def parse_count(self, count_str):
    """Convert Instagram's formatted numbers (142M, 3.5K) to integers"""
    if count_str.endswith('M'):
        return int(float(count_str[:-1]) * 1000000)
    elif count_str.endswith('K'):
        return int(float(count_str[:-1]) * 1000)
    # etc...
```

### 3. **Fallback Support**
- Still supports old `window._sharedData` structure for compatibility
- Multiple extraction methods for reliability

### 4. **Enhanced Error Handling**
- Better handling of missing data
- Graceful degradation when certain fields aren't available

## 📋 Data Structure

```json
{
  "username": "champagnepapi",
  "full_name": null,
  "biography": "@stake stake.com @officialnocta @octobersveryown...",
  "follower_count": 142000000,
  "following_count": 3512,
  "post_count": 582,
  "profile_pic_url": "https://scontent.cdninstagram.com/v/t51.2885-19/...",
  "external_url": null,
  "is_verified": null,
  "is_private": false,
  "is_business": null,
  "scraped_at": "2024-01-15T12:34:56.789"
}
```

## 🚀 Usage

### Single Profile
```python
from clean_scraper import CleanInstagramScraper

scraper = CleanInstagramScraper()
result = scraper.scrape_profile("champagnepapi")

if "error" not in result:
    print(f"Followers: {result['follower_count']:,}")
    print(f"Biography: {result['biography']}")
```

### Bulk Profiles
```python
usernames = ["champagnepapi", "instagram", "natgeo"]
results = scraper.scrape_bulk_profiles(usernames)

for username, data in results.items():
    if "error" not in data:
        print(f"{username}: {data['follower_count']:,} followers")
```

### Test with Local HTML
```python
# For testing with saved HTML files
python test_scraper.py
python comprehensive_test.py
```

## 🔍 How It Works

1. **Fetches Profile Page**: Gets HTML content from Instagram profile URL
2. **Meta Tag Parsing**: Extracts data from `og:description` and similar tags
3. **Pattern Matching**: Uses regex to parse follower counts, bio, etc.
4. **JSON Fallback**: Falls back to old JSON structure if available
5. **Data Cleaning**: Converts formatted numbers and cleans text

## 📊 Test Results

When tested with Drake's profile (@champagnepapi):
- ✅ **Username**: champagnepapi
- ✅ **Followers**: 142,000,000 (parsed from "142M")
- ✅ **Following**: 3,512
- ✅ **Posts**: 582
- ✅ **Biography**: Full bio text extracted
- ✅ **Profile Picture**: High-res URL extracted
- ✅ **Account Status**: Correctly identified as public

## 🛠️ Technical Details

### Meta Tag Structure
Instagram now uses this structure:
```html
<meta property="og:description" content="142M Followers, 3,512 Following, 582 Posts - See Instagram photos and videos from @champagnepapi" />
<meta content="142M Followers, 3,512 Following, 582 Posts - @champagnepapi on Instagram: &quot;@stake stake.com...&quot;" name="description" />
```

### Number Parsing
The scraper handles Instagram's formatting:
- `142M` → `142,000,000`
- `3.5K` → `3,500`
- `1.2B` → `1,200,000,000`

## ⚠️ Important Notes

1. **Rate Limiting**: Use delays between requests to avoid being blocked
2. **Proxy Support**: Included in the scraper for better reliability
3. **Error Handling**: Always check for errors in response
4. **Instagram Changes**: May need updates if Instagram changes structure again

## 📁 Files

- `clean_scraper.py` - Main scraper with updated logic
- `test_scraper.py` - Test with local HTML file
- `comprehensive_test.py` - Full functionality test
- `usage_example.py` - Usage examples
- `response.html` - Sample Instagram profile page for testing

## 🔮 Future Improvements

- Add support for extracting external links
- Improve full name detection
- Add business account detection
- Support for story highlights count
- Better verified badge detection

The scraper is now compatible with Instagram's current page structure and successfully extracts all key profile metrics!
