import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

new, old = ROOT / "risultati_seed", ROOT / "risultati_csv"
pairs = [(f"B1_N{n}_residenziale_uniform_seed42.csv",
          f"risultati_{n}u_varN_Nmax1000_Nact{n}_seed42_gamma0.50.csv") for n in (100, 250, 500, 750, 1000)]
pairs += [(f"B2_N400_{sc}_uniform_seed42.csv", f"risultati_400u_tipo_{sc}_gamma0.50.csv")
          for sc in ("residenziale", "suburbano", "grandi_condomini", "villette", "misto_periferia")]
pairs += [("B3_N400_residenziale_cluster_seed42.csv", "risultati_400u_distrib_cluster_gamma0.50.csv"),
          ("B5_N200_residenziale_std_seed42.csv", "risultati_200u_std_seed42_gamma0.50.csv")]
key = ["algoritmo", "rifiuto", "X_r"]
cols = ["n_vehicles", "F_insoddis", "F_costo_fisso", "F_viaggio", "F_lavoro", "sat_fisica", "sat_tempo"]
for fn, fo in pairs:
    a = pd.read_csv(new / fn).set_index(key).sort_index()
    b = pd.read_csv(old / fo).set_index(key).sort_index()
    com = a.index.intersection(b.index)
    d = max((a.loc[com, c] - b.loc[com, c]).abs().max() for c in cols)
    dk = abs(a.k_scala.iloc[0] - b.k_scala.iloc[0])
    print(f"{fn:50s} righe {len(a)}/{len(b)}  max|diff|={d:.4f}  dk={dk:.5f}")
