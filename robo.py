import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Simulamos um navegador real para evitar bloqueios do servidor
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        # Link exato que enviou
        url_utimix = "https://www.utimix.com/novidades/?utm_source=brevo&utm_campaign=Seguimento%20%201%20Pedido%20-%204%20envio&utm_medium=email&utm_id=22"
        
        print("🔗 Acessando Novidades Utimix...")
        try:
            # 'commit' faz com que ele comece a ler assim que o HTML chegar, sem esperar imagens/rastreadores
            await page.goto(url_utimix, wait_until="commit", timeout=60000)
            
            # Espera apenas 5 segundos para o catálogo renderizar
            await asyncio.sleep(5)
            
            # Extração focada nos seletores de preço e nome da Utimix
            produtos_utimix = await page.evaluate('''() => {
                const cards = Array.from(document.querySelectorAll('.product-item'));
                return cards.map(c => {
                    const nome = c.querySelector('.product-name a')?.innerText.trim();
                    const preco = c.querySelector('.price')?.innerText.replace('R$', '').trim();
                    return { nome, preco };
                }).filter(p => p.nome && p.preco && p.preco !== "0");
            }''')
            
            print(f"📦 Sucesso! Encontrados {len(produtos_utimix)} produtos com preço visível.")

        except Exception as e:
            print(f"❌ Erro ao aceder à Utimix: {e}")
            await browser.close()
            return

        resultados = []
        # Analisamos os primeiros 30 para manter a execução rápida e segura
        for item in produtos_utimix[:30]:
            try:
                # Limpa o nome para a busca na Amazon (remove referências e códigos)
                termo_busca = item['nome'].split('-')[-1].strip()
                print(f"🔍 Cruzando na Amazon: {termo_busca}")
                
                await page.goto(f"https://www.amazon.com.br/s?k={termo_busca.replace(' ', '+')}", wait_until="domcontentloaded")
                await asyncio.sleep(2)

                # Captura o primeiro anúncio relevante
                card = await page.query_selector(".s-result-item[data-asin]")
                if card:
                    asin = await card.get_attribute("data-asin")
                    preco_amz_el = await card.query_selector(".a-price-whole")
                    
                    if preco_amz_el:
                        venda = float((await preco_amz_el.inner_text()).replace('.', '').replace(',', '.').strip())
                        custo = float(item['preco'].replace('.', '').replace(',', '.').strip())
                        
                        # Cálculo: Venda - Custo - (15% Comissão + R$ 13 taxa FBA estimada)
                        lucro = round(venda - custo - (venda * 0.15 + 13), 2)
                        
                        resultados.append({
                            "titulo": item['nome'][:60],
                            "venda_amazon": venda,
                            "custo_utimix": custo,
                            "lucro_liquido": lucro,
                            "roi": round((lucro / custo) * 100, 2) if custo > 0 else 0,
                            "link": f"https://www.amazon.com.br/dp/{asin}"
                        })
            except:
                continue

        # Guarda os dados para o seu Dashboard
        with open("dados_fba.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        await browser.close()
        print(f"✅ Processo concluído. Verifique o seu Dashboard!")

if __name__ == "__main__":
    asyncio.run(run())
