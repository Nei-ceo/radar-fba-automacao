import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def calcular_analise(preco_venda, preco_custo):
    comissao = preco_venda * 0.15
    imposto = preco_venda * 0.06
    taxa_fba = 13.00
    sobra = preco_venda - (comissao + imposto + taxa_fba)
    lucro = sobra - preco_custo
    roi = (lucro / preco_custo * 100) if preco_custo > 0 else 0
    return round(sobra, 2), round(lucro, 2), round(roi, 2)

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🔗 Acessando Utimix...")
        try:
            await page.goto("https://www.utimix.com/novidades/", timeout=60000)
            await page.wait_for_load_state("networkidle")
            
            produtos_brutos = await page.evaluate('''() => {
                const itens = Array.from(document.querySelectorAll('.product-item'));
                return itens.map(i => ({
                    nome: i.querySelector('.product-name a')?.innerText.trim(),
                    preco: i.querySelector('.price')?.innerText.replace('R$', '').trim() || "0"
                })).filter(x => x.nome).slice(0, 30);
            }''')
        except Exception as e:
            print(f"Erro na Utimix: {e}")
            await browser.close()
            return

        resultados = []
        for p_uti in produtos_brutos:
            try:
                custo = float(p_uti['preco'].replace('.', '').replace(',', '.'))
                if custo <= 0: continue

                print(f"🔍 Buscando: {p_uti['nome'][:30]}")
                search_url = f"https://www.amazon.com.br/s?k={p_uti['nome'].split('-')[0].strip()}"
                await page.goto(search_url, timeout=60000)
                
                preco_el = await page.query_selector('.a-price-whole')
                asin_el = await page.query_selector('[data-asin]')
                
                if preco_el and asin_el:
                    venda = float((await preco_el.inner_text()).replace('.', '').replace(',', '.').strip())
                    asin = await asin_el.get_attribute('data-asin')
                    
                    sobra, lucro, roi = await calcular_analise(venda, custo)
                    if lucro > 0:
                        resultados.append({
                            "titulo": p_uti['nome'][:60],
                            "venda_amazon": venda,
                            "custo_utimix": custo,
                            "lucro_liquido": lucro,
                            "roi": roi,
                            "link": f"https://www.amazon.com.br/dp/{asin}"
                        })
            except: continue

        with open("dados_fba.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
