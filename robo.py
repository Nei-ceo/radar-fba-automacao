import asyncio
import sys
import json
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

URL_BASE_FORNECEDOR = "https://www.utimix.com/novidades/"

async def calcular_lucro(preco_venda):
    comissao = preco_venda * 0.15
    imposto = preco_venda * 0.06
    taxa_fba_est = 14.00 
    sobra_liquida = preco_venda - (comissao + imposto + taxa_fba_est)
    return round(sobra_liquida, 2)

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        itens_para_cruzar = []
        url_atual = URL_BASE_FORNECEDOR

        # PASSO 1: Varre TODAS as páginas da Utimix
        while url_atual:
            try:
                await page.goto(url_atual, wait_until="networkidle", timeout=60000)
                nomes = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('.product-name a')).map(n => n.innerText.trim());
                }''')
                itens_para_cruzar.extend(nomes)
                proxima_pag_el = await page.query_selector('a.next, .pagination .next a') 
                if proxima_pag_el:
                    url_atual = await proxima_pag_el.get_attribute('href')
                    if "http" not in url_atual: url_atual = "https://www.utimix.com" + url_atual
                else: url_atual = None
            except: break

        # PASSO 2: Cruza até 150 itens na Amazon
        resultados = []
        for item in itens_para_cruzar[:150]: 
            try:
                search_url = f"https://www.amazon.com.br/s?k={item.replace(' ', '+')}"
                await page.goto(search_url, wait_until="domcontentloaded")
                await asyncio.sleep(2) # Pausa anti-bloqueio

                prod = await page.query_selector('.s-result-item[data-asin]')
                if prod:
                    asin = await prod.get_attribute('data-asin')
                    selo = await prod.query_selector('.a-badge-text')
                    trending = "🔥 ALTA" if selo else "Normal"
                    titulo_el = await prod.query_selector('h2 span')
                    preco_el = await prod.query_selector('.a-price-whole')

                    if titulo_el and preco_el:
                        titulo = await titulo_el.inner_text()
                        preco_clean = (await preco_el.inner_text()).replace('\\n', '').replace('.', '').replace(',', '.').strip()
                        preco_venda = float(preco_clean)
                        sobra = await calcular_lucro(preco_venda)

                        if sobra > 15:
                            custo_est = preco_venda * 0.4
                            resultados.append({
                                "asin": asin,
                                "titulo": f"[{trending}] {titulo[:50]}",
                                "preco": preco_venda,
                                "sobra_fba": sobra,
                                "roi": round(((sobra - custo_est) / custo_est) * 100, 2),
                                "link": f"https://www.amazon.com.br/dp/{asin}"
                            })
            except: continue

        with open("dados_fba.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
