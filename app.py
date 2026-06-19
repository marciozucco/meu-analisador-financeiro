import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests

st.set_page_config(page_title="Plataforma de Investimentos Global Pro", layout="wide")

st.title("💼 Simulador de Investimentos Global & IA")
st.subheader("Análise Fundamentalista, Alocação Moderada com FIIs e Busca Global")

# --- CONFIGURAÇÃO DE APIS (PROVEDORES) ---
st.sidebar.header("🔑 Configurações de API")

# >>> SUBSTUIÇÃO DO TOKEN AQUI <<<
BRAPI_TOKEN = "oxKJf3tRSyn6uf6WdurNbt" 

gemini_api_key = st.sidebar.text_input("Digite sua Gemini API Key:", type="password")
st.sidebar.markdown("[Obter chave Gemini grátis](https://aistudio.google.com/)")
st.sidebar.markdown("[Obter token Brapi grátis](https://brapi.dev/)")
st.sidebar.markdown("---")

# --- LISTAS FIXAS DE MONITORAMENTO ---
SCANNER_BR_ACOES = ["VALE3", "PETR4", "ITUB4", "WEGE3", "BBAS3", "BBDC4", "ABEV3", "ELET3", "RENT3", "ITSA4", "GGBR4", "LREN3", "EQTL3", "RADL3", "VBBR3"]
SCANNER_BR_FIIS = ["HGLG11", "XPLG11", "KNCR11", "MXRF11", "BTLG11", "XPML11", "VISC11", "KNRI11", "HGRU11", "HGBS11", "RECR11", "VILG11", "CPTS11", "TRXF11", "TGAR11"]
SCANNER_EUA_ACOES = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "KO", "PEP", "DIS", "JNJ", "V", "WMT", "XOM", "JPM"]
SCANNER_EUA_REITS = ["O", "STAG", "PLD", "AMT", "SPG", "CCI", "EQIX", "PSA", "DLR", "SBAC", "WELL", "AVB", "VRE", "WY", "NLY"]

# --- FUNÇÃO DE BUSCA GLOBAL (AUTOCOMPLETE VIA BRAPI) ---
def buscar_ticker_global(termo_busca):
    if not termo_busca or len(termo_busca) < 2:
        return []
    if BRAPI_TOKEN == "oxKJf3tRSyn6uf6WdurNbt":
        return [{"label": "⚠️ Configure o Token da Brapi no código", "ticker": ""}]
    try:
        url = f"https://brapi.dev/api/v2/prime-boxes?search={termo_busca}&token={BRAPI_TOKEN}"
        resposta = requests.get(url, timeout=5).json()
        
        opcoes = []
        for resultado in resposta.get("boxes", []):
            ticker = resultado.get("ticker")
            nome = resultado.get("name", "Sem nome")
            tipo = resultado.get("type", "Ação")
            
            opcoes.append({
                "label": f"{ticker} - {nome} [{tipo}]",
                "ticker": ticker
            })
        return opcoes[:8]
    except:
        return []

# --- FUNÇÃO DE ANÁLISE FUNDAMENTALISTA EM TEMPO REAL (BRAPI) ---
def analisar_saude_ativos(lista_tickers):
    dados_filtrados = []
    
    if BRAPI_TOKEN == "COLE_SEU_TOKEN_AQUI" or not BRAPI_TOKEN:
        st.error("Por favor, mude o texto 'COLE_SEU_TOKEN_AQUI' na linha 14 para o seu Token gerado no site da Brapi.")
        return pd.DataFrame()

    tickers_formatados = ",".join([t.strip().upper() for t in lista_tickers])
    
    try:
        url = f"https://brapi.dev/api/quote/{tickers_formatados}?fundamental=true&token={BRAPI_TOKEN}"
        req = requests.get(url, timeout=10)
        
        # Mostra o erro real se o token for inválido
        if req.status_code == 401 or req.status_code == 403:
            st.error("❌ Erro da API Brapi: O token inserido foi rejeitado pelo servidor (Acesso Não Autorizado). Verifique se copiou o token completo.")
            return pd.DataFrame()
            
        resposta = req.json()
        results = resposta.get("results", [])
        
        if not results:
            st.warning("Nenhum dado retornado para a lista de ativos.")
            return pd.DataFrame()
        
        for ativo in results:
            ticker = ativo.get("symbol", "").upper()
            nome = ativo.get("longName", ativo.get("shortName", ticker))
            
            preco_bruto = ativo.get("regularMarketPrice", 0)
            is_eua = not ticker.endswith(".SA") and ticker not in SCANNER_BR_ACOES and ticker not in SCANNER_BR_FIIS
            moeda_prefixo = "US$ " if is_eua else "R$ "
            preco_formatado = f"{moeda_prefixo}{preco_bruto:,.2f}" if preco_bruto else "N/A"
            
            is_fii = "11" in ticker or ticker in SCANNER_EUA_REITS
            
            try:
                fundamental = ativo.get("fundamentalData", [{}])[0]
            except:
                fundamental = {}
                
            roe = fundamental.get("returnOnEquity", 0) or 0
            margem = fundamental.get("netProfitMargin", 0) or 0
            divida = fundamental.get("totalDebtToEquity", 0) or 0
            pe_ratio = fundamental.get("peRatio", "N/A")
            price_to_book = fundamental.get("priceToBook", "N/A")
            dividend_yield_final = fundamental.get("dividendYield", 0) or 0

            pe_str = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A"
            pvp_str = f"{price_to_book:.2f}" if isinstance(price_to_book, (int, float)) else "N/A"
            dy_str = f"{dividend_yield_final:.2f}%" if dividend_yield_final > 0 else "0.00%"

            if is_fii:
                if isinstance(price_to_book, (int, float)) and 0.85 <= price_to_book <= 1.15 and dividend_yield_final > 5.0:
                    status_carteira = "🔥 COMPRAR"
                elif dividend_yield_final > 2.0:
                    status_carteira = "⚠️ QUARENTENA"
                else:
                    status_carteira = "❌ EVITAR"
            else:
                if roe > 0.10 and margem > 0.05:
                    status_carteira = "🔥 COMPRAR"
                elif roe > 0.02:
                    status_carteira = "⚠️ QUARENTENA"
                else:
                    status_carteira = "❌ EVITAR"
                
            dados_filtrados.append({
                "Ticker": ticker, "Nome": nome, "Classe": "FII / REIT" if is_fii else "Ação", "Preço": preco_formatado,
                "ROE": f"{roe*100:.2f}%" if not is_fii and roe else "N/A", 
                "Margem Líquida": f"{margem*100:.2f}%" if not is_fii and margem else "N/A", 
                "Dívida/Patr.": f"{divida:.1f}%" if divida else "0.0%",
                "P/L": pe_str, "P/VP (Múltiplo)": pvp_str, "Div. Yield (DY)": dy_str,
                "Decisão da Carteira": status_carteira
            })
            
    except Exception as e:
        st.error(f"Erro inesperado de rede: {e}")
        return pd.DataFrame()
            
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
        with st.spinner("Conectando com os servidores de alta velocidade da Brapi..."):
            lista_acoes = SCANNER_BR_ACOES if "Brasileiro" in mercado else SCANNER_EUA_ACOES
            lista_fiis = SCANNER_BR_FIIS if "Brasileiro" in mercado else SCANNER_EUA_REITS
            
            df_acoes_analisadas = analisar_saude_ativos(lista_acoes)
            df_fiis_analisados = analisar_saude_ativos(lista_fiis)
            
            if not df_acoes_analisadas.empty or not df_fiis_analisados.empty:
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

# --- CALCULADORA ---
elif menu == "🧮 Calculadora de Alocação (Com FIIs)":
    st.header("🧮 Calculadora Patrimonial Inteligente")
    valor_total = st.number_input("Digite o montante total que deseja investir:", min_value=100.0, value=10000.0, step=500.0)
    
    v_rf = valor_total * 0.60
    v_acoes_br = valor_total * 0.15
    v_fiis = valor_total * 0.15
    v_acoes_global = valor_total * 0.05
    v_reits = valor_total * 0.05
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔒 Renda Fixa (60%)", f"{v_rf:,.2f}")
    c2.metric("🇧🇷 Ações BR (15%)", f"{v_acoes_br:,.2f}")
    c3.metric("🏢 FIIs Brasil (15%)", f"{v_fiis:,.2f}")
    c4.metric("📈 Ações EUA (5%)", f"{v_acoes_global:,.2f}")
    c5.metric("🗽 REITs EUA (5%)", f"{v_reits:,.2f}")

# --- BUSCA GLOBAL ---
elif menu == "🔍 Busca Global de Qualquer Ativo":
    st.header("🔍 Mecanismo de Busca Inteligente")
    busca_usuario = st.text_input("Digite para pesquisar (Ex: Apple, Itaú, Microsoft, Petrobras):", value="")
    
    if busca_usuario:
        sugestoes = buscar_ticker_global(busca_usuario)
        if congestoes := [s for s in sugestoes if s["ticker"]]:
            lista_labels = [item["label"] for item in congestoes]
            selecao = st.selectbox("Resultados encontrados (Selecione um):", lista_labels)
            
            ticker_alvo = next(item["ticker"] for item in congestoes if item["label"] == selecao)
            
            if st.button(f"Analisar Fundamentalista de {ticker_alvo}"):
                with st.spinner(f"Baixando dados consolidados de {ticker_alvo}..."):
                    df_ind = analisar_saude_ativos([ticker_alvo])
                    if not df_ind.empty:
                        st.dataframe(df_ind, use_container_width=True)
                        st.markdown(pedir_analise_ia(df_ind, ticker_alvo))
        else:
            st.warning("Nenhum ativo encontrado ou Token ausente.")
