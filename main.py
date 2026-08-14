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
    found_links = set()
    
    title_match = re.search(r'/titles/(\d+)', url)
    season_match = re.search(r'/season/(\d+)', url)
    episode_match = re.search(r'/episode/(\d+)', url)

    if not title_match or not episode_match:
        return {"status": "error", "message": "Gecerli bir URL girilmedi", "links": []}

    title_id = title_match.group(1)
    season_num = season_match.group(1) if season_match else "1"
    episode_num = episode_match.group(1)

    api_url = f"https://animecix.tv/secure/titles/{title_id}?seasonNumber={season_num}"

    try:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=20.0) as client:
            res = await client.get(api_url)
            
            if res.status_code == 200:
                raw_text = res.text
                
                # 1. Metin içindeki doğrudan Tau/Takurox/Sibnet/CDN URL'lerini yakala
                direct_urls = re.findall(r'https?://[^\s"\']*(?:tau-video|takurox|sibnet|vidmoly)[^\s"\']*', raw_text)
                for u in direct_urls:
                    found_links.add(u.replace("\\", ""))

                # 2. Metin içindeki 24 haneli Tau embed ID'lerini yakala
                tau_ids = re.findall(r'[a-f0-9]{24}', raw_text)
                for t_id in tau_ids:
                    found_links.add(f"https://tau-video.xyz/embed/{t_id}")

            else:
                return {"status": "error", "message": f"API HTTP {res.status_code}", "links": []}

    except Exception as e:
        return {"status": "error", "message": str(e), "links": []}

    clean_links = list(found_links)
    return {
        "status": "success" if clean_links else "error",
        "url": url,
        "count": len(clean_links),
        "links": clean_links
    }
    
