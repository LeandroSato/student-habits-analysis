# 2. Engenharia de dados

Gerado por `analysis/run_analysis.py`. Cada transformação desta página tem o motivo escrito junto, porque decisão sem motivo não se defende.

## 2.1 Decisão sobre os valores ausentes

`parental_education_level` é a única coluna com ausência: **91 de 1000 alunos**. Antes de decidir o que fazer, a pergunta é se essa ausência tem relação com a nota.

| grupo | alunos | nota média |
|---|---|---|
| não informou | 91 | 70.03 |
| informou | 909 | 69.56 |

O teste de Mann-Whitney dá **p = 0.7079**, bem acima de 0,05: não há evidência de que a nota de quem não informou seja diferente (diferença observada de 0.48 ponto). A ausência parece aleatória em relação ao alvo.

### As três opções, e por que a escolhida

| Opção | Efeito | Decisão |
|---|---|---|
| Descartar as 91 linhas | Perde 9.1% da base sem corrigir viés nenhum, já que a ausência não se liga à nota | descartada |
| Preencher pela moda (`High School`) | Põe 91 alunos em um grupo sem nenhuma evidência: infla esse grupo e dilui a comparação entre grupos da tarefa 3 | descartada |
| Categoria própria `Não informado` + flag `parental_education_level_informado` | Mantém os 1000 alunos, não inventa valor e deixa a própria ausência disponível para análise | **escolhida** |

A flag existe por um motivo prático: se não informar a escolaridade dos pais estivesse associado à nota, a flag mostraria isso na matriz de correlação. Aqui ela serve de prova de que não está.

## 2.2 O que o tratamento fez

| passo | resultado |
|---|---|
| linhas na entrada | 1000 |
| linhas duplicadas removidas | 0 |
| valores impossíveis corrigidos | 0 |
| colunas com ausência virada categoria | 1 |
| nulos restantes | 0 |
| linhas na saída | 1000 |

### Inconsistências: barrar em vez de consertar escondido

A tarefa 1 não encontrou nenhum valor fora do domínio, então não havia o que corrigir. Em vez de escrever um tratamento para um problema inexistente — código morto que ninguém testa — o pipeline **valida e interrompe**: se um arquivo futuro trouxer 30 horas de estudo por dia, `clean()` levanta `DomainViolationError` e para. Corrigir em silêncio com um `clip` seria pior: o número ficaria plausível e errado.

A remoção de duplicatas segue no pipeline pelo mesmo raciocínio ao contrário: custa nada, e o log registrando zero é um resultado verificado, não um passo inútil.

## 2.3 Faixas criadas

Faixa serve à leitura: “alunos que passam mais de 4h em redes sociais tiram X” se explica em uma frase, coeficiente de regressão não. Todas as faixas são **fechadas à esquerda** — um valor exatamente no corte cai na faixa de cima, senão 2,0 h cairia em “1 a 2h” e contradiria o rótulo.

### `faixa_redes_sociais` — de `social_media_hours`

Cortes: 0, 1, 2, 3, 4, infinito.

**Por quê:** Cortes em horas inteiras: é a unidade em que uma recomendação é dada (“reduza 1 hora por dia”) e em que o aluno consegue se enxergar. Os quartis observados (1,7 / 2,5 / 3,3 h) caem dentro das faixas, então nenhuma delas fica vazia.

| faixa | alunos | pct |
|---|---|---|
| Até 1h | 98 | 9.8 |
| 1 a 2h | 227 | 22.7 |
| 2 a 3h | 311 | 31.1 |
| 3 a 4h | 251 | 25.1 |
| 4h ou mais | 113 | 11.3 |

### `faixa_estudo` — de `study_hours_per_day`

Cortes: 0, 2, 4, 6, infinito.

**Por quê:** Blocos de 2 horas em vez de 1: mantém grupos grandes o bastante para comparar (a mediana é 3,5 h e o máximo 8,3 h) sem criar faixa com pouquíssimos alunos no extremo.

| faixa | alunos | pct |
|---|---|---|
| Até 2h | 133 | 13.3 |
| 2 a 4h | 482 | 48.2 |
| 4 a 6h | 332 | 33.2 |
| 6h ou mais | 53 | 5.3 |

### `faixa_sono` — de `sleep_hours`

Cortes: 0, 6, 7, 9, infinito.

**Por quê:** Único corte vindo de fora da base: a faixa de 7 a 9 horas é a recomendação usual para jovens adultos. É convenção externa, não um número do CSV — está marcada como tal para que a comparação seja “dentro ou fora do recomendado”, e não um corte arbitrário.

| faixa | alunos | pct |
|---|---|---|
| Menos de 6h | 343 | 34.3 |
| 6 a 7h | 312 | 31.2 |
| 7 a 9h (recomendado) | 319 | 31.9 |
| 9h ou mais | 26 | 2.6 |

### `faixa_saude_mental` — de `mental_health_rating`

Cortes: 1, 4, 7, 11.

**Por quê:** A escala vai de 1 a 10 e é autodeclarada; três blocos de largura parecida (3, 3 e 4 pontos) separam o grupo em risco do grupo bem sem fingir precisão que uma nota subjetiva não tem.

| faixa | alunos | pct |
|---|---|---|
| Baixa (1-3) | 301 | 30.1 |
| Média (4-6) | 317 | 31.7 |
| Alta (7-10) | 382 | 38.2 |

### `faixa_frequencia` — de `attendance_percentage`

Cortes: 0, 75, 85, 95, infinito.

**Por quê:** 75% é o mínimo de presença exigido em boa parte das instituições — convenção externa, assim como no sono. Acima dele, cortes de 10 pontos para separar presença boa de presença quase perfeita.

| faixa | alunos | pct |
|---|---|---|
| Abaixo de 75% | 168 | 16.8 |
| 75 a 85% | 358 | 35.8 |
| 85 a 95% | 325 | 32.5 |
| 95% ou mais | 149 | 14.9 |

## 2.4 Combinações entre colunas

**`leisure_screen_hours`** = `social_media_hours` + `netflix_hours`. As duas medem tempo de tela por lazer; somadas, dão o tamanho real do concorrente do estudo, em vez de duas metades analisadas à parte.

**`study_share`** = estudo ÷ (estudo + tela de lazer). É a medida relativa: 2h de estudo com 1h de tela é uma rotina diferente de 2h de estudo com 6h de tela, e em horas absolutas as duas aparecem iguais.

| coluna | contagem | media | desvio | minimo | q25 | mediana | q75 | maximo | assimetria |
|---|---|---|---|---|---|---|---|---|---|
| leisure_screen_hours | 1000 | 4.33 | 1.6 | 0.2 | 3.3 | 4.4 | 5.4 | 10.1 | 0.09 |
| study_share | 1000 | 0.45 | 0.16 | 0 | 0.36 | 0.45 | 0.55 | 0.9643 | -0.15 |

Nulos em `study_share`: **0**. A coluna fica nula quando o aluno não registra nem estudo nem tela (divisão por zero); na base do desafio isso não ocorre, mas o guarda existe para não gerar infinito em silêncio.

## 2.5 Codificações

Texto com ordem natural vira número para poder entrar em correlação e no modelo. Sim/não vira 0/1 pelo mesmo motivo.

| coluna | nova coluna | escala |
|---|---|---|
| diet_quality | diet_quality_ord | Poor = 0 < Fair = 1 < Good = 2 |
| internet_quality | internet_quality_ord | Poor = 0 < Average = 1 < Good = 2 |
| part_time_job | part_time_job_bin | No = 0 · Yes = 1 |
| extracurricular_participation | extracurricular_participation_bin | No = 0 · Yes = 1 |

`parental_education_level` ficou **de fora** da codificação ordinal de propósito: depois do tratamento ela tem a categoria `Não informado`, que não ocupa lugar nenhum em uma escala ordenada. Ela entra no modelo da tarefa 4 como one-hot.

### Todas as colunas derivadas

`faixa_redes_sociais`, `faixa_estudo`, `faixa_sono`, `faixa_saude_mental`, `faixa_frequencia`, `leisure_screen_hours`, `study_share`, `diet_quality_ord`, `internet_quality_ord`, `part_time_job_bin`, `extracurricular_participation_bin`, `parental_education_level_informado` — 12 colunas novas, nenhuma substituindo a original.
