from fastapi import FastAPI, Query
import httpx
import re

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://animecix.tv/",
    "Accept": "application/json, text/plain, */*"
}

@app.get("/")
def home():
    return {"status": "ok", "message": "Animecix Extractor Calisiyor"}

@app.get("/extract")
async def extract_tau(url: str = Query(..., description="Animecix Bolum URL'si")):
    title_match = re.search(r'/titles/(\d+)', url)
    season_match = re.search(r'/season/(\d+)', url)

    if not title_match:
        return {"status": "error", "message": "Gecerli bir URL girilmedi"}

    title_id = title_match.group(1)
    season_num = season_match.group(1) if season_match else "1"

    api_url = f"https://animecix.tv/secure/titles/{title_id}?seasonNumber={season_num}"

    try:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=20.0) as client:
            res = await client.get(api_url)
            if res.status_code == 200:
                data = res.json()
                return {"status": "debug", "raw_data": data}
            else:
                return {"status": "error", "code": res.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}
        
