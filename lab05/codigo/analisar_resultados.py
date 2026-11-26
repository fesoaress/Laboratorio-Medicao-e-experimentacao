#!/usr/bin/env python3
"""Analisa os blocos pareados; usa sessões, não consultas individuais, para inferência."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import binomtest
import matplotlib.pyplot as plt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    root=p.parse_args().root
    meta=json.loads((root/"dados"/"metadados.json").read_text(encoding="utf-8"))
    data=pd.read_csv(root/"dados"/"medicoes_blocos.csv")
    assert len(data)==2*meta["sessions"]*meta["blocks_per_session"]
    assert set(data.tratamento)=={"sem_indice","com_indice"}
    assert not data.isna().any().any()
    assert (data.tempo_por_consulta_ms>0).all()
    assert data.duplicated(["sessao","bloco","tratamento"]).sum()==0
    assert data.groupby(["sessao","bloco"]).tratamento.nunique().eq(2).all()
    pair=data.pivot(index=["sessao","bloco"],columns="tratamento",values="tempo_por_consulta_ms")
    by_sess=pair.groupby(level="sessao").median()
    by_sess["diferenca_ms"]=by_sess.sem_indice-by_sess.com_indice
    by_sess["aceleracao_x"]=by_sess.sem_indice/by_sess.com_indice
    by_sess["reducao_pct"]=100*(1-by_sess.com_indice/by_sess.sem_indice)
    by_sess.to_csv(root/"dados"/"resumo_sessoes.csv",float_format="%.9f")
    pos=int((by_sess.diferenca_ms>0).sum())
    neg=int((by_sess.diferenca_ms<0).sum())
    pvalue=float(binomtest(pos,pos+neg,.5,alternative="greater").pvalue)
    rng=np.random.default_rng(20261121)
    x=by_sess[["sem_indice","com_indice"]].to_numpy()
    ix=rng.integers(0,len(x),size=(20000,len(x)))
    m=np.median(x[ix],axis=1)
    ci_speed=np.quantile(m[:,0]/m[:,1],[.025,.975]).tolist()
    ci_diff=np.quantile(m[:,0]-m[:,1],[.025,.975]).tolist()
    no=float(data[data.tratamento=="sem_indice"].tempo_por_consulta_ms.median())
    yes=float(data[data.tratamento=="com_indice"].tempo_por_consulta_ms.median())
    result={
      "alpha":.05,"status":"coleta local sintética; não produção",
      "unidade_inferencial":"sessão",
      "n_sessoes":len(by_sess),"n_blocos_pareados":len(pair),
      "n_consultas_por_tratamento":meta["n_queries_per_treatment"],
      "mediana_blocos_sem_indice_ms":no,"mediana_blocos_com_indice_ms":yes,
      "diferenca_de_medianas_blocos_ms":no-yes,
      "aceleracao_razao_de_medianas_blocos":no/yes,
      "reducao_latencia_pct":100*(1-yes/no),
      "n_sessoes_positivas":pos,"n_sessoes_negativas":neg,
      "p_valor_unilateral":pvalue,
      "ic95_bootstrap_percentil_aceleracao_razao_medianas_sessoes_x":ci_speed,
      "ic95_bootstrap_percentil_diferenca_razao_medianas_sessoes_ms":ci_diff,
      "bootstrap_n":20000,"bootstrap_seed":20261121,
      "armazenamento_adicional_indice_bytes":meta["extra_index_bytes"],
      "armazenamento_adicional_indice_kib":meta["extra_index_bytes"]/1024
    }
    (root/"dados"/"analise.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    folder=root/"graficos"; folder.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(8.5,4.1))
    ax.barh(["Sem índice","Com índice"],[no,yes])
    ax.invert_yaxis();ax.set_xlabel("Mediana por consulta (ms)")
    ax.set_title("SQLite: comparação de latência")
    fig.tight_layout();fig.savefig(folder/"01_latencia.png",dpi=170);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8.5,4.1))
    ax.plot(by_sess.index,by_sess.aceleracao_x,marker="o")
    ax.set_xlabel("Sessão");ax.set_ylabel("Aceleração (vezes)")
    ax.set_title("Aceleração em cada sessão")
    fig.tight_layout();fig.savefig(folder/"02_aceleracao_sessoes.png",dpi=170);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8.5,4.1))
    ax.boxplot([pair.sem_indice,pair.com_indice],tick_labels=["Sem índice","Com índice"])
    ax.set_yscale("log");ax.set_ylabel("ms/consulta (escala log)")
    ax.set_title("Distribuição de médias por bloco")
    fig.tight_layout();fig.savefig(folder/"03_distribuicao_blocos.png",dpi=170);plt.close(fig)
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
