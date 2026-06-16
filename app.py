import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="Scanner de Mercado Premium com IA", layout="wide")

st.title("🤖 Scanner de Mercado & Relatórios com IA")
st.subheader("Análise quantitativa integrada ao Google Gemini")

# --- CONFIGURAÇÃO DA IA NA BARRA LATERAL ---
st.sidebar.header("🤖 Configuração da Inteligência Artificial")
gemini_api_key = st.sidebar.text_input("Digite sua Gemini API Key:", type="password")
st.sidebar.markdown("[Como conseguir uma chave grátis?](https://aistudio.google.com/)")
st.sidebar.markdown("---")

# --- DICIONÁRIOS DE ATIVOS PARA BUSCA INTELIGENTE ---
# Listas expandidas com nomes amigáveis para preenchimento automático
DIC_ACOES_BR = {
    "VALE3.SA (Vale)": "VALE3.SA",
    "PETR4.SA (Petrobras)": "PETR4.SA",
    "ITUB4.SA (Itaú Unibanco)": "ITUB4.SA",
    "BBDC4.SA (Bradesco)": "BBDC4.SA",
    "WEGE3.SA (WEG)": "WEGE3.SA",
    "ABEV3.SA (Ambev)": "ABEV3.SA",
    "ELET3.SA (Eletrobras)": "ELET3.SA",
    "BBAS3.SA (Banco do Brasil)": "BBAS3.SA",
    "RENT3.SA (Localiza)": "RENT3.SA",
    "LREN3.SA (Lojas Renner)": "LREN3.SA",
    "B3SA3.SA (B3 S.A.)": "B3SA3.SA",
    "GGBR4.SA (Gerdau)": "GGBR4.SA",
    "ITSA4.SA (Itaúsa)": "ITSA4.SA"
}

DIC_ACOES_EUA = {
    "AAPL (Apple)": "AAPL",
    "MSFT (Microsoft)": "MSFT",
    "GOOGL (Google)": "GOOGL",
    "AMZN (Amazon)": "AMZN",
    "META (Meta / Facebook)": "META",
    "NVDA (NVIDIA)": "NVDA",
    "TSLA (Tesla)": "TSLA",
    "KO (Coca-Cola)": "KO",
    "DIS (Disney)": "DIS",
    "JNJ (Johnson & Johnson)": "JNJ",
    "V (Visa)": "V",
    "WMT (Walmart)": "WMT"
}

def analisar_saude_ativos(lista_tickers):
    dados_filtrados = []
    for ticker in lista_tickers:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            
            nome = info.get("longName", ticker)
            preco = info.get("currentPrice", info.get("regularMarketPrice", 0)) or 0
            
            # --- MÉTRICAS EXPANDIDAS DE SAÚDE E VALUATION ---
            roe = info.get("returnOnEquity", 0) or 0
            margem = info.get("profitMargins", 0) or 0
            divida = info.get("debtToEquity", 0) or 0
            pe_ratio = info.get("trailingPE", "N/A")
            price_to_book = info.get("priceToBook", "N/A")  # P/VP (Preço sobre Valor Patrimonial)
            dividend_yield = info.get("dividendYield", 0) or 0
            
            # Formatação amigável das métricas de valuation
            pe_str = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A"
            pvp_str = f"{price_to_book:.2f}" if isinstance(price_to_book, (int, float)) else "N/A"
            dy_str = f"{dividend_yield * 100:.2f}%" if dividend_yield else "0.00%"

            # Critério de Saúde Otimizado
            if roe > 0.12 and margem > 0.10 and divida < 120:
                saude, sugestao = "Excelente ❤️", "Forte Compra / Manter"
            elif roe > 0.05 and margem > 0.05 and divida < 200:
                saude, sugestao = "Regular 🟡", "Observar / Neutro"
            else:
                saude, sugestao = "Fraca ⚠️", "Evitar / Maior Risco"
                
            dados_filtrados.append({
                "Ticker": ticker, 
                "Nome": nome, 
                "Preço": preco,
                "ROE (Eficiência)": f"{roe*100:.2f}%", 
                "Margem Líquida": f"{margem*100:.2f}%", 
                "Dívida/Patr.": f"{divida:.1f}%" if divida else "0.0%",
                "P/L (Múltiplo)": pe_str,
                "P/VP (Patrimônio)": pvp_str,
                "Div. Yield": dy_str,
                "Saúde": saude, 
                "Sugestão": sugestao
            })
        except:
            continue
    return pd.DataFrame(dados_filtrados)

def pedir_analise_ia(df_dados, mercado_nome):
    if not gemini_api_key:
        return "⚠️ Para receber o relatório da IA, insira sua chave API na barra lateral."
    
    try:
        # Força o uso do modelo de produção atualizado
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        dados_texto = df_dados.to_string(index=False)
        
        prompt = f"""
        Você é um analista financeiro sênior extremamente analítico.
        Abaixo estão os dados financeiros reais extraídos agora do mercado para o segmento: {mercado_nome}.
        
        Dados das Empresas:
        {dados_texto}
        
        Com base nesses indicadores:
        1. Faça um raio-X detalhado apontando quais empresas apresentam a melhor combinação de alta lucratividade (ROE/Margem), dívida saudável e valuation atraente (P/L e P/VP baixos). Explique o motivo.
        2. Alerte sobre qualquer distorção (ex: endividamento muito alto, ou múltiplos P/L exagerados que indiquem que a ação está cara).
        3. Crie uma conclusão profissional indicando uma estratégia equilibrada de alocação de ativos baseada nesta lista.
        
        Responda em português, use formatação limpa com tópicos e negritos. Seja direto e técnico.
        """
        
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"❌ Erro ao conectar com o Gemini: {e}. Verifique se sua chave está correta e ativa."

# --- INTERFACE ---
menu = st.sidebar.radio("Navegação", ["Carteira Recomendada IA", "Análise Individual Avançada"])

if menu == "Carteira Recomendada IA":
    st.header("🎯 Sugestão de Carteira Otimizada por IA")
    mercado = st.selectbox("Escolha o Mercado para Scannear:", ["Mercado Brasileiro (B3)", "Mercado Internacional (EUA)"])
    
    # Extrai os tickers dos dicionários globais para a varredura automática
    lista_ativos = list(DIC_ACOES_BR.values()) if mercado == "Mercado Brasileiro (B3)" else list(DIC_ACOES_EUA.values())
    
    if st.button("Executar Análise Completa em Tempo Real"):
        with st.spinner("Acessando bases financeiras e gerando insights com IA..."):
            df_resultado = analisar_saude_ativos(lista_ativos)
            
            if not df_resultado.empty:
                st.subheader("📋 Dados Avançados de Saúde & Valuation Coletados Ao Vivo")
                st.dataframe(df_resultado, use_container_width=True)
                
                st.subheader("🧠 Relatório e Auditoria da Inteligência Artificial")
                relatorio_ia = pedir_analise_ia(df_resultado, mercado)
                st.markdown(relatorio_ia)
            else:
                st.error("Erro ao coletar dados do Yahoo Finance para a lista informada.")

elif menu == "Análise Individual Avançada":
    st.header("🔍 Busca Inteligente & Laudo de Ativos")
    
    mercado_ind = st.radio("Selecione o mercado do ativo:", ["Nacional (B3)", "Internacional (EUA)", "Digitar Ticker Manualmente"])
    
    ticker_final = ""
    
    if mercado_ind == "Nacional (B3)":
        # Caixa de seleção com preenchimento automático para o Brasil
        escolha = st.selectbox("Comece a digitar ou selecione a ação brasileira:", list(DIC_ACOES_BR.keys()))
        ticker_final = DIC_ACOES_BR[escolha]
        
    elif mercado_ind == "Internacional (EUA)":
        # Caixa de seleção com preenchimento automático para os EUA
        escolha = st.selectbox("Comece a digitar ou selecione a ação americana:", list(DIC_ACOES_EUA.keys()))
        ticker_final = DIC_ACOES_EUA[escolha]
        
    else:
        # Opção caso queira testar uma que não está na lista pré-definida
        ticker_final = st.text_input("Digite o ticker exato (Ex: Sanepar seria SAPR4.SA, ou Tesla seria TSLA):", value="PETR4.SA").strip().upper()
        
    if st.button("Gerar Diagnóstico Avançado"):
        if ticker_final:
            with st.spinner(f"Analisando balanço de {ticker_final}..."):
                df_individual = analisar_saude_ativos([ticker_final])
                if not df_individual.empty:
                    st.subheader(f"📊 Indicadores Fundamentais de {ticker_final}")
                    st.dataframe(df_individual, use_container_width=True)
                    
                    st.subheader("🧠 Parecer Técnico Emitido pela Inteligência Artificial")
                    relatorio_ia = pedir_analise_ia(df_individual, f"Ativo Específico ({ticker_final})")
                    st.markdown(relatorio_ia)
                else:
                    st.error("Não encontramos dados suficientes para este ativo. Certifique-se de usar o sufixo .SA para ações brasileiras.")
