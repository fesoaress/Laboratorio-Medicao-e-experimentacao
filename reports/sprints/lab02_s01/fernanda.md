# Lab02 S01 — Fernanda (RQ3 / métricas estruturais)

## O que foi entregue

Artefato de código para coleta reproduzível das métricas estáticas da RQ3:

- complexidade ciclomática média por função/método (Radon);
- percentual de duplicação (jscpd);
- LOC de controle (`lloc` via Radon raw);
- script `lab02/metrics/run_metrics.py`;
- configuração versionada das ferramentas;
- exemplo validado em `lab02/metrics/examples/exemplo_validacao/`;
- saída estruturada JSON + CSV (`results/metrics.csv`).

## Decisões metodológicas

- Analisar apenas `solucao.py` do trial.
- Excluir testes automatizados (iguais para todos; não são código do participante).
- LOC operacional = `lloc` do Radon.
- Configuração do jscpd congelada (mesmos limiares em todos os trials).

## Como validar

Ver `lab02/metrics/README.md`.
