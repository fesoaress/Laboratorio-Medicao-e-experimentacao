"""Teste de integridade do experimento com SQLite local e dados sintéticos."""
import csv
import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
SCRIPT=Path(__file__).with_name("experimento_sqlite.py")
with tempfile.TemporaryDirectory(prefix="lab05_") as temp:
    root=Path(temp)
    subprocess.run([sys.executable,str(SCRIPT),"--rows","300","--sessions","2",
                    "--blocks-per-session","2","--queries","5","--outdir",str(root)],
                   check=True,capture_output=True,text=True)
    data=list(csv.DictReader((root/"medicoes_blocos.csv").open()))
    meta=json.loads((root/"metadados.json").read_text())
    assert len(data)==8
    assert len({(r["sessao"],r["bloco"],r["tratamento"]) for r in data})==8
    assert {r["tratamento"] for r in data}=={"sem_indice","com_indice"}
    assert all(float(r["tempo_por_consulta_ms"])>0 for r in data)
    assert meta["n_queries_per_treatment"]==20
    assert meta["extra_index_bytes"]>0
    assert "SCAN pedidos_sem" in str(meta["planos"]["sem_indice"])
    assert "USING INDEX" in str(meta["planos"]["com_indice"])
    conn=sqlite3.connect(root/"sqlite_experimento.db")
    for k in (1,24,200,299):
        a=conn.execute("SELECT valor FROM pedidos_sem WHERE chave=?",(k,)).fetchone()
        b=conn.execute("SELECT valor FROM pedidos_com WHERE chave=?",(k,)).fetchone()
        assert a==b
    conn.close()
print("OK: pares, dados, planos de execução e metadados.")
