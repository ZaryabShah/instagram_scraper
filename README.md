# Instagram Profile Scraper

A comprehensive Instagram profile scraper that extracts all available profile data using rotating proxies.

## Features

- ✅ Single username scraping
- ✅ Bulk username processing
- ✅ URL input support (direct Instagram URLs)
- ✅ Rotating proxy support
- ✅ Comprehensive data extraction
- ✅ JSON output format
- ✅ Raw HTML backup
- ✅ Rate limiting protection
- ✅ Error handling and validation

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Run the scraper:
```bash
python simple.py
```

### Options:

1. **Single Username**: Enter one username or Instagram URL
2. **Bulk Usernames**: Enter multiple usernames separated by commas
3. **File Input**: Load usernames from a text file (one per line)

### Input Formats Supported:

- `username` - Plain username
- `@username` - Username with @ symbol
- `https://www.instagram.com/username/` - Full Instagram URL
- `https://instagram.com/username` - Short Instagram URL

## Data Extracted

The scraper extracts comprehensive profile data including:

### Profile Information:
- User ID
- Username
- Full name
- Biography
- External URL
- Follower count
- Following count
- Post count
- Profile picture URL
- Verification status
- Privacy status
- Business account status
- Business category
- Connected Facebook page

### Additional Data:
- Meta tags
- Page title
- Raw JSON data from Instagram
- Instagram-specific elements
- All visible text content
- HTML attributes and data

## Output Files

For each scraped profile, the following files are generated:

- `{username}_profile_data.json` - Complete profile data in JSON format
- `{username}_raw.html` - Raw HTML for debugging
- `bulk_scrape_results_{timestamp}.json` - Combined results for bulk operations

## Proxy Configuration

The scraper uses rotating proxies with the provided credentials:
- Proxy: `proxy-jet.io:1010`
- Credentials: `250621Ev04e-resi-any:5PjDM1IoS0JSr2c`

## Rate Limiting

- Random delays between 1-3 seconds for single requests
- Random delays between 2-5 seconds for bulk requests
- Proper error handling and retries

## Example Output Structure

```json
{
  "username": "champagnepapi",
  "scraped_at": "2025-07-13T...",
  "profile_info": {
    "id": "...",
    "username": "champagnepapi",
    "full_name": "...",
    "biography": "...",
    "follower_count": 123456,
    "following_count": 789,
    "post_count": 456,
    "is_verified": true,
    "is_private": false
  },
  "meta_data": {
    "og:title": "...",
    "og:description": "...",
    "og:image": "..."
  },
  "extracted_text": {...},
  "instagram_elements": {...},
  "raw_data": {...}
}
```

## Error Handling

- Invalid username format validation
- Network request error handling
- JSON parsing error handling
- File I/O error handling
- Rate limiting protection

## Notes

- This scraper is for educational purposes
- Respect Instagram's robots.txt and terms of service
- Use responsibly and don't overload Instagram's servers
- Consider Instagram's rate limiting policies
#   i n s t a g r a m _ s c r a p e r  
 