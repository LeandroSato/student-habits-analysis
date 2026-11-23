# 1. Exploração inicial e diagnóstico de qualidade

Gerado por `analysis/run_analysis.py`. Todo número desta página sai do arquivo `data/raw/habitos_e_desempenho_estudantil.csv`.

## 1.1 O que é a base

- **1000 linhas x 16 colunas**, uma linha por aluno.
- Alvo da análise: `exam_score` (nota na prova).
- Linhas inteiras duplicadas: **0**.
- Valores de `student_id` repetidos: **0**.

### Tipos, preenchimento e cardinalidade

| coluna | dtype | nao_nulos | nulos | pct_nulos | unicos |
|---|---|---|---|---|---|
| student_id | str | 1000 | 0 | 0 | 1000 |
| age | int64 | 1000 | 0 | 0 | 8 |
| gender | str | 1000 | 0 | 0 | 3 |
| study_hours_per_day | float64 | 1000 | 0 | 0 | 78 |
| social_media_hours | float64 | 1000 | 0 | 0 | 60 |
| netflix_hours | float64 | 1000 | 0 | 0 | 51 |
| part_time_job | str | 1000 | 0 | 0 | 2 |
| attendance_percentage | float64 | 1000 | 0 | 0 | 320 |
| sleep_hours | float64 | 1000 | 0 | 0 | 68 |
| diet_quality | str | 1000 | 0 | 0 | 3 |
| exercise_frequency | int64 | 1000 | 0 | 0 | 7 |
| parental_education_level | str | 909 | 91 | 9.1 | 3 |
| internet_quality | str | 1000 | 0 | 0 | 3 |
| mental_health_rating | int64 | 1000 | 0 | 0 | 10 |
| extracurricular_participation | str | 1000 | 0 | 0 | 2 |
| exam_score | float64 | 1000 | 0 | 0 | 480 |

## 1.2 Valores ausentes

Ausência concentrada em **1** de 16 colunas. A mais afetada é `parental_education_level`, com **91 registros (9.1%)** em branco.

| coluna | nulos | pct_nulos |
|---|---|---|
| parental_education_level | 91 | 9.1 |

O que fazer com esses registros é decisão da etapa de engenharia de dados (tarefa 2), não desta: aqui o objetivo é medir o tamanho do problema.

## 1.3 Distribuição das variáveis numéricas

| coluna | contagem | media | desvio | minimo | q25 | mediana | q75 | maximo | assimetria |
|---|---|---|---|---|---|---|---|---|---|
| age | 1000 | 20.5 | 2.31 | 17 | 18.75 | 20 | 23 | 24 | 0.01 |
| study_hours_per_day | 1000 | 3.55 | 1.47 | 0 | 2.6 | 3.5 | 4.5 | 8.3 | 0.05 |
| social_media_hours | 1000 | 2.51 | 1.17 | 0 | 1.7 | 2.5 | 3.3 | 7.2 | 0.12 |
| netflix_hours | 1000 | 1.82 | 1.08 | 0 | 1 | 1.8 | 2.52 | 5.4 | 0.24 |
| attendance_percentage | 1000 | 84.13 | 9.4 | 56 | 78 | 84.4 | 91.03 | 100 | -0.24 |
| sleep_hours | 1000 | 6.47 | 1.23 | 3.2 | 5.6 | 6.5 | 7.3 | 10 | 0.09 |
| exercise_frequency | 1000 | 3.04 | 2.03 | 0 | 1 | 3 | 5 | 6 | -0.03 |
| mental_health_rating | 1000 | 5.44 | 2.85 | 1 | 3 | 5 | 8 | 10 | 0.04 |
| exam_score | 1000 | 69.6 | 16.89 | 18.4 | 58.48 | 70.5 | 81.33 | 100 | -0.16 |

Nenhuma variável numérica tem assimetria relevante (|assimetria| >= 0,5): as distribuições são aproximadamente simétricas.

## 1.4 Distribuição das variáveis categóricas

São 6 colunas categóricas (fora o identificador). A linha `(ausente)` aparece quando a coluna tem valor em branco.

| coluna | valor | contagem | pct |
|---|---|---|---|
| gender | Female | 481 | 48.1 |
| gender | Male | 477 | 47.7 |
| gender | Other | 42 | 4.2 |
| part_time_job | No | 785 | 78.5 |
| part_time_job | Yes | 215 | 21.5 |
| diet_quality | Fair | 437 | 43.7 |
| diet_quality | Good | 378 | 37.8 |
| diet_quality | Poor | 185 | 18.5 |
| parental_education_level | High School | 392 | 39.2 |
| parental_education_level | Bachelor | 350 | 35 |
| parental_education_level | Master | 167 | 16.7 |
| parental_education_level | (ausente) | 91 | 9.1 |
| internet_quality | Good | 447 | 44.7 |
| internet_quality | Average | 391 | 39.1 |
| internet_quality | Poor | 162 | 16.2 |
| extracurricular_participation | No | 682 | 68.2 |
| extracurricular_participation | Yes | 318 | 31.8 |

## 1.5 Diagnóstico de qualidade

### a) Valores impossíveis

A pergunta aqui não é se o valor é raro, e sim se ele **pode existir**. Os limites são de domínio (horas de um dia, percentual de 0 a 100, escala de 1 a 10), não os observados na amostra.

| coluna | minimo_esperado | maximo_esperado | minimo_observado | maximo_observado | violacoes |
|---|---|---|---|---|---|
| age | 10 | 100 | 17 | 24 | 0 |
| study_hours_per_day | 0 | 24 | 0 | 8.3 | 0 |
| social_media_hours | 0 | 24 | 0 | 7.2 | 0 |
| netflix_hours | 0 | 24 | 0 | 5.4 | 0 |
| attendance_percentage | 0 | 100 | 56 | 100 | 0 |
| sleep_hours | 0 | 24 | 3.2 | 10 | 0 |
| exercise_frequency | 0 | 7 | 0 | 6 | 0 |
| mental_health_rating | 1 | 10 | 1 | 10 | 0 |
| exam_score | 0 | 100 | 18.4 | 100 | 0 |

Total de valores fora do domínio: **0**. Nenhuma coluna tem valor impossível.

### b) Horas declaradas por dia

Somando `study_hours_per_day`, `social_media_hours`, `netflix_hours`, `sleep_hours`, a maior soma observada é de **21.5 h/dia** (média de 14.35 h) e **0 linhas** passam de 24 h. Nenhum aluno declara um dia impossível: as colunas de tempo são coerentes entre si.

### c) Outliers (regra do IQR, k = 1,5)

| coluna | limite_inferior | limite_superior | abaixo | acima | total_outliers | pct_outliers |
|---|---|---|---|---|---|---|
| age | 12.38 | 29.38 | 0 | 0 | 0 | 0 |
| study_hours_per_day | -0.25 | 7.35 | 0 | 7 | 7 | 0.7 |
| social_media_hours | -0.7 | 5.7 | 0 | 5 | 5 | 0.5 |
| netflix_hours | -1.29 | 4.81 | 0 | 4 | 4 | 0.4 |
| attendance_percentage | 58.46 | 110.56 | 3 | 0 | 3 | 0.3 |
| sleep_hours | 3.05 | 9.85 | 0 | 2 | 2 | 0.2 |
| exercise_frequency | -5 | 11 | 0 | 0 | 0 | 0 |
| mental_health_rating | -4.5 | 15.5 | 0 | 0 | 0 | 0 |
| exam_score | 24.2 | 115.6 | 2 | 0 | 2 | 0.2 |

Colunas com pontos fora da cerca: `study_hours_per_day` (7; 0.7%), `social_media_hours` (5; 0.5%), `netflix_hours` (4; 0.4%), `attendance_percentage` (3; 0.3%), `sleep_hours` (2; 0.2%), `exam_score` (2; 0.2%). Como nenhum deles viola o domínio (item a), são valores extremos **plausíveis** e serão mantidos: descartá-los apagaria justamente os alunos de comportamento mais acentuado, que são os que interessam à análise.

### d) Concentração nos extremos do alvo

`exam_score` vai de **18.4** a **100.0**. No valor máximo há **48 alunos (4.8%)** e no mínimo **1 (0.1%)**.

A concentração de 4.8% dos alunos exatamente em 100.0 indica **efeito teto**: a nota não tem para onde subir. Um modelo linear vai errar para baixo nesse grupo e pode prever nota acima de 100.0, o que não existe. Fica registrado como limitação e será tratado na tarefa 4, limitando a previsão ao intervalo válido.

## 1.6 Veredito

A base está em boa condição: sem duplicatas de linha ou de identificador; nenhum valor impossível e horas coerentes entre si; ausência restrita a `parental_education_level` (9.1%); efeito teto em `exam_score` (4.8%).

Os dois pontos que exigem decisão explícita adiante:

1. **Ausência em `parental_education_level`** (91 registros): decidir na tarefa 2.
2. **Efeito teto em `exam_score`** (48 alunos em 100.0): limita o modelo da tarefa 4.
