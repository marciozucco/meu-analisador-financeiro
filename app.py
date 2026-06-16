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

# --- LISTAS FIXAS DE MONITORAMENTO (EXATAMENTE 15 ATIVOS POR CATEGORIA) ---
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
def analisar_saude_ativos(lista_tickers, mercado_selecionado):
    dados_filtrados = []
    # Define o prefixo da moeda com base no mercado escolhido
    moeda_prefixo = "R$ " if "B3" in mercado_selecionado else "US$ "
    
    for ticker in lista_tickers:
        try:
            ticker_limpo = ticker.strip().upper()
            t = yf.Ticker(ticker_limpo)
            info = t.info
            
            nome = info.get("longName", ticker_limpo)
            preco_bruto = info.get("currentPrice", info.get("regularMarketPrice", 0)) or 0
            preco_formatado = f"{moeda_prefixo}{preco_bruto:,.2f}"
            
            tipo = info.get("quoteType", "N/A")
            is_fii = "11.SA" in ticker_limpo or ticker_limpo in SCANNER_EUA_REITS or tipo == "ETF"
            
            # Captura de Indicadores
            roe = info.get("returnOnEquity", 0) or 0
            margem = info.get("profitMargins", 0) or 0
            divida = info.get("debtToEquity", 0) or 0
            pe_ratio = info.get("trailingPE", "N/A")
            price_to_book = info.get("priceToBook", "N/A")
            
            # Tratamento do Dividend Yield
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

            # Classificação estrita
            if is_fii:
                if isinstance(price_to_book, (int, float)) and 0.85 <= price_to_book <= 1.09 and dividend_yield_final > 5.0:
                    status_carteira = "🔥 COMPRAR"
                elif dividend_yield_final > 4.0:
                    status_carteira = "⚠️ QUARENTENA"
                else:
                    status_carteira = "❌ EVITAR"
            else:
                if roe > 0.11 and margem > 0.09 and divida < 140:
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
        except:
            dados_filtrados.append({
                "Ticker": ticker.upper(), "Nome": "Erro de Conexão Yahoo", "Classe": "FII / REIT" if "11.SA" in ticker else "Ação",
                "Preço": f"{moeda_prefixo}0.00", "ROE": "N/A", "Margem Líquida": "N/A", "Dívida/Patr.": "N/A", "P/L": "N/A", "P/VP (Múltiplo)": "N/A",
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
        Você é um analista financeiro CFP experiente.
        Abaixo estão os dados analisados e filtrados pelo algoritmo:
        {dados_texto}
        
        Gere um relatório macro em português usando tópicos e negritos indicando:
        1. Quais ativos da lista estão com a melhor relação risco-retorno na sua visão técnica.
        2. Um aviso rápido sobre o perigo dos ativos marcados como 'EVITAR'.
        Seja muito direto, prático e focado em apoiar a decisão do investidor.
        """
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"❌ Erro ao conectar com o Gemini: {e}."

# --- INTERFACE DO USUÁRIO ---
menu = st.sidebar.radio("Navegação", ["🎯 Carteira Recomendada", "🧮 Calculadora de Alocação (Com FIIs)", "🔍 Busca Global de Qualquer Ativo"])

if menu == "🎯 Carteira Recomendada":
    st.header("🎯 Scanner de Mercado Permanente: Top 15 Ações & Top 15 FIIs")
    st.write("Abaixo você acompanha a lista fixa dos 15 ativos selecionados por classe. Olhe a coluna **'Decisão da Carteira'** para saber quais comprar.")
    
    mercado = st.selectbox("Escolha o Mercado para Monitorar:", ["Mercado Brasileiro (B3)", "Mercado Internacional (EUA)"])
    
    if st.button("Escanear Mercado Agora"):
        with st.spinner("Atualizando cotações e indicadores fundamentalistas dos 30 ativos selecionados..."):
            lista_acoes = SCANNER_BR_ACOES if "Brasileiro" in mercado else SCANNER_EUA_ACOES
            lista_fiis = SCANNER_BR_FIIS if "Brasileiro" in mercado else SCANNER_EUA_REITS
            
            df_acoes_analisadas = analisar_saude_ativos(lista_acoes, mercado)
            df_fiis_analisados = analisar_saude_ativos(lista_fiis, mercado)
            
            tab_acoes, tab_fiis = st.tabs(["📈 Lista Monitorada: Ações (TOP 15)", "🏢 Lista Monitorada: Fundos Imobiliários / REITs (TOP 15)"])
            
            with tab_acoes:
                st.markdown("### Monitoramento de Ações")
                st.dataframe(df_acoes_analisadas, use_container_width=True)
                
            with tab_fiis:
                st.markdown("### Monitoramento de Fundos Imobiliários / REITs")
                st.dataframe(df_fiis_analisados, use_container_width=True)
            
            # --- DESTAQUES DIRETOS DE COMPRA ---
            st.success("🤖 Resumo Rápido: Ativos com Recomendação de COMPRA Ativa hoje:")
            df_geral_total = pd.concat([df_acoes_analisadas, df_fiis_analisados])
            df_so_compras = df_geral_total[df_geral_total["Decisão da Carteira"] == "🔥 COMPRAR"].reset_index(drop=True)
            
            if not df_so_compras.empty:
                st.dataframe(df_so_compras[["Ticker", "Nome", "Classe", "Preço", "P/VP (Múltiplo)", "Div. Yield (DY)", "Decisão da Carteira"]], use_container_width=True)
            else:
                st.info("Nenhum ativo com margem de desconto extremo nesta rodada. Monitore a lista geral.")

            # --- RELATÓRIO DA IA ---
            st.markdown("---")
            st.subheader("🧠 Relatório Estratégico do Analista Virtual IA")
            relatorio = pedir_analise_ia(df_geral_total, "Carteira")
            st.markdown(relatorio)

# --- CALCULADORA ---
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

# --- BUSCA GLOBAL ---
elif menu == "🔍 Busca Global de Qualquer Ativo":
    st.header("🔍 Mecanismo de Busca Inteligente Global")
    st.write("Encontre qualquer papel do mundo (Ações, Fundos Imobiliários Brasileiros, REITs Americanos, ETFs).")
    
    texto_busca = st.text_input("Digite o nome ou sigla do investmento:")
    
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
                    df_ind = analisar_saude_ativos([ticker_alvo], "B3" if ".SA" in ticker_alvo else "EUA")
                    if not df_ind.empty:
                        st.dataframe(df_ind, use_container_width=True)
