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

# --- LISTAS EXPANDIDAS PARA A CARTEIRA RECOMENDADA AUTOMÁTICA ---
# Separados por classe para o robô escanear e organizar perfeitamente
SCANNER_BR_ACOES = ["VALE3.SA", "PETR4.SA", "ITUB4.SA", "WEGE3.SA", "BBAS3.SA"]
SCANNER_BR_FIIS = ["HGLG11.SA", "XPLG11.SA", "KNCR11.SA", "MXRF11.SA", "BTLG11.SA"]
SCANNER_EUA_ACOES = ["AAPL", "MSFT", "GOOGL", "NVDA", "KO"]
SCANNER_EUA_REITS = ["O", "STAG", "PLD", "AMT", "SPG"] # Principais fundos imobiliários americanos

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
            t = yf.Ticker(ticker)
            info = t.info
            
            nome = info.get("longName", ticker)
            preco = info.get("currentPrice", info.get("regularMarketPrice", 0)) or 0
            
            # Identificação inteligente do tipo de ativo
            tipo = info.get("quoteType", "N/A")
            # É considerado FII se termina com 11.SA ou se for um REIT americano conhecido na nossa lista
            is_fii = "11.SA" in ticker or ticker in SCANNER_EUA_REITS or tipo == "ETF"
            
            # Coleta de indicadores
            roe = info.get("returnOnEquity", 0) or 0
            margem = info.get("profitMargins", 0) or 0
            divida = info.get("debtToEquity", 0) or 0
            pe_ratio = info.get("trailingPE", "N/A")
            price_to_book = info.get("priceToBook", "N/A")  # P/VP
            dividend_yield = info.get("dividendYield", 0) or 0
            
            pe_str = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A"
            pvp_str = f"{price_to_book:.2f}" if isinstance(price_to_book, (int, float)) else "N/A"
            dy_str = f"{dividend_yield * 100:.2f}%" if dividend_yield else "0.00%"

            # Filtros de Seleção (Diferenciando Ações de FIIs)
            if is_fii:
                # Para FIIs/REITs: Foco em dividendos e P/VP próximo de 1
                if isinstance(price_to_book, (int, float)) and 0.85 <= price_to_book <= 1.08 and dividend_yield > 0.05:
                    saude, sugestao = "Excelente ❤️ (Preço Justo)", "Forte Compra"
                elif dividend_yield > 0.04:
                    saude, sugestao = "Regular 🟡", "Manter / Observar"
                else:
                    saude, sugestao = "Fraca ⚠️", "Evitar no Momento"
            else:
                # Para Ações: Foco em eficiência de lucros e endividamento baixo
                if roe > 0.12 and margem > 0.10 and divida < 130:
                    saude, sugestao = "Excelente ❤️", "Forte Compra"
                elif roe > 0.05 and margem > 0.05:
                    saude, sugestao = "Regular 🟡", "Observar"
                else:
                    saude, sugestao = "Fraca ⚠️", "Evitar / Risco"
                
            dados_filtrados.append({
                "Ticker": ticker, "Nome": nome, "Classe": "FII / REIT" if is_fii else "Ação", "Preço": preco,
                "ROE": f"{roe*100:.2f}%" if not is_fii else "N/A", 
                "Margem Líquida": f"{margem*100:.2f}%" if not is_fii else "N/A", 
                "Dívida/Patr.": f"{divida:.1f}%" if divida else "0.0%",
                "P/L": pe_str, "P/VP (Múltiplo)": pvp_str, "Div. Yield (DY)": dy_str,
                "Saúde": saude, "Sugestão": sugestao
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
        Você é um analista financeiro experiente especializado em alocação de portfólios.
        Abaixo estão dados reais extraídos ao vivo do mercado:
        {dados_texto}
        
        Forneça um laudo em português usando tópicos e negritos:
        1. Avalie a distribuição proposta (Renda Fixa, Ações e Fundos Imobiliários) sob a ótica de um investidor Moderado que deseja renda e crescimento equilibrados.
        2. Justifique quais Ações ou FIIs listados estão mais atraentes usando os dados de Dividend Yield (DY) e P/VP fornecidos.
        Seja muito prático e direto.
        """
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"❌ Erro ao conectar com o Gemini: {e}."

# --- INTERFACE DO USUÁRIO ---
menu = st.sidebar.radio("Navegação", ["🎯 Carteira Recomendada", "🧮 Calculadora de Alocação (Com FIIs)", "🔍 Busca Global de Qualquer Ativo"])

# 1. ABA: CARTEIRA RECOMENDADA
if menu == "🎯 Carteira Recomendada":
    st.header("🎯 Scanner de Mercado: Carteiras de Ações & FIIs")
    st.write("Análise em tempo real de grandes ativos divididos por classes de investimento.")
    
    mercado = st.selectbox("Escolha o Mercado para Monitorar:", ["Mercado Brasileiro (B3)", "Mercado Internacional (EUA)"])
    
    if st.button("Escanear Mercado Agora"):
        with st.spinner("Varrendo cotações, dividendos e balanços..."):
            # Define as listas com base no mercado escolhido
            lista_acoes = SCANNER_BR_ACOES if "Brasileiro" in mercado else SCANNER_EUA_ACOES
            lista_fiis = SCANNER_BR_FIIS if "Brasileiro" in mercado else SCANNER_EUA_REITS
            
            # Junta tudo para passar pelo scanner
            df_geral = analisar_saude_ativos(lista_acoes + lista_fiis)
            
            if not df_geral.empty:
                # Divide a visualização na tela em duas abas organizadas
                tab_acoes, tab_fiis = st.tabs(["📈 Ações Recomendadas", "🏢 Fundos Imobiliários / REITs"])
                
                with tab_acoes:
                    df_s_acoes = df_geral[df_geral["Classe"] == "Ação"]
                    st.dataframe(df_s_acoes, use_container_width=True)
                    
                with tab_fiis:
                    df_s_fiis = df_geral[df_geral["Classe"] == "FII / REIT"]
                    st.dataframe(df_s_fiis, use_container_width=True)
                
                # Destaca apenas as melhores oportunidades
                st.success("🤖 Destaques do Robô (Ativos classificados como 'Forte Compra'):")
                df_fortes = df_geral[df_geral["Sugestão"] == "Forte Compra"]
                if not df_fortes.empty:
                    st.dataframe(df_fortes[["Ticker", "Nome", "Classe", "P/VP (Múltiplo)", "Div. Yield (DY)", "Sugestão"]], use_container_width=True)
                else:
                    st.info("Nenhum ativo com desconto extremo hoje. Siga a tabela geral.")
                
                # Laudo do Gemini
                st.subheader("🧠 Relatório Estratégico da Inteligência Artificial")
                relatorio = pedir_analise_ia(df_geral, "Carteira")
                st.markdown(relatorio)
            else:
                st.error("Erro ao puxar os dados do Yahoo Finance.")

# 2. ABA: CALCULADORA DE ALOCAÇÃO (TOTALMENTE INTEGRADA)
elif menu == "🧮 Calculadora de Alocação (Com FIIs)":
    st.header("🧮 Calculadora Patrimonial Inteligente")
    st.write("Configuração matemática de aportes para o **Perfil Moderado** dividida estrategicamente entre segurança, dividendos e crescimento.")
    
    valor_total = st.number_input("Digite o montante total que deseja investir (R$ ou $):", min_value=100.0, value=10000.0, step=500.0)
    
    # Modelo Matemático de Alocação Moderada Definitiva: 60% Fixa / 20% Ações / 20% FIIs
    v_rf = valor_total * 0.60
    v_acoes = valor_total * 0.20
    v_fiis = valor_total * 0.20
    
    m1, m2, m3 = st.columns(3)
    m1.metric("🔒 Renda Fixa Segura (60%)", f"{v_rf:,.2f}")
    m2.metric("📈 Ações Globais (20%)", f"{v_acoes:,.2f}")
    m3.metric("🏢 FIIs / REITs Globais (20%)", f"{v_fiis:,.2f}")
    
    st.markdown("---")
    st.subheader("🛒 Monte sua Cesta de Renda Variável")
    st.write("Insira os códigos dos ativos que deseja comprar com a sua verba de Renda Variável (separe por vírgula):")
    
    col_input1, col_input2 = st.columns(2)
    compras_acoes = col_input1.text_input("Ações desejadas (Ex: PETR4.SA, AAPL):", value="ITUB4.SA, AAPL")
    compras_fiis = col_input2.text_input("FIIs/REITs desejados (Ex: MXRF11.SA, O):", value="HGLG11.SA, O")
    
    if st.button("Calcular Divisão Exata por Ativo"):
        lista_final_acoes = [a.strip().upper() for a in compras_acoes.split(",") if a.strip()]
        lista_final_fiis = [f.strip().upper() for f in compras_fiis.split(",") if f.strip()]
        
        tabela_distribuida = []
        
        # Divisão da verba de ações igualmente entre as digitadas
        if lista_final_acoes:
            fatia_acao = v_acoes / len(lista_final_acoes)
            for ac in lista_final_acoes:
                tabela_distribuida.append({"Classe": "Renda Variável (Ação)", "Ticker": ac, "Sugestão de Aporte": f"{fatia_acao:,.2f}"})
                
        # Divisão da verba de FIIs igualmente entre os digitados
        if lista_final_fiis:
            fatia_fii = v_fiis / len(lista_final_fiis)
            for fi in lista_final_fiis:
                tabela_distribuida.append({"Classe": "Renda Variável (FII/REIT)", "Ticker": fi, "Sugestão de Aporte": f"{fatia_fii:,.2f}"})
                
        # Inclusão automática dos 60% da Renda Fixa para fechar a conta do patrimônio
        tabela_distribuida.append({"Classe": "Renda Fixa Conservadora", "Ticker": "Tesouro Selic / T-Bills", "Sugestão de Aporte": f"{(v_rf * 0.5):,.2f}"})
        tabela_distribuida.append({"Classe": "Renda Fixa Anti-Inflação", "Ticker": "Tesouro IPCA+ / TIPS", "Sugestão de Aporte": f"{(v_rf * 0.5):,.2f}"})
        
        df_distribuido = pd.DataFrame(tabela_distribuida)
        st.subheader("📊 Boleta Prática de Compras")
        st.dataframe(df_distribuido, use_container_width=True)
        
        # Auditoria da IA sobre as escolhas do usuário
        st.subheader("🤖 Análise Consultiva da IA sobre a Alocação")
        with st.spinner("Consultando analista virtual..."):
            relatorio_ia = pedir_analise_ia(df_distribuido, "Plano de Alocação Customizado")
            st.markdown(relatorio_ia)

# 3. ABA: BUSCA GLOBAL COMPLETA
elif menu == "🔍 Busca Global de Qualquer Ativo":
    st.header("🔍 Mecanismo de Busca Inteligente Global")
    st.write("Encontre qualquer papel do mundo (Ações, Fundos Imobiliários Brasileiros, REITs Americanos, ETFs).")
    
    texto_busca = st.text_input("Digite o nome ou sigla do investimento (Ex: Taesa, MXRF11, Realty Income, Microsoft):")
    
    if texto_busca:
        resultados = buscar_ticker_global(texto_busca)
        if resultados:
            opcoes_labels = [r["label"] for r in resultados]
            escolha = st.selectbox("Selecione o resultado exato:", "%" if len(opcoes_labels)==0 else opcoes_labels)
            
            ticker_alvo = ""
            for r in resultados:
                if r["label"] == escolha:
                    ticker_alvo = r["ticker"]
            
            if st.button(f"Analisar Fundamentalista de {ticker_alvo}"):
                with st.spinner("Acessando balanços consolidados..."):
                    df_ind = analisar_saude_actifs([ticker_alvo])
                    if not df_ind.empty:
                        st.dataframe(df_ind, use_container_width=True)
                        st.subheader("🧠 Avaliação da IA")
                        st.markdown(pedir_analise_ia(df_ind, ticker_alvo))
                    else:
                        st.error("Dados fundamentalistas insuficientes para este ativo no momento.")
        else:
            st.warning("Nenhum ativo encontrado com esse nome.")
