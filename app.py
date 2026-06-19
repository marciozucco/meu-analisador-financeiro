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

# --- LISTAS FIXAS DE MONITORAMENTO ---
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

# --- FUNÇÃO DE BUSCA GLOBAL (AUTOCOMPLETE) ---
def buscar_ticker_global(termo_busca):
    if not termo_busca or len(termo_busca) < 2:
        return []
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={termo_busca}&quotesCount=8&newsCount=0"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resposta = requests.get(url, headers=headers, timeout=5).json()
        
        opcoes = []
        for resultado in resposta.get("quotes", []):
            ticker = resultado.get("symbol")
            nome = resultado.get("longname", resultado.get("shortname", "Sem nome"))
            tipo = resultado.get("quoteType", "N/A")
            exchange = resultado.get("exchDisp", "Global")
            
            if tipo == "EQUITY": tipo_PT = "Ação"
            elif tipo == "ETF": tipo_PT = "ETF / FII"
            else: tipo_PT = tipo
                
            opcoes.append({
                "label": f"{ticker} - {nome} [{tipo_PT} | {exchange}]",
                "ticker": ticker
            })
        return opcoes
    except:
        return []

# --- FUNÇÃO DE ANÁLISE FUNDAMENTALISTA EM TEMPO REAL ---
def analisar_saude_ativos(lista_tickers):
    dados_filtrados = []
    
    # Criando uma sessão HTTP com User-Agent para evitar blocos do Yahoo Finance
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    })
    
    for ticker in lista_tickers:
        try:
            ticker_limpo = ticker.strip().upper()
            t = yf.Ticker(ticker_limpo, session=session)
            info = t.info
            
            if not info or len(info) <= 1:
                raise ValueError("Yahoo retornou dados vazios para este ticker")
            
            nome = info.get("longName", info.get("shortName", ticker_limpo))
            preco_bruto = info.get("currentPrice", info.get("regularMarketPrice", 0)) or 0
            moeda = info.get("financialCurrency", info.get("currency", "USD"))
            
            moeda_prefixo = "R$ " if moeda == "BRL" else f"{moeda} "
            preco_formatado = f"{moeda_prefixo}{preco_bruto:,.2f}" if preco_bruto else "N/A"
            
            tipo = info.get("quoteType", "N/A")
            setor = str(info.get("sector", "")).lower()
            industria = str(info.get("industry", "")).lower()
            
            is_fii = (
                "11.SA" in ticker_limpo or 
                ticker_limpo in SCANNER_EUA_REITS or 
                tipo == "ETF" or 
                "reit" in industria or 
                "real estate" in setor
            )
            
            roe = info.get("returnOnEquity", 0) or 0
            margem = info.get("profitMargins", 0) or 0
            divida = info.get("debtToEquity", 0) or 0
            pe_ratio = info.get("trailingPE", "N/A")
            price_to_book = info.get("priceToBook", "N/A")
            
            raw_dy = info.get("dividendYield", 0)
            if raw_dy is None: raw_dy = 0
            dividend_yield_final = raw_dy if raw_dy > 1 else raw_dy * 100
                
            pe_str = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A"
            pvp_str = f"{price_to_book:.2f}" if isinstance(price_to_book, (int, float)) else "N/A"
            dy_str = f"{dividend_yield_final:.2f}%"

            if is_fii:
                if isinstance(price_to_book, (int, float)) and 0.80 <= price_to_book <= 1.25 and dividend_yield_final > 4.5:
                    status_carteira = "🔥 COMPRAR"
                elif dividend_yield_final > 3.5:
                    status_carteira = "⚠️ QUARENTENA"
                else:
                    status_carteira = "❌ EVITAR"
            else:
                if roe > 0.11 and margem > 0.09 and (divida < 140 or divida == 0):
                    status_carteira = "🔥 COMPRAR"
                elif roe > 0.04 and margem > 0.04:
                    status_carteira = "⚠️ QUARENTENA"
                else:
                    status_carteira = "❌ EVITAR"
                
            dados_filtrados.append({
                "Ticker": ticker_limpo, "Nome": nome, "Classe": "FII / REIT" if is_fii else "Ação", "Preço": preco_formatado,
                "ROE": f"{roe*100:.2f}%" if not is_fii else "N/A", 
                "Margem Líquida": f"{margem*100:.2f}%" if not is_fii else "N/A", 
                "Dívida/Patr.": f"{divida:.1f}%" if divida else "0.0%",
                "P/L": pe_str, "P/VP (Múltiplo)": pvp_str, "Div. Yield (DY)": dy_str,
                "Decisão da Carteira": status_carteira
            })
        except Exception as e:
            # Printa o erro real no terminal do Streamlit para você monitorar por que falhou
            print(f"Erro ao analisar ticker {ticker}: {e}")
            
            is_fii_fallback = "11.SA" in ticker.upper() or ticker.upper() in SCANNER_EUA_REITS
            dados_filtrados.append({
                "Ticker": ticker.upper(), "Nome": "Erro de Conexão Yahoo", "Classe": "FII / REIT" if is_fii_fallback else "Ação",
                "Preço": "N/A", "ROE": "N/A", "Margem Líquida": "N/A", "Dívida/Patr.": "N/A", "P/L": "N/A", "P/VP (Múltiplo)": "N/A",
                "Div. Yield (DY)": "N/A", "Decisão da Carteira": "⚠️ REAVALIAR"
            })
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
        Você é um analista financeiro experiente.
        Abaixo estão os dados reais do mercado coletados agora:
        {dados_texto}
        
        Gere uma avaliação condensada em português usando tópicos e negritos indicando:
        1. Quais ativos se destacam positivamente para um portfólio moderado.
        2. Alertas críticos sobre as ações ou fundos listados como 'EVITAR'.
        Seja analítico e direto.
        """
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"❌ Erro ao conectar com o Gemini: {e}."

# --- INTERFACE ---
menu = st.sidebar.radio("Navegação", ["🎯 Carteira Recomendada", "🧮 Calculadora de Alocação (Com FIIs)", "🔍 Busca Global de Qualquer Ativo"])

if menu == "🎯 Carteira Recomendada":
    st.header("🎯 Scanner de Mercado Permanente: Top 15 Ações & Top 15 FIIs / REITs")
    st.write("Acompanhe o monitoramento em tempo real das principais bolsas globais divididas por classes.")
    
    mercado = st.selectbox("Escolha o Mercado para Monitorar:", ["Mercado Brasileiro (B3)", "Mercado Internacional (EUA)"])
    
    if st.button("Escanear Mercado Agora"):
        with st.spinner("Conectando com os servidores globais do Yahoo Finance..."):
            lista_acoes = SCANNER_BR_ACOES if "Brasileiro" in mercado else SCANNER_EUA_ACOES
            lista_fiis = SCANNER_BR_FIIS if "Brasileiro" in mercado else SCANNER_EUA_REITS
            
            df_acoes_analisadas = analisar_saude_ativos(lista_acoes)
            df_fiis_analisados = analisar_saude_ativos(lista_fiis)
            
            nome_aba_fii = "🏢 Lista Monitorada: Fundos Imobiliários (TOP 15)" if "Brasileiro" in mercado else "🏢 Lista Monitorada: REITs Americanos (TOP 15)"
            
            tab_acoes, tab_fiis = st.tabs(["📈 Lista Monitorada: Ações (TOP 15)", nome_aba_fii])
            
            with tab_acoes:
                st.dataframe(df_acoes_analisadas, use_container_width=True)
                
            with tab_fiis:
                st.dataframe(df_fiis_analisados, use_container_width=True)
            
            st.success("🤖 Resumo de Sinais de COMPRA Identificados na Varredura:")
            df_geral_total = pd.concat([df_acoes_analisadas, df_fiis_analisados])
            df_so_compras = df_geral_total[df_geral_total["Decisão da Carteira"] == "🔥 COMPRAR"].reset_index(drop=True)
            
            if not df_so_compras.empty:
                st.dataframe(df_so_compras[["Ticker", "Nome", "Classe", "Preço", "P/VP (Múltiplo)", "Div. Yield (DY)", "Decisão da Carteira"]], use_container_width=True)
            else:
                st.info("Nenhum ativo operando com desconto extremo ou assimetria forte nesta rodada.")

            st.markdown("---")
            st.subheader("🧠 Relatório Estratégico do Analista Virtual IA")
            relatorio = pedir_analise_ia(df_geral_total, "Carteira")
            st.markdown(relatorio)

# --- CALCULADORA PRIORIZANDO O MERCADO NACIONAL ---
elif menu == "🧮 Calculadora de Alocação (Com FIIs)":
    st.header("🧮 Calculadora Patrimonial Inteligente")
    st.write("Configuração matemática de aportes calibrada para o **Perfil Moderado com Foco no Mercado Nacional**.")
    
    valor_total = st.number_input("Digite o montante total que deseja investir:", min_value=100.0, value=10000.0, step=500.0)
    
    # 60% Renda Fixa / 40% Renda Variável calibrada (30% Brasil / 10% Internacional)
    v_rf = valor_total * 0.60
    v_acoes_br = valor_total * 0.15      # 15% focado no Brasil
    v_fiis = valor_total * 0.15          # 15% focado no Brasil
    v_acoes_global = valor_total * 0.05  # 5% Internacional
    v_reits = valor_total * 0.05         # 5% Internacional
    
    # Exibição visual das métricas em 5 colunas estruturadas
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔒 Renda Fixa (60%)", f"{v_rf:,.2f}")
    c2.metric("🇧🇷 Ações BR (15%)", f"{v_acoes_br:,.2f}")
    c3.metric("🏢 FIIs Brasil (15%)", f"{v_fiis:,.2f}")
    c4.metric("📈 Ações EUA (5%)", f"{v_acoes_global:,.2f}")
    c5.metric("🗽 REITs EUA (5%)", f"{v_reits:,.2f}")
    
    st.markdown("---")
    st.subheader("🛒 Monte sua Cesta de Renda Variável")
    
    col_in1, col_in2, col_in3, col_in4 = st.columns(4)
    compras_br = col_in1.text_input("Ações do Brasil (Ex: PETR4.SA, ITUB4.SA):", value="ITUB4.SA")
    compras_fiis = col_in2.text_input("FIIs Brasileiros (Ex: HGLG11.SA):", value="HGLG11.SA")
    compras_global = col_in3.text_input("Ações Globais/EUA (Ex: AAPL, MSFT):", value="AAPL")
    compras_reits = col_in4.text_input("REITs Americanos (Ex: O, STAG):", value="O")
    
    if st.button("Calcular Divisão Exata por Ativo"):
        lista_final_br = [b.strip().upper() for b in compras_br.split(",") if b.strip()]
        lista_final_fiis = [f.strip().upper() for f in compras_fiis.split(",") if f.strip()]
        lista_final_global = [g.strip().upper() for g in compras_global.split(",") if g.strip()]
        lista_final_reits = [r.strip().upper() for r in compras_reits.split(",") if r.strip()]
        
        tabela_distribuida = []
        
        if lista_final_br:
            fatia_br = v_acoes_br / len(lista_final_br)
            for ac_br in lista_final_br:
                tabela_distribuida.append({"Classe": "Renda Variável (Ação Brasil)", "Ticker": ac_br, "Sugestão de Aporte": f"{fatia_br:,.2f}"})
                
        if lista_final_fiis:
            fatia_fii = v_fiis / len(lista_final_fiis)
            for fi in lista_final_fiis:
                tabela_distribuida.append({"Classe": "Renda Variável (FII Brasil)", "Ticker": fi, "Sugestão de Aporte": f"{fatia_fii:,.2f}"})

        if lista_final_global:
            fatia_global = v_acoes_global / len(lista_final_global)
            for ac_g in lista_final_global:
                tabela_distribuida.append({"Classe": "Renda Variável (Ação Global/EUA)", "Ticker": ac_g, "Sugestão de Aporte": f"{fatia_global:,.2f}"})
                
        if lista_final_reits:
            fatia_reit = v_reits / len(lista_final_reits)
            for re in lista_final_reits:
                tabela_distribuida.append({"Classe": "Renda Variável (REIT EUA)", "Ticker": re, "Sugestão de Aporte": f"{fatia_reit:,.2f}"})
                
        tabela_distribuida.append({"Classe": "Renda Fixa Conservadora", "Ticker": "Tesouro Selic / T-Bills", "Sugestão de Aporte": f"{(v_rf * 0.5):,.2f}"})
        tabela_distribuida.append({"Classe": "Renda Fixa Anti-Inflação", "Ticker": "Tesouro IPCA+ / TIPS", "Sugestão de Aporte": f"{(v_rf * 0.5):,.2f}"})
        
        df_distribuido = pd.DataFrame(tabela_distribuida)
        st.subheader("📊 Boleta Prática de Compras")
        st.dataframe(df_distribuido, use_container_width=True)

# --- BUSCA GLOBAL ---
elif menu == "🔍 Busca Global de Qualquer Ativo":
    st.header("🔍 Mecanismo de Busca Inteligente Global")
    st.write("Comece a digitar o nome da empresa ou o ticker para obter sugestões automáticas das principais bolsas.")
    
    busca_usuario = st.text_input("Digite para pesquisar (Ex: Apple, Itaú, Microsoft, Petrobras):", value="")
    
    if busca_usuario:
        sugestoes = buscar_ticker_global(busca_usuario)
        
        if sugestoes:
            lista_labels = [item["label"] for item in sugestoes]
            selecao = st.selectbox("Resultados encontrados (Selecione um):", lista_labels)
            
            ticker_alvo = ""
            for item in sugestoes:
                if item["label"] == selecao:
                    ticker_alvo = item["ticker"]
            
            if st.button(f"Analisar Fundamentalista de {ticker_alvo}"):
                with st.spinner(f"Baixando balanços consolidados de {ticker_alvo}..."):
                    df_ind = analisar_saude_ativos([ticker_alvo])
                    
                    if not df_ind.empty and df_ind.iloc[0]["Nome"] != "Erro de Conexão Yahoo":
                        st.markdown("### 📊 Indicadores Fundamentalistas Coletados")
                        st.dataframe(df_ind, use_container_width=True)
                        
                        st.subheader("🧠 Avaliação da Inteligência Artificial")
                        with st.spinner("Gerando laudo consultivo..."):
                            st.markdown(pedir_analise_ia(df_ind, ticker_alvo))
                    else:
                        st.error("Este ativo não possui dados fundamentalistas suficientes para um diagnóstico automático.")
        else:
            st.warning("Nenhum ativo encontrado.")
