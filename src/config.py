"""Caminhos, nomes de colunas e regras de plausibilidade do projeto.

Tudo que é "constante do negócio" fica aqui para que os outros módulos não
carreguem literais soltos e para que os testes possam apontar para outro CSV.
"""

from pathlib import Path

# --- Caminhos ---------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

RAW_CSV = RAW_DIR / "habitos_e_desempenho_estudantil.csv"

# --- Colunas ----------------------------------------------------------------

ID_COL = "student_id"
TARGET = "exam_score"

EXPECTED_COLUMNS = [
    "student_id",
    "age",
    "gender",
    "study_hours_per_day",
    "social_media_hours",
    "netflix_hours",
    "part_time_job",
    "attendance_percentage",
    "sleep_hours",
    "diet_quality",
    "exercise_frequency",
    "parental_education_level",
    "internet_quality",
    "mental_health_rating",
    "extracurricular_participation",
    "exam_score",
]

# Horas de um dia: a soma delas não pode passar de 24h.
DAILY_HOURS_COLS = [
    "study_hours_per_day",
    "social_media_hours",
    "netflix_hours",
    "sleep_hours",
]

# --- Regras de plausibilidade ----------------------------------------------
# Limites de domínio (o que é possível no mundo real), não os limites
# observados na amostra: a ideia é flagrar valor impossível, não valor raro.

PLAUSIBLE_RANGES = {
    "age": (10, 100),
    "study_hours_per_day": (0, 24),
    "social_media_hours": (0, 24),
    "netflix_hours": (0, 24),
    "attendance_percentage": (0, 100),
    "sleep_hours": (0, 24),
    "exercise_frequency": (0, 7),  # vezes por semana
    "mental_health_rating": (1, 10),
    "exam_score": (0, 100),
}

MAX_HOURS_PER_DAY = 24

# --- Tratamento de ausentes -------------------------------------------------

# `parental_education_level` é a única coluna com ausência (9,1%). A ausência
# virou categoria própria em vez de ser imputada ou descartada; o motivo está
# em reports/02_engenharia.md, apoiado no teste de Mann-Whitney.
MISSING_LABEL = "Não informado"
MISSING_FLAG_SUFFIX = "_informado"
COLS_MISSING_AS_CATEGORY = ["parental_education_level"]

# --- Variáveis derivadas ----------------------------------------------------

INF = float("inf")

# Faixas. `bins` são fechadas à esquerda e abertas à direita ([0, 1) etc.), para
# que um valor exato no corte caia sempre na faixa de cima e nenhum aluno fique
# fora de faixa. O campo `motivo` existe para que a justificativa viaje junto
# com o código e apareça no relatório.
BIN_SPECS = {
    "faixa_redes_sociais": {
        "coluna": "social_media_hours",
        "bins": [0, 1, 2, 3, 4, INF],
        "labels": ["Até 1h", "1 a 2h", "2 a 3h", "3 a 4h", "4h ou mais"],
        "motivo": (
            "Cortes em horas inteiras: é a unidade em que uma recomendação é dada "
            "(“reduza 1 hora por dia”) e em que o aluno consegue se enxergar. Os "
            "quartis observados (1,7 / 2,5 / 3,3 h) caem dentro das faixas, então "
            "nenhuma delas fica vazia."
        ),
    },
    "faixa_estudo": {
        "coluna": "study_hours_per_day",
        "bins": [0, 2, 4, 6, INF],
        "labels": ["Até 2h", "2 a 4h", "4 a 6h", "6h ou mais"],
        "motivo": (
            "Blocos de 2 horas em vez de 1: mantém grupos grandes o bastante para "
            "comparar (a mediana é 3,5 h e o máximo 8,3 h) sem criar faixa com "
            "pouquíssimos alunos no extremo."
        ),
    },
    "faixa_sono": {
        "coluna": "sleep_hours",
        "bins": [0, 6, 7, 9, INF],
        "labels": [
            "Menos de 6h",
            "6 a 7h",
            "7 a 9h (recomendado)",
            "9h ou mais",
        ],
        "motivo": (
            "Único corte vindo de fora da base: a faixa de 7 a 9 horas é a "
            "recomendação usual para jovens adultos. É convenção externa, não um "
            "número do CSV — está marcada como tal para que a comparação seja "
            "“dentro ou fora do recomendado”, e não um corte arbitrário."
        ),
    },
    "faixa_saude_mental": {
        "coluna": "mental_health_rating",
        "bins": [1, 4, 7, 11],
        "labels": ["Baixa (1-3)", "Média (4-6)", "Alta (7-10)"],
        "motivo": (
            "A escala vai de 1 a 10 e é autodeclarada; três blocos de largura "
            "parecida (3, 3 e 4 pontos) separam o grupo em risco do grupo bem sem "
            "fingir precisão que uma nota subjetiva não tem."
        ),
    },
    "faixa_frequencia": {
        "coluna": "attendance_percentage",
        "bins": [0, 75, 85, 95, INF],
        "labels": [
            "Abaixo de 75%",
            "75 a 85%",
            "85 a 95%",
            "95% ou mais",
        ],
        "motivo": (
            "75% é o mínimo de presença exigido em boa parte das instituições — "
            "convenção externa, assim como no sono. Acima dele, cortes de 10 pontos "
            "para separar presença boa de presença quase perfeita."
        ),
    },
}

# Escalas de qualidade que têm ordem natural: viram número para entrar em
# correlação e no modelo. `parental_education_level` ficou de fora de propósito,
# porque a categoria "Não informado" não tem lugar em uma escala ordenada.
ORDINAL_MAPS = {
    "diet_quality": {"Poor": 0, "Fair": 1, "Good": 2},
    "internet_quality": {"Poor": 0, "Average": 1, "Good": 2},
}

# Sim/não viram 0/1 para poderem entrar na matriz de correlação.
BINARY_MAPS = {
    "part_time_job": {"No": 0, "Yes": 1},
    "extracurricular_participation": {"No": 0, "Yes": 1},
}

ORDINAL_SUFFIX = "_ord"
BINARY_SUFFIX = "_bin"

# Colunas de tela de lazer, somadas em `leisure_screen_hours`.
LEISURE_SCREEN_COLS = ["social_media_hours", "netflix_hours"]

# --- Grupos de colunas para a análise estatística ---------------------------

# Hábitos medidos direto na base.
HABIT_COLS = [
    "study_hours_per_day",
    "social_media_hours",
    "netflix_hours",
    "attendance_percentage",
    "sleep_hours",
    "exercise_frequency",
    "mental_health_rating",
]

# Contexto do aluno: não é hábito, mas pode explicar nota.
CONTEXT_COLS = [
    "age",
    "diet_quality" + ORDINAL_SUFFIX,
    "internet_quality" + ORDINAL_SUFFIX,
    "part_time_job" + BINARY_SUFFIX,
    "extracurricular_participation" + BINARY_SUFFIX,
    "parental_education_level" + MISSING_FLAG_SUFFIX,
]

# Derivadas da tarefa 2. Correlacionam por construção com as colunas de origem,
# então aparecem na análise mas ficam fora do modelo (ver tarefa 4).
DERIVED_COLS = ["leisure_screen_hours", "study_share"]

# Tudo que entra na matriz de correlação, junto com o alvo.
CORRELATION_COLS = HABIT_COLS + CONTEXT_COLS + DERIVED_COLS

# Colunas categóricas usadas na comparação entre grupos.
GROUP_COLS = [
    "gender",
    "diet_quality",
    "internet_quality",
    "parental_education_level",
    "part_time_job",
    "extracurricular_participation",
    "faixa_saude_mental",
]

# Limite para considerar duas variáveis preditoras redundantes entre si.
MULTICOLLINEARITY_THRESHOLD = 0.7

# Nível de significância usado em todos os testes.
ALPHA = 0.05
