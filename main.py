from fastapi import FastAPI, Query
from playwright.async_api import async_playwright
import re

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok", "message": "Animecix Tau-Video Extractor API Calisiyor!"}

@app.get("/extract")
async def extract_tau(url: str = Query(..., description="Animecix Bolum URL'si")):
    found_links = set()

    async with async_playwright() as p:
        # Cloudflare engelini aşmak için headless tarayıcıyı başlatıyoruz
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Arka planda geçen ağ trafiğinde tau-video ve takurox URL'lerini yakala
        def handle_request(request):
            req_url = request.url
            if "tau-video" in req_url or "takurox" in req_url:
                found_links.add(req_url)

        page.on("request", handle_request)

        try:
            # Sayfaya git ve ağ trafiğinin oturmasını bekle
            await page.goto(url, wait_until="networkidle", timeout=35000)
            
            # Sayfanın kaynak kodundaki 24 haneli Tau ID'lerini de tara
            content = await page.content()
            tau_ids = re.findall(r'[a-f0-9]{24}', content)
            for t_id in tau_ids:
                found_links.add(f"https://tau-video.xyz/embed/{t_id}")

        except Exception as e:
            print(f"Hata olustu: {e}")
        finally:
            await browser.close()

    # Linkleri temizle ve filtrelere uygun olanları al
    clean_links = list(set([l for l in found_links if "/embed/" in l or "takurox" in l or "tau-video" in l]))

    return {
        "status": "success" if clean_links else "error",
        "url": url,
        "count": len(clean_links),
        "links": clean_links
    }
  
