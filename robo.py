import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        url_utimix = "https://www.utimix.com/novidades/?utm_source=brevo&utm_campaign=Seguimento%20%201%20Pedido%20-%204%20envio&utm_medium=email&utm_id=22"
        
        print("🔗 Acessando Novidades Utimix...")
        try:
            await page.goto(url_utimix, wait_until="domcontentloaded", timeout=60000)
            await page.mouse.wheel(0, 1500)
            await asyncio.sleep(4)
            
            # Agora capturamos o NOME, PREÇO e a IMAGEM da Utimix
            produtos_utimix = await page.evaluate('''() => {
                const cards = Array.from(document.querySelectorAll('.product-item, .item, .product-card, div.product'));
                return cards.map(c => {
                    const nome = (c.querySelector('.product-name a, .name, h2, h3, .product-title')?.innerText || "").trim();
                    const preco = (c.querySelector('.price, .preco, .best-price')?.innerText || "").replace('R$', '').trim();
                    const img = c.querySelector('img')?.src || ""; // Captura a foto
                    return { nome, preco, img };
                }).filter(p => p.nome.length > 3 && p.preco && p.preco !== "0");
            }''')
            
            print(f"📦 Encontrados {len(produtos_utimix)} produtos para análise visual.")

            if len(produtos_utimix) == 0:
                await browser.close()
                return

        except Exception as e:
            print(f"❌ Erro Utimix: {e}")
            await browser.close()
            return

        resultados = []
        for item in produtos_utimix[:30]:
            try:
                termo_busca = item['nome'].split('-')[-1].strip()
                print(f"🔍 Buscando na Amazon: {termo_busca}")
                
                await page.goto(f"https://www.amazon.com.br/s?k={termo_busca.replace(' ', '+')}", wait_until="domcontentloaded")
                await asyncio.sleep(2)

                card = await page.query_selector(".s-result-item[data-asin]")
                if card:
                    asin = await card.get_attribute("data-asin")
                    preco_amz_el = await card.query_selector(".a-price-whole")
                    img_amz_el = await card.query_selector(".s-image") # Captura foto da Amazon
                    
                    if preco_amz_el and img_amz_el:
                        venda = float((await preco_amz_el.inner_text()).replace('.', '').replace(',', '.').strip())
                        custo = float(item['preco'].replace('.', '').replace(',', '.').strip())
                        img_amz = await img_amz_el.get_attribute("src")
                        
                        lucro = round(venda - custo - (venda * 0.15 + 13), 2)
                        
                        resultados.append({
                            "titulo": item['nome'][:60],
                            "venda_amazon": venda,
                            "custo_utimix": custo,
                            "lucro_liquido": lucro,
                            "roi": round((lucro / custo) * 100, 2) if custo > 0 else 0,
                            "link": f"https://www.amazon.com.br/dp/{asin}",
                            "img_utimix": item['img'], # Salva foto fornecedor
                            "img_amazon": img_amz # Salva foto concorrente
                        })
            except:
                continue

        with open("dados_fba.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        await browser.close()
        print(f"✅ Análise concluída: {len(resultados)} cruzamentos gerados.")

if __name__ == "__main__":
    asyncio.run(run())
