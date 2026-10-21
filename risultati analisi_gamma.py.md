(base) davide_tom@MacBook-Air-di-Davide-2 Euristiche % /opt/anaconda3/bin/python "/Users/davide_to
m/Documents/Obsidian Note/SPIL/Euristiche/risultati_seed/analisi_gamma.py"
seed distinti per scenario:
bench  N     scenario          modo   
B1     100   residenziale      uniform    30
       250   residenziale      uniform    30
       500   residenziale      uniform    30
       750   residenziale      uniform    30
       1000  residenziale      uniform    30
B2     400   grandi_condomini  uniform    30
             misto_periferia   uniform    30
             residenziale      uniform    30
             suburbano         uniform    30
             villette          uniform    30
B3     400   residenziale      cluster    30
                               uniform    30
B4     3932  reale             reale       1
B5     200   residenziale      std        30

istanze con utenti serviti < 5N: 0

CONTROLLO seed 42 (B5):
 gamma  gap_tot  da_routing  da_shiftX
   0.1     3.12        3.04       0.07
   0.5     8.18        7.98       0.20
   0.9     2.91        2.91       0.00
CONTROLLO seed 42 (B1, N=100, gamma=0.5): atteso gap_tot 29.05
 gamma  gap_tot
   0.5    29.05

RIEPILOGO GAP (media, CI95 sui seed)
bench    N         scenario    modo  gamma  n_seed  gap_tot_mean  gap_tot_ci95  da_routing_mean  da_shiftX_mean  d_F_costi_mean  d_F_ins_mean  d_V_mean
   B1  100     residenziale uniform    0.1      30         11.81          0.99             8.11            3.70           -0.33        -17.66    -34.67
   B1  100     residenziale uniform    0.5      30         21.67          2.36            19.86            1.81          -18.49        -16.08    -35.00
   B1  100     residenziale uniform    0.9      30          5.99          0.57             5.98            0.02          -29.22         -0.20    -35.00
   B1  250     residenziale uniform    0.1      30          7.45          0.57             5.20            2.25            5.54        -16.59    -18.24
   B1  250     residenziale uniform    0.5      30         13.82          1.53            12.97            0.85          -11.78        -12.11    -18.31
   B1  250     residenziale uniform    0.9      30          4.20          0.44             4.18            0.02          -20.65         -0.20    -18.31
   B1  500     residenziale uniform    0.1      30          7.16          0.52             5.72            1.44           -2.16        -10.07    -11.74
   B1  500     residenziale uniform    0.5      30          8.70          0.54             8.18            0.52           -5.96        -10.22     -6.51
   B1  500     residenziale uniform    0.9      30          2.77          0.17             2.76            0.01          -13.80         -0.13     -6.51
   B1  750     residenziale uniform    0.1      30          7.17          0.35             6.26            0.90            0.39        -14.05    -14.97
   B1  750     residenziale uniform    0.5      30         10.65          0.62            10.08            0.57           -8.45        -10.94    -10.18
   B1  750     residenziale uniform    0.9      30          3.48          0.18             3.47            0.01          -16.67         -0.23    -10.18
   B1 1000     residenziale uniform    0.1      30          7.46          0.32             6.59            0.87            1.92        -16.73    -20.61
   B1 1000     residenziale uniform    0.5      30          9.42          0.47             8.99            0.43           -7.84         -9.39     -7.03
   B1 1000     residenziale uniform    0.9      30          3.14          0.16             3.13            0.01          -15.77         -0.08     -7.03
   B2  400 grandi_condomini uniform    0.1      30          4.03          0.28             3.82            0.20           -2.77         -5.15    -10.36
   B2  400 grandi_condomini uniform    0.5      30         12.38          1.50            12.38            0.00          -12.15          0.00     -3.73
   B2  400 grandi_condomini uniform    0.9      30          6.40          0.74             6.40            0.00          -12.15          0.00     -3.73
   B2  400  misto_periferia uniform    0.1      30          5.82          0.36             4.84            0.97            2.19        -12.07    -18.07
   B2  400  misto_periferia uniform    0.5      30          9.68          0.73             9.33            0.35           -8.38         -9.37     -5.08
   B2  400  misto_periferia uniform    0.9      30          2.99          0.22             2.98            0.00          -12.54         -0.03     -5.08
   B2  400     residenziale uniform    0.1      30          6.17          0.48             5.30            0.88           -1.66         -9.11     -7.53
   B2  400     residenziale uniform    0.5      30         11.58          1.04            10.86            0.72           -8.39        -12.46     -8.74
   B2  400     residenziale uniform    0.9      30          3.69          0.28             3.69            0.00          -18.28         -0.10     -8.74
   B2  400        suburbano uniform    0.1      30          6.88          0.63             5.48            1.39            0.95        -13.08    -16.96
   B2  400        suburbano uniform    0.5      30         11.97          1.01            11.96            0.01          -16.36         -0.77    -12.10
   B2  400        suburbano uniform    0.9      30          3.45          0.24             3.43            0.02          -16.18         -0.15    -12.10
   B2  400         villette uniform    0.1      30          7.31          0.50             7.23            0.08           -9.22         -4.76     -5.54
   B2  400         villette uniform    0.5      30         12.10          0.80            11.91            0.19          -12.66         -5.30     -5.54
   B2  400         villette uniform    0.9      30          4.06          0.28             4.06            0.00          -14.67          0.00     -5.54
   B3  400     residenziale cluster    0.1      30          6.25          0.60             4.84            1.41           -2.24         -9.55     -7.58
   B3  400     residenziale cluster    0.5      30          8.87          0.65             8.42            0.44           -8.10         -8.25    -10.32
   B3  400     residenziale cluster    0.9      30          2.79          0.16             2.78            0.01          -14.53         -0.04    -10.32
   B3  400     residenziale uniform    0.1      30          6.17          0.48             5.30            0.88           -1.66         -9.11     -7.53
   B3  400     residenziale uniform    0.5      30         11.58          1.04            10.86            0.72           -8.39        -12.46     -8.74
   B3  400     residenziale uniform    0.9      30          3.69          0.28             3.69            0.00          -18.28         -0.10     -8.74
   B4 3932            reale   reale    0.1       1          3.88           NaN             2.94            0.94            7.23        -17.81    -22.76
   B4 3932            reale   reale    0.5       1          4.21           NaN             4.18            0.03            3.79        -14.58     -5.38
   B4 3932            reale   reale    0.9       1          1.46           NaN             1.46            0.00           -6.92          0.00     -5.38
   B5  200     residenziale     std    0.1      30          8.22          0.79             7.53            0.69           -5.28         -8.90    -11.90
   B5  200     residenziale     std    0.5      30          9.20          0.41             8.99            0.21          -10.87         -4.97     -6.97
   B5  200     residenziale     std    0.9      30          2.89          0.11             2.89            0.01          -15.43         -0.04     -6.97