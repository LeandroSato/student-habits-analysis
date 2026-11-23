# 4. Aplicação prática: simulador de cenários

Gerado por `analysis/run_analysis.py`. O app está em `app/streamlit_app.py` e roda com `streamlit run app/streamlit_app.py`.

> **Correlação não é causa.** Tudo nesta página mede se duas coisas andam juntas, nunca se uma produz a outra. O dado é observacional e de um único momento: não há grupo de controle, nada foi sorteado e qualquer relação aqui pode vir de uma terceira variável não medida, ou valer no sentido inverso.

## 4.1 Que decisão isso apoia, e quem usaria

A tarefa 3 terminou com um ranking de correlações. Um ranking responde “o que anda junto com nota alta” — não responde **o que fazer com um aluno específico na segunda-feira de manhã**. É essa a lacuna que o simulador fecha.

**Quem usaria:** coordenação pedagógica e tutoria de uma instituição de ensino.

**A decisão apoiada:** onde colocar o esforço. Diante do retrato de hábitos de um aluno, qual mudança o modelo associa ao maior ganho — levar sono para a conversa ou tempo de tela? Encaminhar para apoio psicológico ou para oficina de organização de estudo? O app ordena as opções por tamanho do efeito previsto, para aquele aluno, e não no geral.

**Uso secundário:** rodar a previsão na turma inteira e começar a tutoria pelos alunos de previsão mais baixa, em vez de esperar a primeira prova.

**O que o app explicitamente não faz:** prometer que mudar o hábito muda a nota. O aviso está na primeira tela, não escondido no rodapé.

## 4.2 Qual modelo, e por quê

### Regressão linear, não algo mais forte

O produto aqui é a frase “uma hora a mais de estudo está associada a X pontos”. Árvore, floresta ou boosting ganhariam alguns pontos de precisão e **perderiam a frase** — e sem a frase o app não apoia decisão nenhuma, só cospe um número. A tarefa 3 ajuda: Pearson e Spearman concordaram em todas as variáveis, ou seja, as relações são lineares e monótonas. A escolha não é só de conveniência.

### Quais variáveis entram

Dois conjuntos foram treinados e comparados, com a regra escrita antes de ver o resultado: o modelo maior só vence se ganhar mais de 0.005 de R² em validação cruzada.

| conjunto | variáveis | r2 | mae | rmse | R² (validação cruzada) | desvio entre dobras |
|---|---|---|---|---|---|---|
| completo | 13 | 0.8991 | 4.1 | 5.09 | 0.8947 | 0.0197 |
| enxuto | 7 | 0.9007 | 4.07 | 5.05 | 0.8965 | 0.0194 |

**Escolhido: o conjunto enxuto.** A diferença de R² entre os dois é de 0.0018 — dentro da tolerância. O conjunto enxuto usa só os sete hábitos que passaram no teste de significância da tarefa 3; idade, dieta, qualidade da internet, trabalho de meio período, atividade extracurricular e escolaridade dos pais ficam de fora porque não mostraram relação com a nota e não melhoram a previsão.

As duas derivadas da tarefa 2 `leisure_screen_hours`, `study_share` também ficam de fora, pelo motivo já registrado na tarefa 3: são redundantes com as colunas de origem e tornariam os coeficientes instáveis.

## 4.3 O modelo acerta?

| métrica | valor |
|---|---|
| R² (teste) | 0.9007 |
| R² (treino) | 0.9107 |
| R² médio (validação cruzada) | 0.8965 |
| desvio do R² entre as dobras | 0.0194 |
| erro médio absoluto (pontos) | 4.07 |
| raiz do erro quadrático médio | 5.05 |
| erro ao chutar sempre a média | 12.38 |
| alunos no treino | 800 |
| alunos no teste | 200 |

O modelo erra em média **4.07 pontos**. Chutar sempre a nota média erraria **12.38** — é essa a comparação que importa, porque um R² solto não diz se o modelo faz algo melhor que o óbvio.

R² de treino e de teste diferem em 0.01, e o R² varia 0.0194 entre as cinco dobras da validação cruzada. Os dois números juntos dizem que o resultado não depende de qual pedaço da base caiu no treino, e que o modelo não decorou os dados.

Dobras: 0.8996, 0.9068, 0.9251, 0.8813, 0.8699.

## 4.4 O que cada hábito pesa

| hábito | pontos por unidade | pontos por desvio padrão | direção |
|---|---|---|---|
| Horas de estudo por dia | 9.536 | 14.007 | positiva |
| Saúde mental autodeclarada (1 a 10) | 1.949 | 5.551 | positiva |
| Horas em redes sociais por dia | -2.703 | -3.169 | negativa |
| Exercício (vezes por semana) | 1.315 | 2.664 | positiva |
| Horas de streaming por dia | -2.318 | -2.493 | negativa |
| Horas de sono por noite | 1.992 | 2.443 | positiva |
| Frequência nas aulas (%) | 0.146 | 1.369 | positiva |

Intercepto: 7.003. Ele é a nota prevista com todas as variáveis em zero — situação que não existe (ninguém dorme 0 hora e tem 0% de frequência), então não tem leitura prática; entra só na conta.

**Duas unidades, duas perguntas.** “Pontos por unidade” responde quanto a nota muda por uma hora a mais — é o número que o simulador usa. “Pontos por desvio padrão” responde qual hábito pesa mais, e é o único jeito honesto de comparar: hora de estudo e ponto percentual de frequência não se comparam direto.

Por qualquer uma das duas medidas, **horas de estudo por dia** domina (9.536 pontos por unidade, 14.007 por desvio padrão).

## 4.5 Onde o modelo falha

| Limite | O que foi feito |
|---|---|
| **Efeito teto.** 48 alunos tiraram exatamente 100; sem travar, o modelo preveria nota acima de 100 | previsão truncada em [0, 100], e o app avisa quando bate no teto |
| **Suposição linear.** O modelo assume que a oitava hora de estudo vale o mesmo que a primeira | sustentado pela concordância entre Pearson e Spearman (tarefa 3), mas continua sendo suposição |
| **Extrapolação.** Fora da faixa observada a previsão é invenção | os controles do app param no mínimo e no máximo da base |
| **Nada é causa.** O modelo descreve quem tira nota alta, não o que produz nota alta | aviso fixo na primeira tela do app e em toda conclusão |
| **Saúde mental é autodeclarada e pode ser consequência.** Ir mal na prova afeta como o aluno avalia a própria saúde mental | registrado como limitação; o sentido da relação não é testável com este dado |

### Decisão de engenharia: modelo treinado na hora

O app treina o modelo ao abrir, em cache de sessão, em vez de carregar um arquivo `.pkl` versionado. São 1000 linhas e o treino leva milissegundos; um artefato binário no repositório envelheceria em silêncio na primeira vez que o tratamento mudasse.
