import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Camuflagem para o site não saber que é um robô automatizado
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        url_utimix = "https://www.utimix.com/novidades/?utm_source=brevo&utm_campaign=Seguimento%20%201%20Pedido%20-%204%20envio&utm_medium=email&utm_id=22"
        
        print("🔗 Acessando Utimix (Modo Investigador)...")
        try:
            await page.goto(url_utimix, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            
            # --- DIAGNÓSTICO: O QUE O ROBÔ ESTÁ A VER? ---
            titulo = await page.title()
            print(f"👀 Título da Página lido pelo robô: '{titulo}'")
            
            texto_pagina = await page.evaluate("document.body.innerText")
            print(f"📝 Primeiras palavras na tela: '{texto_pagina[:150].strip()}'...")
            
            if "Cloudflare" in titulo or "Access Denied" in titulo or "Security" in titulo or "Just a moment" in titulo:
                print("🚨 ALERTA VERMELHO: O site ativou a defesa Anti-Bot contra o GitHub.")
                await browser.close()
                return
            # ----------------------------------------------

            print("📜 Rolando a página para renderizar imagens e preços...")
            for _ in range(4):
                await page.mouse.wheel(0, 800)
                await asyncio.sleep(2)

            # Busca extrema: Ignora nomes de classes e procura a estrutura visual
            produtos_utimix = await page.evaluate('''() => {
                const todosElementos = Array.from(document.querySelectorAll('*'));
                const candidatos = [];

                todosElementos.forEach(el => {
                    const texto = el.innerText || "";
                    // Se tem "R$", uma imagem, um link, e não é a página inteira (<300 letras)
                    if (texto.includes('R$') && el.querySelector('img') && el.querySelector('a') && texto.length < 300) {
                        candidatos.push(el);
                    }
                });

                // Remove elementos duplicados (caixas dentro de caixas)
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
                            preco = linha.replace(/[^0-9,]/g, ''); // Extrai só os números
                        } else if (linha.length > 5 && !linha.toLowerCase().includes('novo') && !linha.toLowerCase().includes('partir') && !nome) {
                            nome = linha;
                        }
                    });

                    const img = c.querySelector('img')?.src || "";
                    return { nome, preco, img };
                }).filter(p => p.nome && p.preco !== "0");
            }''')
            
            print(f"📦 Sucesso! Encontrados {len(produtos_utimix)} produtos após diagnóstico.")

            if len(produtos_utimix) == 0:
                print("⚠️ Ainda 0 produtos. Envie-me o log acima para eu ver o Título e o Texto da página.")
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
                print(f"🔍 Buscando na Amazon: {termo_busca[:30]}...")
                
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
            except:
                continue

        with open("dados_fba.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        await browser.close()
        print(f"✅ Terminado: {len(resultados)} cruzamentos gerados.")

if __name__ == "__main__":
    asyncio.run(run())
