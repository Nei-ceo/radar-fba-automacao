import streamlit as st
import json
import os

st.set_page_config(page_title="Radar FBA Pro - Utimix", layout="wide")

st.title("📊 Radar de Arbitragem: Utimix x Amazon")
st.markdown("---")

if os.path.exists("dados_fba.json"):
    with open("dados_fba.json", "r", encoding="utf-8") as f:
        try:
            dados = json.load(f)
        except:
            dados = []
    
    if not dados:
        st.info("Nenhum produto lucrativo encontrado na última varredura. Rode o robô novamente!")
    else:
        st.sidebar.header("Filtros de Análise")
        roi_min = st.sidebar.slider("ROI Mínimo (%)", 0, 100, 20)
        
        df_dados = [d for d in dados if d.get('roi', 0) >= roi_min]
        df_dados = sorted(df_dados, key=lambda x: x.get('roi', 0), reverse=True)

        cols = st.columns(3)
        for idx, item in enumerate(df_dados):
            with cols[idx % 3]:
                st.subheader(f"{item['titulo']}")
                st.write(f"🏷️ **Preço na Amazon: R$ {item['preco']}**")
                st.success(f"💰 Sobra Líquida (FBA): R$ {item['sobra_fba']}")
                st.warning(f"📈 ROI Est.: {item.get('roi', 0)}%")
                st.link_button("🚀 Ver na Amazon", item['link'])
                st.divider()
else:
    st.error("Arquivo de dados não encontrado. Rode o robô no GitHub Actions!")
