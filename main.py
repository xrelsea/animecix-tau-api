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
    found_links = []

    # Title ID çıkar
    title_match = re.search(r'/titles/(\d+)', url)
    if not title_match:
        return {"status": "error", "message": "Gecerli Title ID bulunamadi", "links": []}

    title_id = title_match.group(1)
    api_url = f"https://animecix.tv/secure/titles/{title_id}"

    try:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30.0) as client:
            res = await client.get(api_url)
            
            if res.status_code == 200:
                data = res.json()
                # Animecix yapısına göre title veya ana objeden videoları al
                title_obj = data.get("title", {}) if isinstance(data, dict) else {}
                videos = title_obj.get("videos", []) or data.get("videos", []) or []

                # Eğer videolar dizisi sağlamsa, her video ID'si için Tau linkini derinlemesine çek
                for vid in videos:
                    v_id = vid.get("id")
                    v_name = vid.get("name") or vid.get("number") or "Bölüm"
                    
                    if v_id:
                        v_res = await client.get(f"https://animecix.tv/secure/videos/{v_id}")
                        if v_res.status_code == 200:
                            v_text = v_res.text
                            # 24 haneli Tau ID'leri
                            tau_ids = re.findall(r'[a-f0-9]{24}', v_text)
                            for t_id in tau_ids:
                                found_links.append({"ep": str(v_name), "link": f"https://tau-video.xyz/embed/{t_id}"})
                            
                            # Doğrudan Tau/Takurox URL'leri
                            raw_urls = re.findall(r'https?://[^\s"\']*(?:tau-video|takurox)[^\s"\']*', v_text)
                            for u in raw_urls:
                                found_links.append({"ep": str(v_name), "link": u.replace("\\", "").rstrip('",;')})

            else:
                return {"status": "error", "message": f"API HTTP {res.status_code}", "links": []}

    except Exception as e:
        return {"status": "error", "message": str(e), "links": []}

    # Çift kayıtları temizle
    unique_links = []
    seen = set()
    for item in found_links:
        if item["link"] not in seen:
            seen.add(item["link"])
            unique_links.append(item)

    return {
        "status": "success" if unique_links else "error",
        "title_id": title_id,
        "count": len(unique_links),
        "links": unique_links
    }
    
