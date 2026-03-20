import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timezone, timedelta
import os
from pandas.errors import ParserError

# Obter o diretório do script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuração da página
st.set_page_config(
    page_title="Dashboard Jira - Subtarefas",
    page_icon="📊",
    layout="wide"
)

# Seletor de tema na sidebar (no topo)
st.sidebar.markdown("### ⚙️ Configurações")
tema_selecionado = st.sidebar.radio("Tema:", ["🌙 Escuro", "☀️ Claro"], index=0, horizontal=True)
plotly_template = "plotly_white" if tema_selecionado == "☀️ Claro" else "plotly_dark"
plotly_font_color = "#1f1f1f" if tema_selecionado == "☀️ Claro" else "#ffffff"
plotly_paper_bgcolor = "#ffffff" if tema_selecionado == "☀️ Claro" else None
plotly_plot_bgcolor = "#ffffff" if tema_selecionado == "☀️ Claro" else None
plotly_axis_style = dict(
    tickfont=dict(color="#1f1f1f"),
    title_font=dict(color="#1f1f1f"),
    linecolor="#cccccc",
    gridcolor="#e0e0e0"
) if tema_selecionado == "☀️ Claro" else {}

# Aplicar CSS customizado baseado no tema
if tema_selecionado == "☀️ Claro":
    st.markdown("""
    <style>
        /* Tema Claro - Fundo geral */
        .stApp {
            background-color: #f5f5f5 !important;
            color: #1f1f1f !important;
        }
        /* Textos gerais */
        .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, label {
            color: #1f1f1f !important;
        }
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
        }
        [data-testid="stSidebar"] * {
            color: #1f1f1f !important;
        }
        /* Selectbox / dropdowns */
        [data-testid="stSelectbox"] > div > div,
        [data-baseweb="select"] > div,
        [data-baseweb="popover"] {
            background-color: #ffffff !important;
            color: #1f1f1f !important;
            border-color: #cccccc !important;
        }
        [data-baseweb="select"] span,
        [data-baseweb="select"] div {
            color: #1f1f1f !important;
            background-color: #ffffff !important;
        }
        /* Opções do dropdown aberto */
        [data-baseweb="menu"],
        [data-baseweb="menu"] ul,
        [data-baseweb="menu"] li {
            background-color: #ffffff !important;
            color: #1f1f1f !important;
        }
        [data-baseweb="menu"] li:hover {
            background-color: #e8f0fe !important;
        }
        /* Radio buttons */
        [data-testid="stRadio"] label {
            color: #1f1f1f !important;
        }
        /* Métricas */
        .stMetric label {
            color: #555555 !important;
        }
        .stMetric [data-testid="stMetricValue"] {
            color: #1f1f1f !important;
        }
        /* Dataframe / tabelas - wrapper externo */
        [data-testid="stDataFrame"] {
            background-color: #ffffff !important;
        }
        /* Forçar fundo branco no elemento raiz do glide-data-grid */
        [data-testid="stDataFrame"] > div > div {
            background-color: #ffffff !important;
        }
        /* Scrollbar e container interno */
        .stDataFrameResizable,
        [data-testid="stDataFrame"] [class*="wrapper"],
        [data-testid="stDataFrame"] [class*="container"] {
            background-color: #ffffff !important;
        }
        /* Checkbox */
        [data-testid="stCheckbox"] label {
            color: #1f1f1f !important;
        }
        /* Info/success boxes */
        [data-testid="stAlert"] {
            background-color: #e8f0fe !important;
            color: #1f1f1f !important;
        }
        /* Subheaders */
        [data-testid="stHeadingWithActionElements"] h2,
        [data-testid="stHeadingWithActionElements"] h3 {
            color: #1f1f1f !important;
        }
        /* Barra superior (toolbar/header do Streamlit) */
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        .stAppHeader {
            background-color: #ffffff !important;
        }
        /* Textos na barra superior - sem forçar fill para não quebrar ícones SVG */
        header[data-testid="stHeader"] span,
        header[data-testid="stHeader"] p,
        header[data-testid="stHeader"] a {
            color: #1f1f1f !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Título principal
st.markdown("""
<div style="text-align: center; background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
    <h1 style="color: white; margin: 0;">Projeto Migração Stellantis</h1>
    <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0;">Dashboard de Subtarefas - Jira</p>
</div>
""", unsafe_allow_html=True)

# Data de atualização (UTC-3 = horário de Brasília)
brt_time = datetime.now(timezone(timedelta(hours=-3)))
st.markdown(f"**📅 Atualizado em:** {brt_time.strftime('%d/%m/%Y %H:%M:%S')} | **Fase:** FASE 3")
st.markdown("<hr style='margin: 10px 0;'/>", unsafe_allow_html=True)

# Função para carregar dados
def carregar_dados(arquivo):
    if os.path.exists(arquivo):
        try:
            return pd.read_csv(arquivo, encoding='utf-8-sig')
        except ParserError:
            # Fallback para linhas com vírgulas sem aspas no campo "Titulo".
            with open(arquivo, 'r', encoding='utf-8-sig') as f:
                linhas = f.readlines()

            if not linhas:
                return pd.DataFrame()

            cabecalho = linhas[0].strip().split(',')
            if len(cabecalho) != 11:
                raise

            registros = []
            for idx, linha in enumerate(linhas[1:], start=2):
                linha = linha.rstrip('\n').rstrip('\r')
                if not linha:
                    continue

                partes = linha.split(',')
                if len(partes) < 11:
                    # Linha incompleta: ignora de forma segura.
                    continue

                # Estrutura esperada: 5 colunas fixas + Titulo (com vírgulas) + 5 colunas fixas finais.
                inicio = partes[:5]
                fim = partes[-5:]
                titulo = ','.join(partes[5:-5]).strip()
                if titulo.startswith('"') and titulo.endswith('"'):
                    titulo = titulo[1:-1]

                registro = inicio + [titulo] + fim
                if len(registro) == 11:
                    registros.append(registro)

            df = pd.DataFrame(registros, columns=cabecalho)
            return df
    return None

# Carregar arquivo FASE 3
arquivo_selecionado = os.path.join(SCRIPT_DIR, "FASE_3.csv")

df = carregar_dados(arquivo_selecionado)

if df is None:
    st.error(f"Arquivo '{arquivo_selecionado}' nao encontrado!")
    st.info("Execute primeiro o script de extracao para gerar o arquivo CSV.")
    st.stop()

# Filtros na sidebar
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filtros")

# Filtro por Data-Lake
data_lakes_unicos = ['Todas'] + sorted([str(d) for d in df['Data-Lake'].unique() if pd.notna(d) and str(d) != 'N/A'])
data_lake_selecionado = st.sidebar.selectbox("Data-Lake:", data_lakes_unicos, index=0)

# Aplicar filtro de Data-Lake primeiro
df_filtrado = df.copy()
if data_lake_selecionado != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Data-Lake'] == data_lake_selecionado]

# Filtro por História (usando título) - baseado no filtro de Data-Lake
historias_unicas = ['Todas'] + sorted([str(h) for h in df_filtrado['Titulo Historia'].unique() if pd.notna(h)])
historia_selecionada = st.sidebar.selectbox("História:", historias_unicas)

# Aplicar filtro de História
if historia_selecionada != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Titulo Historia'] == historia_selecionada]

# Filtro por Categoria - baseado nos filtros anteriores
categorias_unicas = ['Todas'] + sorted([str(c) for c in df_filtrado['Categoria_Analise'].unique() if pd.notna(c)])
categoria_selecionada = st.sidebar.selectbox("Categoria:", categorias_unicas)

# Aplicar filtro de Categoria
if categoria_selecionada != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Categoria_Analise'] == categoria_selecionada]

# Definir status concluídos e cancelados
status_concluidos = ['Done', 'Closed', 'Resolved', 'Concluído', 'Concluida', 'Canceled', 'Cancelled', 'Cancelado']

# Calcular métricas
total_subtarefas = len(df_filtrado)
concluidas = len(df_filtrado[df_filtrado['Status'].isin(status_concluidos)])
pendentes = total_subtarefas - concluidas
percentual_concluido = (concluidas / total_subtarefas * 100) if total_subtarefas > 0 else 0
percentual_pendente = 100 - percentual_concluido

# Calcular issues abertos há mais de 1 semana (Story Bug, RN, RN-FMK)
categorias_criticas = ['Story Bug', 'RN', 'RN-FMK']
df_nao_concluidos = df_filtrado[~df_filtrado['Status'].isin(status_concluidos)]
df_criticos = df_nao_concluidos[df_nao_concluidos['Categoria_Analise'].isin(categorias_criticas)].copy()

# Converter coluna de data de criação para datetime e calcular diferença
try:
    # Método robusto de parsing de data
    def parse_data_criacao(data_str):
        if pd.isna(data_str) or data_str == '':
            return pd.NaT
        
        # Converte para string e remove espaços
        data_str = str(data_str).strip()
        
        # Tenta parsing com diferentes formatos
        formatos = [
            '%Y-%m-%dT%H:%M:%S.%f%z',  # ISO com microsegundos e timezone
            '%Y-%m-%dT%H:%M:%S%z',      # ISO sem microsegundos com timezone
            '%Y-%m-%d %H:%M:%S',        # Formato padrão sem timezone
            '%d/%m/%Y',                  # Formato BR
        ]
        
        for fmt in formatos:
            try:
                # Remove o timezone manualmente se existir (substitui por Z para UTC)
                if '+' in data_str or data_str.count('-') > 2:
                    # Remove timezone (tudo após o último ':' seguido de dígitos)
                    if 'T' in data_str:
                        data_str_sem_tz = data_str[:data_str.rfind('+' if '+' in data_str else '-')] if ('+' in data_str or data_str.rfind('-') > 10) else data_str
                        return pd.to_datetime(data_str_sem_tz)
                return pd.to_datetime(data_str, format=fmt)
            except:
                continue
        
        # Se nenhum formato funcionou, tenta o parsing automático do pandas
        return pd.to_datetime(data_str, errors='coerce')
    
    # Aplica o parsing robusto
    df_criticos['Data Criacao'] = df_criticos['Data Criacao'].apply(parse_data_criacao)
    
    # Remove linhas com datas inválidas
    df_criticos = df_criticos[df_criticos['Data Criacao'].notna()].copy()
    
    # Calcula dias em aberto
    data_atual = pd.Timestamp.now()
    df_criticos['Dias_Aberto'] = (data_atual - df_criticos['Data Criacao']).dt.days
    
    # Filtra issues com mais de 7 dias abertos
    issues_abertos_1_semana = len(df_criticos[df_criticos['Dias_Aberto'] > 7])
except Exception as e:
    issues_abertos_1_semana = 0
    df_criticos = pd.DataFrame()  # DataFrame vazio em caso de erro

# =====================
# Gráfico de Burn-out semanal (Planejado vs Real)
# =====================
df_lake = pd.read_csv(os.path.join(SCRIPT_DIR, 'datas_esperadas_por_lake.csv'), encoding='utf-8-sig', sep=',')

def normalizar_id_historia(valor):
    if pd.isna(valor):
        return None
    texto = str(valor).strip().upper()
    texto = texto.replace('[', '').replace(']', '')
    texto = ' '.join(texto.split())
    texto = texto.replace(' - ', '-')
    texto = texto.replace(' -', '-')
    texto = texto.replace('- ', '-')
    return texto

# Planejado: sempre baseado no datas_esperadas_por_lake.csv (data_fim por história)
if data_lake_selecionado == 'Todas':
    lakes_fase = df_lake.copy()
else:
    lakes_fase = df_lake[df_lake['lake'] == data_lake_selecionado].copy()

lakes_fase['data_fim'] = pd.to_datetime(lakes_fase['data_fim'], dayfirst=True, errors='coerce')
lakes_fase['id_historia_norm'] = lakes_fase['id_historia'].apply(normalizar_id_historia)

# Planejado agrupado por DIA (data_fim exata)
burn_planejado = (
    lakes_fase.dropna(subset=['data_fim'])
    .groupby('data_fim')
    .size()
    .reset_index(name='planejado')
)
burn_planejado.rename(columns={'data_fim': 'data'}, inplace=True)

# Real: história concluída quando todas as subtarefas estiverem concluídas
df_real_base = df.copy()
if data_lake_selecionado != 'Todas':
    df_real_base = df_real_base[df_real_base['Data-Lake'] == data_lake_selecionado]

df_real_base['id_historia_raw'] = df_real_base['Titulo Historia'].str.extract(r'\[([^\]]+)\]', expand=False)
df_real_base['id_historia_norm'] = df_real_base['id_historia_raw'].apply(normalizar_id_historia)
ids_planejados = set(lakes_fase['id_historia_norm'].dropna().unique())
df_real_base = df_real_base[df_real_base['id_historia_norm'].isin(ids_planejados)].copy()

status_entregue = {'done', 'closed', 'resolved', 'concluído', 'concluida', 'canceled', 'cancelled'}
df_real_base['status_norm'] = df_real_base['Status'].astype(str).str.strip().str.lower()
df_real_base['entregue_subtarefa'] = df_real_base['status_norm'].isin(status_entregue)
df_real_base['data_atualizacao_dt'] = pd.to_datetime(df_real_base['Data Atualizacao'], errors='coerce', utc=True)

# Realizado parcial: cada subtarefa concluída contribui com uma fração da história
totais_por_historia = (
    df_real_base.groupby('id_historia_norm')
    .size()
    .reset_index(name='total_subtarefas_historia')
)

subtarefas_concluidas = df_real_base[
    df_real_base['entregue_subtarefa'] & df_real_base['data_atualizacao_dt'].notna()
].copy()

if not subtarefas_concluidas.empty:
    subtarefas_concluidas = subtarefas_concluidas.merge(
        totais_por_historia,
        on='id_historia_norm',
        how='left'
    )
    subtarefas_concluidas['peso_historia'] = 1 / subtarefas_concluidas['total_subtarefas_historia']
    subtarefas_concluidas['data'] = subtarefas_concluidas['data_atualizacao_dt'].dt.tz_convert(None).dt.normalize()
    burn_real_parcial = (
        subtarefas_concluidas.groupby('data')['peso_historia']
        .sum()
        .reset_index(name='realizado_parcial')
    )
else:
    burn_real_parcial = pd.DataFrame(columns=['data', 'realizado_parcial'])

hist_entregues = (
    df_real_base.groupby('id_historia_norm')
    .agg(
        historia_entregue=('entregue_subtarefa', 'all'),
        data_entrega_real=('data_atualizacao_dt', 'max')
    )
    .reset_index()
)
hist_entregues = hist_entregues[
    hist_entregues['historia_entregue'] & hist_entregues['data_entrega_real'].notna()
].copy()

if not hist_entregues.empty:
    hist_entregues['data'] = hist_entregues['data_entrega_real'].dt.tz_convert(None).dt.normalize()
    burn_real = hist_entregues.groupby('data').size().reset_index(name='realizado')
else:
    burn_real = pd.DataFrame(columns=['data', 'realizado'])

# Junta planejado, realizado total e realizado parcial
burn = pd.merge(burn_planejado, burn_real, on='data', how='outer')
burn = pd.merge(burn, burn_real_parcial, on='data', how='outer').fillna(0)
burn = burn.sort_values('data')
burn['planejado_acum'] = burn['planejado'].cumsum()
burn['realizado_acum'] = burn['realizado'].cumsum()
burn['realizado_parcial_acum'] = burn['realizado_parcial'].cumsum()

# Limita a linha do realizado até a última data de entrega
if not burn_real_parcial.empty:
    ultima_data_real_parcial = burn_real_parcial['data'].max()
    burn_real_parcial_mask = burn['data'] <= ultima_data_real_parcial
else:
    burn_real_parcial_mask = burn['data'] == False

# Projeção: extrapola o ritmo real até as datas finais esperadas
dados_real = burn.loc[burn_real_parcial_mask, ['data', 'realizado_parcial_acum']].copy()
datas_proj = []
valores_proj = []
datas_proj_melhor = []
valores_proj_melhor = []
datas_proj_pior = []
valores_proj_pior = []
ritmo_hist_dia = 0.0
realizado_atual = 0.0

total_planejado = float(burn['planejado'].sum()) if not burn.empty else 0.0
prazo_final_planejado = lakes_fase['data_fim'].max() if 'data_fim' in lakes_fase.columns and not lakes_fase.empty else pd.NaT

if not dados_real.empty and dados_real['realizado_parcial_acum'].iloc[-1] > 0 and pd.notna(prazo_final_planejado):
    x = np.arange(len(dados_real))
    y = dados_real['realizado_parcial_acum'].values

    if len(x) > 1:
        coef = np.polyfit(x, y, 1)
        ritmo_hist_dia = float(coef[0])
    else:
        ritmo_hist_dia = float(y[-1])

    realizado_atual = float(y[-1])
    
    if ritmo_hist_dia > 0 and total_planejado > 0 and realizado_atual < total_planejado:
        ultima_data_real = dados_real['data'].iloc[-1]
        historias_faltantes = total_planejado - realizado_atual
        
        # Cenários de projeção
        ritmo_melhor = ritmo_hist_dia * 1.3  # 30% mais rápido
        ritmo_pior = ritmo_hist_dia * 0.7     # 30% mais lento
        
        # Função auxiliar para gerar projeção
        def gerar_projecao(ritmo, prazo_limite):
            datas = []
            valores = []
            dias_necessarios = int(np.ceil(historias_faltantes / ritmo))
            
            for i in range(dias_necessarios + 1):
                data_proj = ultima_data_real + pd.Timedelta(days=i)
                
                # Se passar da data final planejada, para
                if pd.notna(prazo_limite) and data_proj > prazo_limite:
                    break
                
                valor_proj = realizado_atual + ritmo * i
                if valor_proj >= total_planejado:
                    datas.append(data_proj)
                    valores.append(total_planejado)
                    break
                datas.append(data_proj)
                valores.append(valor_proj)
            
            return datas, valores
        
        # Gera as três projeções
        datas_proj, valores_proj = gerar_projecao(ritmo_hist_dia, prazo_final_planejado)
        datas_proj_melhor, valores_proj_melhor = gerar_projecao(ritmo_melhor, prazo_final_planejado)
        datas_proj_pior, valores_proj_pior = gerar_projecao(ritmo_pior, prazo_final_planejado)

st.subheader('Burn-out (Planejado x Real)')
fig_burn = go.Figure()
fig_burn.add_trace(go.Scatter(
    x=burn['data'],
    y=burn['planejado_acum'],
    mode='lines+markers',
    name='Planejado',
    line=dict(color='royalblue')
))
fig_burn.add_trace(go.Scatter(
    x=burn.loc[burn_real_parcial_mask, 'data'],
    y=burn.loc[burn_real_parcial_mask, 'realizado_parcial_acum'],
    mode='lines+markers',
    name='Realizado',
    line=dict(color='orange')
))

# Adiciona linha de melhor cenário
if len(datas_proj_melhor) > 1:
    fig_burn.add_trace(go.Scatter(
        x=datas_proj_melhor,
        y=valores_proj_melhor,
        mode='lines',
        name='Projeção (Melhor)',
        line=dict(color='green', dash='dash', width=2),
        opacity=0.6
    ))

# Adiciona linha de projeção atual
if len(datas_proj) > 1:
    fig_burn.add_trace(go.Scatter(
        x=datas_proj,
        y=valores_proj,
        mode='lines+markers',
        name='Projeção (Atual)',
        line=dict(color='red', dash='dot', width=2)
    ))

# Adiciona linha de pior cenário
if len(datas_proj_pior) > 1:
    fig_burn.add_trace(go.Scatter(
        x=datas_proj_pior,
        y=valores_proj_pior,
        mode='lines',
        name='Projeção (Pior)',
        line=dict(color='darkred', dash='dash', width=2),
        opacity=0.6
    ))

# Define o range do eixo X para não ultrapassar a data final planejada
if pd.notna(prazo_final_planejado):
    data_inicio_grafico = burn['data'].min() if not burn.empty else prazo_final_planejado
    xaxis_range = [data_inicio_grafico, prazo_final_planejado]
else:
    xaxis_range = None

fig_burn.update_layout(
    xaxis_title='Data',
    yaxis_title='Historias acumuladas',
    legend_title='Legenda',
    height=350,
    template=plotly_template,
    paper_bgcolor=plotly_paper_bgcolor,
    plot_bgcolor=plotly_plot_bgcolor,
    font=dict(color=plotly_font_color),
    xaxis=dict(tickformat='%d/%m/%Y', range=xaxis_range, **plotly_axis_style),
    yaxis=dict(**plotly_axis_style),
    legend=dict(font=dict(color=plotly_font_color))
)
st.plotly_chart(fig_burn, use_container_width=True)

# Indicadores do burn-out
col_burn1, col_burn2, col_burn3, col_burn4 = st.columns(4)

total_historias = int(total_planejado)
historias_concluidas = int(burn['realizado_acum'].max()) if not burn.empty else 0
percentual_concluido_hist = (historias_concluidas / total_historias * 100) if total_historias > 0 else 0

# Calcula as previsões de conclusão para os três cenários
if not dados_real.empty and ritmo_hist_dia > 0 and realizado_atual < total_planejado:
    historias_faltantes = total_planejado - realizado_atual
    
    # Cenário atual
    dias_faltantes = int(np.ceil(historias_faltantes / ritmo_hist_dia))
    previsao_conclusao = dados_real['data'].iloc[-1] + pd.Timedelta(days=dias_faltantes)
    
    # Melhor cenário
    ritmo_melhor = ritmo_hist_dia * 1.3
    dias_faltantes_melhor = int(np.ceil(historias_faltantes / ritmo_melhor))
    previsao_melhor = dados_real['data'].iloc[-1] + pd.Timedelta(days=dias_faltantes_melhor)
    
    # Pior cenário
    ritmo_pior = ritmo_hist_dia * 0.7
    dias_faltantes_pior = int(np.ceil(historias_faltantes / ritmo_pior))
    previsao_pior = dados_real['data'].iloc[-1] + pd.Timedelta(days=dias_faltantes_pior)
elif historias_concluidas >= total_historias:
    # Se já concluiu tudo, usa a última data de entrega
    previsao_conclusao = burn.loc[burn['realizado_acum'] >= total_historias, 'data'].min() if not burn.empty else pd.NaT
    previsao_melhor = previsao_conclusao
    previsao_pior = previsao_conclusao
else:
    previsao_conclusao = pd.NaT
    previsao_melhor = pd.NaT
    previsao_pior = pd.NaT

with col_burn1:
    st.metric(
        label="Total de Histórias",
        value=total_historias
    )

with col_burn2:
    st.metric(
        label="Histórias Concluídas",
        value=historias_concluidas,
        delta=f"{percentual_concluido_hist:.1f}%"
    )

with col_burn3:
    prazo_planejado_txt = prazo_final_planejado.strftime('%d/%m/%Y') if pd.notna(prazo_final_planejado) else 'N/A'
    st.metric(
        label="Data Planejada",
        value=prazo_planejado_txt
    )

with col_burn4:
    # Mostra range de previsão (melhor a pior cenário)
    if pd.notna(previsao_melhor) and pd.notna(previsao_pior):
        previsao_melhor_txt = previsao_melhor.strftime('%d/%m')
        previsao_pior_txt = previsao_pior.strftime('%d/%m/%y')
        previsao_txt = f"{previsao_melhor_txt} a {previsao_pior_txt}"
    else:
        previsao_txt = 'N/A'
    
    # Calcula o delta em dias baseado no cenário atual
    if pd.notna(previsao_conclusao) and pd.notna(prazo_final_planejado):
        delta_dias = (previsao_conclusao - prazo_final_planejado).days
        delta_txt = f"{delta_dias:+d} dias"
        delta_color = "normal" if delta_dias >= 0 else "inverse"
    else:
        delta_txt = None
        delta_color = "off"
    
    st.metric(
        label="Previsão (Melhor/Pior)",
        value=previsao_txt,
        delta=delta_txt,
        delta_color=delta_color
    )

# KPIs principais
st.subheader("Indicadores Principais")
col1, col1b, col2, col3, col4, col5 = st.columns(6)

with col1:
    st.metric(
        label="Total",
        value=total_subtarefas
    )

# Novo indicador: In progress
in_progress = len(df_filtrado[df_filtrado['Status'].str.lower() == 'in progress'])
with col1b:
    st.metric(
        label="In Progress",
        value=in_progress
    )

with col2:
    st.metric(
        label="Concluidas",
        value=concluidas,
        delta=f"{percentual_concluido:.1f}%"
    )

with col3:
    st.metric(
        label="Pendentes",
        value=pendentes,
        delta=f"-{percentual_pendente:.1f}%",
        delta_color="red"
    )

with col4:
    st.metric(
        label="% Falta",
        value=f"{percentual_pendente:.1f}%"
    )

with col5:
    st.metric(
        label="Criticos >1 Sem",
        value=issues_abertos_1_semana,
        delta="Bug/RN",
        delta_color="off"
    )

st.markdown("---")

# Gráficos
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("Distribuicao por Status")
    
    status_counts = df_filtrado['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Quantidade']
    
    fig_status = px.pie(
        status_counts,
        values='Quantidade',
        names='Status',
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    fig_status.update_layout(
        height=300,
        template=plotly_template,
        paper_bgcolor=plotly_paper_bgcolor,
        font=dict(color=plotly_font_color)
    )
    st.plotly_chart(fig_status, use_container_width=True)

with col_graf2:
    st.subheader("Progresso de Conclusao")
    
    fig_progress = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=percentual_concluido,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "% Concluído", 'font': {'size': 24}},
        delta={'reference': 100, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#ffcccc'},
                {'range': [50, 75], 'color': '#ffffcc'},
                {'range': [75, 100], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig_progress.update_layout(
        height=300,
        template=plotly_template,
        paper_bgcolor=plotly_paper_bgcolor,
        font=dict(color=plotly_font_color)
    )
    st.plotly_chart(fig_progress, use_container_width=True)

# Segunda linha de gráficos
col_graf3, col_graf4 = st.columns(2)

with col_graf3:
    st.subheader("Distribuicao por Categoria")
    
    categoria_counts = df_filtrado['Categoria_Analise'].value_counts().reset_index()
    categoria_counts.columns = ['Categoria', 'Quantidade']
    
    fig_categoria = px.bar(
        categoria_counts,
        x='Categoria',
        y='Quantidade',
        color='Quantidade',
        color_continuous_scale='Blues'
    )
    fig_categoria.update_layout(
        height=300,
        showlegend=False,
        template=plotly_template,
        paper_bgcolor=plotly_paper_bgcolor,
        plot_bgcolor=plotly_plot_bgcolor,
        font=dict(color=plotly_font_color),
        xaxis=dict(**plotly_axis_style),
        yaxis=dict(**plotly_axis_style)
    )
    st.plotly_chart(fig_categoria, use_container_width=True)

with col_graf4:
    st.subheader("Subtarefas por Data-Lake")
    
    data_lake_counts = df_filtrado['Data-Lake'].value_counts().reset_index()
    data_lake_counts.columns = ['Data-Lake', 'Quantidade']
    
    fig_data_lake = px.bar(
        data_lake_counts,
        x='Data-Lake',
        y='Quantidade',
        color='Quantidade',
        color_continuous_scale='Teal'
    )
    fig_data_lake.update_layout(
        height=300,
        showlegend=False,
        template=plotly_template,
        paper_bgcolor=plotly_paper_bgcolor,
        plot_bgcolor=plotly_plot_bgcolor,
        font=dict(color=plotly_font_color),
        xaxis=dict(**plotly_axis_style),
        yaxis=dict(**plotly_axis_style)
    )
    st.plotly_chart(fig_data_lake, use_container_width=True)

st.markdown("<hr style='margin: 10px 0;'/>", unsafe_allow_html=True)

# Detalhes de Issues Críticos Abertos há mais de 1 Semana
st.subheader("Criticos Abertos > 1 Semana")

if issues_abertos_1_semana > 0 and not df_criticos.empty:
    st.info(f"Encontrados {issues_abertos_1_semana} issues criticos (Story Bug, RN e RN-FMK) abertos ha mais de 7 dias")
    
    # Preparar dados para exibição
    df_criticos_exibir = df_criticos[df_criticos['Dias_Aberto'] > 7].copy()
    df_criticos_exibir = df_criticos_exibir.sort_values('Dias_Aberto', ascending=False)
    
    # Layout com gráfico e tabela lado a lado
    col_crit1, col_crit2 = st.columns([1, 2])
    
    with col_crit1:
        st.write("**Distribuicao por Categoria**")
        categoria_critica_counts = df_criticos_exibir['Categoria_Analise'].value_counts().reset_index()
        categoria_critica_counts.columns = ['Categoria', 'Quantidade']
        
        fig_critico = px.bar(
            categoria_critica_counts,
            x='Categoria',
            y='Quantidade',
            color='Quantidade',
            color_continuous_scale='Reds',
            text='Quantidade'
        )
        fig_critico.update_layout(
            height=250,
            showlegend=False,
            template=plotly_template,
            paper_bgcolor=plotly_paper_bgcolor,
            plot_bgcolor=plotly_plot_bgcolor,
            font=dict(color=plotly_font_color),
            xaxis=dict(**plotly_axis_style),
            yaxis=dict(**plotly_axis_style)
        )
        fig_critico.update_traces(textposition='outside')
        st.plotly_chart(fig_critico, use_container_width=True)
    
    with col_crit2:
        st.write("**Detalhes dos Issues**")
        # Mostrar tabela com informações relevantes
        colunas_criticos = ['Chave', 'Titulo Historia', 'Data-Lake', 'Titulo', 'Status', 'Categoria_Analise', 'Dias_Aberto']
        if tema_selecionado == "☀️ Claro":
            df_crit_show = df_criticos_exibir[colunas_criticos]
            html = '<div style="overflow-x:auto; overflow-y:auto; max-height:250px;">'
            html += '<table style="width:100%; border-collapse:collapse; font-size:13px; background:#fff; color:#1f1f1f;">'
            html += '<thead><tr style="background:#e8e8e8; position:sticky; top:0;">'
            for col in df_crit_show.columns:
                html += f'<th style="padding:6px 8px; text-align:left; border-bottom:1px solid #ccc; white-space:nowrap; color:#1f1f1f;">{col}</th>'
            html += '</tr></thead><tbody>'
            for idx_c, (_, row) in enumerate(df_crit_show.iterrows()):
                bg_row = '#ffffff' if idx_c % 2 == 0 else '#f9f9f9'
                html += f'<tr style="background:{bg_row};">'
                for col in df_crit_show.columns:
                    val = str(row[col]) if pd.notna(row[col]) else ''
                    html += f'<td style="padding:5px 8px; border-bottom:1px solid #eee; color:#1f1f1f; white-space:nowrap;">{val}</td>'
                html += '</tr>'
            html += '</tbody></table></div>'
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.dataframe(
                df_criticos_exibir[colunas_criticos],
                use_container_width=True,
                height=250
            )
else:
    st.success("Nenhum issue critico aberto ha mais de 1 semana!")

st.markdown("<hr style='margin: 10px 0;'/>", unsafe_allow_html=True)

# Tabela de detalhes
st.subheader("Detalhes")

# Opções de visualização
exibir_todas = st.checkbox("Exibir todas as colunas", value=False)

# Função para colorir Status
def colorir_status(val):
    cores_status = {
        'Done': 'background-color: #90EE90; color: black',
        'Closed': 'background-color: #90EE90; color: black',
        'Resolved': 'background-color: #90EE90; color: black',
        'Concluído': 'background-color: #90EE90; color: black',
        'Concluida': 'background-color: #90EE90; color: black',
        'In Progress': 'background-color: #87CEEB; color: black',
        'To Do': 'background-color: #FFE4B5; color: black',
        'Backlog': 'background-color: #D3D3D3; color: black',
        'Canceled': 'background-color: #FFD700; color: black',
        'Cancelled': 'background-color: #FFD700; color: black',
        'Cancelado': 'background-color: #FFD700; color: black'
    }
    return cores_status.get(val, '')

def renderizar_tabela(df_render, tema):
    if tema == "☀️ Claro":
        cores_status_html = {
            'Done': '#90EE90', 'Closed': '#90EE90', 'Resolved': '#90EE90',
            'Concluído': '#90EE90', 'Concluida': '#90EE90',
            'In Progress': '#87CEEB', 'To Do': '#FFE4B5', 'Backlog': '#D3D3D3',
            'Canceled': '#FFD700', 'Cancelled': '#FFD700', 'Cancelado': '#FFD700'
        }
        html = '<div style="overflow-x:auto; overflow-y:auto; max-height:300px;">'
        html += '<table style="width:100%; border-collapse:collapse; font-size:13px; background:#fff; color:#1f1f1f;">'
        html += '<thead><tr style="background:#e8e8e8; position:sticky; top:0;">'
        for col in df_render.columns:
            html += f'<th style="padding:6px 8px; text-align:left; border-bottom:1px solid #ccc; white-space:nowrap; color:#1f1f1f;">{col}</th>'
        html += '</tr></thead><tbody>'
        for idx_r, (i, row) in enumerate(df_render.iterrows()):
            bg_row = '#ffffff' if idx_r % 2 == 0 else '#f9f9f9'
            html += f'<tr style="background:{bg_row};">'
            for col in df_render.columns:
                val = str(row[col]) if pd.notna(row[col]) else ''
                if col == 'Status':
                    cor = cores_status_html.get(val, 'transparent')
                    html += f'<td style="padding:5px 8px; border-bottom:1px solid #eee; background:{cor}; color:#1f1f1f; white-space:nowrap;">{val}</td>'
                else:
                    html += f'<td style="padding:5px 8px; border-bottom:1px solid #eee; color:#1f1f1f;">{val}</td>'
            html += '</tr>'
        html += '</tbody></table></div>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.dataframe(
            df_render.style.applymap(colorir_status, subset=['Status']),
            use_container_width=True,
            height=300
        )

if exibir_todas:
    colunas_todas = ['Data-Lake', 'Historia'] + [c for c in df_filtrado.columns if c not in ['Data-Lake', 'Historia']]
    renderizar_tabela(df_filtrado[colunas_todas].sort_index(ascending=False), tema_selecionado)
else:
    colunas_resumo = ['Data-Lake', 'Historia', 'Titulo Historia', 'Chave', 'Titulo', 'Status', 'Categoria_Analise']
    renderizar_tabela(df_filtrado[colunas_resumo].sort_index(ascending=False), tema_selecionado)

# Estatísticas adicionais
st.markdown("<hr style='margin: 10px 0;'/>", unsafe_allow_html=True)
st.subheader("Adicionais")

col_stat1, col_stat2 = st.columns(2)

with col_stat1:
    story_bugs = len(df_filtrado[df_filtrado['Categoria_Analise'] == 'Story Bug'])
    st.metric(
        label="Story Bugs",
        value=story_bugs
    )

with col_stat2:
    rn_total = len(df_filtrado[df_filtrado['Categoria_Analise'].str.contains('RN', na=False)])
    st.metric(
        label="Regras de Negocio",
        value=rn_total
    )


