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
