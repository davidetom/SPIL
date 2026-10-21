import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/
sys.path.insert(0, str(ROOT))

from Generazione_Dati import generate_mock_data
import Greedy, ClarkeWright as CW

data = generate_mock_data(n_users=200, seed=42, r_factor=1.2,
                          user_scenario="residenziale")
for mod in (Greedy, CW):
    for r in data["waste_types"]:
        for X in (0.5, 1.0, 2.5, 5.0):
            a = mod.build_routes(data, r, X, gamma=0.1, k_scala=1.2375)
            b = mod.build_routes(data, r, X, gamma=0.9, k_scala=1.2375)
            print(mod.__name__, f"{r:16s} X={X}",
                  "stesse rotte:", a["routes"] == b["routes"],
                  "| V:", a["n_vehicles"], b["n_vehicles"])
