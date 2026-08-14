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
async def extract_tau(url: str = Query(..., description="Animecix URL'si")):
    found_links = set()

    # Double slash (//) ve URL hatalarini temizle
    clean_url = re.sub(r'(?<!:)/{2,}', '/', url)

    # Title ID bul
    title_match = re.search(r'/titles/(\d+)', clean_url)
    if not title_match:
        return {"status": "error", "message": "Gecerli Title ID bulunamadi", "links": []}

    title_id = title_match.group(1)
    
    # 1. Title bilgilerini çek
    api_url = f"https://animecix.tv/secure/titles/{title_id}"

    try:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=25.0) as client:
            res = await client.get(api_url)
            
            if res.status_code == 200:
                raw_text = res.text
                
                # Metin icindeki dogrudan Tau / Takurox / Embed ID'lerini tara
                tau_ids = re.findall(r'[a-f0-9]{24}', raw_text)
                for t_id in tau_ids:
                    found_links.add(f"https://tau-video.xyz/embed/{t_id}")

                direct_urls = re.findall(r'https?://[^\s"\']*(?:tau-video|takurox|sibnet|vidmoly)[^\s"\']*', raw_text)
                for u in direct_urls:
                    found_links.add(u.replace("\\", "").rstrip('",;'))

                # Eğer ana title yanıtında çıkmadıysa, video ID'lerini bulup sorgula
                video_ids = re.findall(r'"id":\s*"?(\d+)"?', raw_text)
                for vid in video_ids[:10]:  # Ilk 10 video ucu sorgula
                    v_res = await client.get(f"https://animecix.tv/secure/videos/{vid}")
                    if v_res.status_code == 200:
                        v_text = v_res.text
                        v_tau_ids = re.findall(r'[a-f0-9]{24}', v_text)
                        for t_id in v_tau_ids:
                            found_links.add(f"https://tau-video.xyz/embed/{t_id}")
                        
                        v_urls = re.findall(r'https?://[^\s"\']*(?:tau-video|takurox|sibnet|vidmoly)[^\s"\']*', v_text)
                        for u in v_urls:
                            found_links.add(u.replace("\\", "").rstrip('",;'))

            else:
                return {"status": "error", "message": f"API HTTP {res.status_code}", "links": []}

    except Exception as e:
        return {"status": "error", "message": str(e), "links": []}

    clean_links = list(found_links)
    return {
        "status": "success" if clean_links else "error",
        "title_id": title_id,
        "count": len(clean_links),
        "links": clean_links
    }
    
