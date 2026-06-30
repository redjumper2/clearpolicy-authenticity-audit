import requests
from openai import OpenAI
import time

# --- CONFIGURATION ---
# Paste your official Regulations.gov API key between the quotes below:
API_KEY = "YOUR_API_KEY_HERE" 
# ---------------------

# Initialize local LLM connection (Assuming a local server like LM Studio/Ollama on port 8080)
client = OpenAI(base_url="http://localhost:8080/v1", api_key="not-needed")

print("Establishing secure connection to Regulations.gov API...")

# Fetch recent comments mentioning "broadband" as a sample dataset
search_url = f"https://api.regulations.gov/v4/comments?filter[searchTerm]=broadband&sort=-postedDate&api_key={API_KEY}"
response = requests.get(search_url)

if response.status_code == 200:
    comment_data = response.json().get('data', [])[:3]
    print(f"Successfully pulled {len(comment_data)} live government dockets. Initiating AI Analysis...\n")
    print("="*60)
    
    # Create or overwrite the report file with a clean header
    with open("authenticity_report.md", "w", encoding="utf-8") as f:
        f.write("# ClearPolicy Task #2: Authenticity Audit Report\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")

    for item in comment_data:
        comment_id = item['id']
        details_url = f"https://api.regulations.gov/v4/comments/{comment_id}?api_key={API_KEY}"
        details_response = requests.get(details_url)
        
        if details_response.status_code == 200:
            details_json = details_response.json().get('data', {})
            attributes = details_json.get('attributes', {})
            comment_text = attributes.get('comment', 'No text provided.')
            
            if len(comment_text) > 800:
                comment_text = comment_text[:800] + "... [TRUNCATED]"
                
            print(f"Docket ID: {comment_id}")
            print(f"Raw Text from Web: {comment_text}\n")
            print("--- ClearPolicy Authenticity Check ---")
            
            prompt = f"""
            You are ClearPolicy's Authenticity AI. Read this public comment submitted to a US government agency.
            Determine if it sounds like a template/bot (repetitive corporate language, overly formal phrasing with no personal anecdote) OR a real human (uses personal pronouns, mentions specific personal impacts, uses natural language).
            
            Respond in this exact format:
            STATUS: [Likely Bot / Likely Human]
            REASON: [1 sentence explaining why]
            
            Comment Text: "{comment_text}"
            """
            
            try:
                llm_response = client.chat.completions.create(
                    model="local-model",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2 
                )
                verdict = llm_response.choices[0].message.content.strip()
                print(verdict)
                
                # Append the audited data directly to the Markdown report
                with open("authenticity_report.md", "a", encoding="utf-8") as f:
                    f.write(f"## Docket ID: {comment_id}\n")
                    f.write(f"**Raw Text Snippet:** {comment_text}\n\n")
                    f.write(f"### AI Analysis Verdict\n")
                    f.write(f"```text\n{verdict}\n```\n")
                    f.write("\n" + "-"*40 + "\n\n")
                    
            except Exception as e:
                print(f"LLM Error: {e}")
                
            print("\n" + "="*60 + "\n")
            time.sleep(1) # Rate limiting for the API
else:
    print(f"Failed to connect to government API. Status code: {response.status_code}")