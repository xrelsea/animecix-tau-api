from fastapi import FastAPI, Query
from playwright.async_api import async_playwright
import re

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok", "message": "Animecix Extractor Calisiyor"}

@app.get("/extract")
async def extract_tau(url: str = Query(..., description="Animecix Bolum URL'si")):
    found_links = set()

    try:
        async with async_playwright() as p:
            # Render ortamında çökmemesi için gerekli sandbox parametreleri
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            # Ağ trafiğinde geçen tau-video / takurox isteklerini yakala
            def handle_request(request):
                req_url = request.url
                if "tau-video" in req_url or "takurox" in req_url:
                    found_links.add(req_url)

            page.on("request", handle_request)

            try:
                # Sayfaya git ve JS yuklenmesini bekle
                await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                await page.wait_for_timeout(5000)  # Ekstra 5 sn bekle (JS API isteklerini atsın)
                
                content = await page.content()
                tau_ids = re.findall(r'[a-f0-9]{24}', content)
                for t_id in tau_ids:
                    found_links.add(f"https://tau-video.xyz/embed/{t_id}")

            except Exception as e:
                print(f"Sayfa yukleme hatasi: {e}")
            finally:
                await browser.close()

    except Exception as e:
        print(f"Playwright hatasi: {e}")
        return {"status": "error", "message": str(e), "links": []}

    clean_links = list(set([l for l in found_links if "/embed/" in l or "takurox" in l or "tau-video" in l]))

    return {
        "status": "success" if clean_links else "error",
        "url": url,
        "count": len(clean_links),
        "links": clean_links
    }
    
