import asyncio
import sys
import json
import random
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # 1. Argumentos furtivos para enganar o Firewall
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox"
            ]
        )
        
        # 2. Perfil 100% Humano e Brasileiro
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            has_touch=False
        )
        
        page = await context.new_page()

        # 3. Injeção de script (Apaga a etiqueta "Sou um Robô" do navegador)
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
        """)
        
        url_utimix = "https://www.utimix.com/novidades/?utm_source=brevo&utm_campaign=Seguimento%20%201%20Pedido%20-%204%20envio&utm_medium=email&utm_id=22"
        
        print("🔗 Iniciando Operação Stealth na Utimix...")
        try:
            await page.goto(url_utimix, wait_until="domcontentloaded", timeout=60000)
            
            # 4. Simulação de Leitura (Pausas e movimentos aleatórios)
            print("🖱️ Simulando comportamento humano...")
            await asyncio.sleep(random.uniform(2.0, 4.0))
            
            for _ in range(4):
                # Rola a página e mexe o mouse de forma errática
                await page.mouse.wheel(0, random.randint(400, 800))
                await page.mouse.move(random.randint(100, 700), random.randint(100, 500))
                await asyncio.sleep(random.uniform(1.5, 3.5))

            # Motor visual de extração
            produtos_utimix = await page.evaluate('''() => {
                const todosElementos = Array.from(document.querySelectorAll('*'));
                const candidatos = [];

                todosElementos.forEach(el => {
                    const texto = el.innerText || "";
                    if (texto.includes('R$') && el.querySelector('img') && el.querySelector('a') && texto.length < 300) {
                        candidatos.push(el);
                    }
                });

                const unicos = [];
                candidatos.forEach(c => {
                    if (!candidatos.some(outro => outro !== c && outro.contains(c))) {
                        unicos.push(c);
                    }
                });

                return unicos.map(c => {
                    const linhas = c.innerText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                    let nome = "";
                    let preco = "0";

                    linhas.forEach(linha => {
                        if (linha.includes('R$')) {
                            preco = linha.replace(/[^0-9,]/g, ''); 
                        } else if (linha.length > 5 && !linha.toLowerCase().includes('novo') && !linha.toLowerCase().includes('partir') && !nome) {
                            nome = linha;
                        }
                    });

                    const img = c.querySelector('img')?.src || "";
                    return { nome, preco, img };
                }).filter(p => p.nome && p.preco !== "0");
            }''')
            
            print(f"📦 Bypass concluído! Encontrados {len(produtos_utimix)} produtos.")

            if len(produtos_utimix) == 0:
                print("⚠️ Bloqueio severo por IP detectado.")
                await browser.close()
                return

        except Exception as e:
            print(f"❌ Erro na extração: {e}")
            await browser.close()
            return

        resultados = []
        for item in produtos_utimix[:30]:
            try:
                termo_busca = item['nome'].split('-')[-1].strip()
                print(f"🔍 Cruzando Amazon: {termo_busca[:30]}...")
                
                await page.goto(f"https://www.amazon.com.br/s?k={termo_busca.replace(' ', '+')}", wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(1.5, 2.5)) # Pausa humana na Amazon também

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
            except:
                continue

        with open("dados_fba.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        await browser.close()
        print(f"✅ Missão cumprida: {len(resultados)} produtos avaliados.")

if __name__ == "__main__":
    asyncio.run(run())
