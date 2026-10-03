# Lab01S02 — Vinicius

## O que fiz

Validei RQ05 e RQ06 sobre os 1.000 repositórios coletados por Islayder (`data/raw/repositories_s02.csv`), definindo o **TIOBE Index** como fonte de referência para "linguagens mais populares" (edição de agosto/2026, `https://www.tiobe.com/tiobe-index/`), mantida daqui em diante para todo o Lab01, inclusive o bônus RQ07.

Estendi `build_collection_statistics()` em `src/collection/validation.py` com duas funções novas — `build_language_distribution()` e `build_closed_issues_ratio_distribution()` — para calcular a distribuição de frequência de linguagens (RQ05) e as estatísticas de dispersão e outliers (regra do IQR) da razão de issues fechadas (RQ06), sem duplicar o que já existia (contagem de "não informado" e "indefinida" já estava em `build_collection_statistics()`). Também atualizei `print_collection_summary()` em `collect_repositories.py` para exibir essas duas seções no resumo do CLI.

## Decisões técnicas

Optei por integrar as estatísticas de RQ05/RQ06 dentro do `validation.py` compartilhado, em vez de criar um script de análise separado, para evitar fragmentar a lógica de validação em vários arquivos — o dataset é o mesmo, então faz sentido que as estatísticas derivadas dele fiquem no mesmo módulo. Para detecção de outliers em RQ06, usei a regra do IQR (1,5×IQR além de Q1/Q3) por ser o método mais simples e amplamente aceito para dados de proporção como esse.

## Validações e testes

Antes de mexer no dataset de 1.000, validei a lógica de `rq05_rq06.py` isoladamente com um teste offline (sem chamar a API), cobrindo: repositório normal, `primaryLanguage: null`, zero issues (razão deve ser indefinida, não zero) e o caso de erro (issues fechadas maior que o total). Os 4 casos passaram.

Rodei a leitura e validação sobre o CSV completo de 1.000 repositórios: nenhum erro de validação relacionado a RQ05/RQ06 (nenhuma issue fechada excedendo o total, nenhuma razão fora do intervalo 0–1, nenhum caso de "indefinida" incorreto).

## RQ05 e RQ06

Na distribuição de RQ05, foram identificadas 44 linguagens distintas, com 87 repositórios (8,70%) sem linguagem primária informada. O top 5 é Python (22,90%), TypeScript (17,40%), JavaScript (11,00%), Não informado (8,70%) e Go (7,60%) — Python, TypeScript e JavaScript somados já respondem por 51,3% da amostra.

Comparando com o TIOBE Index de agosto/2026 (Python 1º, C 2º, C++ 3º, Java 4º, C# 5º, JavaScript 6º), a hipótese informal de que repositórios populares seguem as linguagens mais populares em geral se confirma parcialmente: Python lidera em ambos. Mas há divergência notável — TypeScript e Go têm presença desproporcionalmente alta no GitHub em relação à sua posição no TIOBE (ambos fora do top 10), sugerindo que popularidade por volume de busca (TIOBE) não captura totalmente as tendências de adoção em projetos open-source hospedados no GitHub.

Na distribuição de RQ06, 957 repositórios têm razão de issues fechadas definida (43 ficaram indefinidos por zero issues). A mediana foi 87,50%, com Q1 em 70,46% e Q3 em 96,78%, mínimo de 7,69% e máximo de 100%. Foram identificados 39 outliers (4,08%) pela regra do IQR. Como hipótese preliminar, repositórios populares realmente concentram issues fechadas em taxa alta, mas existe uma cauda de projetos com taxa de fechamento bem abaixo da mediana — provavelmente projetos muito ativos onde a abertura de novas issues supera a capacidade de triagem dos mantenedores.

## Limitações

Assim como no relatório do Islayder, esta ainda não é a análise estatística final da Sprint 3 — os outliers de RQ06 foram apenas identificados, não investigados individualmente. A comparação com o TIOBE é uma hipótese informal baseada só no top 6-10 de cada ranking; uma análise mais completa (Sprint 3) deve considerar a cauda longa de linguagens menos frequentes.