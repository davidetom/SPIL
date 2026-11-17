import pandas as pd, re
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

CD, CM = 0.35, 0.25
BENCH = "risultati_3932u_mappa_reale"

# ---------- caricamento ----------
dfs = []
for f in (ROOT / "risultati_csv").glob("*_gamma*.csv"):
    d = pd.read_csv(f)
    d["gamma"] = float(re.search(r"gamma(\d+\.\d+)", f.name).group(1))
    d["bench"] = f.name.split("_gamma")[0]
    dfs.append(d)
D = pd.concat(dfs, ignore_index=True)

D["F_costi"]  = D.F_costo_fisso + D.F_viaggio + D.F_lavoro
D["V_x_X"]    = D.n_vehicles * D.X_r
D["km_sett"]  = D.F_viaggio / CD
D["km_giro"]  = D.km_sett / D.X_r
D["min_sett"] = D.F_lavoro / CM
D["min_giro"] = D.min_sett / D.X_r

# ---------- totali per bench / gamma / algoritmo ----------
print("\n=== TOTALI (soluzioni scelte) ===")
tot = (D[D.is_best == 1].groupby(["bench","gamma","algoritmo"])
       .agg(V=("n_vehicles","sum"), VxX=("V_x_X","sum"), km=("km_sett","sum"),
            ore=("min_sett", lambda s: s.sum()/60), F_ins=("F_insoddis","sum"),
            F_costi=("F_costi","sum"), sat_f=("sat_fisica","mean"),
            sat_t=("sat_tempo","mean")))
print(tot.round(1).to_string())

# ---------- T3: gap F_tot = routing a pari X + spostamento di X* ----------
print("\n=== T3: scomposizione del gap su F_tot (in % di F_tot CW) ===")
rows = []
for (bench, g), dg in D.groupby(["bench","gamma"]):
    F  = dg.set_index(["algoritmo","rifiuto","X_r"])["F_total"]
    xb = dg[dg.is_best == 1].set_index(["algoritmo","rifiuto"])["X_r"]
    tG = tC = rout = shift = 0.0
    for r in dg.rifiuto.unique():
        try:
            xg, xc = xb[("greedy", r)], xb[("clarke_wright", r)]
            fg  = F[("greedy", r, xg)]
            fcg = F[("clarke_wright", r, xg)]
            fc  = F[("clarke_wright", r, xc)]
        except KeyError:
            continue
        tG += fg; tC += fc; rout += fg - fcg; shift += fcg - fc
    rows.append(dict(bench=bench, gamma=g, gap_tot=(tG-tC)/tC*100,
                     da_routing=rout/tC*100, da_shift_X=shift/tC*100))
print(pd.DataFrame(rows).round(2).to_string(index=False))

# ---------- T4: servizio contro viaggio (25 km/h -> 2.4 min/km) ----------
print("\n=== T4: servizio incomprimibile? (differenza max tra algoritmi/gamma, min) ===")
D["travel_min_giro"]  = 2.4 * D.km_giro
D["service_min_giro"] = D.min_giro - D.travel_min_giro
D["travel_share"]     = 100 * D.travel_min_giro / D.min_giro
chk = D.groupby(["bench","rifiuto","X_r"]).service_min_giro.agg(lambda s: s.max()-s.min())
print(chk.describe().round(3))

B = D[D.is_best == 1]
print("\n--- quota di viaggio sul tempo di giro (%) ---")
print(B.groupby(["bench","algoritmo"]).travel_share.mean().unstack().round(1))
print("\n--- km per giro (media sui rifiuti) ---")
print(B.groupby(["bench","algoritmo"]).km_giro.mean().unstack().round(1))

print("\n--- Fabriano, CW, gamma=0.5: costo logistico per giro vs X ---")
x = D[(D.bench == BENCH) & (D.gamma == 0.5) & (D.algoritmo == "clarke_wright")]
print(x.assign(c_giro=x.F_costi / x.X_r)
       .pivot(index="X_r", columns="rifiuto", values="c_giro").round(1))

# 1) tabelle fisiche per i due casi aperti
cols = ["X_r","n_vehicles","V_x_X","km_sett","min_sett","F_insoddis","sat_fisica","sat_tempo"]
best = D[D.is_best == 1].set_index(["bench","algoritmo","gamma","rifiuto"])[cols].sort_index()
for b in ["risultati_400u_distrib_cluster", "risultati_400u_tipo_grandi_condomini"]:
    print("\n===", b); print(best.loc[b].round(2).to_string())

# 2) plateau del gap logistico a X fissato, per bench (gamma irrilevante dopo il fix)
d = D[D.gamma == 0.5]
p = d.pivot_table(index=["bench","rifiuto","X_r"], columns="algoritmo", values="F_costi")
p["gap"] = (p["greedy"] - p["clarke_wright"]) / p["clarke_wright"] * 100
print("\n=== gap logistico: plateau (X>=3) e X=0.5, media sui rifiuti ===")
plat = p.reset_index().query("X_r >= 3").groupby("bench")["gap"].mean().rename("plateau")
low  = p.reset_index().query("X_r == 0.5").groupby("bench")["gap"].mean().rename("X=0.5")
print(pd.concat([plat, low], axis=1).round(1).to_string())

# 3) tempi di calcolo (media sui tre gamma)
print("\n=== tempi di calcolo (s) ===")
t = D.groupby(["bench","algoritmo"]).algo_time_sec.mean().unstack()
t["CW/Greedy"] = t["clarke_wright"] / t["greedy"]
print(t.round(2).to_string())

# --- A: F_tot ricostruibile da componenti grezze per qualunque gamma? ---
D["k_rec"] = (D.F_total - (1-D.gamma)*D.F_costi) / (D.gamma*D.F_insoddis)
D = D.join(D[D.gamma == 0.5].groupby("bench").k_rec.median().rename("k_ref"), on="bench")
D["F_pred"] = D.gamma * D.k_ref * D.F_insoddis + (1 - D.gamma) * D.F_costi
print("errore relativo max:", ((D.F_total - D.F_pred).abs() / D.F_total).max())
ok = tot = 0
for _, dd in D.groupby(["bench","algoritmo","gamma","rifiuto"]):
    ok += (dd.loc[dd.is_best == 1, "X_r"].iloc[0] == dd.loc[dd.F_pred.idxmin(), "X_r"]); tot += 1
print("argmin ricostruito == is_best:", ok, "su", tot)

# --- B: scomposizione del vantaggio logistico a X fissato (regime a tempo) ---
pl = D[(D.gamma == 0.5) & (D.X_r >= 3)]
g = pl.groupby(["bench","algoritmo"])[["F_costo_fisso","F_viaggio","F_lavoro","F_costi"]].sum().unstack("algoritmo")
dF = g["F_costi"]["greedy"] - g["F_costi"]["clarke_wright"]
out = pd.DataFrame({
    "gap_costi_%":     dF / g["F_costi"]["clarke_wright"] * 100,
    "quota_fisso_%":   (g["F_costo_fisso"]["greedy"] - g["F_costo_fisso"]["clarke_wright"]) / dF * 100,
    "quota_viaggio_%": (g["F_viaggio"]["greedy"] - g["F_viaggio"]["clarke_wright"]) / dF * 100,
    "quota_lavoro_%":  (g["F_lavoro"]["greedy"] - g["F_lavoro"]["clarke_wright"]) / dF * 100})
V = (pl.groupby(["bench","algoritmo","X_r"]).n_vehicles.sum()
       .groupby(["bench","algoritmo"]).mean().unstack())
out["V_CW"] = V["clarke_wright"]; out["dV"] = V["greedy"] - V["clarke_wright"]
V05 = D[(D.gamma == 0.5) & (D.X_r == 0.5)].groupby(["bench","algoritmo"]).n_vehicles.sum().unstack()
out["dV_X0.5"] = V05["greedy"] - V05["clarke_wright"]
print("\n", out.round(1).to_string())

# --- C: perché CW sceglie X=0.5 per l'organico nel cluster a gamma=0.1 ---
x = D[(D.bench == "risultati_400u_distrib_cluster") & (D.gamma == 0.1) &
      (D.rifiuto == "organico") & (D.X_r <= 2)]
print("\n", x[["algoritmo","X_r","n_vehicles","F_costi","F_insoddis","F_total","is_best",
              "sat_fisica","sat_tempo"]].sort_values(["algoritmo","X_r"]).round(1).to_string(index=False))
