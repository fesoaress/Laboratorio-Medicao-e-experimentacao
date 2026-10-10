"""CLI offline: python -m src.s02 {generate,validate,analyze}."""

import argparse
import json
from pathlib import Path

from .agreement import analyze
from .gold_sample import RATERS, SEED, generate
from .label_validation import load_sample, public_result, validate_labels


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Lab03 S02 — amostra cega e concordância humana")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="Exige coleta final real; não consulta API nem heurística")
    gen.add_argument("--repositories", type=Path, required=True)
    gen.add_argument("--releases", type=Path, required=True)
    gen.add_argument("--commits", type=Path)
    gen.add_argument("--intervals", type=Path)
    gen.add_argument("--start-date", required=True)
    gen.add_argument("--end-date", required=True)
    gen.add_argument("--seed", type=int, default=SEED)
    gen.add_argument("--output-dir", type=Path, default=Path("data/gold_sample"))
    gen.add_argument("--report", type=Path, default=Path("reports/lab03_s02_islayder_review.md"))
    val = sub.add_parser("validate", help="Erro enquanto faltarem avaliações")
    val.add_argument("file", type=Path)
    val.add_argument("--sample", type=Path, default=Path("data/gold_sample/gold_sample.csv"))
    val.add_argument("--json", type=Path, help="Salvar todos os diagnósticos")
    ana = sub.add_parser("analyze", help="Kappa e consenso somente após três arquivos completos")
    ana.add_argument("--sample", type=Path, default=Path("data/gold_sample/gold_sample.csv"))
    for rater in RATERS:
        ana.add_argument(f"--{rater}", type=Path, default=Path(f"data/gold_sample/gold_sample_{rater}.csv"))
    ana.add_argument("--output-dir", type=Path, default=Path("data/validation"))
    ana.add_argument("--consensus-dir", type=Path, default=Path("data/gold_sample"))
    ana.add_argument("--report", type=Path, default=Path("reports/lab03_s02_validation.md"))
    ana.add_argument("--resolutions", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            result = generate(args.repositories, args.releases, args.output_dir, args.report,
                              start_date=args.start_date, end_date=args.end_date, seed=args.seed,
                              commits_path=args.commits, intervals_path=args.intervals)
            print(f"Elegíveis: {result['eligible_repositories']}; sorteados: 60; releases: 300; seed: {args.seed}")
            return 0
        if args.command == "validate":
            result = public_result(validate_labels(args.file, load_sample(args.sample)))
            serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
            print(serialized)
            if args.json:
                if args.json.resolve() in (args.file.resolve(), args.sample.resolve()):
                    raise ValueError("Diagnóstico não pode sobrescrever entradas.")
                args.json.parent.mkdir(parents=True, exist_ok=True)
                args.json.write_text(serialized, encoding="utf-8")
            return 0 if result["complete"] else 1
        code = analyze(args.sample, {rater: getattr(args, rater) for rater in RATERS},
                       args.output_dir, args.report, args.resolutions, args.consensus_dir)
        print("Análise concluída." if code == 0 else "Aguardando rotulagens." if code == 1 else "Aguardando revisão manual de consenso.")
        return code
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Não executado: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
