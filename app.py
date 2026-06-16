import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="Plataforma de Investimentos Global Pro", layout="wide")

st.title("💼 Simulador de Investimentos Global & IA")
st.subheader("Análise Fundamentalista, Alocação Moderada e Renda Fixa Internacional")

# --- CONFIGURAÇÃO DA IA NA BARRA LATERAL ---
st.sidebar.header("🤖 Inteligência Artificial")
gemini_api_key = st.sidebar.text_input("Digite sua Gemini API Key:", type="password")
st.sidebar.markdown("[Obter chave grátis](https://aistudio.google.com/)")
st.sidebar.markdown("---")

# --- BANCO DE DADOS DE ATIVOS (BUSCA INTELIGENTE) ---
DIC_ACOES_BR = {
    "VALE3.SA (Vale)": "VALE3.SA",
    "PETR4.SA (Petrobras)": "PETR4.SA",
    "ITUB4.SA (Itaú Unibanco)": "ITUB4.SA",
    "BBDC4.SA (Bradesco)": "BBDC4.SA",
    "WEGE3.SA (WEG)": "WEGE3.SA",
    "ABEV3.SA (Ambev)": "ABEV3.SA",
    "BBAS3.SA (Banco do Brasil)": "BBAS3.SA",
    "ITSA4.SA (Itaúsa)": "ITSA4.SA"
}

DIC_ACOES_EUA = {
    "AAPL (Apple)": "AAPL",
    "MSFT (Microsoft)": "MSFT",
    "GOOGL (Google)": "GOOGL",
    "AMZN (Amazon)": "AMZN",
    "META (Meta / Facebook)": "META",
    "NVDA (NVIDIA)": "NVDA",
    "KO (Coca-Cola)": "KO",
    "DIS (Disney)": "DIS"
}

# --- DICIONÁRIOS DE RENDA FIXA (BRASIL E EUA) ---
RENDA_FIXA_BR = [
    {"Produto": "Tesouro Selic (Pos-fixado)", "Indicador": "Taxa Selic", "Liquidez": "Diária (D+1)", "Objetivo": "Reserva de Emergência / Curto Prazo"},
    {"Produto": "Tesouro IPCA+ (Híbrido)", "Indicador": "Inflação (IPCA) + Taxa Fixa", "Liquidez": "No Vencimento (D+0 no mercado secundário)", "Objetivo": "Ganho Real / Longo Prazo"},
    {"Produto": "Tesouro Prefixado", "Indicador": "Taxa Fixa Contratada", "Liquidez": "No Vencimento", "Objetivo": "Apostar na queda dos juros / Médio Prazo"},
    {"Produto": "Tesouro RendA+ (Previdência)", "Indicador": "IPCA + Juros acumulados", "Liquidez": "Foco na aposentadoria", "Objetivo": "Complemento de Renda por 20 anos"},
    {"Produto": "LCI / LCA (Bancos Brasileiros)", "Indicador": "Geralmente % do CDI", "Liquidez": "Isento de IR / Varia conforme o banco", "Objetivo": "Isenção Fiscal / Curto a Médio Prazo"}
]

RENDA_FIXA_EUA = [
    {"Produto": "Treasury Bills (T-Bills)", "Indicador": "Taxa Fixa de Curto Prazo", "Liquidez": "Até 1 ano (Alta liquidez)", "Objetivo": "Proteção cambial em Dólar de curto prazo"},
    {"Produto": "Treasury Notes (T-Notes)", "Indicador": "Cupom Fixo Semestral", "Liquidez": "De 2 a 10 anos", "Objetivo": "Renda previsível em Dólar de médio prazo"},
    {"Produto": "Treasury Bonds (T-Bonds)", "Indicador": "Cupom Fixo Semestral", "Liquidez": "De 20 a 30 anos", "Objetivo": "Investimento institucional de longo prazo em Dólar"},
    {"Produto": "TIPS (Inflation-Protected)", "Indicador": "Variação do CPI (Inflação EUA) + Taxa", "Liquidez": "5, 10 e 30 anos", "Objetivo": "Proteger o poder de compra global contra a inflação americana"}
]

# --- FUNÇÃO AUXILIAR DA IA ---
def pedir_analise_ia(df_dados, mercado_nome):
    if not gemini_api_key:
        return "⚠️ Para receber o relatório da IA, insira sua chave API na barra lateral."
    try:
        genai.configure(api_key=gemini_api_key)
        # CORRIGIDO DEFINITIVAMENTE: Caminho estável de produção
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        dados_texto = df_dados.to_string(index=False) if isinstance(df_dados, pd.DataFrame) else str(df_dados)
        
        prompt = f"""
        Você é um analista financeiro CFP (Certified Financial Planner).
        Responda em português estruturado com tópicos e negritos.
        
        Contexto do Cliente: Perfil Moderado.
        Dados carregados da simulação:
        {dados_texto}
        
        Com base no que foi simulado para {mercado_nome}, faça uma breve auditoria sobre a diversificação sugerida, se as ações escolhidas são saudáveis e dê um conselho estratégico profissional sobre como equilibrar essa Renda Fixa e Variável.
        """
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"❌ Erro ao conectar com o Gemini: {e}. Verifique sua chave."

# --- INTERFACE ---
menu = st.sidebar.radio("Navegação", ["Calculadora de Alocação (Moderado)", "Catálogo de Renda Fixa", "Busca de Ações Individual"])

if menu == "Calculadora de Alocação (Moderado)":
    st.header("🧮 Calculadora de Distribuição Patrimonial")
    st.write("O **Perfil Moderado** busca segurança na Renda Fixa, mas expõe parte do capital em Renda Variável buscando superar a inflação.")
    
    # 1. Campo de Entrada de Valor para o Usuário
    valor_total = st.number_input("Digite o valor total que pretende investir (R$ ou $):", min_value=100.0, value=10000.0, step=500.0)
    
    st.markdown("### Definição Estratégica Recomendada (Perfil Moderado)")
    
    # Divisão Padrão de Perfil Moderado: 60% Renda Fixa / 40% Renda Variável (20% BR / 20% EUA)
    v_renda_fixa = valor_total * 0.60
    v_acoes_br = valor_total * 0.20
    v_acoes_eua = valor_total * 0.20
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🔒 Renda Fixa (60%)", f"{v_renda_fixa:,.2f}")
    col2.metric("🇧🇷 Ações Brasil (20%)", f"{v_acoes_br:,.2f}")
    col3.metric("🇺🇸 Ações EUA (20%)", f"{v_acoes_eua:,.2f}")
    
    st.markdown("---")
    st.subheader("🛒 Sugestão Prática de Compras")
    
    # Seleção inteligente das carteiras usando o selectbox com busca
    st.write("Selecione os ativos que deseja incluir na sua parcela de Renda Variável:")
    escolha_br = st.multiselect("Escolha as Ações Brasileiras desejadas:", list(DIC_ACOES_BR.keys()), default=list(DIC_ACOES_BR.keys())[:2])
    escolha_eua = st.multiselect("Escolha as Ações Americanas desejadas:", list(DIC_ACOES_EUA.keys()), default=list(DIC_ACOES_EUA.keys())[:2])
    
    if st.button("Calcular Divisão de Compras por Ativo"):
        # Distribuição de compras por ativo selecionado
        tabela_compras = []
        
        if escolha_br:
            valor_por_acao_br = v_acoes_br / len(escolha_br)
            for item in escolha_br:
                tabela_compras.append({"Classe": "Renda Variável (BR)", "Ativo/Produto": DIC_ACOES_BR[item], "Valor a Aportar": f"{valor_por_acao_br:,.2f}"})
                
        if escolha_eua:
            valor_por_acao_eua = v_acoes_eua / len(escolha_eua)
            for item in escolha_eua:
                tabela_compras.append({"Classe": "Renda Variável (EUA)", "Ativo/Produto": DIC_ACOES_EUA[item], "Valor a Aportar": f"{valor_por_acao_eua:,.2f}"})
        
        # Sugestão genérica de divisão da Renda Fixa (Metade Emergência / Metade Inflação)
        tabela_compras.append({"Classe": "Renda Fixa", "Ativo/Produto": "Tesouro Selic / T-Bills (Liquidez)", "Valor a Aportar": f"{(v_renda_fixa/2):,.2f}"})
        tabela_compras.append({"Classe": "Renda Fixa", "Ativo/Produto": "Tesouro IPCA+ / TIPS (Proteção)", "Valor a Aportar": f"{(v_renda_fixa/2):,.2f}"})
        
        df_compras = pd.DataFrame(tabela_compras)
        st.dataframe(df_compras, use_container_width=True)
        
        # Chamada de IA para auditar a carteira do usuário
        st.subheader("🤖 Consultoria de Alocação emitida pela IA")
        with st.spinner("IA processando seu plano de investimento..."):
            relatorio = pedir_analise_ia(tabela_compras, "Calculadora Moderada")
            st.markdown(relatorio)

elif menu == "Catálogo de Renda Fixa":
    st.header("📋 Catálogo de Ativos de Renda Fixa (Brasil vs EUA)")
    st.write("Estes são os principais títulos de dívida emitidos e garantidos pelos governos soberanos do Brasil e dos Estados Unidos (considerado o ativo mais seguro do planeta).")
    
    aba1, aba2 = st.tabs(["🇧🇷 Tesouro Direto (Brasil)", "🇺🇸 US Treasuries (Bolsa EUA)"])
    
    with aba1:
        st.subheader("Títulos Públicos Federais - B3")
        df_rf_br = pd.DataFrame(RENDA_FIXA_BR)
        st.dataframe(df_rf_br, use_container_width=True)
        st.info("💡 **Dica do Analista:** O Tesouro Selic serve para reservas que você pode precisar sacar amanhã. Já o Tesouro IPCA protege seu dinheiro contra o aumento de preços no supermercado no longo prazo.")
        
    with aba2:
        st.subheader("Government Debt Securities - Estados Unidos")
        df_rf_eua = pd.DataFrame(RENDA_FIXA_EUA)
        st.dataframe(df_rf_eua, use_container_width=True)
        st.info("💡 **Dica do Analista:** Comprar T-Bills ou T-Notes através de uma corretora internacional permite que você receba rendimentos diretamente na moeda mais forte do mundo (Dólar americano).")

elif menu == "Busca de Ações Individual":
    st.header("🔍 Busca Preditiva de Ativos")
    
    tipo_mercado = st.radio("Selecione o Mercado:", ["Nacional (B3)", "Internacional (EUA)"])
    
    if tipo_mercado == "Nacional (B3)":
        acao_selecionada = st.selectbox("Digite ou escolha a Ação Brasileira:", list(DIC_ACOES_BR.keys()))
        ticker = DIC_ACOES_BR[acao_selecionada]
    else:
        acao_selecionada = st.selectbox("Digite ou escolha a Ação Americana:", list(DIC_ACOES_EUA.keys()))
        ticker = DIC_ACOES_EUA[acao_selecionada]
        
    if st.button("Puxar Saúde Financeira & Parecer da IA"):
        with st.spinner("Buscando múltiplos e chamando IA..."):
            try:
                t = yf.Ticker(ticker)
                info = t.info
                df_single = pd.DataFrame([{
                    "Ticker": ticker,
                    "Nome": info.get("longName", ticker),
                    "Preço": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                    "ROE": f"{((info.get('returnOnEquity', 0) or 0)*100):.2f}%",
                    "Margem Líquida": f"{((info.get('profitMargins', 0) or 0)*100):.2f}%"
                }])
                st.dataframe(df_single, use_container_width=True)
                
                st.markdown("#### Relatório Cognitivo")
                relatorio = pedir_analise_ia(df_single, ticker)
                st.markdown(relatorio)
            except Exception as e:
                st.error(f"Erro ao buscar o ativo {ticker}: {e}")
