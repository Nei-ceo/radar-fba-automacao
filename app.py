import streamlit as st
import json
import os

# Configuração da página para ocupar a tela toda
st.set_page_config(page_title="Radar FBA Pro", layout="wide")

st.title("📊 Painel de Arbitragem Profissional (FBA)")
st.markdown("---")

# Verifica se o arquivo de dados existe
if os.path.exists("dados_fba.json"):
    with open("dados_fba.json", "r", encoding="utf-8") as f:
        try:
            dados = json.load(f)
        except:
            dados = []
    
    if not dados:
        st.info("O robô ainda não encontrou produtos lucrativos hoje. Aguarde a próxima rodada!")
    else:
        # Filtros na Barra Lateral para facilitar a análise
        st.sidebar.header("Filtros de Oportunidade")
        roi_min = st.sidebar.slider("ROI Mínimo (%)", 0, 100, 30)
        
        # Filtragem dos dados
        df_dados = [d for d in dados if d.get('roi', 0) >= roi_min]
        # Ordenar pelos melhores ROIs
        df_dados = sorted(df_dados, key=lambda x: x.get('roi', 0), reverse=True)

        # Exibição em Colunas (Grid)
        cols = st.columns(3)
        for idx, item in enumerate(df_dados):
            with cols[idx % 3]:
                # Estilização do Card
                st.subheader(f"{item['titulo']}")
                st.write(f"🏷️ **Preço de Venda: R$ {item['preco']}**")
                
                # Métricas de Lucro
                st.success(f"💰 Sobra Líquida: R$ {item['sobra_fba']}")
                st.caption("*(Valor bruto após comissões e logística est. da Amazon)*")
                
                # Alerta de ROI
                st.warning(f"📈 Lucro Est.: R$ {item.get('lucro_potencial', 0)} (ROI: {item.get('roi', 0)}%)")
                
                st.info(f"💡 Dica: Pague no máximo R$ {round(item['sobra_fba'] - 10, 2)} no fornecedor para manter margem.")
                
                st.link_button("🚀 Ver na Amazon", item['link'])
                st.divider()
else:
    st.error("Arquivo 'dados_fba.json' não encontrado. O robô precisa rodar primeiro!")
