# test_ottimizzato.py
# ------------------------------------------------------------------------------
# Verifica della ricerca potata (main_ottimizzato.py) contro i CSV della griglia completa.
#   T1  condizione di esattezza su TUTTE le istanze gia' calcolate (non serve rieseguire nulla):
#       per ogni profilo (istanza, seed, algoritmo, rifiuto) il costo per X > X_min non scende sotto
#       quello di X_min, e X*(gamma) <= X_min per tutti i 19 valori di gamma
#   T2  righe ricalcolate = righe dei CSV (camion e componenti di costo/disservizio)
#   T3  X*(gamma) scelta sulla griglia potata = X*(gamma) dei CSV, per 19 gamma (k_scala dei CSV)
#   T4  tempi: griglia completa vs potata (stesso pool, stessa macchina)
# Input : risultati_ottimizzati/ (da main_ottimizzato.py), risultati_seed/, risultati_csv/, analisi_seed/
# Uso   : python <cartella>/test_ottimizzato.py      (dalla cartella Euristiche/)
# ------------------------------------------------------------------------------
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
RAW, OUT = ROOT / "risultati_seed", ROOT / "risultati_ottimizzati"
B4_CSV = ROOT / "risultati_csv" / "risultati_3932u_mappa_reale_gamma0.50.csv"
KS = ["bench", "N", "scenario", "modo"]
KI = KS + ["seed"]
KC = KI + ["algoritmo", "rifiuto"]
GAMMAS = np.round(np.arange(0.05, 0.951, 0.05), 2)
CAMPI = ["n_vehicles", "F_insoddis", "F_costo_fisso", "F_viaggio", "F_lavoro", "sat_fisica", "sat_tempo"]
pd.set_option("display.width", 200)


def carica_b4() -> pd.DataFrame:
    d = pd.read_csv(B4_CSV)
    c = d.F_costo_fisso + d.F_viaggio + d.F_lavoro
    d["k_scala"] = ((d.F_total - 0.5 * c) / (0.5 * d.F_insoddis)).median()     # come analisi_gamma.py
    d["bench"], d["N"], d["scenario"], d["modo"], d["seed"] = "B4", 3932, "reale", "reale", 0
    return d


def riferimento(solo: pd.DataFrame | None = None) -> pd.DataFrame:
    """Griglie complete dai CSV. Se `solo` e' dato, legge solo quelle istanze."""
    if solo is None:
        ist = pd.read_csv(ROOT / "analisi_seed" / "metriche_istanza.csv")[KS].drop_duplicates()
        files = sorted(RAW.glob("*.csv"))
    else:
        ist = solo[KS].drop_duplicates()
        files = [RAW / f"{r.bench}_N{r.N}_{r.scenario}_{r.modo}_seed{r.seed}.csv"
                 for r in solo[KI].drop_duplicates().itertuples() if r.bench != "B4"]
    R = pd.concat([pd.read_csv(f) for f in files if f.exists()], ignore_index=True).merge(ist, on=KS)
    if B4_CSV.exists() and (solo is None or (solo.bench == "B4").any()):
        R = pd.concat([R, carica_b4()[R.columns.intersection(carica_b4().columns)]], ignore_index=True)
    R["F_costi"] = R.F_costo_fisso + R.F_viaggio + R.F_lavoro
    return R.sort_values(KC + ["X_r"]).reset_index(drop=True)


def scelte(R: pd.DataFrame, k: pd.Series | None = None) -> pd.DataFrame:
    """X*(gamma) per ogni profilo; k_scala dalla colonna o da `k` (indicizzato per KI)."""
    out = []
    for key, g in R.groupby(KC, sort=False):
        kk = k.loc[key[:5]] if k is not None else g.k_scala.iloc[0]
        ft = GAMMAS[:, None] * kk * g.F_insoddis.values[None, :] + (1 - GAMMAS[:, None]) * g.F_costi.values[None, :]
        out.append(pd.DataFrame({**dict(zip(KC, key)), "gamma": GAMMAS, "X_star": g.X_r.values[ft.argmin(axis=1)]}))
    return pd.concat(out, ignore_index=True)


# ------------------------------------------------------------------------------
def t1() -> None:
    R = riferimento()
    righe = []
    for key, g in R.groupby(KC, sort=False):
        X, F, C = g.X_r.values, g.F_insoddis.values, g.F_costi.values
        i = int(np.argmin(F))
        oltre = C[i + 1:]
        righe.append(dict(zip(KC, key), X_min=X[i], n_X=i + 1,
                          dominata=bool(np.all(oltre >= C[i] - 1e-6)) if oltre.size else True,
                          calo_max_pct=float(100 * (C[i] - oltre.min()) / C[i]) if oltre.size else 0.0))
    P = pd.DataFrame(righe)
    S = scelte(R).merge(P[KC + ["X_min"]], on=KC)
    ok_x = (S.X_star <= S.X_min + 1e-9)
    print(f"=== T1: condizione di esattezza su {R.groupby(KS).ngroups} istanze, {len(P)} profili ===")
    print(f"costo per X > X_min mai sotto il costo di X_min: {100 * P.dominata.mean():.3f}% dei profili "
          f"({int((~P.dominata).sum())} eccezioni)")
    if (~P.dominata).any():
        print("eccezioni per benchmark (n. profili, calo massimo del costo in %):")
        print(P[~P.dominata].groupby(["bench", "algoritmo"]).agg(n=("dominata", "size"),
                                                                  calo_max=("calo_max_pct", "max")).round(3))
    print(f"X*(gamma) <= X_min per tutti i 19 gamma: {100 * ok_x.mean():.3f}% delle {len(S)} scelte")
    print(f"X valutate dalla potatura: {P.n_X.mean():.2f} su 12 in media ({100 * (1 - P.n_X.mean() / 12):.1f}% in meno)")
    print(P.groupby("rifiuto").n_X.mean().round(2).to_string())


def t2_t3() -> None:
    f = OUT / "righe.csv"
    if not f.exists():
        print("\nT2/T3 saltati: manca risultati_ottimizzati/righe.csv (lancia prima main_ottimizzato.py)")
        return
    O = pd.read_csv(f)
    R = riferimento(O)
    m = O.merge(R, on=KC + ["X_r"], suffixes=("", "_csv"))
    print(f"\n=== T2: riproducibilita' - righe ricalcolate vs CSV ({len(O)} righe, {len(m)} confrontabili) ===")
    # tolleranze pari alla precisione dei CSV: main.py (B4) arrotonda F a 4 decimali e saturazioni a 2,
    # batch_seed a 6 e 4 decimali; in piu' 2e-6 relativo perche' alcune componenti sono float32
    b4 = (m.bench == "B4").values
    tol_F = np.where(b4, 5.1e-5, 5.1e-7)
    tol_sat = np.where(b4, 5.1e-3, 5.1e-5)

    def entro(c: str, tol: np.ndarray) -> np.ndarray:
        rif = m[c + "_csv"].abs().values
        return (m[c] - m[c + "_csv"]).abs().values <= tol + 2e-6 * rif

    ok_F = np.all([entro(c, tol_F) for c in ("F_insoddis", "F_costo_fisso", "F_viaggio", "F_lavoro")], axis=0)
    ok_sat = np.all([entro(c, tol_sat) for c in ("sat_fisica", "sat_tempo")], axis=0)
    m["identica"] = (m.n_vehicles == m.n_vehicles_csv).values & ok_F & ok_sat
    print(m.groupby(["ricerca", "algoritmo"]).identica.mean().mul(100).round(2).rename("righe identiche %").to_string())
    if (~m.identica).any():
        print("istanze con righe diverse (algoritmo, n. righe):")
        print(m[~m.identica].groupby(KI + ["algoritmo"]).size().to_string())

    O["F_costi"] = O.F_costo_fisso + O.F_viaggio + O.F_lavoro
    k = R.groupby(KI).k_scala.first()                        # k_scala dei CSV, uguale per le due ricerche
    sp = scelte(O[O.ricerca == "potata"].sort_values(KC + ["X_r"]), k).rename(columns={"X_star": "X_potata"})

    # T3a (verifica principale): potata vs completa calcolate nella stessa esecuzione, sulla stessa macchina
    if (O.ricerca == "completa").any():
        C = O[O.ricerca == "completa"]
        pc = O[O.ricerca == "potata"].merge(C, on=KC + ["X_r"], suffixes=("", "_c"))
        uguali = (pc.n_vehicles == pc.n_vehicles_c) & np.all(
            [np.isclose(pc[c], pc[c + "_c"], rtol=1e-9, atol=1e-9) for c in CAMPI[1:]], axis=0)
        s = sp.merge(scelte(C.sort_values(KC + ["X_r"]), k).rename(columns={"X_star": "X_completa"}),
                     on=KC + ["gamma"])
        s["uguale"] = np.isclose(s.X_potata, s.X_completa)
        print(f"\n=== T3a: potata vs completa (stessa esecuzione) ===")
        print(f"righe della griglia potata identiche alla completa: {100 * uguali.mean():.3f}% di {len(pc)}")
        print(f"X*(gamma) uguali: {100 * s.uguale.mean():.3f}% su {len(s)} scelte "
              f"({s.groupby(KI).ngroups} istanze x 2 algoritmi x 5 rifiuti x 19 gamma)")
        if (~s.uguale).any():
            print(s[~s.uguale].head(20).to_string(index=False))

    # T3b (riproducibilita'): potata vs griglia completa dei CSV
    sc = scelte(R[R.set_index(KI).index.isin(O.set_index(KI).index)]).rename(columns={"X_star": "X_csv"})
    s = sp.merge(sc, on=KC + ["gamma"])
    s["uguale"] = np.isclose(s.X_potata, s.X_csv)
    print(f"\n=== T3b: X*(gamma) potata vs CSV: {100 * s.uguale.mean():.3f}% uguali su {len(s)} scelte ===")
    print(s.groupby("algoritmo").uguale.mean().mul(100).round(3).to_string())
    if (~s.uguale).any():
        print("differenze (dipendono dalla riproducibilita' delle rotte, vedi T2):")
        print(s[~s.uguale].head(10).to_string(index=False))


def t4() -> None:
    f = OUT / "tempi.csv"
    if not f.exists():
        return
    T = pd.read_csv(f)
    if not {"completa", "potata"} <= set(T.ricerca):
        print("\nT4 saltato: serve anche la griglia completa (main_ottimizzato.py senza --solo-potata)")
        return
    w = T.pivot_table(index=KI + ["algoritmo"], columns="ricerca", values=["wall_s", "cpu_s", "n_valutazioni"])
    d = pd.DataFrame({"valutazioni": w["n_valutazioni"]["potata"] / w["n_valutazioni"]["completa"],
                      "wall": w["wall_s"]["potata"] / w["wall_s"]["completa"],
                      "cpu": w["cpu_s"]["potata"] / w["cpu_s"]["completa"],
                      "wall_completa_s": w["wall_s"]["completa"]}).reset_index()
    print("\n=== T4: tempi potata / completa (stesso pool, stessa macchina; mediana per gruppo) ===")
    print(d.groupby(["bench", "N", "scenario", "algoritmo"])[["valutazioni", "wall", "cpu", "wall_completa_s"]]
          .median().round(3).to_string())
    tot = T.groupby("ricerca")[["wall_s", "cpu_s"]].sum()
    print(f"\ntotale: tempo reale {tot.wall_s['potata']:.0f} s contro {tot.wall_s['completa']:.0f} s "
          f"({100 * (1 - tot.wall_s['potata'] / tot.wall_s['completa']):.1f}% in meno); "
          f"tempo CPU {100 * (1 - tot.cpu_s['potata'] / tot.cpu_s['completa']):.1f}% in meno")


if __name__ == "__main__":
    t1()
    t2_t3()
    t4()