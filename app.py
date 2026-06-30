import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time
import json

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="InvestAI Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS PERSONALIZADO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.4rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.5px;
    }
    .sub-title { color: #64748B; font-size: 1rem; margin-top: -0.5rem; }

    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.1rem 1.2rem;
        text-align: center;
    }
    .metric-card .label { font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; }
    .metric-card .value { font-size: 1.45rem; font-weight: 700; color: #0F172A; margin-top: 0.2rem; }

    /* Decisão badges */
    .badge-buy   { background:#DCFCE7; color:#166534; border-radius:6px; padding:3px 10px; font-weight:600; font-size:0.82rem; }
    .badge-watch { background:#FEF9C3; color:#854D0E; border-radius:6px; padding:3px 10px; font-weight:600; font-size:0.82rem; }
    .badge-avoid { background:#FEE2E2; color:#991B1B; border-radius:6px; padding:3px 10px; font-weight:600; font-size:0.82rem; }

    /* Ranking card */
    .rank-card {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 100%);
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        color: #F8FAFC;
        margin-bottom: 0.8rem;
        border-left: 4px solid #38BDF8;
    }
    .rank-card .rank-num { font-size: 2rem; font-weight: 700; color: #38BDF8; }
    .rank-card .rank-ticker { font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 700; }
    .rank-card .rank-score { font-size: 0.85rem; color: #94A3B8; }
    .rank-card .rank-reason { font-size: 0.88rem; color: #CBD5E1; margin-top: 0.4rem; line-height: 1.5; }

    /* Per-stock AI expander */
    .ai-analysis-box {
        background: #F0F9FF;
        border: 1px solid #BAE6FD;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        font-size: 0.9rem;
        color: #0C4A6E;
        line-height: 1.7;
    }

    div[data-testid="stExpander"] { border: 1px solid #E2E8F0 !important; border-radius: 10px !important; }

    .section-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #38BDF8;
        margin-bottom: 1.2rem;
    }

    .stButton > button {
        background: #0F172A;
        color: #F8FAFC;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.55rem 1.4rem;
        transition: background 0.2s;
    }
    .stButton > button:hover { background: #1E40AF; }

    .sidebar-note { font-size: 0.8rem; color: #94A3B8; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    anthropic_api_key = st.text_input("🔑 Chave da API Anthropic (Claude):", type="password",
                                       help="Usada para análises por ativo e ranking inteligente.")
    st.markdown("[→ Obter chave grátis](https://console.anthropic.com/)", unsafe_allow_html=False)
    st.markdown("---")
    st.markdown("**Modelo:** Claude Sonnet 4.6")
    st.markdown('<p class="sidebar-note">A IA analisa cada ativo individualmente e gera um ranking fundamentado com justificativas detalhadas.</p>', unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("📌 Navegação", [
        "🎯 Scanner de Mercado",
        "🏆 Ranking IA — Melhores para Comprar",
        "🧮 Calculadora de Alocação",
        "🔍 Busca Global de Ativo",
    ])

# ─────────────────────────────────────────────────────────────────────────────
# DADOS FIXOS
# ─────────────────────────────────────────────────────────────────────────────
SCANNER_BR_ACOES = [
    "VALE3.SA","PETR4.SA","ITUB4.SA","WEGE3.SA","BBAS3.SA",
    "BBDC4.SA","ABEV3.SA","ELET3.SA","RENT3.SA","ITSA4.SA",
    "GGBR4.SA","LREN3.SA","EQTL3.SA","RADL3.SA","VBBR3.SA",
]
SCANNER_BR_FIIS = [
    "HGLG11.SA","XPLG11.SA","KNCR11.SA","MXRF11.SA","BTLG11.SA",
    "XPML11.SA","VISC11.SA","KNRI11.SA","HGRU11.SA","HGBS11.SA",
    "RECR11.SA","VILG11.SA","CPTS11.SA","TRXF11.SA","TGAR11.SA",
]
SCANNER_EUA_ACOES = [
    "AAPL","MSFT","GOOGL","AMZN","META",
    "NVDA","TSLA","KO","PEP","DIS",
    "JNJ","V","WMT","XOM","JPM",
]
SCANNER_EUA_REITS = [
    "O","STAG","PLD","AMT","SPG",
    "CCI","EQIX","PSA","DLR","SBAC",
    "WELL","AVB","VRE","WY","NLY",
]

# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ─────────────────────────────────────────────────────────────────────────────
def buscar_ticker_global(termo):
    if not termo or len(termo) < 2:
        return []
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={termo}&quotesCount=8&newsCount=0"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
        out = []
        for q in r.get("quotes", []):
            tipo = q.get("quoteType", "N/A")
            tipo_pt = {"EQUITY": "Ação", "ETF": "ETF/FII"}.get(tipo, tipo)
            out.append({
                "label": f"{q.get('symbol')} - {q.get('longname', q.get('shortname',''))} [{tipo_pt} | {q.get('exchDisp','Global')}]",
                "ticker": q.get("symbol"),
            })
        return out
    except:
        return []


def analisar_ativo(ticker: str) -> dict:
    """Retorna dict com todos os dados fundamentalistas de um ticker."""
    ticker_limpo = ticker.strip().upper()
    try:
        t = yf.Ticker(ticker_limpo)
        info = t.info

        nome        = info.get("longName", ticker_limpo)
        moeda       = info.get("financialCurrency", info.get("currency", "USD"))
        preco_bruto = info.get("currentPrice", info.get("regularMarketPrice", 0)) or 0
        prefix      = "R$ " if moeda == "BRL" else f"{moeda} "
        preco_fmt   = f"{prefix}{preco_bruto:,.2f}"

        tipo     = info.get("quoteType", "N/A")
        setor    = str(info.get("sector", "")).lower()
        industria= str(info.get("industry", "")).lower()
        is_fii   = ("11.SA" in ticker_limpo or ticker_limpo in SCANNER_EUA_REITS
                    or tipo == "ETF" or "reit" in industria or "real estate" in setor)

        roe    = info.get("returnOnEquity", 0) or 0
        margem = info.get("profitMargins", 0) or 0
        divida = info.get("debtToEquity", 0) or 0
        pe     = info.get("trailingPE")
        pvp    = info.get("priceToBook")
        beta   = info.get("beta")
        ev_ebitda = info.get("enterpriseToEbitda")
        mkt_cap   = info.get("marketCap", 0) or 0
        payout    = info.get("payoutRatio", 0) or 0
        cresc_rec = info.get("revenueGrowth", 0) or 0
        cresc_luc = info.get("earningsGrowth", 0) or 0

        raw_dy = info.get("dividendYield", 0) or 0
        dy = raw_dy if raw_dy > 1 else raw_dy * 100

        # Score interno (0–100)
        score = 0
        if not is_fii:
            if roe > 0.20:   score += 25
            elif roe > 0.11: score += 15
            elif roe > 0.04: score += 5

            if margem > 0.20: score += 20
            elif margem > 0.09: score += 12
            elif margem > 0.04: score += 5

            if divida == 0 or divida < 60:  score += 15
            elif divida < 140:              score += 8

            if isinstance(pe, (int, float)) and 0 < pe < 15:    score += 15
            elif isinstance(pe, (int, float)) and 15 <= pe < 25: score += 8

            if isinstance(pvp, (int, float)) and 0 < pvp < 1.5: score += 10
            elif isinstance(pvp, (int, float)) and pvp < 3:     score += 5

            if cresc_luc > 0.15: score += 10
            elif cresc_luc > 0:  score += 5

            if dy > 3: score += 5
        else:
            if isinstance(pvp, (int, float)) and 0.80 <= pvp <= 1.10: score += 30
            elif isinstance(pvp, (int, float)) and pvp <= 1.25:       score += 15
            if dy > 8:   score += 30
            elif dy > 6: score += 20
            elif dy > 4: score += 10
            if dy > 0 and payout < 0.95: score += 15
            score += 10  # baseline

        # Decisão
        if is_fii:
            if isinstance(pvp, (int, float)) and 0.80 <= pvp <= 1.25 and dy > 4.5:
                decisao = "🔥 COMPRAR"
            elif dy > 3.5:
                decisao = "⚠️ QUARENTENA"
            else:
                decisao = "❌ EVITAR"
        else:
            if roe > 0.11 and margem > 0.09 and (divida < 140 or divida == 0):
                decisao = "🔥 COMPRAR"
            elif roe > 0.04 and margem > 0.04:
                decisao = "⚠️ QUARENTENA"
            else:
                decisao = "❌ EVITAR"

        return {
            "ticker": ticker_limpo, "nome": nome, "preco": preco_fmt, "preco_bruto": preco_bruto,
            "moeda": moeda, "is_fii": is_fii, "classe": "FII/REIT" if is_fii else "Ação",
            "roe": roe, "margem": margem, "divida": divida,
            "pe": pe, "pvp": pvp, "beta": beta, "ev_ebitda": ev_ebitda,
            "mkt_cap": mkt_cap, "dy": dy, "payout": payout,
            "cresc_rec": cresc_rec, "cresc_luc": cresc_luc,
            "setor": info.get("sector", "N/A"), "industria": info.get("industry", "N/A"),
            "decisao": decisao, "score": min(score, 100),
            "ok": True,
        }
    except Exception as e:
        return {"ticker": ticker_limpo, "nome": "N/A", "preco": "N/A", "decisao": "⚠️ ERRO",
                "score": 0, "ok": False, "is_fii": "11.SA" in ticker_limpo.upper(),
                "classe": "FII/REIT" if "11.SA" in ticker_limpo.upper() else "Ação"}


def fmt_pct(v, mult=100):
    if isinstance(v, (int, float)):
        return f"{v*mult:.2f}%"
    return "N/A"

def fmt_num(v, dec=2):
    if isinstance(v, (int, float)):
        return f"{v:.{dec}f}"
    return "N/A"

def fmt_bi(v):
    if isinstance(v, (int, float)) and v:
        if v >= 1e12: return f"{v/1e12:.2f} T"
        if v >= 1e9:  return f"{v/1e9:.2f} B"
        if v >= 1e6:  return f"{v/1e6:.2f} M"
        return str(v)
    return "N/A"


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES DE IA (Claude via Anthropic API)
# ─────────────────────────────────────────────────────────────────────────────
def _claude(prompt: str, system: str = "", max_tokens: int = 900) -> str:
    if not anthropic_api_key:
        return "⚠️ Insira sua chave de API Anthropic na barra lateral para ativar a análise de IA."
    headers = {
        "x-api-key": anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system

    try:
        r = requests.post("https://api.anthropic.com/v1/messages", headers=headers,
                          json=body, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data["content"][0]["text"]
    except requests.exceptions.HTTPError as e:
        return f"❌ Erro HTTP {r.status_code}: {r.text}"
    except Exception as e:
        return f"❌ Erro: {e}"


def analise_ia_por_ativo(d: dict) -> str:
    """Análise individual de um ativo."""
    system = (
        "Você é um analista fundamentalista sênior especializado em mercados brasileiro e americano. "
        "Responda sempre em português, de forma objetiva, em tópicos curtos com negrito nos destaques. "
        "Máximo 250 palavras."
    )
    prompt = f"""
Analise o ativo abaixo com base nos dados fornecidos:

**{d.get('ticker')} — {d.get('nome')}**
- Classe: {d.get('classe')} | Setor: {d.get('setor')} | Indústria: {d.get('industria')}
- Preço atual: {d.get('preco')}
- ROE: {fmt_pct(d.get('roe'))} | Margem Líquida: {fmt_pct(d.get('margem'))}
- Dívida/Patrimônio: {fmt_num(d.get('divida'))}%
- P/L: {fmt_num(d.get('pe'))} | P/VP: {fmt_num(d.get('pvp'))}
- EV/EBITDA: {fmt_num(d.get('ev_ebitda'))} | Beta: {fmt_num(d.get('beta'))}
- Dividend Yield: {d.get('dy', 0):.2f}% | Payout: {fmt_pct(d.get('payout'))}
- Crescimento Receita: {fmt_pct(d.get('cresc_rec'))} | Crescimento Lucro: {fmt_pct(d.get('cresc_luc'))}
- Market Cap: {fmt_bi(d.get('mkt_cap'))}
- Decisão automática do sistema: {d.get('decisao')} | Score interno: {d.get('score')}/100

Forneça:
1. **Pontos fortes** do ativo
2. **Pontos de atenção / riscos**
3. **Veredito final** em 1 frase (comprar, aguardar ou evitar e por quê)
"""
    return _claude(prompt, system, max_tokens=500)


def ranking_ia(lista_dados: list) -> str:
    """Gera ranking dos melhores ativos para comprar."""
    system = (
        "Você é um gestor de portfólio experiente focado em retorno ajustado ao risco. "
        "Responda sempre em português. Use negritos e tópicos. Seja direto e assertivo."
    )
    resumo = []
    for d in lista_dados:
        resumo.append({
            "ticker": d.get("ticker"), "classe": d.get("classe"),
            "roe": fmt_pct(d.get("roe")), "margem": fmt_pct(d.get("margem")),
            "divida": d.get("divida"), "pe": fmt_num(d.get("pe")),
            "pvp": fmt_num(d.get("pvp")), "dy": f"{d.get('dy',0):.2f}%",
            "cresc_luc": fmt_pct(d.get("cresc_luc")), "score": d.get("score"),
            "decisao": d.get("decisao"),
        })

    prompt = f"""
Com base nos dados abaixo de {len(lista_dados)} ativos, crie um **Ranking das Melhores Oportunidades de Compra** agora.

Dados dos ativos:
{json.dumps(resumo, ensure_ascii=False, indent=2)}

Instrução:
- Eleja os **top 5 melhores ativos** para comprar agora, em ordem de prioridade.
- Para cada um, escreva: posição (#1, #2…), ticker, e **2–3 linhas justificando** com base nos indicadores.
- Ao final, indique até **2 ativos para evitar** com justificativa breve.
- Conclua com uma frase sobre a estratégia geral recomendada para o portfólio.
"""
    return _claude(prompt, system, max_tokens=900)


def analise_carteira_ia(df: pd.DataFrame) -> str:
    """Análise geral da carteira escaneada."""
    system = "Você é analista financeiro sênior. Responda em português com tópicos e negritos. Máximo 300 palavras."
    prompt = f"""
Analise a carteira escaneada abaixo e gere um relatório estratégico conciso:

{df[['ticker','classe','roe','margem','pe','pvp','dy','decisao','score']].to_string(index=False) if 'ticker' in df.columns else df.to_string(index=False)}

Destaque:
1. Oportunidades mais relevantes (sinais de COMPRA)
2. Alertas críticos (EVITAR)
3. Recomendação de estratégia para perfil moderado
"""
    return _claude(prompt, system, max_tokens=700)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: converte lista de dicts em DataFrame exibível
# ─────────────────────────────────────────────────────────────────────────────
def dicts_para_df(lista: list) -> pd.DataFrame:
    rows = []
    for d in lista:
        rows.append({
            "Ticker":      d.get("ticker",""),
            "Nome":        d.get("nome",""),
            "Classe":      d.get("classe",""),
            "Preço":       d.get("preco","N/A"),
            "ROE":         fmt_pct(d.get("roe")) if not d.get("is_fii") else "N/A",
            "Margem Líq.": fmt_pct(d.get("margem")) if not d.get("is_fii") else "N/A",
            "Dívida/Pat.": f"{d.get('divida',0):.1f}%" if d.get("divida") else "0.0%",
            "P/L":         fmt_num(d.get("pe")),
            "P/VP":        fmt_num(d.get("pvp")),
            "DY":          f"{d.get('dy',0):.2f}%",
            "Score":       d.get("score", 0),
            "Decisão":     d.get("decisao","N/A"),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 1 — SCANNER DE MERCADO
# ─────────────────────────────────────────────────────────────────────────────
if menu == "🎯 Scanner de Mercado":
    st.markdown('<p class="main-title">📊 Scanner de Mercado</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Análise fundamentalista em tempo real com avaliação individual por IA</p>', unsafe_allow_html=True)
    st.markdown("---")

    mercado = st.selectbox("Selecione o mercado:", ["🇧🇷 Brasil (B3)", "🇺🇸 Estados Unidos (NYSE/NASDAQ)"])
    is_br   = "Brasil" in mercado

    col_a, col_b = st.columns(2)
    tipo_scan = col_a.radio("Tipo de ativo:", ["Ações", "FIIs / REITs", "Ambos"], horizontal=True)
    habilitar_ia_por_ativo = col_b.checkbox("🤖 Análise de IA por ativo (mais lento)", value=False)

    if st.button("🚀 Iniciar Varredura"):
        lista_acoes = SCANNER_BR_ACOES if is_br else SCANNER_EUA_ACOES
        lista_fiis  = SCANNER_BR_FIIS  if is_br else SCANNER_EUA_REITS

        if tipo_scan == "Ações":         listas = [("Ações", lista_acoes)]
        elif tipo_scan == "FIIs / REITs": listas = [("FIIs/REITs", lista_fiis)]
        else:                            listas = [("Ações", lista_acoes), ("FIIs/REITs", lista_fiis)]

        todos_dados = []

        for nome_lista, lista in listas:
            st.markdown(f'<p class="section-title">📈 {nome_lista}</p>', unsafe_allow_html=True)
            progresso = st.progress(0, text=f"Coletando dados de {nome_lista}…")
            dados_lista = []

            for i, tk in enumerate(lista):
                d = analisar_ativo(tk)
                dados_lista.append(d)
                todos_dados.append(d)
                progresso.progress((i + 1) / len(lista), text=f"({i+1}/{len(lista)}) {tk}")

            progresso.empty()
            df_lista = dicts_para_df(dados_lista)

            # Colorir coluna decisão
            def colorir(val):
                if "COMPRAR" in str(val): return "background-color:#DCFCE7; color:#166534; font-weight:600"
                if "QUARENTENA" in str(val): return "background-color:#FEF9C3; color:#854D0E; font-weight:600"
                if "EVITAR" in str(val): return "background-color:#FEE2E2; color:#991B1B; font-weight:600"
                return ""

            styled = df_lista.style.applymap(colorir, subset=["Decisão"])
            st.dataframe(styled, use_container_width=True, hide_index=True)

            # IA por ativo
            if habilitar_ia_por_ativo and anthropic_api_key:
                st.markdown("#### 🤖 Análise individual por IA")
                for d in dados_lista:
                    if not d.get("ok"): continue
                    with st.expander(f"{'🔥' if 'COMPRAR' in d['decisao'] else '⚠️' if 'QUARENTENA' in d['decisao'] else '❌'} {d['ticker']} — {d['nome']}"):
                        with st.spinner("Gerando análise…"):
                            analise = analise_ia_por_ativo(d)
                        st.markdown(f'<div class="ai-analysis-box">{analise}</div>', unsafe_allow_html=True)
            elif habilitar_ia_por_ativo and not anthropic_api_key:
                st.info("Insira sua chave de API na barra lateral para ativar análise por ativo.")

        st.markdown("---")
        # Resumo de COMPRAs
        compras = [d for d in todos_dados if "COMPRAR" in d.get("decisao","")]
        st.markdown(f'<p class="section-title">🔥 Sinais de COMPRA desta varredura ({len(compras)} ativos)</p>', unsafe_allow_html=True)
        if compras:
            st.dataframe(dicts_para_df(compras)[["Ticker","Nome","Classe","Preço","P/VP","DY","Score","Decisão"]], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum ativo com sinal forte de compra nesta rodada.")

        st.markdown("---")
        st.markdown('<p class="section-title">🧠 Relatório Estratégico Geral</p>', unsafe_allow_html=True)
        with st.spinner("Gerando relatório estratégico…"):
            relatorio = analise_carteira_ia(dicts_para_df(todos_dados))
        st.markdown(relatorio)


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 2 — RANKING IA
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "🏆 Ranking IA — Melhores para Comprar":
    st.markdown('<p class="main-title">🏆 Ranking IA — Melhores para Comprar</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">A IA analisa todos os ativos e elege os top 5 com justificativa detalhada</p>', unsafe_allow_html=True)
    st.markdown("---")

    mercado2 = st.selectbox("Mercado:", ["🇧🇷 Brasil (B3)", "🇺🇸 Estados Unidos (NYSE/NASDAQ)", "🌎 Global (BR + EUA)"])
    tipo_rank = st.radio("Classe de ativos:", ["Ações", "FIIs / REITs", "Ambos"], horizontal=True)

    if st.button("🏆 Gerar Ranking com IA"):
        if not anthropic_api_key:
            st.warning("⚠️ Insira a chave de API Anthropic para usar esta funcionalidade.")
            st.stop()

        # Montar lista conforme seleção
        def montar_lista(mercado_str, tipo_str):
            br  = "Brasil" in mercado_str or "Global" in mercado_str
            eua = "Estados" in mercado_str or "Global" in mercado_str
            lst = []
            if tipo_str in ("Ações", "Ambos"):
                if br:  lst += SCANNER_BR_ACOES
                if eua: lst += SCANNER_EUA_ACOES
            if tipo_str in ("FIIs / REITs", "Ambos"):
                if br:  lst += SCANNER_BR_FIIS
                if eua: lst += SCANNER_EUA_REITS
            return list(dict.fromkeys(lst))  # sem duplicatas

        lista_rank = montar_lista(mercado2, tipo_rank)
        n = len(lista_rank)

        progress_bar = st.progress(0, text="Coletando dados para o ranking…")
        todos = []
        for i, tk in enumerate(lista_rank):
            todos.append(analisar_ativo(tk))
            progress_bar.progress((i + 1) / n, text=f"({i+1}/{n}) {tk}")
        progress_bar.empty()

        # Exibir tabela resumo ordenada por score
        df_rank = dicts_para_df(todos).sort_values("Score", ascending=False).reset_index(drop=True)
        df_rank.index = df_rank.index + 1

        col1, col2, col3 = st.columns([2, 1, 1])
        col1.metric("Ativos analisados", n)
        col2.metric("Sinais de COMPRA", sum(1 for d in todos if "COMPRAR" in d.get("decisao","")))
        col3.metric("Score médio", f"{df_rank['Score'].mean():.0f}/100")

        st.markdown("#### 📋 Tabela Completa (ordenada por Score)")
        st.dataframe(df_rank, use_container_width=True)

        st.markdown("---")
        st.markdown('<p class="section-title">🤖 Ranking Inteligente gerado pela IA</p>', unsafe_allow_html=True)
        with st.spinner("A IA está elaborando o ranking fundamentado… aguarde."):
            resultado_ranking = ranking_ia(todos)
        st.markdown(resultado_ranking)

        st.markdown("---")
        st.markdown('<p class="section-title">🔬 Análise Detalhada por Ativo (Top 10 por Score)</p>', unsafe_allow_html=True)
        top10 = sorted(todos, key=lambda x: x.get("score", 0), reverse=True)[:10]
        for d in top10:
            if not d.get("ok"): continue
            emoji = "🔥" if "COMPRAR" in d["decisao"] else ("⚠️" if "QUARENTENA" in d["decisao"] else "❌")
            with st.expander(f"{emoji} #{top10.index(d)+1} {d['ticker']} — {d['nome']} | Score: {d['score']}/100"):
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Preço", d.get("preco","N/A"))
                col_b.metric("DY", f"{d.get('dy',0):.2f}%")
                col_c.metric("P/VP", fmt_num(d.get("pvp")))
                col_d.metric("ROE", fmt_pct(d.get("roe")))

                with st.spinner("Analisando com IA…"):
                    analise = analise_ia_por_ativo(d)
                st.markdown(f'<div class="ai-analysis-box">{analise}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 3 — CALCULADORA DE ALOCAÇÃO
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "🧮 Calculadora de Alocação":
    st.markdown('<p class="main-title">🧮 Calculadora Patrimonial</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Distribuição calibrada para perfil moderado com foco no mercado nacional</p>', unsafe_allow_html=True)
    st.markdown("---")

    valor = st.number_input("💰 Valor total a investir:", min_value=100.0, value=10000.0, step=500.0, format="%.2f")
    
    st.markdown("#### Distribuição Padrão (Perfil Moderado)")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(f'<div class="metric-card"><div class="label">🔒 Renda Fixa</div><div class="value">R$ {valor*0.60:,.0f}</div><small>60%</small></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="label">🇧🇷 Ações BR</div><div class="value">R$ {valor*0.15:,.0f}</div><small>15%</small></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="label">🏢 FIIs BR</div><div class="value">R$ {valor*0.15:,.0f}</div><small>15%</small></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="label">📈 Ações EUA</div><div class="value">R$ {valor*0.05:,.0f}</div><small>5%</small></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="label">🗽 REITs EUA</div><div class="value">R$ {valor*0.05:,.0f}</div><small>5%</small></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🛒 Monte sua Cesta de Ativos")

    col1, col2 = st.columns(2)
    with col1:
        compras_br    = st.text_input("Ações BR (separadas por vírgula):", "ITUB4.SA, WEGE3.SA")
        compras_fiis  = st.text_input("FIIs BR:", "HGLG11.SA, XPLG11.SA")
    with col2:
        compras_eua   = st.text_input("Ações EUA:", "AAPL, MSFT")
        compras_reits = st.text_input("REITs EUA:", "O, STAG")

    if st.button("📊 Calcular Distribuição Exata"):
        def dividir(texto, valor_classe):
            tickers = [t.strip().upper() for t in texto.split(",") if t.strip()]
            if not tickers: return []
            fatia = valor_classe / len(tickers)
            return [(tk, fatia) for tk in tickers]

        linhas = []
        for tk, v in dividir(compras_br,    valor * 0.15): linhas.append({"Classe":"Ação Brasil",    "Ticker":tk, "Aporte Sugerido":f"R$ {v:,.2f}"})
        for tk, v in dividir(compras_fiis,  valor * 0.15): linhas.append({"Classe":"FII Brasil",     "Ticker":tk, "Aporte Sugerido":f"R$ {v:,.2f}"})
        for tk, v in dividir(compras_eua,   valor * 0.05): linhas.append({"Classe":"Ação EUA",       "Ticker":tk, "Aporte Sugerido":f"R$ {v:,.2f}"})
        for tk, v in dividir(compras_reits, valor * 0.05): linhas.append({"Classe":"REIT EUA",       "Ticker":tk, "Aporte Sugerido":f"R$ {v:,.2f}"})
        linhas.append({"Classe":"Renda Fixa Conservadora","Ticker":"Tesouro Selic / T-Bills",  "Aporte Sugerido":f"R$ {valor*0.30:,.2f}"})
        linhas.append({"Classe":"Renda Fixa Anti-Inflação","Ticker":"Tesouro IPCA+ / TIPS",   "Aporte Sugerido":f"R$ {valor*0.30:,.2f}"})

        df_calc = pd.DataFrame(linhas)
        st.markdown("#### 📋 Boleta de Compras")
        st.dataframe(df_calc, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 4 — BUSCA GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "🔍 Busca Global de Ativo":
    st.markdown('<p class="main-title">🔍 Busca Global de Ativo</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Pesquise qualquer ação, FII, REIT ou ETF de qualquer bolsa do mundo</p>', unsafe_allow_html=True)
    st.markdown("---")

    busca = st.text_input("Digite o nome da empresa ou ticker:", placeholder="Ex: Apple, Petrobras, ITUB4…")

    if busca:
        sugestoes = buscar_ticker_global(busca)
        if sugestoes:
            selecao = st.selectbox("Resultados:", [s["label"] for s in sugestoes])
            ticker_alvo = next(s["ticker"] for s in sugestoes if s["label"] == selecao)

            col_btn1, col_btn2 = st.columns(2)
            analisar_fund = col_btn1.button(f"📊 Análise Fundamentalista de {ticker_alvo}")
            analisar_ia   = col_btn2.button(f"🤖 Análise Completa com IA de {ticker_alvo}")

            if analisar_fund or analisar_ia:
                with st.spinner(f"Coletando dados de {ticker_alvo}…"):
                    d = analisar_ativo(ticker_alvo)

                if not d.get("ok"):
                    st.error("Dados insuficientes para análise fundamentalista deste ativo.")
                    st.stop()

                st.markdown(f"### {d['ticker']} — {d['nome']}")
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                c1.metric("Preço",  d["preco"])
                c2.metric("ROE",    fmt_pct(d.get("roe")))
                c3.metric("Margem", fmt_pct(d.get("margem")))
                c4.metric("P/L",    fmt_num(d.get("pe")))
                c5.metric("P/VP",   fmt_num(d.get("pvp")))
                c6.metric("DY",     f"{d.get('dy',0):.2f}%")

                c7, c8, c9, c10 = st.columns(4)
                c7.metric("Beta",      fmt_num(d.get("beta")))
                c8.metric("EV/EBITDA", fmt_num(d.get("ev_ebitda")))
                c9.metric("Cresc. Receita", fmt_pct(d.get("cresc_rec")))
                c10.metric("Market Cap",    fmt_bi(d.get("mkt_cap")))

                st.markdown(f"**Setor:** {d.get('setor','N/A')} | **Indústria:** {d.get('industria','N/A')} | **Score:** {d.get('score')}/100")
                decisao = d["decisao"]
                if "COMPRAR" in decisao:
                    st.success(decisao)
                elif "QUARENTENA" in decisao:
                    st.warning(decisao)
                else:
                    st.error(decisao)

                if analisar_ia:
                    st.markdown("---")
                    st.markdown("#### 🤖 Análise de IA")
                    with st.spinner("Gerando laudo consultivo…"):
                        st.markdown(f'<div class="ai-analysis-box">{analise_ia_por_ativo(d)}</div>', unsafe_allow_html=True)
        else:
            st.warning("Nenhum ativo encontrado para este termo.")
