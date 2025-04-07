import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image
import base64

st.set_page_config(page_title="Painel de Clientes", layout="wide")

# 🌿 ESTILO VISUAL
st.markdown("""
    <style>
        body { background-color: #f0fdf4; font-family: 'Arial', sans-serif; }
        .main { padding: 2rem; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        h1, h2, h3 { color: #2ecc71; }
        .stMetric { background-color: #eafaf1; border-radius: 12px; padding: 1rem; margin: 0.5rem 0; }
        .stDataFrame div {
            user-select: text !important;
            -webkit-user-select: text !important;
        }
    </style>
""", unsafe_allow_html=True)

# 🖼️ LOGO E TÍTULO
col1, col2 = st.columns([1, 6])
with col1:
    logo = Image.open("logo.png")
    st.image(logo, width=300)
with col2:
    st.markdown("## ✈️ Painel de Análise de Clientes")
    st.markdown("Explore os clientes por ano, veja quedas na recorrência e analise os gastos!")

# 📄 UPLOAD
tabs = st.tabs(["Dashboard"])
with tabs[0]:
    uploaded_file = st.file_uploader("Faça upload da planilha Excel", type=["xlsx"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df.columns = [col.strip() for col in df.columns]
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        colunas_esperadas = ["Cliente", "Vendas", "Ano"]
        if all(col in df.columns for col in colunas_esperadas):

            df["Vendas"] = pd.to_numeric(df["Vendas"], errors="coerce")
            df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce").astype("Int64")

            # ➕ Processar recorrência
            anos_por_cliente = df.groupby("Cliente")["Ano"].apply(lambda x: sorted(set(x.dropna().astype(int)))).reset_index()
            anos_por_cliente["Recorrência"] = anos_por_cliente["Ano"].apply(len)
            anos_por_cliente["Anos Ativos"] = anos_por_cliente["Ano"].apply(lambda x: ", ".join(map(str, x)))
            anos_por_cliente["Último Ano"] = anos_por_cliente["Ano"].apply(max)
            anos_por_cliente["Primeiro Ano"] = anos_por_cliente["Ano"].apply(min)
            anos_por_cliente["Intervalo Sem Compra"] = anos_por_cliente["Último Ano"] - anos_por_cliente["Primeiro Ano"] + 1 - anos_por_cliente["Recorrência"]

            # ➕ Total gasto
            total_gasto = df.groupby("Cliente")["Vendas"].sum().reset_index().rename(columns={"Vendas": "Total Gasto"})

            # ➕ Adicionar coluna de celular se existir
            if "Celular" in df.columns:
                celulares = df.groupby("Cliente")["Celular"].first().reset_index()
                base_final = pd.merge(anos_por_cliente, total_gasto, on="Cliente")
                base_final = pd.merge(base_final, celulares, on="Cliente", how="left")
            else:
                base_final = pd.merge(anos_por_cliente, total_gasto, on="Cliente")
                base_final["Celular"] = "-"

            base_final["Média Anual"] = base_final["Total Gasto"] / base_final["Recorrência"]
            base_final = base_final.sort_values(by="Total Gasto", ascending=False)

            # 🔎 FILTROS
            st.sidebar.header("🔍 Filtros")
            cliente_unico = ["Todos"] + sorted(base_final["Cliente"].unique().tolist())
            cliente_selecionado = st.sidebar.selectbox("Selecionar Cliente", cliente_unico)

            recorrencia_min = int(base_final["Recorrência"].min())
            recorrencia_max = int(base_final["Recorrência"].max())
            recorrencia_range = st.sidebar.slider("Recorrência (anos)", recorrencia_min, recorrencia_max, (recorrencia_min, recorrencia_max))

            anos_disponiveis = sorted(df["Ano"].dropna().unique().astype(int))
            anos_selecionados = st.sidebar.multiselect("Filtrar por Ano da Compra", anos_disponiveis, default=anos_disponiveis)

            regra = st.sidebar.selectbox("🎯 Perfil dos Clientes", [
                "Nenhuma",
                "💰 Fiel e Lucrativo",
                "📦 Médio e Fiel",
                "🚀 Top Clientes"
            ])

            if regra == "🚀 Top Clientes":
                st.sidebar.markdown("""
                <div style='padding: 0.5rem; background-color: #eafaf1; border-left: 4px solid #2ecc71; border-radius: 8px; margin-top: 0.5rem;'>
                    <strong>Critérios:</strong><br>
                    Total Gasto > R$ 200.000<br>
                    E Recorrência > 4 anos <br>
                    ou comprou em <strong>2024</strong> ou <strong>2025</strong>
                </div>
                """, unsafe_allow_html=True)

            elif regra == "📦 Médio e Fiel":
                st.sidebar.markdown("""
                <div style='padding: 0.5rem; background-color: #eafaf1; border-left: 4px solid #2ecc71; border-radius: 8px; margin-top: 0.5rem;'>
                    <strong>Critérios:</strong><br>
                    Total Gasto <= média geral<br>
                    E Recorrência > 4 anos <br>
                    ou comprou em <strong>2024</strong> ou <strong>2025</strong>
                </div>
                """, unsafe_allow_html=True)

            elif regra == "💰 Fiel e Lucrativo":
                st.sidebar.markdown("""
                <div style='padding: 0.5rem; background-color: #eafaf1; border-left: 4px solid #2ecc71; border-radius: 8px; margin-top: 0.5rem;'>
                    <strong>Critérios:</strong><br>
                    Total Gasto > média geral<br>
                    E Recorrência > 4 anos <br>
                    ou comprou em <strong>2024</strong> ou <strong>2025</strong>
                </div>
                """, unsafe_allow_html=True)

            # 🔍 Aplicar filtros
            base_filtrada = base_final.copy()

            if cliente_selecionado != "Todos":
                base_filtrada = base_filtrada[base_filtrada["Cliente"] == cliente_selecionado]

            base_filtrada = base_filtrada[
                (base_filtrada["Recorrência"] >= recorrencia_range[0]) &
                (base_filtrada["Recorrência"] <= recorrencia_range[1])
            ]

            base_filtrada = base_filtrada[base_filtrada["Anos Ativos"].apply(lambda anos: any(str(ano) in anos for ano in anos_selecionados))]

            if regra == "💰 Fiel e Lucrativo":
                media_total = base_final["Total Gasto"].mean()
                base_filtrada = base_filtrada[
                    (base_filtrada["Total Gasto"] > media_total) & (
                        (base_filtrada["Recorrência"] > 4) |
                        (base_filtrada["Anos Ativos"].str.contains("2024")) |
                        (base_filtrada["Anos Ativos"].str.contains("2025"))
                    )
                ]

            elif regra == "📦 Médio e Fiel":
                media_total = base_final["Total Gasto"].mean()
                base_filtrada = base_filtrada[
                    (base_filtrada["Total Gasto"] <= media_total) & (
                        (base_filtrada["Recorrência"] > 4) |
                        (base_filtrada["Anos Ativos"].str.contains("2024")) |
                        (base_filtrada["Anos Ativos"].str.contains("2025"))
                    )
                ]

            elif regra == "🚀 Top Clientes":
                base_filtrada = base_filtrada[
                    (base_filtrada["Total Gasto"] > 200000) & (
                        (base_filtrada["Recorrência"] > 4) |
                        (base_filtrada["Anos Ativos"].str.contains("2024")) |
                        (base_filtrada["Anos Ativos"].str.contains("2025"))
                    )
                ]
                base_filtrada = base_filtrada.sort_values(by="Total Gasto", ascending=False)

            # 💡 MÉTRICAS
            st.markdown("### 📊 Métricas Gerais")
            col1, col2, col3 = st.columns(3)
            col1.metric("Qt. de Clientes", base_filtrada["Cliente"].nunique())
            col2.metric("Total Geral Gasto", f"R${base_filtrada['Total Gasto'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            col3.metric("Recorrência Média", f"{base_filtrada['Recorrência'].mean():.2f} anos")

            # 📈 GRÁFICO - TOP CLIENTES
            st.markdown("### 🥇 Top 50 Clientes")
            top_clientes = base_filtrada.sort_values(by="Total Gasto", ascending=False).head(50)

            grafico = alt.Chart(top_clientes).mark_bar(color="#2ecc71").encode(
                x=alt.X("Total Gasto", title="Total Gasto (R$)"),
                y=alt.Y("Cliente", sort='-x', title="Cliente"),
                tooltip=[
                    alt.Tooltip("Cliente"),
                    alt.Tooltip("Celular", title="Celular"),
                    alt.Tooltip("Total Gasto", title="Total Gasto (R$)", format=",.2f"),
                    alt.Tooltip("Média Anual", title="Média Anual (R$)", format=",.2f"),
                    alt.Tooltip("Anos Ativos", title="Anos Ativos"),
                    alt.Tooltip("Recorrência", title="Anos de Compra"),
                    alt.Tooltip("Intervalo Sem Compra", title="Intervalo sem Compra (anos)")
                ]
            ).properties(height=600)

            st.altair_chart(grafico, use_container_width=True)

            # 📋 TABELA DE CLIENTES
            st.markdown("### 📄 Tabela de Clientes")
            base_exibicao = base_filtrada[["Cliente", "Celular", "Total Gasto", "Recorrência", "Média Anual", "Anos Ativos", "Intervalo Sem Compra"]]
            base_exibicao = base_exibicao.sort_values(by="Total Gasto", ascending=False)
            base_exibicao["Total Gasto"] = base_exibicao["Total Gasto"].apply(lambda x: f"R${x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            base_exibicao["Média Anual"] = base_exibicao["Média Anual"].apply(lambda x: f"R${x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.dataframe(base_exibicao.reset_index(drop=True), use_container_width=True)

            # 📥 DOWNLOAD - CSV separado por colunas (Excel-friendly)
            if not base_filtrada.empty:
                exportar = base_filtrada.copy()
                exportar["Total Gasto"] = exportar["Total Gasto"].apply(lambda x: f"R${x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                exportar["Média Anual"] = exportar["Média Anual"].apply(lambda x: f"R${x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                csv_data = exportar.to_csv(index=False, sep=";", encoding="utf-8-sig")
                b64 = base64.b64encode(csv_data.encode()).decode()
                download_link = f'''
                    <a href="data:file/csv;base64,{b64}" download="clientes.csv">
                        <button style="background-color:#2ecc71;color:white;border:none;padding:10px 20px;border-radius:8px;cursor:pointer;">
                            ⬇️ Baixar CSV
                        </button>
                    </a>
                '''
                st.markdown("### 📤 Exportar Dados")
                st.markdown(download_link, unsafe_allow_html=True)

        else:
            st.error("A planilha deve conter as colunas: Cliente, Vendas e Ano.")
    else:
        st.info("Envie uma planilha Excel com os dados dos seus clientes.")
