import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Lançando o navegador
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🔗 Acessando Utimix...")
        await page.goto("https://www.utimix.com/novidades/", wait_until="networkidle", timeout=90000)
        
        # Captura os produtos da Utimix
        produtos_utimix = await page.evaluate('''() => {
            const itens = Array.from(document.querySelectorAll('.product-item'));
            return itens.map(i => ({
                nome: i.querySelector('.product-name a')?.innerText.trim() || "",
                preco: i.querySelector('.price')?.innerText.replace('R$', '').trim() || "0"
            })).filter(x => x.nome.length > 3);
        }''')

        print(f"📦 Encontrados {len(produtos_utimix)} itens. Iniciando busca na Amazon...")

        resultados = []
        for item in produtos_utimix[:40]: # Vamos testar com os primeiros 40
            try:
                # LIMPEZA CRÍTICA: Remove referências e códigos do nome para a Amazon achar
                # Exemplo: "Ref 123 - Organizador" vira apenas "Organizador"
                nome_limpo = item['nome'].split('-')[-1].split('Ref')[0].strip()
                
                print(f"🔍 Buscando: {nome_limpo}")
                search_url = f"https://www.amazon.com.br/s?k={nome_limpo.replace(' ', '+')}"
                
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3) # Pausa para carregar preços

                # Pega o primeiro produto real da Amazon
                card = await page.query_selector('.s-result-item[data-asin]')
                if card:
                    asin = await card.get_attribute('data-asin')
                    preco_el = await card.query_selector('.a-price-whole')
                    titulo_el = await card.query_selector('h2 span')

                    if preco_el and titulo_el:
                        venda = (await preco_el.inner_text()).replace('.', '').replace(',', '.').strip()
                        custo = item['preco'].replace('.', '').replace(',', '.').strip()
                        
                        resultados.append({
                            "titulo": await titulo_el.inner_text(),
                            "venda_amazon": float(venda),
                            "custo_utimix": float(custo),
                            "lucro_liquido": round(float(venda) - float(custo) - 15, 2), # Calculo bruto rápido
                            "roi": 0,
                            "link": f"https://www.amazon.com.br/dp/{asin}"
                        })
                        print(f"✅ Achou: {nome_limpo}")
            except Exception as e:
                print(f"Erro no item {item['nome']}: {e}")
                continue

        # Salva o resultado
        with open("dados_fba.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        await browser.close()
        print("🏁 Fim da varredura.")

if __name__ == "__main__":
    asyncio.run(run())
