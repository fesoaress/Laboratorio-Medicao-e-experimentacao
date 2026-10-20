# CFR(b) — definição operacional confirmada pelo grupo

Em 20/10/2026, o grupo confirmou o enunciado de RQ03(b): release R falha se
for seguida em até sete dias por uma corretiva; originais nos últimos sete
dias da janela ficam fora do denominador. A decisão sobre intermediárias foi
explicitada pelo grupo: **qualquer corretiva posterior** é suficiente, não
apenas a imediatamente seguinte. Essa interpretação não é apresentada como
um detalhamento literal adicional do professor.

Política `any_corrective_7d_v1`, heurística **v5** (F1=0,7248908296943232):

1. Usar todas as releases estáveis principais coletadas (sem draft/prerelease)
   dentro de `[2025-10-01, 2026-10-01)`, ordenadas por publicação/ID.
2. Para cada original R, procurar evidência com publicação estritamente
   posterior a R e no máximo R+7 dias (limite de sete dias inclusivo).
   Instantes iguais não comprovam publicação posterior.
3. Qualquer classificação corretiva positiva e utilizável basta, mesmo com
   releases não corretivas intermediárias. Cada original conta uma única vez.
4. Originais a partir de **2026-09-24T00:00:00Z** são censurados
   incondicionalmente, mesmo que haja positiva posterior. Ficam fora do
   numerador/denominador, mas podem servir de evidência para originais anteriores.
5. Fora da censura, se não há positiva conhecida e existe classificação
   posterior não utilizável no intervalo, R fica não calculável, fora do
   denominador. Se há positiva conhecida, a existência já está demonstrada.
6. Sem positiva e sem classificação posterior indisponível, R é não falha.
   Ausência de evento é observável quando os sete dias completos estão na janela.
7. A primeira release pode ser original avaliável sem predecessora. A
   heurística não inventa patch SemVer nessa ausência e usa os demais sinais
   disponíveis; v5 não decide por patch isolado.

`CFR(b) = originais failed / (originais failed + originais not_failed)`.
Denominador zero gera ausência e status específico, nunca zero artificial.
Sem dados completos não se infere resultado negativo. As regras foram testadas
com fixtures separadas, incluindo limites exatos, intermediárias, múltiplas
corretivas, censura mesmo com positiva, ausência de predecessora e contexto parcial.

## Resultado real e rastreabilidade

311 repositórios com CFR(b) válido, zero ausentes. Partição das 27.152 releases:
20.038 falhas, 6.406 não falhas, 677 censuradas, 31 não calculáveis por contexto
posterior. O denominador soma 26.444 originais; as razões finais são por repo,
não essa razão global aplicada indiscriminadamente a todos.

`cfr_delivery_releases_s02.csv` preserva a evidência por original, o motivo e
a censura. `cfr_delivery_s02.csv` agrega por repo. O manifesto registra fontes,
versão, avaliação, definição/cutoff e hashes. A fonte em cada linha do dataset
identifica esse manifesto, a política, v5 e o SHA-256 da avaliação aceita.

```powershell
python -m src.corrective_population
python -m src.cfr_delivery
python -m src.s02_dataset
python -m src.s02_quality
```

População e CFR(b) recusam sobrescrever saídas. Para nova execução, usar nova
pasta de população e cópia das entradas em novo `--folder`. Não requer API
nem nova rotulagem. A consolidação preserva as outras 46 colunas do dataset.
