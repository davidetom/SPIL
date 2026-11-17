import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/
sys.path.insert(0, str(ROOT))

import pandas as pd
from Generazione_Dati import generate_mock_data
import Greedy, ClarkeWright as CW

X_VALUES = [x / 2 for x in range(1, 13)]

def main():
    d = pd.read_csv(ROOT / "risultati_csv/risultati_200u_std_seed42_gamma0.50.csv")
    d["F_costi"] = d.F_costo_fisso + d.F_viaggio + d.F_lavoro
    g0 = d.gamma.iloc[0]
    k = ((d.F_total - (1 - g0) * d.F_costi) / (g0 * d.F_insoddis)).median()
    data = generate_mock_data(n_users=200, seed=42, r_factor=1.2,
                              user_scenario="residenziale")
    for gam in (0.3, 0.7):
        for mod, name in ((Greedy, "greedy"), (CW, "clarke_wright")):
            for r in data["waste_types"]:
                gs = mod.grid_search(data, r, X_VALUES, gamma=gam, k_scala=k)
                sub = d[(d.algoritmo == name) & (d.rifiuto == r)].copy()
                sub["Fp"] = gam * k * sub.F_insoddis + (1 - gam) * sub.F_costi
                i = sub.Fp.idxmin()
                print(f"{name:14s} g={gam} {r:16s} "
                      f"reale X*={gs['best_X_r']} V={gs['best_routes']['n_vehicles']} | "
                      f"predetto X*={sub.loc[i, 'X_r']} V={int(sub.loc[i, 'n_vehicles'])}")

if __name__ == "__main__":
    main()
