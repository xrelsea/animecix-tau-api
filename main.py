from fastapi import FastAPI, Query
import httpx
import re
import json

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
async def extract_tau(url: str = Query(..., description="Animecix URL'si")):
    found_links = set()
    
    # URL'den sadece Title ID'yi çek (Örn: /titles/7511 -> 7511)
    title_match = re.search(r'/titles/(\d+)', url)
    if not title_match:
        return {"status": "error", "message": "Gecerli Title ID bulunamadi", "links": []}

    title_id = title_match.group(1)
    
    # Animecix'in tum bolum ve video verilerini veren ana API ucu
    api_url = f"https://animecix.tv/secure/titles/{title_id}"

    try:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=25.0) as client:
            res = await client.get(api_url)
            
            if res.status_code == 200:
                raw_text = res.text
                
                # 1. Metin icindeki dogrudan Tau / Takurox / CDN iframe URL'lerini cımbızla
                direct_urls = re.findall(r'https?://[^\s"\']*(?:tau-video|takurox|sibnet|vidmoly)[^\s"\']*', raw_text)
                for u in direct_urls:
                    # JSON kacıs karakterlerini (\/) temizle
                    clean_u = u.replace("\\", "").rstrip('",;')
                    found_links.add(clean_u)

                # 2. Metin icindeki 24 haneli Tau ID'lerini yakala ve embed URL yap
                tau_ids = re.findall(r'[a-f0-9]{24}', raw_text)
                for t_id in tau_ids:
                    found_links.add(f"https://tau-video.xyz/embed/{t_id}")

            else:
                return {"status": "error", "message": f"Animecix API HTTP {res.status_code}", "links": []}

    except Exception as e:
        return {"status": "error", "message": str(e), "links": []}

    clean_links = list(found_links)
    return {
        "status": "success" if clean_links else "error",
        "title_id": title_id,
        "count": len(clean_links),
        "links": clean_links
    }
    
