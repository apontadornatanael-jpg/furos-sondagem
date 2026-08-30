import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

st.set_page_config(page_title="Sondagem Mineral Privada", layout="wide")

SUPABASE_URL = "https://lvcvbeariojlzulgkgjm.supabase.co"
SUPABASE_KEY = "sb_publishable_YCteHln3tn1T0-lJpyYPEw_kLuePgxx"


@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_connection()

# --- GERENCIAMENTO DE SESSÃO / LOGIN ---
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_nome" not in st.session_state:
    st.session_state.usuario_nome = ""

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🔒 Acesso Restrito - Sondagem Mineral")

    with st.form("form_login"):
        email_input = st.text_input("Digite seu e-mail cadastrado:")
        btn_entrar = st.form_submit_button("Entrar no Sistema")

        if btn_entrar:
            if email_input:
                try:
                    res = (
                        supabase.table("usuarios_autorizados")
                        .select("*")
                        .eq("email", email_input.strip().lower())
                        .execute()
                    )

                    if res.data:
                        st.session_state.logado = True
                        st.session_state.usuario_nome = res.data[0]["nome"]
                        st.success(
                            f"Bem-vindo(a), {st.session_state.usuario_nome}!"
                        )
                        st.rerun()
                    else:
                        st.error(
                            "Acesso negado. E-mail não cadastrado na equipe autorizada."
                        )
                except Exception as e:
                    st.error(f"Erro na verificação de acesso: {e}")
            else:
                st.warning("Por favor, preencha o campo de e-mail.")

# --- SISTEMA PRINCIPAL (LIBERADO APÓS LOGIN) ---
else:
    # Barra lateral com identificação e logout
    st.sidebar.write(f"👤 **Usuário:** {st.session_state.usuario_nome}")
    if st.sidebar.button("🚪 Sair / Logout"):
        st.session_state.logado = False
        st.session_state.usuario_nome = ""
        st.rerun()

    st.title("⛏️ Gestão de Sondagem Mineral & Data Science")

    menu = st.sidebar.radio(
        "Navegação",
        [
            "📝 Campo: Cadastrar Furo",
            "🪵 Campo: Log Litológico/Ensaios",
            "📊 Painel Data Science em Tempo Real",
        ],
    )

    # --- MENU 1: CADASTRO DO FURO ---
    if menu == "📝 Campo: Cadastrar Furo":
        st.subheader("1. Novo Cabeçalho de Furo (Collar)")
        with st.form("form_collar", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                hole_id = st.text_input("Hole ID*", value="DH-001")
                projeto = st.text_input("Projeto*", value="Projeto Alvo Alpha")
                alvo = st.text_input("Alvo Mineral", value="Anomalia Central")
            with col2:
                utm_x = st.number_input("UTM X (Easting)", value=500000.0)
                utm_y = st.number_input("UTM Y (Northing)", value=7500000.0)
                elevation = st.number_input("Elevação Z (m)", value=350.0)
            with col3:
                azimuth = st.number_input(
                    "Azimute (°)", min_value=0.0, max_value=360.0, value=0.0
                )
                dip = st.number_input(
                    "Inclinação/Dip (°)",
                    min_value=-90.0,
                    max_value=90.0,
                    value=-90.0,
                )
                prof_final = st.number_input(
                    "Profundidade Final Prevista (m)", value=150.0
                )

            btn_salvar_furo = st.form_submit_button("💾 Salvar Furo")

            if btn_salvar_furo:
                dados_collar = {
                    "hole_id": hole_id.strip(),
                    "projeto": projeto.strip(),
                    "alvo": alvo.strip(),
                    "utm_easting": float(utm_x),
                    "utm_northing": float(utm_y),
                    "elevation": float(elevation),
                    "azimuth": float(azimuth),
                    "dip": float(dip),
                    "profundidade_final": float(prof_final),
                }

                try:
                    supabase.table("furos_sondagem").insert(
                        dados_collar
                    ).execute()
                    st.success(
                        f"Furo {hole_id} registrado por {st.session_state.usuario_nome}!"
                    )
                except Exception as e:
                    st.error(f"Erro ao salvar furo no Supabase: {e}")

    # --- MENU 2: DESCRIÇÃO LITOLÓGICA ---
    elif menu == "🪵 Campo: Log Litológico/Ensaios":
        st.subheader("2. Descrição Litológica e Ensaio por Intervalo")
        try:
            furos_resp = (
                supabase.table("furos_sondagem").select("hole_id").execute()
            )
            lista_furos = (
                [item["hole_id"] for item in furos_resp.data]
                if furos_resp.data
                else []
            )
        except Exception as e:
            lista_furos = []
            st.error(f"Erro ao carregar lista de furos: {e}")

        if not lista_furos:
            st.warning(
                "Cadastre pelo menos um Furo antes de registrar a litologia."
            )
        else:
            furo_selecionado = st.selectbox("Selecione o Furo:", lista_furos)
            with st.form("form_intervalo", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    from_m = st.number_input("De (m)", value=0.0, step=1.0)
                    to_m = st.number_input("Até (m)", value=2.0, step=1.0)
                    recuperacao = st.number_input(
                        "Recuperação (%)", value=95.0
                    )
                with col2:
                    litologia = st.text_input(
                        "Litologia Dominante", value="Granito"
                    )
                    alteracao = st.text_input(
                        "Alteração Hidrotermal", value="Potássica"
                    )
                with col3:
                    mineralizacao = st.text_input(
                        "Mineralização", value="Calcopirita"
                    )
                    teor = st.number_input(
                        "Teor Principal", value=0.85, step=0.01
                    )

                obs = st.text_area(
                    "Observações Geológicas", value="Zona mineralizada."
                )
                btn_salvar_intervalo = st.form_submit_button(
                    "➕ Adicionar Intervalo"
                )

                if btn_salvar_intervalo:
                    dados_intervalo = {
                        "hole_id": furo_selecionado,
                        "from_m": float(from_m),
                        "to_m": float(to_m),
                        "recuperacao_pct": float(recuperacao),
                        "litologia": litologia.strip(),
                        "alteracao_hidrotermal": alteracao.strip(),
                        "mineralizacao": mineralizacao.strip(),
                        "teor_principal": float(teor),
                        "observacoes": obs.strip(),
                    }

                    try:
                        supabase.table("ensaios_intervalos").insert(
                            dados_intervalo
                        ).execute()
                        st.success("Intervalo adicionado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar intervalo: {e}")

    # --- MENU 3: DATA SCIENCE & VISUALIZAÇÃO 3D ---
    elif menu == "📊 Painel Data Science em Tempo Real":
        st.subheader("3. Análise de Dados & Métricas de Sondagem")

        if st.button("🔄 Atualizar Dados"):
            st.rerun()

        try:
            df_collar = pd.DataFrame(
                supabase.table("furos_sondagem").select("*").execute().data
            )
            df_intervalos = pd.DataFrame(
                supabase.table("ensaios_intervalos").select("*").execute().data
            )
        except Exception as e:
            st.error(f"Erro ao buscar dados do banco: {e}")
            df_collar = pd.DataFrame()
            df_intervalos = pd.DataFrame()

        if df_collar.empty:
            st.info(
                "Aguardando inserção de furos (Collar) pela equipe autorizada."
            )
        else:
            if not df_intervalos.empty:
                df_completo = pd.merge(
                    df_intervalos, df_collar, on="hole_id", how="left"
                )
                df_completo["intervalo_mid"] = (
                    df_completo["from_m"] + df_completo["to_m"]
                ) / 2
                df_completo["utm_z_calc"] = (
                    df_completo["elevation"] - df_completo["intervalo_mid"]
                )
            else:
                df_completo = df_collar.copy()
                df_completo["utm_z_calc"] = df_completo["elevation"]

            col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
            col_kpi1.metric("Total de Furos", len(df_collar))
            if not df_intervalos.empty:
                col_kpi2.metric(
                    "Teor Médio Geral",
                    round(df_intervalos["teor_principal"].mean(), 2),
                )
                col_kpi3.metric(
                    "Recuperação Média",
                    f"{round(df_intervalos['recuperacao_pct'].mean(), 1)}%",
                )

            st.markdown("---")
            st.write("### 🌐 Visualização Espacial 3D dos Furos (UTM)")

            if not df_intervalos.empty:
                modo_visao = st.radio(
                    "Colorir modelo 3D por:",
                    ["Litologia", "Teor Principal"],
                    horizontal=True,
                )

                if modo_visao == "Litologia":
                    fig_3d = px.scatter_3d(
                        df_completo,
                        x="utm_easting",
                        y="utm_northing",
                        z="utm_z_calc",
                        color="litologia",
                        hover_name="hole_id",
                        hover_data=["from_m", "to_m", "teor_principal"],
                        title="Modelo 3D: Distribuição Litológica",
                        labels={
                            "utm_easting": "UTM E (m)",
                            "utm_northing": "UTM N (m)",
                            "utm_z_calc": "Cota Z (m)",
                        },
                    )
                else:
                    fig_3d = px.scatter_3d(
                        df_completo,
                        x="utm_easting",
                        y="utm_northing",
                        z="utm_z_calc",
                        color="teor_principal",
                        size="teor_principal",
                        hover_name="hole_id",
                        hover_data=["from_m", "to_m", "litologia"],
                        color_continuous_scale="Viridis",
                        title="Modelo 3D: Variabilidade de Teores",
                        labels={
                            "utm_easting": "UTM E (m)",
                            "utm_northing": "UTM N (m)",
                            "utm_z_calc": "Cota Z (m)",
                        },
                    )

                fig_3d.update_layout(
                    height=650,
                    margin=dict(l=0, r=0, b=0, t=40),
                    scene=dict(
                        xaxis_title="UTM Easting (X)",
                        yaxis_title="UTM Northing (Y)",
                        zaxis_title="Elevação Z (m)",
                    ),
                )
                st.plotly_chart(fig_3d, use_container_width=True)
            else:
                fig_3d = px.scatter_3d(
                    df_collar,
                    x="utm_easting",
                    y="utm_northing",
                    z="elevation",
                    hover_name="hole_id",
                    title="Modelo 3D: Posição dos Furos (Collar)",
                )
                st.plotly_chart(fig_3d, use_container_width=True)

            st.markdown("---")
            st.write("### 📄 Tabela Geral de Dados Unificados")
            st.dataframe(df_completo, use_container_width=True)
