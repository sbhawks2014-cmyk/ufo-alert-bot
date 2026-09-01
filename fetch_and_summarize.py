import os
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from google import genai

FEED_URL = "https://nuforc.org/feed/"

FEED_URL = "https://nuforc-sightings-database-api.herokuapp.com/sightings/today/rss.xml"

def fetch_ufo_reports():
    print("Fetching UAP reports...")
    req = urllib.request.Request(FEED_URL, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            reports = []
            for item in root.findall('.//item')[:5]:
                title = item.find('title').text if item.find('title') is not None else "Unknown Sighting"
                description = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                
                # Extract photo or video URLs inside the report description
                media_urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', description)
                image_links = [url for url in media_urls if any(ext in url.lower() for ext in ['.jpg', '.png', '.jpeg', 'imgur', 'youtube', 'vimeo'])]

                reports.append({
                    "title": title, 
                    "description": description, 
                    "link": link,
                    "media_found": image_links
                })
            return reports
    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return []

# 2. Summarize reports using Gemini with Credibility, Flags, and Media Links
def summarize_with_gemini(reports):
    if not reports:
        return "# Daily UAP Alert\n\nNo new official sightings recorded today."

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    prompt = f"""
    You are an expert UAP and aerospace verification analyst. Review these raw UFO/UAP reports:
    {json.dumps(reports, indent=2)}

    Format the output into a clean Markdown bulletin:
    1. A headline summarizing today's overall activity.
    2. A bulleted entry for each sighting featuring:
       - **Location & Observed Shape**
       - **Summary:** A 2-sentence plain-English recap.
       - **Credibility Score (1-10):** Assign a score based on details provided.
       - **Identification Flag:** (Starlink, Drone, Aircraft, or Unexplained Anomaly).
       - **Evidence / Media:** If 'media_found' has links, format them as Markdown image links `![Witness Image](url)` or video links. If empty, write "No direct media attached."
       - **Original Link**
    Keep it concise, analytical, and mobile-friendly.
    """

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt
    )
    return response.text

if __name__ == "__main__":
    reports = fetch_ufo_reports()
    summary = summarize_with_gemini(reports)
    
    with open("ufo_daily_digest.md", "w") as f:
        f.write(summary)
        
    print("Digest with Media Extraction successfully generated!")

        

