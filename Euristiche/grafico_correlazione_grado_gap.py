import matplotlib.pyplot as plt

# Dati sperimentali: Grafi Sintetici
grado_medio_sintetico = [2.400, 2.680, 2.840, 3.080, 3.380, 3.640, 3.980, 4.660, 5.000, 5.480]
gap_sintetico = [13.64, 20.79, 21.23, 21.57, 21.12, 20.68, 25.81, 18.84, 17.07, 9.90]

# Dati sperimentali: Fabriano (Reale)
grado_medio_fabriano = [2.587]
gap_fabriano = [3.53]

# Creazione del grafico
plt.figure(figsize=(10, 6))

# Plot della curva a campana per i grafi sintetici
plt.plot(grado_medio_sintetico, gap_sintetico, marker='o', linestyle='-', color='tab:blue', linewidth=2, label='Grafi Sintetici')

# Plot del punto isolato per Fabriano
plt.scatter(grado_medio_fabriano, gap_fabriano, color='tab:red', s=150, zorder=5, label='Fabriano (reale) (OSM)')

# Etichette e stile
plt.title('Correlazione tra Grado Medio e Gap Prestazionale (CW vs Greedy)', fontsize=14, fontweight='bold')
plt.xlabel('Grado Medio', fontsize=12)
plt.ylabel('Gap CW-Greedy (%)', fontsize=12)
plt.legend(loc='upper left', fontsize=11)
plt.grid(True, linestyle='--', alpha=0.7)

# Annotazioni
plt.annotate(
    'Picco vantaggio CW (~25%)\n(massima flessibilità di fusione)',
    xy=(3.98, 25.81), xytext=(4.2, 24),
    arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
    fontsize=10
)

plt.annotate(
    'Fabriano (Reale): Gap 3.53%\nGrado medio confrontabile (2.59)\nma gap fino a 6× inferiore!',
    xy=(2.587, 3.53), xytext=(2.85, 7),
    arrowprops=dict(facecolor='tab:red', arrowstyle='->', lw=1.5),
    fontsize=10, color='darkred',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffebee', edgecolor='tab:red', alpha=0.9)
)

# Salva immagine in Analisi aggiuntive
out_img = "Analisi aggiuntive/grafico_correlazione_grado_gap.png"
plt.tight_layout()
plt.savefig(out_img, dpi=300)
print(f"Grafico salvato in: {out_img}")

# Mostra il grafico se in ambiente interattivo
try:
    plt.show()
except Exception:
    pass