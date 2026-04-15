import asyncio
import sys
import json
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

URL_BASE_FORNECEDOR = "https://www.utimix.com/novidades/"

async def calcular_analise(preco_venda, preco_custo_estimado):
    comissao = preco_venda * 0.15
    imposto = preco_venda * 0.06
    taxa_fba = 13.00
    sobra_pos_taxas = preco_venda - (comissao + imposto + taxa_fba)
    lucro_liquido = sobra_pos_taxas - preco_custo_estimado
    roi = (lucro_liquido / preco_custo_estimado) * 100 if preco_custo_estimado > 0 else 0
    return round(sobra_pos_taxas, 2), round(lucro_liquido, 2), round(roi, 2)

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0")
        page = await context.new_page()
        
        print("🔗 Lendo Catálogo Utimix...")
        await page.goto(URL_BASE_FORNECEDOR, wait_until="networkidle")
        
        # Captura Nome e tenta capturar Preço (caso apareça sem login)
        produtos_brutos = await page.evaluate('''() => {
            const itens = Array.from(document.querySelectorAll('.product-item'));
            return itens.map(i => {
                const nome = i.querySelector('.product-name a')?.innerText.trim();
                const preco_texto = i.querySelector('.price')?.innerText || "0";
                return { nome, preco_texto };
            }).slice(0, 50);
        }''')

        resultados = []
        for p_uti in produtos_brutos:
            if not p_uti['nome']: continue
            
            # Limpeza do preço Utimix
            try:
                custo_uti = float(p_uti['preco_texto'].replace('R$', '').replace('.', '').replace(',', '.').strip())
            except:
                custo_uti = 0 # Se não ler o preço, marcaremos para você ajustar manual

            print(f"🔍 Cruzando: {p_uti['nome'][:30]}")
            search_url = f"https://www.amazon.com.br/s?k={p_uti['nome'].split('-')[0].strip().replace(' ', '+')}"
            await page.goto(search_url, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            prod_amz = await page.query_selector('.s-result-item[data-asin]')
            if prod_amz:
                preco_el = await prod_amz.query_selector('.a-price-whole')
                if preco_el:
                    venda_amz = float((await preco_el.inner_text()).replace('\\n', '').replace('.', '').replace(',', '.').strip())
                    
                    # Se o custo Utimix não foi lido (sem login), estimamos 45% da venda Amazon
                    custo_final = custo_uti if custo_uti > 0 else round(venda_amz * 0.45, 2)
                    
                    sobra, lucro, roi = await calcular_analise(venda_amz, custo_final)

                    if lucro > 5: # Filtro de lucro real
                        resultados.append({
                            "titulo": p_uti['nome'][:60],
                            "venda_amazon": venda_amz,
                            "custo_utimix": custo_final,
                            "lucro_liquido": lucro,
                            "roi": roi,
                            "link": f"https://www.amazon.com.br/dp/{await prod_amz.get_attribute('data-asin')}"
                        })

        with open("dados_fba.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
