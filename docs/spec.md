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

### Tomadas no planejamento, antes de qualquer código

| Decisão | Por quê |
|---|---|
| Script (`analysis/run_analysis.py`) em vez de notebook | Roda do zero em qualquer máquina, dá diff legível no git e garante que todo número do README é reproduzível. |
| matplotlib + seaborn, não Plotly | O README precisa de PNGs estáticos e o Streamlit renderiza matplotlib sem problema — uma biblioteca a menos. |
| Regressão linear (OLS) com one-hot nas categóricas e coeficientes padronizados | O enunciado pede algo "simples e interpretável"; coeficiente padronizado responde direto "quanto a nota muda por hora de estudo". |
| Outliers do IQR mantidos | Nenhum viola o domínio (ver tarefa 1): são extremos plausíveis. Descartá-los apagaria os alunos de comportamento mais acentuado, que são os que interessam. |
| Teste de hipótese em vez de comparar médias no olho | Diferença entre grupos só vira conclusão com teste. |
| pytest nas funções de tratamento (loading, cleaning, features, stats, model) | Critério de aceite vira teste. App e gráficos ficam fora: saída visual se confere no olho. |
| Código em `src/` separado do script de análise e do app | O mesmo tratamento alimenta o relatório e o Streamlit, sem código duplicado. |

### Tomadas durante a execução

Estas não estavam no planejamento: apareceram ao olhar o dado ou a tela. Ficam
registradas separadas de propósito — decisão tomada no meio do caminho é tão
legítima quanto a planejada, desde que o motivo esteja escrito.

| Decisão | Por quê |
|---|---|
| Ausentes viram categoria `Não informado` + flag, em vez de descarte ou imputação | Mann-Whitney entre quem informou e quem não informou deu **p = 0,71**: a ausência não se liga à nota. Descartar perderia 9,1% da base sem corrigir viés; imputar pela moda poria 91 alunos num grupo sem evidência. A decisão saiu de um teste, não de preferência. |
| Valor impossível **interrompe** o pipeline (`DomainViolationError`) em vez de ser corrigido | A exploração não achou nenhum, então tratamento seria código morto. E corrigir em silêncio com `clip` é pior que falhar: o número fica plausível e errado. |
| `scipy` acrescentada à stack | É o que torna possível o teste de hipótese (Mann-Whitney e Kruskal-Wallis). Sem ela, restaria comparar médias no olho. |
| Correção de Holm-Bonferroni em todos os p-valores | 15 variáveis testadas contra a mesma nota a 5% fariam esperar quase um achado falso por acaso. Holm é menos conservadora que Bonferroni e não exige testes independentes — e aqui eles não são. |
| Tamanho de efeito (ε²) reportado junto do p | Com 1000 alunos quase tudo fica significativo. `attendance_percentage` passa no teste com r = 0,09; sem o efeito, isso viraria "achado". |
| As duas derivadas da tarefa 2 ficam **fora** do modelo | São redundantes por construção com as colunas de origem (\|r\| de 0,74 e 0,72). Com variáveis quase idênticas o coeficiente de cada uma fica instável, e a leitura "quanto cada hora pesa" deixa de valer. |
| Modelo escolhido por regra escrita **antes** de ver o resultado | O conjunto maior só venceria se ganhasse mais de 0,005 de R² em validação cruzada. Venceu o enxuto, de 7 hábitos. Definir o critério antes evita escolher o modelo pelo resultado que se prefere. |
| Previsão truncada em [0, 100] | 48 alunos tiraram exatamente 100; sem truncar o modelo preveria nota acima do máximo, que não existe. |
| Modelo treinado na hora, sem `.pkl` versionado | São 1000 linhas e o treino leva milissegundos. Um artefato binário no repositório envelheceria em silêncio na primeira vez que o tratamento mudasse. |
| Sliders limitados ao mínimo e máximo observados | Extrapolar fora da faixa da base é invenção, e a interface diz isso. |
| `altair` acrescentada à stack | O `st.line_chart` do Streamlit escolhia sozinho um eixo até 180 numa nota que vai a 100. O Altair permite fixar o domínio da escala. |
| Vega/Altair no app, matplotlib/seaborn nos relatórios | O README precisa de PNG que apareça no GitHub sem servidor; o app precisa de gráfico interativo. A skill do Streamlit também recomenda Vega em vez de matplotlib dentro do app. |
| Paleta validada por script, não no olho | O par azul/vermelho passou nos cinco testes de contraste e daltonismo (ΔE 21,6 em protanopia, 32,3 em visão normal). Onde a cor marca direção, o sinal aparece também no número. |
| Paleta centralizada no `config.py` | Para que as figuras do relatório e os gráficos do app não divirjam. |
| Cards de métrica em `st.grid` com `height="stretch"` | `st.container(horizontal=True)` dimensiona cada card pelo próprio conteúdo, e os três saíam com larguras diferentes. |
| Unidade dentro do valor de cada controle (`3,5 h/dia`) | Hora decimal sem unidade se lê como relógio: "3.70" parecia 3h70min, que não existe (são 3 h 42 min). Não arredondei para hora cheia porque entre 83% e 90% dos valores das colunas de tempo têm casa decimal — arredondar descartaria resolução que o modelo usa. |
| Barras no lugar da tabela em "onde mexer primeiro" | A pergunta ali é "qual é maior", e comprimento se compara de relance. A tabela com os valores exatos continua, um clique abaixo. |
| Conclusões no topo do README, antes das instruções | Quem avalia dá uns 30 segundos de rolagem antes de decidir se lê o resto, e via `pip install` nesses 30 segundos. |

## Ferramentas usadas

O enunciado deixa a stack livre — inclusive assistentes de IA. Lista completa do
que foi usado, com o motivo de cada escolha.

### Linguagem

| Linguagem | Motivo |
|---|---|
| **Python 3.14.6** | É a única linguagem em que carregar CSV, rodar teste estatístico, treinar modelo e subir uma interface web cabem no mesmo projeto, sem ponte entre linguagens. Em R a estatística seria melhor e o app pior; em JavaScript, o contrário. |

### Bibliotecas

| Biblioteca | O que é | Motivo de ter entrado |
|---|---|---|
| **pandas** | Tabelas em memória | Base de tudo: leitura, filtro, agrupamento por faixa, estatística descritiva. Usada em todos os módulos. |
| **numpy** | Cálculo com vetores | Operação em coluna inteira sem laço: truncamento da previsão em 0–100 e divisão protegida do `study_share`. |
| **scipy** | Estatística científica | Os testes de hipótese: Mann-Whitney (decidiu o tratamento dos nulos) e Kruskal-Wallis (diferença entre grupos). Sem ela, restaria comparar médias no olho. |
| **scikit-learn** | Aprendizado de máquina | Regressão linear, divisão treino/teste, validação cruzada e métricas (R², MAE, RMSE). Só em `src/model.py`. |
| **matplotlib** | Gráficos estáticos | Gera os PNGs dos relatórios, que precisam aparecer no README do GitHub sem servidor. Só em `src/plots.py`. |
| **seaborn** | Camada sobre o matplotlib | Resolve em uma linha o mapa de calor e os boxplots, que no matplotlib puro levariam vinte. |
| **streamlit** | Framework de app web | Transforma script Python em app com controles, sem escrever HTML, CSS ou JavaScript. |
| **altair** | Gráficos interativos | Os gráficos dentro do app. Entrou porque o gráfico nativo do Streamlit escolhia sozinho um eixo até 180 numa nota que vai a 100. |
| **pytest** | Framework de teste | Os 76 testes das funções de tratamento, estatística e modelo. Padrão de fato em Python. |

### Assistente de IA

| Ferramenta | Motivo |
|---|---|
| **Claude Code** (Anthropic) | Usado em todo o projeto, como o enunciado permite: acelerar a escrita de código, de testes e de texto, e revisar decisões. O que não foi delegado: a escolha técnica de cada etapa e a conferência dos resultados. Todo número do repositório vem de código que roda, e a reprodutibilidade foi testada em clone limpo. |

### Skills

Conjuntos de instruções especializadas acionados dentro do Claude Code.

| Skill | Objetivo | O que mudou de verdade |
|---|---|---|
| `developing-with-streamlit` | Construir o app segundo a documentação da versão instalada | Gráfico Vega em vez de matplotlib dentro do app, componentes nativos sem CSS, ícones em vez de emoji |
| `dataviz` | Decidir forma e cor dos gráficos com método, não por gosto | Paleta validada por script (contraste e daltonismo), escala divergente só onde há polaridade, nada de arco-íris |
| `ui-ux-pro-max` | Revisar a interface | Pouco: a busca não trouxe nada específico sobre cards de métrica. Aproveitei a regra de escala tipográfica consistente; a solução dos cards veio da documentação do Streamlit |

### O que ficou de fora, e por quê

"Não usei X" também é decisão, então fica registrado:

- **Banco de dados** — a fonte é um CSV de 73 KB; SQLite seria cerimônia sem ganho.
- **Teste de carga e de estresse** — não há servidor próprio nem usuários simultâneos.
- **Teste end-to-end** — o app é uma tela só, sem fluxo de navegação a percorrer.
- **Biblioteca de componentes de interface** — o Streamlit não aceita, e a documentação dele desaconselha CSS.
- **Plotly** — não resolveria o PNG estático do README e seria uma dependência a mais.
- **CI/CD e deploy** — fora do escopo da entrega.
- **Modelos complexos** (boosting, floresta, rede neural) — ganhariam precisão e perderiam a frase "uma hora a mais vale 9,5 pontos", que é o produto do simulador.

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
