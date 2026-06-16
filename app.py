import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="Scanner de Mercado com IA", layout="wide")

st.title("🤖 Scanner de Mercado & Relatórios com IA")
st.subheader("Análise quantitativa integrada ao Google Gemini")

# --- CONFIGURAÇÃO DA IA NA BARRA LATERAL ---
st.sidebar.header("🤖 Configuração da Inteligência Artificial")
gemini_api_key = st.sidebar.text_input("Digite sua Gemini API Key:", type="password")

st.sidebar.markdown("[Como conseguir uma chave grátis?](https://aistudio.google.com/)")
st.sidebar.markdown("---")

# Listas padrão de monitoramento
ACOES_BR = ["VALE3.SA", "PETR4.SA", "ITUB4.SA", "WEGE3.SA", "ABEV3.SA"]
ACOES_EUA = ["AAPL", "MSFT", "GOOGL", "NVDA", "KO"]

def analisar_saude_ativos(lista_tickers):
    dados_filtrados = []
    for ticker in lista_ativos:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            nome = info.get("longName", ticker)
            preco = info.get("currentPrice", info.get("regularMarketPrice", 0))
            roe = info.get("returnOnEquity", 0) or 0
            margem = info.get("profitMargins", 0) or 0
            divida = info.get("debtToEquity", 0) or 0
            
            if roe > 0.10 and margem > 0.08 and divida < 150:
                saude, sugestao = "Excelente ❤️", "Forte Compra / Manter"
            elif roe > 0.05 and margem > 0.05:
                saude, sugestao = "Regular 🟡", "Observar / Neutro"
            else:
                saude, sugestao = "Fraca ⚠️", "Evitar no momento"
                
            dados_filtrados.append({
                "Ticker": ticker, "Nome": nome, "Preço": preco,
                "ROE": f"{roe*100:.2f}%", "Margem": f"{margem*100:.2f}%", "Dívida/Patr.": f"{divida:.1f}%",
                "Saúde": saude, "Sugestão": sugestao
            })
        except:
            continue
    return pd.DataFrame(dados_filtrados)

def pedir_analise_ia(df_dados, mercado_nome):
    """Envia os dados reais capturados para a IA criar o relatório resumo"""
    if not gemini_api_key:
        return "⚠️ Para receber o relatório da IA, insira sua chave API na barra lateral."
    
    try:
        # Configura a IA com a sua chave informada
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Transforma os dados da tabela em texto legível para a IA ler
        dados_texto = df_dados.to_string(index=False)
        
        prompt = f"""
        Você é um analista financeiro sênior experiente e amigável.
        Abaixo estão os dados reais e atuais de algumas ações do {mercado_nome}, coletados agora do mercado.
        A saúde foi pré-calculada com base em ROE, Margem de Lucro e Endividamento.
        
        Dados das Empresas:
        {dados_texto}
        
        Com base exclusivamente nesses dados:
        1. Faça um resumo direto destacando as 2 melhores empresas saudáveis para investir hoje e explique o porquê de forma simples.
        2. Diga qual empresa deve ser evitada ou olhada com muito cuidado devido aos números apresentados.
        3. Dê uma dica educacional rápida de até 2 linhas sobre gestão de risco.
        Responda em português de forma escaneável, usando tópicos e negritos. Seja direto.
        """
        
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"❌ Erro ao conectar com o Gemini: {e}. Verifique se sua chave está correta."

# --- INTERFACE ---
menu = st.sidebar.radio("Navegação", ["Carteira Recomendada IA", "Análise Individual"])

if menu == "Carteira Recomendada IA":
    st.header("🎯 Sugestão de Carteira Otimizada por IA")
    mercado = st.selectbox("Escolha o Mercado:", ["Mercado Brasileiro (B3)", "Mercado Internacional (EUA)"])
    lista_ativos = ACOES_BR if mercado == "Mercado Brasileiro (B3)" else ACOES_EUA
    
    if st.button("Executar Análise em Tempo Real"):
        with st.spinner("Buscando dados financeiros e consultando a IA..."):
            # 1. Busca os dados reais
            df_resultado = analisar_saude_ativos(lista_ativos)
            
            if not df_resultado.empty:
                st.subheader("📋 Dados de Saúde Coletados Ao Vivo")
                st.dataframe(df_resultado, use_container_width=True)
                
                # 2. IA gera o relatório interpretando a tabela
                st.subheader("🤖 Relatório e Sugestões da Inteligência Artificial")
                relatorio_ia = pedir_analise_ia(df_resultado, mercado)
                st.markdown(relatorio_ia)
            else:
                st.error("Erro ao buscar dados do Yahoo Finance.")

elif menu == "Análise Individual":
    st.header("🔍 Parecer do Especialista (IA) sobre um Ativo")
    ticker_usuario = st.text_input("Digite o ticker (ex: WEGE3.SA ou AAPL):", value="WEGE3.SA")
    lista_ativos = [ticker_usuario]
    
    if st.button("Pedir Laudo da IA"):
        with st.spinner("Avaliando balanços..."):
            df_individual = analisar_saude_ativos(lista_ativos)
            if not df_individual.empty:
                st.dataframe(df_individual)
                
                st.subheader("🧠 Análise Cognitiva da IA")
                relatorio_ia = pedir_analise_ia(df_individual, "Ativo Individual")
                st.markdown(relatorio_ia)
            else:
                st.error("Ticker inválido ou sem dados disponíveis.")
