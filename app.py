import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import requests

st.set_page_config(page_title="Plataforma de Investimentos Global Pro", layout="wide")

st.title("💼 Simulador de Investimentos Global & IA")
st.subheader("Análise Fundamentalista, Alocação Moderada com FIIs e Busca Global")

# --- CONFIGURAÇÃO DA IA ---
st.sidebar.header("🤖 Inteligência Artificial")
gemini_api_key = st.sidebar.text_input("Digite sua Gemini API Key:", type="password")
st.sidebar.markdown("[Obter chave grátis](https://aistudio.google.com/)")
st.sidebar.markdown("---")

# --- LISTAS EXPANDIDAS DE MONITORAMENTO (15 POR CATEGORIA) ---
SCANNER_BR_ACOES = [
    "VALE3.SA", "PETR4.SA", "ITUB4.SA", "WEGE3.SA", "BBAS3.SA",
    "BBDC4.SA", "ABEV3.SA", "ELET3.SA", "RENT3.SA", "ITSA4.SA",
    "GGBR4.SA", "LREN3.SA", "EQTL3.SA", "RADL3.SA", "VBBR3.SA"
]
SCANNER_BR_FIIS = [
    "HGLG11.SA", "XPLG11.SA", "KNCR11.SA", "MXRF11.SA", "BTLG11.SA",
    "XPML11.SA", "VISC11.SA", "KNRI11.SA", "HGRU11.SA", "HGBS11.SA",
    "RECR11.SA", "VILG11.SA", "CPTS11.SA", "TRXF11.SA", "TGAR11.SA"
]

SCANNER_EUA_ACOES = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "NVDA", "TSLA", "KO", "PEP", "DIS",
    "JNJ", "V", "WMT", "XOM", "JPM"
]
SCANNER_EUA_REITS = [
    "O", "STAG", "PLD", "AMT", "SPG",
    "CCI", "EQIX", "PSA", "DLR", "SBAC",
    "WELL", "AVB", "VRE", "WY", "NLY"
]

# --- FUNÇÃO DE BUSCA GLOBAL ---
def buscar_ticker_global(termo_busca):
    if not termo_busca or len(termo_busca) < 2:
        return []
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={termo_busca}&quotesCount=6&newsCount=0"
        headers = {"User-Agent": "Mozilla/5.0"}
        resposta = requests.get(url, headers=headers).json()
        
        opcoes = []
        for resultado in resposta.get("quotes", []):
            ticker = resultado.get("symbol")
            nome = resultado.get("longname", resultado.get("shortname", "Sem nome"))
            tipo = resultado.get("quoteType", "N/A")
            
            if tipo == "EQUITY": tipo_PT = "Ação"
            elif tipo == "ETF": tipo_PT = "FII / ETF"
            else: tipo_PT = tipo
                
            opcoes.append({
                "label": f"{ticker} - {nome} ({tipo_PT})",
                "ticker": ticker
            })
        return opcoes
    except:
        return []

# --- FUNÇÃO DE ANÁLISE FUNDAMENTALISTA EM TEMPO REAL ---
def analisar_saude_ativos(lista_tickers):
    dados_filtrados = []
    for ticker in lista_tickers:
        try:
            ticker_limpo = ticker.strip().upper()
            t = yf.Ticker(ticker_limpo)
            info = t.info
            
            if not info or (info.get("regularMarketPrice") is None and info.get("currentPrice") is None):
                continue
                
            nome = info.get("longName", ticker_limpo)
            preco = info.get("currentPrice", info.get("regularMarketPrice", 0)) or 0
            
            tipo = info.get("quoteType", "N/A")
            is_fii = "11.SA" in ticker_limpo or ticker_limpo in SCANNER_EUA_REITS or tipo == "ETF"
            
            roe = info.get("returnOnEquity", 0) or 0
            margem = info.get("profitMargins", 0) or 0
            divida = info.get("debtToEquity", 0) or 0
            pe_ratio = info.get("trailingPE", "N/A")
            price_to_book = info.get("priceToBook", "N/A")
            
            # Tratamento robusto do Dividend Yield
            raw_dy = info.get("dividendYield", 0)
            if raw_dy is None:
                raw_dy = 0
                
            if raw_dy > 1:
                dividend_yield_final = raw_dy
            else:
                dividend_yield_final = raw_dy * 100
                
            pe_str = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A"
            pvp_str = f"{price_to_book:.2f}" if isinstance(price_to_book, (int, float)) else "N/A"
            dy_str = f"{dividend_yield_final:.2f}%"

            # Classificação rígida de recomendação
            if is_fii:
                if isinstance(price_to_book, (int, float)) and 0.85 <= price_to_book <= 1.09 and dividend_yield_final > 5.0:
                    status_carteira = "COMPRAR 🔥"
                    detalhe = "Excelente desconto patrimonial e renda sólida."
                elif dividend_yield_final > 4.0:
                    status_carteira = "QUARENTENA ⚠️"
                    detalhe = "Apenas manter caso já possua. Preço esticado."
                else:
                    status_carteira = "EVITAR ❌"
                    detalhe = "Baixo rendimento ou risco estrutural."
            else:
                if roe > 0.11 and margem > 0.09 and divida < 140:
                    status_carteira = "COMPRAR 🔥"
                    detalhe = "Empresa altamente eficiente e com saúde financeira."
                elif roe > 0.04 and margem > 0.04:
                    status_carteira = "QUARENTENA ⚠️"
                    detalhe = "Empresa estável, mas fora do ponto ideal de entrada."
                else:
                    status_carteira = "EVITAR ❌"
                    detalhe = "Indicadores fracos ou endividamento alarmante."
                
            dados_filtrados.append({
                "Ticker": ticker_limpo, "Nome": nome, "Classe": "FII / REIT" if is_fii else "Ação", "Preço": preco,
                "ROE": f"{roe*100:.2f}%" if not is_fii else "N/A", 
                "Margem Líquida": f"{margem*100:.2f}%" if not is_fii else "N/A", 
                "Dívida/Patr.": f"{divida:.1f}%" if divida else "0.0%",
                "P/L": pe_str, "P/VP (Múltiplo)": pvp_str, "Div. Yield (DY)": dy_str,
                "Decisão da Carteira": status_carteira, "Diagnóstico": detalhe
            })
        except:
            continue
    return pd.DataFrame(dados_filtrados)

# --- FUNÇÃO DA IA ---
def pedir_analise_ia(df_dados, tipo_analise):
    if not gemini_api_key:
        return "⚠️ Para receber o relatório da IA, insira sua chave API na barra lateral."
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        dados_texto = df_dados.to_string(index=False) if isinstance(df_dados, pd.DataFrame) else str(df_dados)
        
        prompt = f"""
        Você é um analista financeiro CFP experiente.
        Abaixo estão os dados analisados e filtrados pelo algoritmo:
        {dados_texto}
        
        Gere um relatório macro em português usando tópicos e negritos indicando:
        1. Por que os ativos marcados com 'COMPRAR 🔥' foram selecionados.
        2. Um aviso rápido sobre o perigo dos ativos da lista de 'QUARENTENA/EVITAR'.
        Seja muito direto, prático e focado em apoiar a decisão do investidor.
        """
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"❌ Erro ao conectar com o Gemini: {e}."

# --- INTERFACE DO USUÁRIO ---
menu = st.sidebar.radio("Navegação", ["🎯 Carteira Recomendada", "🧮 Calculadora de Alocação (Com FIIs)", "🔍 Busca Global de Qualquer Ativo"])

if menu == "🎯 Carteira Recomendada":
    st.header("🎯 Scanner de Mercado Inteligente")
    st.write("O sistema analisa os dados fundamentalistas ao vivo e filtra o mercado exatamente entre o que comprar e o que evitar.")
    
    mercado = st.selectbox("Escolha o Mercado para Monitorar:", ["Mercado Brasileiro (B3)", "Mercado Internacional (EUA)"])
    
    if st.button("Escanear e Montar Carteiras"):
        with st.spinner("Varrendo e aplicando filtros de segurança em todos os ativos..."):
            lista_acoes = SCANNER_BR_ACOES if "Brasileiro" in mercado else SCANNER_EUA_ACOES
            lista_fiis = SCANNER_BR_FIIS if "Brasileiro" in mercado else SCANNER_EUA_REITS
            
            df_geral = analisar_saude_ativos(lista_acoes + lista_fiis)
            
            if not df_geral.empty:
                # --- SEÇÃO 1: CARTEIRA DE COMPRA RECOMENDADA ---
                st.markdown("## 🔥 O QUE COMPRAR AGORA (Ativos Recomendados)")
                st.info("Estes ativos passaram em todos os testes de margem de lucro, dívida controlada ou desconto patrimonial atraente.")
                
                df_compras = df_geral[df_geral["Decisão da Carteira"] == "COMPRAR 🔥"].reset_index(drop=True)
                
                if not df_compras.empty:
                    tab_compra_acoes, tab_compra_fiis = st.tabs(["📈 Ações para Comprar", "🏢 FIIs / REITs para Comprar"])
                    with tab_compra_acoes:
                        df_c_ac = df_compras[df_compras["Classe"] == "Ação"]
                        if not df_c_ac.empty:
                            st.dataframe(df_c_ac.drop(columns=["Decisão da Carteira"]), use_container_width=True)
                        else:
                            st.warning("Nenhuma ação das 15 avaliadas cumpre todos os requisitos rígidos de compra hoje.")
                            
                    with tab_compra_fiis:
                        df_c_fi = df_compras[df_compras["Classe"] == "FII / REIT"]
                        if not df_c_fi.empty:
                            st.dataframe(df_c_fi.drop(columns=["Decisão da Carteira"]), use_container_width=True)
                        else:
                            st.warning("Nenhum fundo imobiliário das 15 avaliados cumpre todos os requisitos rígidos de compra hoje.")
                else:
                    st.error("Alerta de Mercado: Nenhum ativo obteve nota máxima de compra neste momento.")

                st.markdown("---")

                # --- SEÇÃO 2: ATIVOS EM QUARENTENA OU RISCO ---
                st.markdown("## ⚠️ ATIVOS FORA DA CARTEIRA DE COMPRA (Quarentena / Evitar)")
                st.warning("Estes ativos estão caros (múltiplos elevados), muito endividados ou apresentando lucros instáveis na janela atual.")
                
                df_quarentena = df_geral[df_geral["Decisão da Carteira"] != "COMPRAR 🔥"].reset_index(drop=True)
                
                if not df_quarentena.empty:
                    tab_q_acoes, tab_q_fiis = st.tabs(["📉 Ações (Quarentena/Evitar)", "🏚️ FIIs / REITs (Quarentena/Evitar)"])
                    with tab_q_acoes:
                        df_q_ac = df_quarentena[df_quarentena["Classe"] == "Ação"]
                        st.dataframe(df_q_ac, use_container_width=True)
                    with tab_q_fiis:
                        df_q_fi = df_quarentena[df_quarentena["Classe"] == "FII / REIT"]
                        st.dataframe(df_q_fi, use_container_width=True)

                # --- RELATÓRIO DA IA ---
                st.markdown("---")
                st.subheader("🧠 Relatório Estratégico do Analista Virtual IA")
                relatorio = pedir_analise_ia(df_geral, "Carteira")
                st.markdown(relatorio)
            else:
                st.error("Erro ao puxar dados do provedor Yahoo Finance.")

# 2. ABA: CALCULADORA
elif menu == "🧮 Calculadora de Alocação (Com FIIs)":
    st.header("🧮 Calculadora Patrimonial Inteligente")
    st.write("Configuração matemática de aportes para o **Perfil Moderado**.")
    
    valor_total = st.number_input("Digite o montante total que deseja investir (R$ ou $):", min_value=100.0, value=10000.0, step=500.0)
    
    v_rf = valor_total * 0.60
    v_acoes = valor_total * 0.20
    v_fiis = valor_total * 0.20
    
    m1, m2, m3 = st.columns(3)
    m1.metric("🔒 Renda Fixa Segura (60%)", f"{v_rf:,.2f}")
    m2.metric("📈 Ações Globais (20%)", f"{v_acoes:,.2f}")
    m3.metric("🏢 FIIs / REITs Globais (20%)", f"{v_fiis:,.2f}")
    
    st.markdown("---")
    st.subheader("🛒 Monte sua Cesta de Renda Variável")
    
    col_input1, col_input2 = st.columns(2)
    compras_acoes = col_input1.text_input("Ações desejadas (Ex: PETR4.SA, AAPL):", value="ITUB4.SA, AAPL")
    compras_fiis = col_input2.text_input("FIIs/REITs desejados (Ex: MXRF11.SA, O):", value="HGLG11.SA, O")
    
    if st.button("Calcular Divisão Exata por Ativo"):
        lista_final_acoes = [a.strip().upper() for a in compras_acoes.split(",") if a.strip()]
        lista_final_fiis = [f.strip().upper() for f in compras_fiis.split(",") if f.strip()]
        
        tabela_distribuida = []
        
        if lista_final_acoes:
            fatia_acao = v_acoes / len(lista_final_acoes)
            for ac in lista_final_acoes:
                tabela_distribuida.append({"Classe": "Renda Variável (Ação)", "Ticker": ac, "Sugestão de Aporte": f"{fatia_acao:,.2f}"})
                
        if lista_final_fiis:
            fatia_fii = v_fiis / len(lista_final_fiis)
            for fi in lista_final_fiis:
                tabela_distribuida.append({"Classe": "Renda Variável (FII/REIT)", "Ticker": fi, "Sugestão de Aporte": f"{fatia_fii:,.2f}"})
                
        tabela_distribuida.append({"Classe": "Renda Fixa Conservadora", "Ticker": "Tesouro Selic / T-Bills", "Sugestão de Aporte": f"{(v_rf * 0.5):,.2f}"})
        tabela_distribuida.append({"Classe": "Renda Fixa Anti-Inflação", "Ticker": "Tesouro IPCA+ / TIPS", "Sugestão de Aporte": f"{(v_rf * 0.5):,.2f}"})
        
        df_distribuido = pd.DataFrame(tabela_distribuida)
        st.subheader("📊 Boleta Prática de Compras")
        st.dataframe(df_distribuido, use_container_width=True)
        
        st.subheader("🤖 Análise Consultiva da IA sobre a Alocação")
        with st.spinner("Consultando analista virtual..."):
            relatorio_ia = pedir_analise_ia(df_distribuido, "Plano de Alocação Customizado")
            st.markdown(relatorio_ia)

# 3. ABA: BUSCA
elif menu == "🔍 Busca Global de Qualquer Ativo":
    st.header("🔍 Mecanismo de Busca Inteligente Global")
    st.write("Encontre qualquer papel do mundo (Ações, Fundos Imobiliários Brasileiros, REITs Americanos, ETFs).")
    
    texto_busca = st.text_input("Digite o nome ou sigla do investimento:")
    
    if texto_busca:
        resultados = buscar_ticker_global(texto_busca)
        if resultados:
            opcoes_labels = [r["label"] for r in resultados]
            escolha = st.selectbox("Selecione o resultado exato:", opcoes_labels)
            
            ticker_alvo = ""
            for r in resultados:
                if r["label"] == escolha:
                    ticker_alvo = r["ticker"]
            
            if st.button(f"Analisar Fundamentalista de {ticker_alvo}"):
                with st.spinner("Acessando balanços consolidados..."):
                    df_ind = analisar
