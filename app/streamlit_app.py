"""Simulador de cenários de hábitos (tarefa 4 do desafio).

Para que serve: a análise mostrou quais hábitos acompanham nota alta, mas um
ranking de correlações não diz o que fazer com um aluno específico. Este app
transforma o modelo em uma ferramenta de conversa — dado o retrato de hábitos de
um aluno, qual mudança o modelo associa ao maior ganho de nota.

Quem usaria: coordenação pedagógica e tutoria. A decisão que o app apoia é onde
colocar o esforço — qual hábito levar para a conversa com o aluno e qual aluno
chamar primeiro.

Rode com:  streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src import cleaning, config, features, model  # noqa: E402
from src.data_loading import load_raw  # noqa: E402

st.set_page_config(
    page_title="Simulador de hábitos e nota",
    page_icon=":material/insights:",
    layout="wide",
)


@st.cache_data
def carregar_base() -> pd.DataFrame:
    """Lê e trata a base. Em cache porque não muda entre interações."""
    tratado, _ = cleaning.clean(load_raw())
    return features.build_features(tratado)


@st.cache_resource
def treinar_modelo(_base: pd.DataFrame) -> model.FittedModel:
    """Treina o modelo uma vez por sessão.

    Treinado na hora em vez de carregado de um `.pkl`: são 1000 linhas, leva
    milissegundos, e assim o app nunca usa um modelo mais velho que o código de
    tratamento.
    """
    return model.train(_base)


base = carregar_base()
ajustado = treinar_modelo(base)
coeficientes = model.coefficient_table(ajustado)
nota_media = float(base[config.TARGET].mean())
erro_medio = ajustado.metrics["mae"]

st.title("Simulador de hábitos e nota")
st.markdown(
    "Para a conversa de tutoria: **qual hábito levar para a mesa primeiro**."
)

st.warning(
    "O app mostra a nota **associada** a um perfil de hábitos, não o efeito de "
    "mudar um hábito. Ponto de partida de conversa, nunca promessa de resultado — "
    "o porquê está em “Como este modelo funciona”, no fim da página.",
    title="Correlação não é causa",
    icon=":material/warning:",
)

# --- Controles ---------------------------------------------------------------

st.sidebar.header("Hábitos do aluno")
st.sidebar.caption(
    "Os limites de cada controle são o mínimo e o máximo observados na base: "
    "fora dessa faixa o modelo estaria chutando."
)

cenario: dict[str, float] = {}
for coluna in ajustado.numeric:
    serie = base[coluna]
    passo = config.FEATURE_STEPS.get(coluna, 0.1)
    cenario[coluna] = st.sidebar.slider(
        config.FEATURE_LABELS.get(coluna, coluna),
        min_value=float(serie.min()),
        max_value=float(serie.max()),
        value=float(serie.median()),
        step=float(passo),
        key=f"slider_{coluna}",
        format=config.FEATURE_FORMATS.get(coluna),
        # Saber o que é típico na base evita simular um perfil que quase não
        # existe sem perceber.
        help=f"Na base: mediana {serie.median():g}, "
        f"metade dos alunos entre {serie.quantile(0.25):g} e "
        f"{serie.quantile(0.75):g}.",
    )

st.sidebar.caption(
    "As horas são **decimais**, não relógio: 3,7 h/dia são 3 h 42 min, não "
    "3 h 70 min. É assim que a base registra, com uma casa depois da vírgula."
)

def voltar_ao_aluno_mediano() -> None:
    """Repõe todos os controles na mediana da base.

    Precisa ser um callback (`on_click`), e não código no corpo do script: o
    Streamlit proíbe alterar a chave de um widget depois que ele já foi criado
    na mesma execução, e os sliders são criados acima. O callback roda **antes**
    do rerun, quando os widgets ainda não existem, e aí a escrita é permitida.
    """
    for coluna in ajustado.numeric:
        st.session_state[f"slider_{coluna}"] = float(base[coluna].median())


st.sidebar.button(
    "Voltar ao aluno mediano",
    width="stretch",
    on_click=voltar_ao_aluno_mediano,
)

# --- Resultado ---------------------------------------------------------------

nota_prevista = float(model.predict(ajustado, cenario)[0])
limite_min, limite_max = config.SCORE_LIMITS

percentil = float((base[config.TARGET] < nota_prevista).mean() * 100)
faixa_min = max(limite_min, nota_prevista - erro_medio)
faixa_max = min(limite_max, nota_prevista + erro_medio)

# Grade em vez de container horizontal: o container dimensiona cada card pelo
# próprio conteúdo, e os três saíam com larguras diferentes. A grade dá colunas
# iguais, e `height="stretch"` iguala a altura pela mais alta da linha.
with st.grid(3, gap="medium"):
    st.metric(
        "Nota prevista",
        f"{nota_prevista:.1f}",
        round(nota_prevista - nota_media, 1),
        delta_description="vs. média da base",
        border=True,
        height="stretch",
        help="O que o modelo associa a este perfil de hábitos — não o que "
        "aconteceria se o aluno mudasse de hábito.",
    )
    st.metric(
        "Faixa provável",
        f"{faixa_min:.0f} a {faixa_max:.0f}",
        border=True,
        height="stretch",
        help=f"A previsão mais ou menos o erro médio do modelo "
        f"(± {erro_medio:.1f} pontos no conjunto de teste), truncada em "
        f"{limite_min:.0f} e {limite_max:.0f}.",
    )
    # O valor vai curto de propósito: o Streamlit encolhe a fonte de valores
    # longos, e os três cards ficariam com tamanhos de número diferentes.
    st.metric(
        "Percentil na base",
        f"{percentil:.0f}º",
        border=True,
        height="stretch",
        help="Este perfil fica acima de "
        f"{percentil:.0f}% dos {len(base)} alunos da base.",
    )

if nota_prevista >= limite_max:
    st.info(
        "A previsão bateu no teto de 100 — acima disso a nota não existe, e o "
        "modelo não distingue perfis muito dedicados entre si.",
        icon=":material/info:",
    )

# --- Onde mexer primeiro -----------------------------------------------------

st.subheader("Onde mexer primeiro")
st.caption(
    "O mesmo aluno com **um** hábito alterado por vez, mantendo os outros parados."
)

# Cada mudança tem duas escritas: a curta vai no eixo do gráfico, porque rótulo
# longo é cortado com reticências e "Passar 1 hora a m…" apareceria duas vezes,
# indistinguível; a longa vai na tabela e na frase de recomendação.
MUDANCAS = [
    ("study_hours_per_day", +1.0, "Estudar 1 hora a mais por dia", "Estudo +1 h"),
    ("social_media_hours", -1.0, "Passar 1 hora a menos em redes sociais", "Redes sociais −1 h"),
    ("netflix_hours", -1.0, "Passar 1 hora a menos em streaming", "Streaming −1 h"),
    ("sleep_hours", +1.0, "Dormir 1 hora a mais por noite", "Sono +1 h"),
    ("exercise_frequency", +1.0, "Exercitar-se 1 vez a mais por semana", "Exercício +1 x"),
    ("mental_health_rating", +1.0, "Subir 1 ponto na saúde mental autodeclarada", "Saúde mental +1"),
    ("attendance_percentage", +5.0, "Aumentar 5 pontos de frequência", "Frequência +5 p.p."),
]

linhas = []
for coluna, passo, descricao, curto in MUDANCAS:
    limite_inferior = float(base[coluna].min())
    limite_superior = float(base[coluna].max())
    novo_valor = min(max(cenario[coluna] + passo, limite_inferior), limite_superior)
    if novo_valor == cenario[coluna]:
        continue  # já está no limite do que a base observou
    efeito = model.scenario_delta(ajustado, cenario, {coluna: novo_valor})
    linhas.append(
        {
            "Mudança": descricao,
            "Rótulo": curto,
            "Nota prevista": efeito["nota_depois"],
            "Diferença": efeito["diferenca"],
        }
    )

simulacoes = pd.DataFrame(linhas).sort_values("Diferença", ascending=False)

if simulacoes.empty:
    st.info(
        "Todos os hábitos já estão no limite observado na base: não há mudança "
        "a simular para este perfil.",
        icon=":material/info:",
    )
else:
    # Barras em vez de tabela: a pergunta aqui é "qual é maior", e comprimento
    # se compara de relance; número em coluna exige ler e subtrair. A tabela
    # continua disponível logo abaixo, para quem quer o valor exato.
    ordem = simulacoes["Rótulo"].tolist()
    eixo_y = alt.Y("Rótulo:N", sort=ordem, title=None)
    eixo_x = alt.X(
        "Diferença:Q",
        title="Pontos de nota a mais",
        scale=alt.Scale(
            domain=[
                0,
                float(simulacoes["Diferença"].max()) * config.CHART_HEADROOM,
            ]
        ),
    )

    barras = (
        alt.Chart(simulacoes)
        .mark_bar(height=18, cornerRadiusEnd=4)
        .encode(
            y=eixo_y,
            x=eixo_x,
            # A cor marca a direção, mas o sinal também aparece no rótulo:
            # a leitura não depende de distinguir azul de vermelho.
            color=alt.condition(
                alt.datum["Diferença"] >= 0,
                alt.value(config.COR_SERIE),
                alt.value(config.COR_NEGATIVA),
            ),
            tooltip=["Mudança", "Nota prevista", "Diferença"],
        )
    )
    # A tinta do rótulo segue o tema em que o app está sendo visto: a do tema
    # claro sumiria no escuro, e vice-versa.
    tema_escuro = getattr(st.context.theme, "type", "light") == "dark"
    tinta_rotulo = "#e8e6e1" if tema_escuro else config.COR_TINTA_SECUNDARIA

    rotulos = (
        alt.Chart(simulacoes)
        .mark_text(align="left", dx=8, fontSize=12, color=tinta_rotulo)
        .encode(y=eixo_y, x=eixo_x, text=alt.Text("Diferença:Q", format="+.2f"))
    )

    st.altair_chart(
        (barras + rotulos).properties(height=30 * len(simulacoes) + 40),
        alt="Efeito previsto de alterar cada hábito em uma unidade, em pontos de nota",
    )

    melhor = simulacoes.iloc[0]
    st.success(
        f"Para este perfil, a maior diferença está em: **{melhor['Mudança'].lower()}** "
        f"({melhor['Diferença']:+.2f} ponto).",
        icon=":material/trending_up:",
    )

    with st.expander("Ver os números exatos"):
        st.dataframe(
            simulacoes.drop(columns="Rótulo"),
            hide_index=True,
            alt="Efeito previsto de alterar cada hábito em uma unidade",
            column_config={
                "Diferença": st.column_config.NumberColumn(format="%+.2f"),
                "Nota prevista": st.column_config.NumberColumn(format="%.2f"),
            },
        )

# --- Curva da variável de maior peso ----------------------------------------

st.subheader("Nota prevista por hora de estudo")
st.caption("Só as horas de estudo variam; os outros hábitos ficam como estão.")

horas = np.round(
    np.arange(
        base["study_hours_per_day"].min(),
        base["study_hours_per_day"].max() + 0.01,
        0.5,
    ),
    1,
)
grade = pd.DataFrame({coluna: valor for coluna, valor in cenario.items()}, index=range(len(horas)))
grade["study_hours_per_day"] = horas
grade["Nota prevista"] = model.predict(ajustado, grade)
grade = grade.rename(columns={"study_hours_per_day": "Horas de estudo por dia"})

eixo_x = alt.X(
    "Horas de estudo por dia:Q",
    scale=alt.Scale(domain=[float(horas.min()), float(horas.max())], nice=False),
)
eixo_y = alt.Y(
    "Nota prevista:Q",
    # Domínio fixo em 0 a 100: é a faixa em que a nota existe, e deixar o Vega
    # escolher faria a escala mudar de lugar a cada ajuste dos controles.
    scale=alt.Scale(domain=list(config.SCORE_LIMITS), nice=False),
)

linha = alt.Chart(grade).mark_line().encode(x=eixo_x, y=eixo_y)
ponto_atual = (
    alt.Chart(pd.DataFrame({
        "Horas de estudo por dia": [cenario["study_hours_per_day"]],
        "Nota prevista": [nota_prevista],
    }))
    .mark_point(size=120, filled=True)
    .encode(x=eixo_x, y=eixo_y, tooltip=["Horas de estudo por dia", "Nota prevista"])
)

st.altair_chart(
    linha + ponto_atual,
    alt="Nota prevista conforme as horas de estudo por dia, com o aluno simulado marcado",
)
st.caption(
    "O ponto marca o aluno dos controles. A linha é reta porque o modelo é "
    "linear, e achata no topo onde a previsão bate em 100."
)

# --- Transparência do modelo -------------------------------------------------

with st.expander("Como este modelo funciona, e onde ele falha"):
    st.markdown(
        f"""
**O modelo.** Regressão linear simples, treinada em {ajustado.metrics['n_treino']}
alunos e medida em {ajustado.metrics['n_teste']} que ela nunca viu. Escolhida por
ser explicável: cada hábito tem um coeficiente que se lê em uma frase. Um modelo
mais forte ganharia alguns pontos de precisão e perderia essa frase, que é o
produto aqui.

**Desempenho no conjunto de teste.** R² de {ajustado.metrics['r2']},
erro médio de {ajustado.metrics['mae']} pontos. Chutar sempre a nota média erraria
{ajustado.metrics['mae_baseline']} pontos — é essa a comparação que importa.

**As variáveis.** Só os sete hábitos que passaram no teste de significância da
tarefa 3. Idade, dieta, qualidade da internet, trabalho de meio período e
atividade extracurricular ficaram fora porque não mostraram relação com a nota;
incluí-las não melhorou o modelo.
"""
    )

    st.markdown("**Peso de cada hábito**")
    tabela_coef = coeficientes.copy()
    tabela_coef["variavel"] = tabela_coef["variavel"].map(
        lambda c: config.FEATURE_LABELS.get(c, c)
    )
    st.dataframe(
        tabela_coef.rename(
            columns={
                "variavel": "Hábito",
                "pontos_por_unidade": "Pontos por unidade",
                "pontos_por_desvio": "Pontos por desvio padrão",
                "direcao": "Direção",
            }
        ),
        hide_index=True,
        alt="Coeficientes do modelo por hábito",
    )
    st.caption(
        "“Pontos por unidade” é quanto a nota prevista muda por uma hora (ou um "
        "ponto da escala). “Pontos por desvio padrão” permite comparar hábitos de "
        "unidades diferentes: hora de estudo e ponto de frequência não se comparam "
        "direto."
    )

    st.markdown(
        """
**Onde ele falha.**

- **Efeito teto.** 48 alunos da base tiraram exatamente 100. A previsão é
  truncada em 100, então o modelo subestima quem já está no topo.
- **Relação linear.** O modelo supõe que cada hora extra vale o mesmo, da
  primeira à oitava. Pearson e Spearman concordaram em todas as variáveis, o que
  sustenta a suposição, mas ela continua sendo uma suposição.
- **Fora da faixa observada.** Os controles param no mínimo e no máximo da base
  justamente porque extrapolar seria invenção.
- **Nada aqui é causa.** O dado é de um único momento, sem grupo de controle e
  sem nada sorteado: um aluno que estuda mais pode ter nota maior por motivos
  que a base não mediu, e a relação pode valer no sentido inverso. O modelo
  descreve quem tira nota alta, não o que produz nota alta.
"""
    )

st.caption(
    f"Base: {len(base)} alunos. Análise completa em `reports/`. "
    "Modelo treinado a cada sessão a partir do CSV, sem artefato salvo."
)
