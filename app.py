import streamlit as st
import json
import os

st.set_page_config(page_title="Radar de Lucro Real", layout="wide")

st.title("💰 Comparativo Real: Utimix vs Amazon")
st.info("Os preços abaixo são capturados diretamente dos dois sites em tempo real.")

if os.path.exists("dados_fba.json"):
    with open("dados_fba.json", "r", encoding="utf-8") as f:
        dados = json.load(f)

    if not dados:
        st.warning("Nenhum produto com lucro positivo encontrado nesta rodada.")
    
    for item in dados:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1:
                st.markdown(f"**{item['titulo']}**")
                st.caption(f"[Abrir anúncio na Amazon]({item['link']})")
            with c2:
                st.metric("Venda Amazon", f"R$ {item['venda_amazon']}")
            with c3:
                st.metric("Custo Utimix", f"R$ {item['custo_utimix']}")
            with c4:
                # Cor verde para lucro positivo
                st.metric("Lucro Líquido", f"R$ {item['lucro_liquido']}", f"{item['roi']}% ROI")
else:
    st.error("Aguardando primeira execução do robô no GitHub.")
