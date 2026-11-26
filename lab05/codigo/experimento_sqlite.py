#!/usr/bin/env python3
"""LAB05 SQLite: comparação pareada com e sem índice, usando dados sintéticos."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import platform
import random
import sqlite3
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

ARMS = ("sem_indice", "com_indice")
SQL = {
    "sem_indice": "SELECT valor FROM pedidos_sem WHERE chave = ?",
    "com_indice": "SELECT valor FROM pedidos_com WHERE chave = ?",
}

def args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rows", type=int, default=60000)
    p.add_argument("--sessions", type=int, default=10)
    p.add_argument("--blocks-per-session", type=int, default=8)
    p.add_argument("--queries", type=int, default=50)
    p.add_argument("--seed", type=int, default=20261121)
    p.add_argument("--outdir", type=Path, default=Path("dados"))
    a = p.parse_args()
    if min(a.rows,a.sessions,a.blocks_per_session,a.queries) < 1 or a.queries > a.rows:
        p.error("Todos os tamanhos devem ser positivos e queries <= rows")
    return a

def db_create(path, n, rng):
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA automatic_index=OFF")
    conn.execute("PRAGMA cache_size=-2048")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("CREATE TABLE pedidos_sem (id INTEGER PRIMARY KEY, chave INTEGER NOT NULL, valor TEXT NOT NULL)")
    keys = list(range(1,n+1))
    rng.shuffle(keys)
    conn.executemany("INSERT INTO pedidos_sem VALUES (?,?,?)",
        ((i+1,keys[i],f"pedido_sintetico_{i+1:08d}") for i in range(n)))
    conn.execute("CREATE TABLE pedidos_com (id INTEGER PRIMARY KEY, chave INTEGER NOT NULL, valor TEXT NOT NULL)")
    conn.execute("INSERT INTO pedidos_com SELECT * FROM pedidos_sem")
    conn.commit()
    pages_before = conn.execute("PRAGMA page_count").fetchone()[0]
    page_size = conn.execute("PRAGMA page_size").fetchone()[0]
    conn.execute("CREATE INDEX idx_chave_pedidos_com ON pedidos_com(chave)")
    conn.commit()
    pages_after = conn.execute("PRAGMA page_count").fetchone()[0]
    assert conn.execute("SELECT COUNT(*) FROM pedidos_sem").fetchone()[0] == n
    assert conn.execute("SELECT COUNT(*) FROM pedidos_com").fetchone()[0] == n
    unequal=conn.execute("""SELECT COUNT(*) FROM pedidos_sem s JOIN pedidos_com c ON s.id=c.id
                         WHERE s.chave!=c.chave OR s.valor!=c.valor""").fetchone()[0]
    assert unequal == 0
    plans = {a: [r[3] for r in conn.execute("EXPLAIN QUERY PLAN "+SQL[a],(1,))] for a in ARMS}
    assert "SCAN pedidos_sem" in str(plans["sem_indice"])
    assert "USING INDEX idx_chave_pedidos_com" in str(plans["com_indice"])
    conn.close()
    return {"planos": plans, "page_size_bytes": page_size, "pages_before": pages_before,
            "pages_after": pages_after, "extra_index_bytes": (pages_after-pages_before)*page_size}

def measure(path,n,sessions,blocks,queries,rng):
    result=[]
    for sess in range(1,sessions+1):
        conn=sqlite3.connect(path)
        conn.execute("PRAGMA automatic_index=OFF")
        conn.execute("PRAGMA cache_size=-2048")
        conn.execute("PRAGMA temp_store=MEMORY")
        cur={a:conn.cursor() for a in ARMS}
        warm=rng.sample(range(1,n+1),min(n,40))
        for a in ARMS:
            for k in warm:
                assert cur[a].execute(SQL[a],(k,)).fetchone() is not None
        for bloco in range(1,blocks+1):
            keys=rng.sample(range(1,n+1),queries)
            first=ARMS[(bloco+sess)%2]
            order=[first, ARMS[1-ARMS.index(first)]]
            for pos,arm in enumerate(order,1):
                start=time.perf_counter_ns()
                for k in keys:
                    assert cur[arm].execute(SQL[arm],(k,)).fetchone() is not None
                ms=(time.perf_counter_ns()-start)/1000000.
                result.append({"sessao":sess,"bloco":bloco,"ordem_na_dupla":pos,
                    "tratamento":arm,"consultas":queries,
                    "tempo_total_ms":round(ms,8),"tempo_por_consulta_ms":round(ms/queries,9)})
        conn.close()
        print(f"Sessão {sess}/{sessions} concluída.",flush=True)
    assert len(result)==2*sessions*blocks
    return result

def main():
    a=args()
    out=a.outdir.resolve()
    out.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc).isoformat(timespec="seconds")
    rng=random.Random(a.seed)
    db=out/"sqlite_experimento.db"
    metadata=db_create(db,a.rows,rng)
    values=measure(db,a.rows,a.sessions,a.blocks_per_session,a.queries,rng)
    file=out/"medicoes_blocos.csv"
    with file.open("w",encoding="utf-8",newline="") as fp:
        w=csv.DictWriter(fp,fieldnames=list(values[0]))
        w.writeheader();w.writerows(values)
    groups={arm:[r["tempo_por_consulta_ms"] for r in values if r["tratamento"]==arm] for arm in ARMS}
    metadata.update({"tipo":"experimento local com dados sintéticos; não produção",
        "data_inicio_utc":started,"data_fim_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed":a.seed,"sqlite_version":sqlite3.sqlite_version,"python":platform.python_version(),
        "sistema":platform.platform(),"maquina":platform.machine(),"processador":platform.processor(),
        "cpu_count_logico":os.cpu_count(),"rows_per_table":a.rows,"sessions":a.sessions,
        "blocks_per_session":a.blocks_per_session,"queries_per_block":a.queries,
        "n_queries_per_treatment":a.sessions*a.blocks_per_session*a.queries,
        "PRAGMA":{"automatic_index":"OFF","cache_size":"-2048 KiB","temp_store":"MEMORY"},
        "resumo_blocos":{arm:{"mediana_bloco_ms":statistics.median(v),
             "media_bloco_ms":statistics.mean(v),"min_bloco_ms":min(v),
             "max_bloco_ms":max(v)} for arm,v in groups.items()},
        "sha256_medicoes_csv":hashlib.sha256(file.read_bytes()).hexdigest(),
        "observacao":"somente o ambiente local; resultados mudam conforme hardware/carga"})
    (out/"metadados.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"sqlite":sqlite3.sqlite_version,"sessões":a.sessions,
        "pares":a.sessions*a.blocks_per_session,"medianas":{k:statistics.median(v) for k,v in groups.items()},
        "indice_extra_bytes":metadata["extra_index_bytes"]},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
