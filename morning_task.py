import os
import json
import asyncio
import keyring
from datetime import datetime
from langchain_openai import ChatOpenAI
from browser_use import Agent

from dotenv import load_dotenv

# Load environmental variables from .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Get API Key from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in .env. Please set it first.")

# Initialize OpenAI LLM for browser-use (GPT-4o)
llm = ChatOpenAI(
    model="gpt-4o",
    api_key=OPENAI_API_KEY
)

TASK_PROMPT = """
You are a creative director and trend analyst for stock photography.
Your goal is to investigate current creative and stock photo trends for March 2026.
Please follow these steps:
1. Search the web for "Adobe Stock Inspiration blog trends 2026", "PIXTA trend report 2026", or just general "creative stock photography trends March 2026".
2. Browse a few relevant articles to understand what themes, colors, subjects, and concepts are currently in high demand.
3. Based on your research, summarize the top 3 highly demanded themes in English.
4. For each of these 3 themes, generate high-quality Midjourney prompts (a total of 10 prompts across the 3 themes). 
   Midjourney prompts must be in English, highly descriptive, comma-separated tags, including aspect ratio (e.g. --ar 3:2) and stylistic keywords (e.g. 8k, highly detailed, cinematic lighting, photorealistic).

Output your final response EXACTLY in the following format (and nothing else):

### Trend Summary Report ###
[Your 3 themes summary here]

### Midjourney Prompts ###
1. [Prompt 1]
2. [Prompt 2]
...
10. [Prompt 10]
"""

async def run_analysis():
    print(f"[{datetime.now()}] Starting morning trend analysis and prompt generation...")
    agent = Agent(
        task=TASK_PROMPT,
        llm=llm
    )
    
    result = await agent.run()
    
    # Process the result and save to output directory
    output_dir = os.path.join(os.path.dirname(__file__), '2_Output')
    os.makedirs(output_dir, exist_ok=True)
    
    date_str = datetime.now().strftime('%Y%m%d')
    output_file = os.path.join(output_dir, f'daily_trends_{date_str}.txt')
    
    if hasattr(result, 'final_result') and result.final_result:
        final_text = result.final_result()
    else:
        # Fallback if the agent returns a different structure
        final_text = str(result)
        
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_text)
        
    print(f"[{datetime.now()}] Successfully wrote trends and prompts to {output_file}")

if __name__ == "__main__":
    asyncio.run(run_analysis())
