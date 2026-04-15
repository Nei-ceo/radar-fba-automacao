import streamlit as st
import json
import os

st.set_page_config(page_title="Radar Visual FBA", layout="wide")
st.title("👁️ Validação Visual: Utimix vs Amazon")

if os.path.exists("dados_fba.json"):
    with open("dados_fba.json", "r", encoding="utf-8") as f:
        dados = json.load(f)

    if not dados:
        st.warning("Nenhum produto encontrado nesta rodada.")
    
    for item in dados:
        with st.container(border=True):
            # Layout em 4 colunas para caber fotos e dados
            c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
            
            with c1:
                st.caption("📦 Fornecedor (Utimix)")
                if item.get("img_utimix"):
                    st.image(item["img_utimix"], width=120)
                else:
                    st.write("Sem foto")

            with c2:
                st.caption("🛒 Amazon (Concorrente)")
                if item.get("img_amazon"):
                    st.image(item["img_amazon"], width=120)
                else:
                    st.write("Sem foto")

            with c3:
                st.markdown(f"**{item['titulo']}**")
                st.caption(f"ASIN: {item['link'].split('/')[-1]}")
                st.link_button("Abrir Anúncio na Amazon", item['link'])

            with c4:
                st.metric("Venda Amazon", f"R$ {item['venda_amazon']}")
                st.metric("Custo Utimix", f"R$ {item['custo_utimix']}")
                
                # Destaca se o lucro for negativo
                if item['lucro_liquido'] > 0:
                    st.success(f"Lucro: R$ {item['lucro_liquido']} ({item['roi']}%)")
                else:
                    st.error(f"Prejuízo: R$ {item['lucro_liquido']}")
else:
    st.info("Aguardando os dados do robô...")
