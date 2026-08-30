import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Gestão & Data Science - Sondagem Mineral", layout="wide")

import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Gestão & Data Science - Sondagem Mineral", layout="wide")

# CONEXÃO COM SUPABASE
# Substitua pelas suas chaves encontradas em: Project Settings > API
SUPABASE_URL = "https://lvcvbeariojlzulgkgjm.supabase.co"
SUPABASE_KEY = "sb_publishable_YCteHln3tn1T0-lJpyYPEw_kLuePgxx"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_connection()
except Exception as e:
    st.error("Erro ao conectar ao Supabase. Configure suas chaves no código.")

st.title("⛏️ Gestão de Sondagem Mineral & Data Science")

menu = st.sidebar.radio("Navegação", ["📝 Campo: Cadastrar Furo", "🪵 Campo: Log Litológico/Ensaios", "📊 Painel Data Science em Tempo Real"])

# --- MENU 1: CADASTRO DO FURO (COLLAR) ---
if menu == "📝 Campo: Cadastrar Furo":
    st.subheader("1. Novo Cabeçalho de Furo (Collar)")
    
    with st.form("form_collar", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            hole_id = st.text_input("Hole ID (Código do Furo)*", value="DH-001")
            projeto = st.text_input("Projeto*", value="Projeto Alvo Alpha")
            alvo = st.text_input("Alvo Mineral", value="Anomalia Central")
        with col2:
            utm_x = st.number_input("UTM X (Easting)", value=500000.0)
            utm_y = st.number_input("UTM Y (Northing)", value=7500000.0)
            elevation = st.number_input("Elevação/Cota Z (m)", value=350.0)
        with col3:
            azimuth = st.number_input("Azimute (°)", min_value=0.0, max_value=360.0, value=0.0)
            dip = st.number_input("Inclinação/Dip (°)", min_value=-90.0, max_value=90.0, value=-90.0)
            prof_final = st.number_input("Profundidade Final Prevista (m)", value=150.0)

        btn_salvar_furo = st.form_submit_button("💾 Salvar Furo no Banco")

        if btn_salvar_furo:
            dados_collar = {
                "hole_id": hole_id,
                "projeto": projeto,
                "alvo": alvo,
                "utm_easting": utm_x,
                "utm_northing": utm_y,
                "elevation": elevation,
                "azimuth": azimuth,
                "dip": dip,
                "profundidade_final": prof_final
            }
            res = supabase.table("furos_sondagem").insert(dados_collar).execute()
            st.success(f"Furo {hole_id} registrado com sucesso!")

# --- MENU 2: DESCRIÇÃO LITOLÓGICA E TEOR (INTERVALOS) ---
elif menu == "🪵 Campo: Log Litológico/Ensaios":
    st.subheader("2. Descrição Litológica e Ensaio por Intervalo")
    
    # Buscar furos existentes
    furos_resp = supabase.table("furos_sondagem").select("hole_id").execute()
    lista_furos = [item["hole_id"] for item in furos_resp.data] if furos_resp.data else []

    if not lista_furos:
        st.warning("Cadastre pelo menos um Furo antes de registrar a litologia.")
    else:
        furo_selecionado = st.selectbox("Selecione o Furo:", lista_furos)
        
        with st.form("form_intervalo", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                from_m = st.number_input("De (m)", value=0.0, step=1.0)
                to_m = st.number_input("Até (m)", value=2.0, step=1.0)
                recuperacao = st.number_input("Recuperação (%)", value=95.0, min_value=0.0, max_value=100.0)
            with col2:
                litologia = st.text_input("Litologia Dominante", value="Granito Porfiroide")
                alteracao = st.text_input("Alteração Hidrotermal", value="Potássica moderada")
            with col3:
                mineralizacao = st.text_input("Mineralização", value="Calcopirita / Pirita")
                teor = st.number_input("Teor Estimado/Analisado (ex: Cu % ou Au g/t)", value=0.85, step=0.01)

            obs = st.text_area("Observações Geológicas", value="Zona brechada com veio de quartzo.")
            btn_salvar_intervalo = st.form_submit_button("➕ Adicionar Intervalo")

            if btn_salvar_intervalo:
                if to_m <= from_m:
                    st.error("A profundidade 'Até' deve ser maior que 'De'.")
                else:
                    dados_intervalo = {
                        "hole_id": furo_selecionado,
                        "from_m": from_m,
                        "to_m": to_m,
                        "recuperacao_pct": recuperacao,
                        "litologia": litologia,
                        "alteracao_hidrotermal": alteracao,
                        "mineralizacao": mineralizacao,
                        "teor_principal": teor,
                        "observacoes": obs
                    }
                    supabase.table("ensaios_intervalos").insert(dados_intervalo).execute()
                    st.success("Intervalo adicionado!")

# --- MENU 3: PAINEL DE CIÊNCIA DE DADOS (AGORA VOCÊ ENTRA) ---
elif menu == "📊 Painel Data Science em Tempo Real":
    st.subheader("3. Análise de Dados & Métricas de Sondagem")

    if st.button("🔄 Atualizar Dados do Banco"):
        st.rerun()

    # Carregar dados
    df_collar = pd.DataFrame(supabase.table("furos_sondagem").select("*").execute().data)
    df_intervalos = pd.DataFrame(supabase.table("ensaios_intervalos").select("*").execute().data)

    if df_collar.empty or df_intervalos.empty:
        st.info("Aguardando inserção de furos e intervalos pela equipe de campo...")
    else:
        # KPI's Principais
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        col_kpi1.metric("Total de Furos", len(df_collar))
        col_kpi2.metric("Metragem Total Mapeada (m)", float(df_intervalos["to_m"].max()))
        col_kpi3.metric("Teor Médio Geral", round(df_intervalos["teor_principal"].mean(), 2))
        col_kpi4.metric("Média de Recuperação", f"{round(df_intervalos['recuperacao_pct'].mean(), 1)}%")

        st.markdown("---")

        # Análise Exploratória Rápida (EDA)
        st.write("### 📈 Análises Iniciais para Ciência de Dados")
        
        tab_a, tab_b, tab_c = st.columns(3)
        
        with tab_a:
            st.write("**Distribuição dos Teores por Litologia**")
            st.bar_chart(df_intervalos.groupby("litologia")["teor_principal"].mean())

        with tab_b:
            st.write("**Perfil de Teor ao longo da Profundidade (Furo Selecionado)**")
            furo_f = st.selectbox("Filtrar Furo:", df_intervalos["hole_id"].unique())
            df_furo = df_intervalos[df_intervalos["hole_id"] == furo_f].sort_values("from_m")
            st.line_chart(df_furo.set_index("from_m")["teor_principal"])

        with tab_c:
            st.write("**Controle de Qualidade (Recuperação vs Teor)**")
            st.scatter_chart(df_intervalos, x="recuperacao_pct", y="teor_principal", color="litologia")

        st.markdown("---")
        st.write("### 📄 Tabela Unificada Completa (Dataframe)")
        df_completo = pd.merge(df_intervalos, df_collar, on="hole_id", how="left")
        st.dataframe(df_completo, use_container_width=True)
