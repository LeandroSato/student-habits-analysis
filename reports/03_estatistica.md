# 3. Análise estatística

Gerado por `analysis/run_analysis.py`.

> **Correlação não é causa.** Tudo nesta página mede se duas coisas andam juntas, nunca se uma produz a outra. O dado é observacional e de um único momento: não há grupo de controle, nada foi sorteado e qualquer relação aqui pode vir de uma terceira variável não medida, ou valer no sentido inverso.

## 3.1 Ranking de influência

Ordenado pela força da associação com a nota, do mais forte para o mais fraco. `p corrigido` já passou pela correção de Holm-Bonferroni.

| variavel | r (Pearson) | r (Spearman) | p corrigido | significativo | direcao | forca | métodos concordam |
|---|---|---|---|---|---|---|---|
| study_hours_per_day | 0.825 | 0.812 | < 0,000001 | sim | positiva | forte | sim |
| study_share | 0.744 | 0.74 | < 0,000001 | sim | positiva | forte | sim |
| mental_health_rating | 0.322 | 0.323 | < 0,000001 | sim | positiva | moderada | sim |
| leisure_screen_hours | -0.238 | -0.228 | < 0,000001 | sim | negativa | fraca | sim |
| netflix_hours | -0.172 | -0.165 | 1e-06 | sim | negativa | fraca | sim |
| social_media_hours | -0.167 | -0.166 | 1e-06 | sim | negativa | fraca | sim |
| exercise_frequency | 0.16 | 0.15 | 3e-06 | sim | positiva | fraca | sim |
| sleep_hours | 0.122 | 0.123 | 0.000916 | sim | positiva | fraca | sim |
| attendance_percentage | 0.09 | 0.094 | 0.031279 | sim | positiva | desprezível | sim |
| internet_quality_ord | -0.036 | -0.046 | 1 | não | negativa | desprezível | sim |
| part_time_job_bin | -0.027 | -0.03 | 1 | não | negativa | desprezível | sim |
| diet_quality_ord | 0.015 | 0.014 | 1 | não | positiva | desprezível | sim |
| age | -0.009 | -0.01 | 1 | não | negativa | desprezível | sim |
| parental_education_level_informado | -0.008 | -0.012 | 1 | não | negativa | desprezível | sim |
| extracurricular_participation_bin | 0.001 | 0.003 | 1 | não | positiva | desprezível | sim |

Leitura da coluna `força` (convenção usual, não corte desta base): |r| >= 0.5 forte, >= 0.3 moderada, >= 0.1 fraca, abaixo disso desprezível.

## 3.2 As variáveis de maior influência

### Maior influência positiva

**`study_hours_per_day`, r = 0.825** (Spearman 0.812, p corrigido < 0,000001). Associação forte e a mais forte da base — nenhuma outra variável chega perto.

Demais associações positivas significativas: `study_share` (r = 0.744, forte), `mental_health_rating` (r = 0.322, moderada), `exercise_frequency` (r = 0.16, fraca), `sleep_hours` (r = 0.122, fraca), `attendance_percentage` (r = 0.09, desprezível).

### Maior influência negativa

**`leisure_screen_hours`, r = -0.238** (Spearman -0.228, p corrigido < 0,000001). Associação fraca: quanto maior, menor a nota que acompanha.

Demais associações negativas significativas: `netflix_hours` (r = -0.172, fraca), `social_media_hours` (r = -0.167, fraca).

### Significativo não quer dizer relevante

`attendance_percentage` passa no teste estatístico mas tem força desprezível (r = 0.09). Com 1000 alunos, relação minúscula fica significativa; reportar isso como achado seria exagerar o que o dado diz.

### Sem relação detectável com a nota

`internet_quality_ord`, `part_time_job_bin`, `diet_quality_ord`, `age`, `parental_education_level_informado`, `extracurricular_participation_bin`. Nenhuma passa pelo teste depois da correção de Holm. Vale dizer o que isso **não** significa: não é prova de que não exista relação, só de que esta amostra não a mostra.

## 3.3 Os dois métodos contam a mesma história?

Pearson e Spearman concordam em **todas** as variáveis (mesmo sinal e diferença menor que 0,1). Nenhuma relação depende de valor extremo nem esconde curva: as associações são lineares e monótonas, o que sustenta o uso de regressão linear na tarefa 4.

## 3.4 Redundância entre as variáveis

Pares que carregam quase a mesma informação (|r| >= 0.7):

| variavel_a | variavel_b | r |
|---|---|---|
| social_media_hours | leisure_screen_hours | 0.741 |
| study_hours_per_day | study_share | 0.718 |

Isso era esperado: as duas derivadas da tarefa 2 `leisure_screen_hours`, `study_share` são calculadas a partir das colunas de origem, então correlacionam com elas por construção.

**Consequência prática:** elas ficam **fora** do modelo da tarefa 4. Com duas variáveis quase idênticas, o coeficiente de cada uma fica instável e a leitura “quanto cada hora de estudo pesa na nota” deixa de valer. Elas continuam úteis para ler e para os gráficos, não para o modelo.

## 3.5 A nota difere entre grupos?

Teste de Kruskal-Wallis em cada coluna categórica, com p corrigido por Holm. O tamanho de efeito (ε²) está na tabela porque p pequeno em amostra grande não quer dizer diferença grande.

| variável | grupos | H | p corrigido | efeito (ε²) | significativo |
|---|---|---|---|---|---|
| faixa_saude_mental | 3 | 97.89 | < 0,000001 | 0.098 | sim |
| gender | 3 | 0.15 | 1 | 0 | não |
| internet_quality | 3 | 3.22 | 1 | 0.003 | não |
| diet_quality | 3 | 2.46 | 1 | 0.002 | não |
| parental_education_level | 4 | 3.16 | 1 | 0.003 | não |
| part_time_job | 2 | 0.92 | 1 | 0.001 | não |
| extracurricular_participation | 2 | 0.01 | 1 | 0 | não |

### `faixa_saude_mental` — diferença confirmada

p corrigido < 0,000001, ε² = 0.098 (≈ 9.8% da variação de posição na nota ligada a essa variável).

| grupo | alunos | media | mediana | desvio |
|---|---|---|---|---|
| Baixa (1-3) | 301 | 63.43 | 63.6 | 15.94 |
| Média (4-6) | 317 | 67.87 | 69.2 | 16.85 |
| Alta (7-10) | 382 | 75.9 | 75.45 | 15.49 |

Sem diferença detectável: `gender`, `internet_quality`, `diet_quality`, `parental_education_level`, `part_time_job`, `extracurricular_participation`. O caso de `gender` é o mais útil de registrar, porque contraria a expectativa de que haja diferença por gênero: aqui não há.

## 3.6 Método, e por que cada escolha

| Escolha | Por quê |
|---|---|
| Pearson **e** Spearman | Pearson mede relação linear, Spearman mede se a ordem acompanha. Concordando, a relação é sólida; divergindo, há curva ou extremo puxando — e isso precisa aparecer, não ser escondido. |
| Correção de Holm-Bonferroni | São 15 variáveis testadas contra a mesma nota. A 5% por teste, esperar-se-ia quase um achado falso só por acaso. Holm é menos conservadora que Bonferroni puro e não exige que os testes sejam independentes — e aqui eles não são. |
| Kruskal-Wallis para grupos | Serve para 2 ou mais grupos, não exige distribuição normal nem variância igual. Nota autodeclarada em grupos de tamanhos muito diferentes (42 alunos em `Other` contra 481 em `Female`) não cumpre essas condições. |
| Tamanho de efeito junto do p | Com 1000 alunos, quase tudo fica significativo. O ε² responde “a diferença é grande?”, que é a pergunta que interessa. |
| Coluna constante ignorada | Correlação com algo que não varia é indefinida; incluir devolveria um número sem sentido. |
