# Spec — Desafio Analytics Engineer (estágio) · Klubi

Enunciado original: <https://github.com/somosbro/data-analysis-challenge-klubi>

## Objetivo

Entregar um repositório público que, a partir de `habitos_e_desempenho_estudantil.csv`
(1000 alunos, 16 colunas), mostre: diagnóstico da base, tratamento justificado,
relação entre hábitos e nota, **uma aplicação concreta** (simulador em Streamlit)
e conclusões acionáveis. O README é a peça de comunicação principal.

## O que a base é (verificado, não suposto)

- 1000 linhas × 16 colunas, `student_id` único, sem duplicatas.
- Nulos só em `parental_education_level`: 91 (9,1%). As outras 15 colunas estão completas.
- Alvo `exam_score`: média 69,6 · desvio 16,9 · mín. 18,4 · máx. 100 — com 48 alunos
  exatamente em 100,0 (efeito teto, registrado como limitação).
- `attendance_percentage`: 66 alunos em 100%.
- Soma das horas diárias (estudo + redes + streaming + sono) nunca passa de 21,5 h/dia,
  ou seja, não há inconsistência de calendário.
- Sinal forte já visível: `study_hours_per_day` × `exam_score` = 0,825 (Pearson).

## As 6 tarefas

| # | Tarefa | Entregável |
|---|---|---|
| 1 | Exploração inicial | tipos, distribuições, nulos, duplicatas, outliers, efeito teto |
| 2 | Engenharia de dados | faixas derivadas, ordinais codificadas, decisão sobre os 9,1% de nulos — cada escolha com motivo escrito |
| 3 | Análise estatística | Pearson + Spearman, matriz de correlação, ranking de influência, teste de diferença entre grupos |
| 4 | Aplicação prática | app Streamlit: simulador de cenário com regressão linear interpretável |
| 5 | Visualização | mapa de calor, análise da variável de maior impacto, boxplot/histograma por faixas |
| 6 | Síntese de insights | hábitos de maior efeito, recomendações práticas, diferenças por grupo |

## Critérios de avaliação (do enunciado)

Clareza da análise · qualidade e justificativa da engenharia de dados ·
correção estatística · aplicação prática útil · visualizações relevantes e de
leitura fácil · comunicação de insights práticos.

O enunciado diz explicitamente que *descrever a base é o ponto de partida; o
diferencial é o que a entrega permite fazer depois* — por isso a tarefa 4 recebe
peso maior.

## Fora de escopo

- Inferência causal ou qualquer afirmação de efeito ("estudar mais **causa** nota maior").
- Modelos complexos (boosting, rede neural): perdem a interpretabilidade, que é o
  ponto da tarefa 4.
- Clustering/segmentação (caminho alternativo oferecido pelo enunciado; o escolhido
  foi o simulador).
- Deploy do app, CI/CD, banco de dados, dashboard de BI.
- Dados externos. Todo número citado sai deste CSV e de código que roda.

## Decisões técnicas e porquês

| Decisão | Por quê |
|---|---|
| Script (`analysis/run_analysis.py`) em vez de notebook | Roda do zero em qualquer máquina, dá diff legível no git e garante que todo número do README é reproduzível. |
| matplotlib + seaborn, não Plotly | O README precisa de PNGs estáticos e o Streamlit renderiza matplotlib sem problema — uma biblioteca a menos. |
| Regressão linear (OLS) com one-hot nas categóricas e coeficientes padronizados | O enunciado pede algo "simples e interpretável"; coeficiente padronizado responde direto "quanto a nota muda por hora de estudo". |
| Outliers do IQR mantidos | Nenhum viola o domínio (ver tarefa 1): são extremos plausíveis. Descartá-los apagaria os alunos de comportamento mais acentuado, que são os que interessam. |
| Teste de hipótese em vez de comparar médias no olho | Diferença entre grupos só vira conclusão com teste. |
| pytest nas funções de tratamento (loading, cleaning, features, stats, model) | Critério de aceite vira teste. App e gráficos ficam fora: saída visual se confere no olho. |
| Código em `src/` separado do script de análise e do app | O mesmo tratamento alimenta o relatório e o Streamlit, sem código duplicado. |

## Estrutura de pastas

```
README.md               como rodar, estrutura, conclusões, limitações
requirements.txt        versões travadas
data/
  raw/                  CSV do desafio, intacto
  processed/            gerado pela análise (fora do git)
src/
  config.py             caminhos, faixas, nomes de colunas, regras de domínio
  data_loading.py       leitura + contrato de colunas
  profiling.py          diagnóstico de qualidade
  reporting.py          tabelas Markdown dos relatórios
  cleaning.py           ausentes e inconsistências
  features.py           variáveis derivadas
  stats_analysis.py     correlações e ranking de influência
  model.py              regressão linear + métricas
  plots.py              figuras
tests/                  pytest das funções de tratamento
analysis/run_analysis.py  roda tudo: relatórios + figuras
app/streamlit_app.py    simulador
reports/
  figures/              PNGs
  *.md                  relatório de cada etapa
docs/spec.md            esta spec
```

## Ambiente

Python 3.14.6 em venv. `scikit-learn 1.9.1` e `seaborn 0.13.2` instalam normalmente
nessa versão — o risco levantado no planejamento não se confirmou, então a regressão
usa scikit-learn e não precisou de alternativa com `numpy.linalg.lstsq`.
