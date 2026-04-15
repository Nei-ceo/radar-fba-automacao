import asyncio
import sys
import json
import pandas as pd
from playwright.async_api import async_playwright

# Correção essencial para rodar no Windows/Nuvem
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Termos de busca lucrativos
TERMOS = ["utilidades domesticas", "cozinha inox", "ferramentas eletricas", "pet shop premium", "brinquedos educativos"]

async def calcular_lucro(preco_venda):
    """
    Simulação de taxas Amazon FBA Brasil:
    15% Comissão + 6% Impostos + R$ 14,00 Logística Fixa
    """
    comissao = preco_venda * 0.15
    imposto = preco_venda * 0.06
    taxa_fba_est = 14.00 
    sobra_liquida = preco_venda - (comissao + imposto + taxa_fba_est)
    return round(sobra_liquida, 2)

async def run():
    async with async_playwright() as p:
        # CRÍTICO: headless=True para rodar no GitHub/Nuvem
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0")
        page = await context.new_page()
        page.set_default_timeout(90000)
        
        resultados = []

        for termo in TERMOS:
            print(f"📡 Minerando: {termo}")
            try:
                await page.goto(f"https://www.amazon.com.br/s?k={termo.replace(' ', '+')}", wait_until="domcontentloaded")
                await asyncio.sleep(5)
                
                produtos = await page.query_selector_all('.s-result-item[data-asin]')
                
                for prod in produtos[:15]:
                    asin = await prod.get_attribute('data-asin')
                    if not asin or len(asin) < 5: continue
                    
                    titulo_el = await prod.query_selector('h2 span')
                    preco_el = await prod.query_selector('.a-price-whole')
                    
                    if titulo_el and preco_el:
                        titulo = await titulo_el.inner_text()
                        preco_raw = await preco_el.inner_text()
                        preco_clean = preco_raw.replace('\n', '').replace('.', '').replace(',', '.').strip()
                        
                        try:
                            preco_venda = float(preco_clean)
                            sobra = await calcular_lucro(preco_venda)
                            
                            if sobra > 20: # Só pega o que sobra mais de 20 reais
                                custo_compra_est = round(preco_venda * 0.40, 2)
                                lucro_est = round(sobra - custo_compra_est, 2)
                                roi_est = round((lucro_est / custo_compra_est) * 100, 2) if custo_compra_est > 0 else 0

                                resultados.append({
                                    "asin": asin,
                                    "titulo": titulo[:60],
                                    "preco": preco_venda,
                                    "sobra_fba": sobra,
                                    "lucro_potencial": lucro_est,
                                    "roi": roi_est,
                                    "link": f"https://www.amazon.com.br/dp/{asin}"
                                })
                        except: continue
            except: continue

        # Salva o resultado final para o Dashboard ler
        with open("dados_fba.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Sucesso! {len(resultados)} oportunidades salvas.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
