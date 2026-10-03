# Laboratório de Medição e Experimentação de Software

Repositório dos laboratórios da disciplina, com código, testes, dados,
documentação e artefatos finais separados por estudo.

- [Lab01 — Características de repositórios populares](lab01/README.md)
- [Lab02 — Assistentes de IA versus codificação manual](lab02/README.md)
- [Lab03 — Mineração de métricas DORA](lab03/README.md)

## Estrutura

```text
/
├── README.md
├── .gitignore
├── pytest.ini
├── .github/consolidation/  # auditoria global da consolidação
├── lab01/                 # coleta, análise, dados, snapshots e relatórios
├── lab02/                 # katas, trials, métricas, análises e relatórios
└── lab03/                 # seleção, metadados, funil e hipóteses iniciais
```

Cada laboratório possui suas próprias dependências e instruções de execução.
Python 3.11+; a consolidação foi validada em Python 3.13.15. Não há
`requirements.txt` global herdado de um laboratório. Tokens e ambientes
virtuais são locais e ficam fora do versionamento.

Na raiz, após instalar as dependências de testes dos laboratórios em seu
ambiente Python, execute `python -m pytest -q`. O `pytest.ini` seleciona
somente suítes reais; snapshots, soluções de trials e stubs de katas são
artefatos experimentais e não compõem essa suíte global.

A proposta de estrutura canônica deve entrar na `main` somente após revisão
do PR. As branches históricas permanecem preservadas. A origem dos arquivos,
comparações por blob, inventários e limitações estão na
[auditoria de consolidação](.github/consolidation/README.md).
