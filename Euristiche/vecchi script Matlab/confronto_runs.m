% =========================================================================
%  SPIL — Confronto Multi-Run
%
%  Legge TUTTI i file  risultati_<N>_utenti.csv  nella cartella
%  risultati_csv/  e produce grafici di scalabilità:
%
%    Fig A — Tempi di esecuzione vs N utenti
%             (una linea per algoritmo, marker sui punti)
%
%    Fig B — F_total ottimale vs N utenti
%             (due subplot affiancati: Greedy | Clarke-Wright,
%              una linea per tipologia di rifiuto in ciascuno)
%
%  Come usare:
%    >> confronto_runs          % legge da ./risultati_csv/
%    >> confronto_runs('path/alla/cartella')   % cartella personalizzata
%
%  Prerequisiti:
%    - Almeno 2 CSV nella cartella (con N utenti diversi)
%    - Ogni CSV deve avere le colonne standard SPIL (compreso "algoritmo")
% =========================================================================

%% ── 0. Setup ─────────────────────────────────────────────────────────────

clearvars; clc; close all;

% Cartella CSV: argomento opzionale o default
if exist('RUNS_DIR', 'var') && ~isempty(RUNS_DIR)
    csv_dir = RUNS_DIR;
else
    csv_dir = 'risultati_csv';
end

if ~isfolder(csv_dir)
    error('Cartella non trovata: %s\nCrea prima almeno una run con main.py.', csv_dir);
end

%% ── 1. Scansione file CSV ────────────────────────────────────────────────

listing = dir(fullfile(csv_dir, 'risultati_*_utenti.csv'));

if isempty(listing)
    error('Nessun file risultati_*_utenti.csv trovato in: %s', csv_dir);
end

% Estrai N utenti dal nome file tramite regex
%   risultati_500_utenti.csv  →  500
n_files  = numel(listing);
n_arr    = zeros(n_files, 1);   % N utenti per ogni file

for f = 1:n_files
    tok = regexp(listing(f).name, 'risultati_(\d+)_utenti\.csv', 'tokens');
    if isempty(tok)
        error('Nome file non riconosciuto: %s', listing(f).name);
    end
    n_arr(f) = str2double(tok{1}{1});
end

% Ordina per N crescente (così i grafici vengono da sinistra a destra)
[n_arr, sort_idx] = sort(n_arr);
listing = listing(sort_idx);

fprintf('\n%s\n', repmat('=', 1, 70));
fprintf('  SPIL — Confronto Multi-Run   (%d file trovati)\n', n_files);
fprintf('%s\n\n', repmat('=', 1, 70));
fprintf('  %-8s  %s\n', 'N utenti', 'File');
fprintf('  %s\n', repmat('-', 1, 55));
for f = 1:n_files
    fprintf('  %-8d  %s\n', n_arr(f), listing(f).name);
end
fprintf('\n');

%% ── 2. Palette colori ────────────────────────────────────────────────────

ALGO_COLOR = containers.Map( ...
    {'greedy', 'clarke_wright'}, ...
    {[0.13 0.47 0.71], [0.84 0.37 0.05]} );

ALGO_LABEL = containers.Map( ...
    {'greedy', 'clarke_wright'}, ...
    {'Greedy', 'Clarke-Wright'} );

ALGO_MARKER = containers.Map( ...
    {'greedy', 'clarke_wright'}, ...
    {'o', '^'} );

% Colori per i 5 rifiuti (ordine: organico, carta, plastica, vetro, indiff.)
WASTE_COLORS = [
    0.20  0.63  0.17;
    0.12  0.47  0.71;
    1.00  0.50  0.05;
    0.58  0.40  0.74;
    0.84  0.15  0.16;
];

%% ── 3. Lettura e aggregazione dati ───────────────────────────────────────
%
%  Per ogni file costruiamo:
%    times.(algo_key)(f)               → tempo esecuzione
%    f_best.(algo_key).(rifiuto)(f)    → F_total best per rifiuto
%    f_tot_sum.(algo_key)(f)           → somma F_total sui 5 rifiuti (best X_r)
%
%  Usiamo struct con campi dinamici; inizializziamo dopo il primo file
%  quando conosciamo quali algoritmi sono presenti.

times     = struct();
f_best    = struct();
f_tot_sum = struct();

waste_types = {};   % popolato al primo file
algo_keys   = {};   % popolato al primo file

for f = 1:n_files
    fpath = fullfile(csv_dir, listing(f).name);

    opts = detectImportOptions(fpath);
    opts.VariableNamesLine = 1;
    T = readtable(fpath, opts);

    if ~iscell(T.rifiuto),   T.rifiuto   = cellstr(T.rifiuto);   end
    if ~iscell(T.algoritmo), T.algoritmo = cellstr(T.algoritmo); end

    wt_this = unique(T.rifiuto,   'stable');
    ak_this = unique(T.algoritmo, 'stable');

    % Inizializzazione strutture al primo file
    if f == 1
        waste_types = wt_this;
        algo_keys   = ak_this;

        for a = 1:numel(algo_keys)
            ak   = algo_keys{a};
            aKey = matlab.lang.makeValidName(ak);

            times.(aKey)     = NaN(n_files, 1);
            f_tot_sum.(aKey) = NaN(n_files, 1);
            f_best.(aKey)    = struct();

            for k = 1:numel(waste_types)
                rKey = matlab.lang.makeValidName(waste_types{k});
                f_best.(aKey).(rKey) = NaN(n_files, 1);
            end
        end
    end

    % Estrazione valori per ogni algoritmo presente in questo file
    for a = 1:numel(ak_this)
        ak   = ak_this{a};
        aKey = matlab.lang.makeValidName(ak);

        % Salto se questo algo non era nel primo file (edge case)
        if ~isfield(times, aKey), continue; end

        amask = strcmp(T.algoritmo, ak);

        % Tempo (uguale per tutte le righe dell'algo in questo file)
        times.(aKey)(f) = T.algo_time_sec(find(amask, 1));

        % F_total best per rifiuto e somma totale
        soma = 0;
        for k = 1:numel(waste_types)
            r    = waste_types{k};
            rKey = matlab.lang.makeValidName(r);
            mask = amask & strcmp(T.rifiuto, r) & (T.is_best == 1);
            if any(mask)
                val = T.F_total(mask);
                f_best.(aKey).(rKey)(f) = val(1);
                soma = soma + val(1);
            end
        end
        f_tot_sum.(aKey)(f) = soma;
    end

    fprintf('  Letto: %s  (N=%d, algos: %s)\n', ...
            listing(f).name, n_arr(f), strjoin(ak_this, ', '));
end

fprintf('\n');

%% ── 4. FIGURA A — Tempi di esecuzione vs N utenti ────────────────────────

figA = figure('Name', 'Confronto Tempi — Multi-Run', ...
              'NumberTitle', 'off', 'Position', [50 50 820 500]);
hold on; grid on; box on;

leg_hA   = gobjects(0);
leg_txtA = {};

for a = 1:numel(algo_keys)
    ak   = algo_keys{a};
    aKey = matlab.lang.makeValidName(ak);
    col  = ALGO_COLOR(ak);
    mk   = ALGO_MARKER(ak);
    lbl  = ALGO_LABEL(ak);

    t_vec = times.(aKey);
    valid = ~isnan(t_vec);

    if ~any(valid), continue; end

    h = plot(n_arr(valid), t_vec(valid), ...
             ['-', mk], ...
             'Color', col, 'LineWidth', 2.2, ...
             'MarkerSize', 8, 'MarkerFaceColor', col, ...
             'MarkerEdgeColor', 'w');
    leg_hA(end+1)   = h;        %#ok<AGROW>
    leg_txtA{end+1} = lbl;      %#ok<AGROW>

    % Etichetta valore su ogni punto
    for f = 1:n_files
        if valid(f)
            text(n_arr(f), t_vec(f) * 1.04, ...
                 sprintf('%.2fs', t_vec(f)), ...
                 'HorizontalAlignment', 'center', ...
                 'FontSize', 8, 'Color', col * 0.8);
        end
    end
end

xlabel('N utenti', 'FontSize', 12);
ylabel('Tempo di esecuzione  (s)', 'FontSize', 12);
title('Scalabilità temporale — Greedy vs Clarke-Wright', ...
      'FontSize', 14, 'FontWeight', 'bold');
legend(leg_hA, leg_txtA, 'Location', 'northwest', 'FontSize', 10);
xlim([min(n_arr)*0.85, max(n_arr)*1.10]);
ylim([0, max(structfun(@(v) max(v(~isnan(v))), times), [], 'all') * 1.20 + 0.1]);

% Annotazione speedup sull'ultimo punto (il più grande) se entrambi presenti
if numel(algo_keys) == 2
    aKey1 = matlab.lang.makeValidName(algo_keys{1});
    aKey2 = matlab.lang.makeValidName(algo_keys{2});
    t1_last = times.(aKey1)(end);
    t2_last = times.(aKey2)(end);
    if ~isnan(t1_last) && ~isnan(t2_last) && min(t1_last, t2_last) > 0
        ratio = max(t1_last, t2_last) / min(t1_last, t2_last);
        [~, fi] = min([t1_last, t2_last]);
        faster_lbl = ALGO_LABEL(algo_keys{fi});
        text(n_arr(end), max(t1_last, t2_last) * 0.88, ...
             sprintf('%s è %.2fx più veloce\n(N=%d utenti)', faster_lbl, ratio, n_arr(end)), ...
             'HorizontalAlignment', 'right', 'FontSize', 9, ...
             'BackgroundColor', [1 1 0.85], 'EdgeColor', [0.6 0.6 0.4]);
    end
end

%% ── 5. FIGURA B — F_total ottimale vs N utenti (due subplot) ─────────────
%
%  Subplot sinistro  = Greedy
%  Subplot destro    = Clarke-Wright
%  In ogni subplot: una linea per rifiuto + linea tratteggiata F_tot_sum

figB = figure('Name', 'F_total Ottimale — Multi-Run', ...
              'NumberTitle', 'off', 'Position', [120 120 1300 520]);

n_waste = numel(waste_types);

for a = 1:numel(algo_keys)
    ak   = algo_keys{a};
    aKey = matlab.lang.makeValidName(ak);
    col  = ALGO_COLOR(ak);
    lbl  = ALGO_LABEL(ak);

    ax = subplot(1, numel(algo_keys), a);
    hold(ax, 'on'); grid(ax, 'on'); box(ax, 'on');

    leg_hB   = gobjects(0);
    leg_txtB = {};

    % Una linea per rifiuto
    for k = 1:n_waste
        r    = waste_types{k};
        rKey = matlab.lang.makeValidName(r);
        wcol = WASTE_COLORS(k, :);

        f_vec = f_best.(aKey).(rKey);
        valid = ~isnan(f_vec);
        if ~any(valid), continue; end

        h = plot(ax, n_arr(valid), f_vec(valid), ...
                 '-o', 'Color', wcol, 'LineWidth', 1.8, ...
                 'MarkerSize', 6, 'MarkerFaceColor', wcol, ...
                 'MarkerEdgeColor', 'w');
        leg_hB(end+1)   = h;                    %#ok<AGROW>
        leg_txtB{end+1} = upper(r);             %#ok<AGROW>
    end

    % Linea somma totale (tratteggiata, colore algoritmo)
    f_sum_vec = f_tot_sum.(aKey);
    valid_sum = ~isnan(f_sum_vec);
    if any(valid_sum)
        h_sum = plot(ax, n_arr(valid_sum), f_sum_vec(valid_sum), ...
                     '--s', 'Color', col, 'LineWidth', 2.2, ...
                     'MarkerSize', 7, 'MarkerFaceColor', col, ...
                     'MarkerEdgeColor', 'w');
        leg_hB(end+1)   = h_sum;                %#ok<AGROW>
        leg_txtB{end+1} = 'F_{tot} (somma)';    %#ok<AGROW>
    end

    title(ax, lbl, 'FontSize', 12, 'FontWeight', 'bold', 'Color', col);
    xlabel(ax, 'N utenti', 'FontSize', 11);
    ylabel(ax, 'F_{total} ottimale  (€)', 'FontSize', 11);
    legend(ax, leg_hB, leg_txtB, 'Location', 'northwest', 'FontSize', 8);
    xlim(ax, [min(n_arr)*0.85, max(n_arr)*1.10]);
end

sgtitle(figB, 'F_{total} ottimale vs N utenti — per rifiuto e algoritmo', ...
        'FontSize', 14, 'FontWeight', 'bold');

%% ── 6. Console: tabella riepilogativa ────────────────────────────────────

fprintf('%-10s', 'N utenti');
for a = 1:numel(algo_keys)
    lbl = ALGO_LABEL(algo_keys{a});
    fprintf('  %-14s  %-14s', [lbl ' t(s)'], [lbl ' F_sum']);
end
fprintf('\n%s\n', repmat('-', 1, 10 + numel(algo_keys)*32));

for f = 1:n_files
    fprintf('%-10d', n_arr(f));
    for a = 1:numel(algo_keys)
        aKey = matlab.lang.makeValidName(algo_keys{a});
        t_v  = times.(aKey)(f);
        fs_v = f_tot_sum.(aKey)(f);
        if isnan(t_v)
            fprintf('  %-14s  %-14s', 'N/A', 'N/A');
        else
            fprintf('  %-14.4f  %-14.0f', t_v, fs_v);
        end
    end
    fprintf('\n');
end
fprintf('\n');