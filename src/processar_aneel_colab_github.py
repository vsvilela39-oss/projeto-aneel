from __future__ import annotations
from pathlib import Path
import hashlib, json, re, sys
import numpy as np
import pandas as pd

MOTIVOS_EXPURGO = {
    0: "Não houve expurgo",
    1: "Falha nas instalações da unidade consumidora sem afetar terceiros",
    2: "Obra de interesse exclusivo do consumidor",
    3: "Situação de emergência",
    4: "Suspensão por inadimplemento ou deficiência técnica/segurança da UC",
    5: "Programa de racionamento instituído pela União",
    6: "Ocorrência em dia crítico",
    7: "Esquema de alívio de carga solicitado pelo ONS",
    8: "Origem externa ao sistema de distribuição",
}

def get_root():
    if "google.colab" in sys.modules:
        return Path("/content/projeto-aneel")
    return Path.cwd()

def read_csv_aneel(path):
    for enc in ("utf-8-sig", "utf-8", "latin1", "cp1252"):
        for sep in (";", ",", "\t"):
            try:
                df = pd.read_csv(path, sep=sep, encoding=enc, dtype=str, low_memory=False)
                if df.shape[1] >= 4:
                    return df
            except Exception:
                pass
    raise RuntimeError(f"Não foi possível ler CSV: {path}")

def norm_col(df, candidates):
    lookup = {re.sub(r"[^a-z0-9]", "", str(c).lower()): c for c in df.columns}
    for c in candidates:
        k = re.sub(r"[^a-z0-9]", "", c.lower())
        if k in lookup:
            return lookup[k]
    return None

def req(df, candidates, label):
    c = norm_col(df, candidates)
    if not c:
        raise KeyError(f"Coluna ausente: {label}\nDisponíveis: {list(df.columns)}")
    return c

def num(series):
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    s = series.astype("string").str.strip()
    has_comma = s.str.contains(",", regex=False, na=False)
    s = s.where(~has_comma, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce")

def normalize_cnpj(series):
    return series.astype("string").fillna("").str.replace(r"\D", "", regex=True).str.zfill(14)

def skey(series):
    def h(v):
        b = hashlib.blake2b(str(v).encode("utf-8"), digest_size=8).digest()
        return np.int64(int.from_bytes(b, "big", signed=False) & 0x7FFF_FFFF_FFFF_FFFF)
    return series.map(h).astype("int64")

def build_date_dim(min_date, max_date):
    d = pd.DataFrame({"Data": pd.date_range(min_date.normalize(), max_date.normalize(), freq="D")})
    d["DataKey"] = d["Data"].dt.strftime("%Y%m%d").astype("int32")
    d["Ano"] = d["Data"].dt.year.astype("int16")
    d["MesNumero"] = d["Data"].dt.month.astype("int8")
    d["MesNome"] = d["MesNumero"].map({1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"})
    d["AnoMes"] = d["Data"].dt.strftime("%Y-%m")
    d["Trimestre"] = "T" + d["Data"].dt.quarter.astype(str)
    return d[["DataKey","Data","Ano","MesNumero","MesNome","AnoMes","Trimestre"]]

def parse_fato_gerador(series):
    text = series.astype("string").fillna("NAO INFORMADO").str.strip()
    parts = text.str.replace(r"\s*-\s*", ";", regex=True).str.split(";", expand=True)
    out = pd.DataFrame(index=series.index)
    out["FatoGeradorOriginal"] = text
    for i in range(4):
        out[f"FatoNivel{i+1}"] = parts[i].str.strip() if parts.shape[1] > i else pd.NA
    return out

def build_continuidade(cont, limites):
    sig=req(cont,["SigIndicador"],"SigIndicador")
    ano=req(cont,["AnoIndice"],"AnoIndice")
    mes=req(cont,["NumPeriodoIndice"],"NumPeriodoIndice")
    valor=req(cont,["VlrIndiceEnviado"],"VlrIndiceEnviado")
    conjunto=req(cont,["IdeConjUndConsumidoras","IdeConjuntoUnidadeConsumidora"],"Conjunto")
    desc=req(cont,["DscConjUndConsumidoras","DscConjuntoUnidadeConsumidora"],"Descrição conjunto")
    cnpj_col=req(cont,["NumCNPJ","NumCPFCNPJ"],"CNPJ")
    agente=req(cont,["SigAgente"],"SigAgente")
    df=cont.copy(); df[sig]=df[sig].astype("string").str.upper().str.strip(); df=df[df[sig].isin(["DEC","FEC"])].copy()
    df["AnoIndice"]=pd.to_numeric(df[ano],errors="coerce").astype("Int64"); df["MesIndice"]=pd.to_numeric(df[mes],errors="coerce").astype("Int64")
    df=df[df["MesIndice"].between(1,12)].copy(); df["VlrIndicador"]=num(df[valor]); df["CNPJ_Normalizado"]=normalize_cnpj(df[cnpj_col])
    df["DistribuidoraNaturalKey"]=df["CNPJ_Normalizado"]; df["ConjuntoNaturalKey"]=df["CNPJ_Normalizado"]+"|"+df[conjunto].astype("string").str.strip()
    df["Data"]=pd.to_datetime({"year":df["AnoIndice"].astype(int),"month":df["MesIndice"].astype(int),"day":1}); df["DataKey"]=df["Data"].dt.strftime("%Y%m%d").astype("int32")
    dd=df[["DistribuidoraNaturalKey",agente,cnpj_col]].drop_duplicates("DistribuidoraNaturalKey").rename(columns={agente:"SigAgente",cnpj_col:"NumCNPJ"}).copy(); dd["DistribuidoraKey"]=skey(dd["DistribuidoraNaturalKey"])
    dist_map=dd.set_index("DistribuidoraNaturalKey")["DistribuidoraKey"]
    dc=df[["ConjuntoNaturalKey","DistribuidoraNaturalKey",conjunto,desc]].drop_duplicates("ConjuntoNaturalKey").rename(columns={conjunto:"IdeConjunto",desc:"DscConjunto"}).copy(); dc["ConjuntoKey"]=skey(dc["ConjuntoNaturalKey"]); dc["DistribuidoraKey"]=dc["DistribuidoraNaturalKey"].map(dist_map).astype("int64")
    conj_map=dc.set_index("ConjuntoNaturalKey")["ConjuntoKey"]
    di=pd.DataFrame({"IndicadorKey":[1,2],"SigIndicador":["DEC","FEC"],"NomeIndicador":["Duração Equivalente de Interrupção por Unidade Consumidora","Frequência Equivalente de Interrupção por Unidade Consumidora"],"Unidade":["horas","interrupções"]})
    ls=req(limites,["SigIndicador"],"Limite indicador"); la=req(limites,["AnoLimiteQualidade"],"Ano limite"); lv=req(limites,["VlrLimite"],"VlrLimite"); lc=req(limites,["IdeConjUndConsumidoras","IdeConjuntoUnidadeConsumidora"],"Limite conjunto"); lcnpj=req(limites,["NumCNPJ","NumCPFCNPJ"],"Limite CNPJ")
    lim=limites.copy(); lim[ls]=lim[ls].astype("string").str.upper().str.strip(); lim=lim[lim[ls].isin(["DEC","FEC"])].copy(); lim["AnoIndice"]=pd.to_numeric(lim[la],errors="coerce").astype("Int64"); lim["VlrLimite"]=num(lim[lv]); lim["CNPJ_Normalizado"]=normalize_cnpj(lim[lcnpj]); lim["ConjuntoNaturalKey"]=lim["CNPJ_Normalizado"]+"|"+lim[lc].astype("string").str.strip()
    lim=lim[["ConjuntoNaturalKey",ls,"AnoIndice","VlrLimite"]].rename(columns={ls:"SigIndicador"}).drop_duplicates(["ConjuntoNaturalKey","SigIndicador","AnoIndice"],keep="last")
    df=df.merge(lim,left_on=["ConjuntoNaturalKey",sig,"AnoIndice"],right_on=["ConjuntoNaturalKey","SigIndicador","AnoIndice"],how="left")
    df["DistribuidoraKey"]=df["DistribuidoraNaturalKey"].map(dist_map).astype("int64"); df["ConjuntoKey"]=df["ConjuntoNaturalKey"].map(conj_map).astype("int64"); df["IndicadorKey"]=df[sig].map({"DEC":1,"FEC":2}).astype("int8")
    df["UltrapassouLimite"]=(df["VlrIndicador"].notna()&df["VlrLimite"].notna()&(df["VlrIndicador"]>df["VlrLimite"])).astype("int8"); df["ExcessoSobreLimite"]=(df["VlrIndicador"]-df["VlrLimite"]).clip(lower=0); df["PercentualDoLimite"]=df["VlrIndicador"]/df["VlrLimite"]
    natural=df["DataKey"].astype(str)+"|"+df["ConjuntoKey"].astype(str)+"|"+df["IndicadorKey"].astype(str); df["FatoContinuidadeKey"]=skey(natural)
    fato=df[["FatoContinuidadeKey","DataKey","DistribuidoraKey","ConjuntoKey","IndicadorKey","VlrIndicador","VlrLimite","UltrapassouLimite","ExcessoSobreLimite","PercentualDoLimite"]].copy()
    return fato,dd,dc,di

def enrich_dim_conjunto(dc, atributos):
    ac=norm_col(atributos,["IdeConjUndConsumidoras","IdeConjuntoUnidadeConsumidora"]); ag=norm_col(atributos,["NumCNPJ","NumCPFCNPJ"])
    if not ac or not ag: return dc
    a=atributos.copy(); a["CNPJ_Normalizado"]=normalize_cnpj(a[ag]); a["ConjuntoNaturalKey"]=a["CNPJ_Normalizado"]+"|"+a[ac].astype("string").str.strip(); dg=norm_col(a,["DatGeracaoConjuntoDados"])
    if dg: a[dg]=pd.to_datetime(a[dg],errors="coerce"); a=a.sort_values(dg)
    a=a.drop_duplicates("ConjuntoNaturalKey",keep="last"); extras=[c for c in a.columns if c not in {"ConjuntoNaturalKey","CNPJ_Normalizado",ac,ag}][:30]
    return dc.merge(a[["ConjuntoNaturalKey"]+extras],on="ConjuntoNaturalKey",how="left")

def build_interrupcoes(frames, dd, dc):
    raw=pd.concat(frames,ignore_index=True); cj=req(raw,["IdeConjuntoUnidadeConsumidora","IdeConjUndConsumidoras"],"Interrupção conjunto"); cg=req(raw,["NumCPFCNPJ","NumCNPJ"],"Interrupção CNPJ"); ini=req(raw,["DatInicioInterrupcao","DtInicioInterrupcao"],"Data início"); fim=req(raw,["DatFimInterrupcao","DtFimInterrupcao"],"Data fim"); fg=req(raw,["DscFatoGeradorInterrupcao","FatGeradorInterrupcao"],"Fato gerador")
    tipo=norm_col(raw,["DscTipoInterrupcao"]); motivo=norm_col(raw,["IdeMotivoInterrupcao","IdeMotivoExpurgo"]); ordem=norm_col(raw,["NumOrdemInterrupcao"]); uca=norm_col(raw,["NumUnidadeConsumidora"]); ucc=norm_col(raw,["NumConsumidorConjunto"]); tens=norm_col(raw,["NumNivelTensao"])
    df=raw.copy(); df["CNPJ_Normalizado"]=normalize_cnpj(df[cg]); df["DistribuidoraNaturalKey"]=df["CNPJ_Normalizado"]; df["ConjuntoNaturalKey"]=df["CNPJ_Normalizado"]+"|"+df[cj].astype("string").str.strip(); df["DistribuidoraKey"]=df["DistribuidoraNaturalKey"].map(dd.set_index("DistribuidoraNaturalKey")["DistribuidoraKey"]); df["ConjuntoKey"]=df["ConjuntoNaturalKey"].map(dc.set_index("ConjuntoNaturalKey")["ConjuntoKey"])
    df["DatInicio"]=pd.to_datetime(df[ini],errors="coerce"); df["DatFim"]=pd.to_datetime(df[fim],errors="coerce"); df["DuracaoHoras"]=(df["DatFim"]-df["DatInicio"]).dt.total_seconds()/3600; df.loc[df["DuracaoHoras"]<0,"DuracaoHoras"]=np.nan; df["DataKey"]=pd.to_numeric(df["DatInicio"].dt.strftime("%Y%m%d"),errors="coerce").astype("Int64")
    df["NumUnidadesAfetadas"]=num(df[uca]) if uca else np.nan; df["NumConsumidoresConjunto"]=num(df[ucc]) if ucc else np.nan; df["NivelTensao"]=num(df[tens]) if tens else np.nan; df["ConsumidorHoras"]=df["NumUnidadesAfetadas"]*df["DuracaoHoras"]; df["ContribDEC_Estimada"]=df["ConsumidorHoras"]/df["NumConsumidoresConjunto"]; df["ContribFEC_Estimada"]=df["NumUnidadesAfetadas"]/df["NumConsumidoresConjunto"]
    df["MotivoCodigo"]=pd.to_numeric(df[motivo],errors="coerce").astype("Int64") if motivo else pd.Series(pd.NA,index=df.index,dtype="Int64"); df["MotivoDescricao"]=df["MotivoCodigo"].map(MOTIVOS_EXPURGO).fillna("Não informado / outra taxonomia"); df["EhExpurgada"]=df["MotivoCodigo"].fillna(0).ne(0).astype("int8")
    parsed=parse_fato_gerador(df[fg]); df=pd.concat([df,parsed],axis=1)
    tipo_norm=df[tipo].astype("string").fillna("NAO INFORMADO").str.strip() if tipo else pd.Series("NAO INFORMADO",index=df.index,dtype="string"); dt=pd.DataFrame({"TipoInterrupcao":tipo_norm}).drop_duplicates(); dt["TipoInterrupcaoKey"]=skey(dt["TipoInterrupcao"]); df["TipoInterrupcaoKey"]=tipo_norm.map(dt.set_index("TipoInterrupcao")["TipoInterrupcaoKey"]).astype("int64")
    dm=df[["MotivoCodigo","MotivoDescricao","EhExpurgada"]].drop_duplicates().reset_index(drop=True); dm["MotivoInterrupcaoKey"]=skey(dm["MotivoCodigo"].astype("string")+"|"+dm["MotivoDescricao"]); mmap={(r.MotivoCodigo,r.MotivoDescricao):r.MotivoInterrupcaoKey for r in dm.itertuples()}; df["MotivoInterrupcaoKey"]=[mmap.get((a,b)) for a,b in zip(df["MotivoCodigo"],df["MotivoDescricao"])]
    dfg=df[["FatoGeradorOriginal","FatoNivel1","FatoNivel2","FatoNivel3","FatoNivel4"]].drop_duplicates("FatoGeradorOriginal").reset_index(drop=True); dfg["FatoGeradorKey"]=skey(dfg["FatoGeradorOriginal"]); df["FatoGeradorKey"]=df["FatoGeradorOriginal"].map(dfg.set_index("FatoGeradorOriginal")["FatoGeradorKey"]).astype("int64")
    natural=(df["CNPJ_Normalizado"].astype(str)+"|"+df[ordem].astype("string").fillna("")+"|"+df[cj].astype("string").fillna("")) if ordem else (df["CNPJ_Normalizado"].astype(str)+"|"+df[cj].astype("string")+"|"+df["DatInicio"].astype("string")+"|"+df["FatoGeradorOriginal"]); df["InterrupcaoKey"]=skey(natural)
    fi=df[["InterrupcaoKey","DataKey","DistribuidoraKey","ConjuntoKey","TipoInterrupcaoKey","MotivoInterrupcaoKey","FatoGeradorKey","DatInicio","DatFim","DuracaoHoras","NumUnidadesAfetadas","NumConsumidoresConjunto","NivelTensao","ConsumidorHoras","ContribDEC_Estimada","ContribFEC_Estimada","EhExpurgada"]].copy()
    df["MesDataKey"]=pd.to_numeric(df["DatInicio"].dt.to_period("M").dt.to_timestamp().dt.strftime("%Y%m%d"),errors="coerce").astype("Int64"); grupo=["MesDataKey","DistribuidoraKey","ConjuntoKey","TipoInterrupcaoKey","MotivoInterrupcaoKey","FatoGeradorKey"]
    fc=df.groupby(grupo,dropna=False).agg(QtdInterrupcoes=("InterrupcaoKey","nunique"),DuracaoTotalHoras=("DuracaoHoras","sum"),UnidadesAfetadasSoma=("NumUnidadesAfetadas","sum"),ConsumidorHoras=("ConsumidorHoras","sum"),ContribDEC_Estimada=("ContribDEC_Estimada","sum"),ContribFEC_Estimada=("ContribFEC_Estimada","sum")).reset_index().rename(columns={"MesDataKey":"DataKey"}); fc["FatoCausaMensalKey"]=skey(fc.astype("string").agg("|".join,axis=1))
    return fi,fc,dt,dm,dfg

def main(anos_interrupcoes=None):
    if anos_interrupcoes is None: anos_interrupcoes=[2024,2025]
    root=get_root(); raw=root/"dados"/"raw"; out=root/"dados"/"parquet_modelo"; out.mkdir(parents=True,exist_ok=True)
    required=[raw/"continuidade_2020_2029.parquet",raw/"limites.csv",raw/"atributos.csv"]+[raw/f"interrupcoes_{a}.parquet" for a in anos_interrupcoes]
    missing=[str(p) for p in required if not p.exists()]
    if missing: raise FileNotFoundError("Arquivos ausentes:\n- "+"\n- ".join(missing))
    cont=pd.read_parquet(raw/"continuidade_2020_2029.parquet"); lim=read_csv_aneel(raw/"limites.csv"); attrs=read_csv_aneel(raw/"atributos.csv")
    fcont,dd,dc,di=build_continuidade(cont,lim); dc=enrich_dim_conjunto(dc,attrs)
    frames=[]
    for a in anos_interrupcoes:
        p=raw/f"interrupcoes_{a}.parquet"; print(f"Lendo {p.name}..."); d=pd.read_parquet(p); print(f"  {len(d):,} linhas"); frames.append(d)
    fi,fc,dt,dm,dfg=build_interrupcoes(frames,dd,dc)
    d1=pd.to_datetime(fcont["DataKey"].astype(str),format="%Y%m%d"); d2=pd.to_datetime(fi["DataKey"].astype("Int64").astype(str),format="%Y%m%d",errors="coerce"); ddata=build_date_dim(min(d1.min(),d2.min()),max(d1.max(),d2.max()))
    ddata.to_parquet(out/"dim_data.parquet",index=False); dd.drop(columns=["DistribuidoraNaturalKey"],errors="ignore").to_parquet(out/"dim_distribuidora.parquet",index=False); dc.drop(columns=["ConjuntoNaturalKey","DistribuidoraNaturalKey"],errors="ignore").to_parquet(out/"dim_conjunto.parquet",index=False); di.to_parquet(out/"dim_indicador.parquet",index=False); dt.to_parquet(out/"dim_tipo_interrupcao.parquet",index=False); dm.to_parquet(out/"dim_motivo_interrupcao.parquet",index=False); dfg.to_parquet(out/"dim_fato_gerador.parquet",index=False); fcont.to_parquet(out/"fato_continuidade.parquet",index=False); fi.to_parquet(out/"fato_interrupcao.parquet",index=False); fc.to_parquet(out/"fato_causa_mensal.parquet",index=False)
    (out/"_manifesto.json").write_text(json.dumps({"fonte":"ANEEL","anos_interrupcoes":anos_interrupcoes,"arquivos":[p.name for p in sorted(out.glob("*.parquet"))]},ensure_ascii=False,indent=2),encoding="utf-8")
    print("\nConcluído. Arquivos em:",out)
    return out
