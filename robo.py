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
            # Vai para a página e espera até que não haja atividade na rede
            await page.goto(url_utimix, wait_until="networkidle", timeout=60000)
            
            # Força o scroll para carregar todos os elementos visíveis
            print("📜 Rolando a página para carregar imagens e preços...")
            for _ in range(3):
                await page.mouse.wheel(0, 800)
                await asyncio.sleep(2)

            # Espera até que um produto específico seja visível no DOM
            await page.wait_for_selector('.product-item', timeout=15000)
            
            produtos_utimix = await page.evaluate('''() => {
                const cards = Array.from(document.querySelectorAll('.product-item'));
                return cards.map(c => {
                    const nome = (c.querySelector('.product-name a')?.innerText || "").trim();
                    const precoText = c.querySelector('.price')?.innerText || "";
                    // Limpa o texto do preço, ex: "A partir de: R$ 8,99" para "8,99"
                    const precoMatch = precoText.match(/R\\$\\s*([0-9.,]+)/);
                    const preco = precoMatch ? precoMatch[1].trim() : "0";
                    const img = c.querySelector('img')?.src || "";
                    return { nome, preco, img };
                }).filter(p => p.nome.length > 3 && p.preco !== "0");
            }''')
            
            print(f"📦 Encontrados {len(produtos_utimix)} produtos para análise visual.")

            if len(produtos_utimix) == 0:
                print("⚠️ Falha ao encontrar produtos após rolagem e espera.")
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
                
                await page.goto(f"https://www.amazon.com.br/s?k={termo_busca.replace(' ', '+')}", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)

                card = await page.query_selector(".s-result-item[data-asin]")
                if card:
                    asin = await card.get_attribute("data-asin")
                    preco_amz_el = await card.query_selector(".a-price-whole")
                    img_amz_el = await card.query_selector(".s-image")
                    
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
                            "img_utimix": item['img'],
                            "img_amazon": img_amz
                        })
            except Exception as e:
                print(f"Erro ao cruzar {item['nome']}: {e}")
                continue

        with open("dados_fba.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        await browser.close()
        print(f"✅ Análise concluída: {len(resultados)} cruzamentos gerados.")

if __name__ == "__main__":
    asyncio.run(run())
