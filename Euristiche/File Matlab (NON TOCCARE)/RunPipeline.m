% =========================================================================
%  SPIL — Pipeline completa automatizzata
%
%  Questo script fa tutto in sequenza:
%    1. Lancia main.py (Python) con i parametri che vuoi
%    2. Aspetta che il CSV venga generato
%    3. Esegue analisi_pareto.m
%
%  Prerequisiti:
%    - Python nel PATH di sistema (verifica con: system('python --version'))
%    - main.py, Greedy.py, Generazione_Dati.py nella stessa cartella
%    - analisi_pareto.m nella stessa cartella
%    - Le librerie Python: numpy, scipy, matplotlib
%
%  Come usare:
%    Modifica la sezione "CONFIGURAZIONE" qui sotto, poi esegui.
% =========================================================================

clear; clc; close all;

% ── CONFIGURAZIONE ────────────────────────────────────────────────────────

PYTHON_EXE  = '/opt/anaconda3/bin/python3';
MAIN_PY     = 'main.py';         % path relativo a main.py
CSV_FILE    = 'risultati_spil.csv';

% Parametri passati a main.py tramite stdin (echo pipe)
N_USERS     = 1000;
SEED        = 42;
R_FACTOR    = 1.2;
SHOW_PLOT   = 'n';               % 'n' = nessun plot da Python (lo fa MATLAB)

% Timeout massimo attesa CSV (secondi)
TIMEOUT_SEC = 120;

% ── 1. Costruzione comando shell ──────────────────────────────────────────
%
% Passiamo le risposte alle input() di main.py tramite echo pipe.
% Su Windows:  echo 100 & echo 42 & echo 1.2 & echo n
% Su Mac/Linux: printf '100\n42\n1.2\nn\n'
%
% Rileviamo il sistema operativo automaticamente.

if ispc   % Windows
    inputs_str = sprintf('echo %d & echo %d & echo %.1f & echo %s', ...
                         N_USERS, SEED, R_FACTOR, SHOW_PLOT);
    cmd = sprintf('%s | %s %s', inputs_str, PYTHON_EXE, MAIN_PY);
else      % Mac / Linux
    inputs_str = sprintf("printf '%d\\n%d\\n%.1f\\n%s\\n'", ...
                         N_USERS, SEED, R_FACTOR, SHOW_PLOT);
    cmd = sprintf('%s | %s %s', inputs_str, PYTHON_EXE, MAIN_PY);
end

% ── 2. Esecuzione Python ──────────────────────────────────────────────────
fprintf('=== STEP 1: Esecuzione main.py ===\n');
fprintf('Comando: %s\n\n', cmd);

t_py_start = tic;
[status, output] = system(cmd);
t_py_elapsed = toc(t_py_start);

% Stampa output Python nella Command Window MATLAB
fprintf('--- Output Python ---\n%s\n--- Fine output ---\n\n', output);

if status ~= 0
    error('[ERRORE] main.py ha restituito exit code %d.\nVerifica il PATH di Python e le dipendenze.', status);
end
fprintf('Python completato in %.2f s\n\n', t_py_elapsed);

% ── 3. Verifica esistenza CSV ─────────────────────────────────────────────
fprintf('=== STEP 2: Verifica CSV ===\n');

t_wait = tic;
while ~isfile(CSV_FILE)
    if toc(t_wait) > TIMEOUT_SEC
        error('[TIMEOUT] Il file "%s" non è apparso entro %d s.', CSV_FILE, TIMEOUT_SEC);
    end
    pause(0.5);
end

fprintf('File trovato: %s\n\n', CSV_FILE);

% ── 4. Esecuzione analisi Pareto ──────────────────────────────────────────
fprintf('=== STEP 3: Generazione grafici Pareto ===\n');

% Chiamata diretta allo script (stessa cartella)
analisi_pareto;

fprintf('\n=== Pipeline SPIL completata ===\n');