% =========================================================================
%  SPIL — Analisi Pareto e Visualizzazione Risultati (singola run)
%
%  Input  : un file CSV  risultati_<N>_utenti.csv  (generato da main.py)
%  Output : 5 figure
% =========================================================================

%% ── 0. Acquisizione path CSV ─────────────────────────────────────────────

stack_esecutivo = dbstack;
is_standalone = (length(stack_esecutivo) == 1);

if is_standalone || ~exist('CSV_FILE', 'var') || isempty(CSV_FILE)
    [fname, fpath] = uigetfile('*.csv', 'Seleziona il CSV della run');
    if isequal(fname, 0)
        error('Nessun file selezionato. Script interrotto.');
    end
    CSV_FILE = fullfile(fpath, fname);
end

if isstring(CSV_FILE)
    CSV_FILE = char(CSV_FILE);
end

if ~isfile(CSV_FILE)
    error('File non trovato: %s', CSV_FILE);
end

clearvars -except CSV_FILE; 
clc; 
close all;

%% ── 1. Lettura e partizionamento dati ────────────────────────────────────

opts = detectImportOptions(CSV_FILE);
opts.VariableNamesLine = 1;
T = readtable(CSV_FILE, opts);

if ~iscell(T.rifiuto),    T.rifiuto    = cellstr(T.rifiuto);    end
if ~iscell(T.algoritmo),  T.algoritmo  = cellstr(T.algoritmo);  end

waste_types = unique(T.rifiuto,   'stable');   
algo_keys   = unique(T.algoritmo, 'stable');   
n_types     = numel(waste_types);
n_algos     = numel(algo_keys);

algo_labels = containers.Map( ...
    {'greedy','clarke_wright'}, ...
    {'Greedy','Clarke-Wright'} );

%% ── 2. Palette colori ────────────────────────────────────────────────────

% Colori standard per Figure 1, 3 e 4
ALGO_COLOR = containers.Map( ...
    {'greedy','clarke_wright'}, ...
    {[0.13 0.47 0.71], [0.84 0.37 0.05]} );   

ALGO_MARKER = containers.Map( ...
    {'greedy','clarke_wright'}, ...
    {'o', '^'} );

ALGO_LINE = containers.Map( ...
    {'greedy','clarke_wright'}, ...
    {'-', '-'} );   

COMP_COLORS = [   
    0.29 0.67 0.31;   % insoddisfazione
    0.17 0.45 0.70;   % costo fisso
    0.99 0.56 0.05;   % costo viaggio
    0.60 0.40 0.74;   % costo lavoro
];
comp_labels = {'Insoddisfazione','Costo fisso','Costo viaggio','Costo lavoro'};

% Palette dedicata per Pareto (Fig 2) - Coppie di colori (Riga 1: Chiaro, Riga 2: Scuro)
pareto_palette = containers.Map();
pareto_palette('organico')        = [0.4 0.8 0.4;  0.0 0.5 0.0]; % Verde chiaro / Scuro
pareto_palette('carta')           = [0.9 0.7 0.3;  0.7 0.3 0.0]; % Arancione chiaro / Scuro
pareto_palette('plastica')        = [0.4 0.8 1.0;  0.0 0.0 0.8]; % Celeste / Blu
pareto_palette('vetro')           = [0.8 0.5 0.9;  0.4 0.0 0.6]; % Lilla / Viola
pareto_palette('indifferenziata') = [1.0 0.5 0.5;  0.7 0.0 0.0]; % Rosso chiaro / Scuro

%% ── 3. Struttura dati D.(algo).(rifiuto) ─────────────────────────────────

D = struct();
algo_times = struct();   

for a = 1:n_algos
    ak   = algo_keys{a};
    aKey = matlab.lang.makeValidName(ak);
    D.(aKey) = struct();

    for k = 1:n_types
        r    = waste_types{k};
        rKey = matlab.lang.makeValidName(r);
        mask = strcmp(T.algoritmo, ak) & strcmp(T.rifiuto, r);
        sub  = T(mask, :);
        sub  = sortrows(sub, 'X_r');
        D.(aKey).(rKey) = sub;
    end

    amask = strcmp(T.algoritmo, ak);
    if any(amask)
        algo_times.(aKey) = T.algo_time_sec(find(amask, 1));
    else
        algo_times.(aKey) = NaN;
    end
end

%% ── Console: header riepilogo ────────────────────────────────────────────

fprintf('\n%s\n', repmat('=', 1, 90));
fprintf('  SPIL — Analisi run: %s\n', CSV_FILE);
fprintf('  Rifiuti: %d   |   Algoritmi: %s\n', n_types, strjoin(algo_keys, ', '));
for a = 1:n_algos
    ak   = algo_keys{a};
    aKey = matlab.lang.makeValidName(ak);
    lbl  = algo_labels(ak);
    fprintf('  Tempo %-16s: %.4f s\n', lbl, algo_times.(aKey));
end
fprintf('%s\n\n', repmat('=', 1, 90));

% =========================================================================
%  FIGURA 1 — F_total vs X_r: 5 subplot, curve per algoritmo (colore standard)
% =========================================================================

fig1 = figure('Name', 'F_total vs X_r per rifiuto', ...
              'NumberTitle', 'off', 'Position', [30 50 1400 680]);

for k = 1:n_types
    r    = waste_types{k};
    rKey = matlab.lang.makeValidName(r);

    ax = subplot(2, 3, k);
    hold(ax, 'on'); grid(ax, 'on'); box(ax, 'on');

    leg_h   = gobjects(0);
    leg_txt = {};

    for a = 1:n_algos
        ak   = algo_keys{a};
        aKey = matlab.lang.makeValidName(ak);
        sub  = D.(aKey).(rKey);
        if isempty(sub), continue; end

        col = ALGO_COLOR(ak);
        mk  = ALGO_MARKER(ak);
        lbl = algo_labels(ak);

        h = plot(ax, sub.X_r, sub.F_total, ...
                 [ALGO_LINE(ak), mk], ...
                 'Color', col, 'LineWidth', 2.0, ...
                 'MarkerSize', 5, 'MarkerFaceColor', col);
        leg_h(end+1)   = h;                          
        leg_txt{end+1} = ['F_{total} ', lbl];        

        plot(ax, sub.X_r, sub.F_insoddis,    '-', 'Color', [col 0.40], 'LineWidth', 0.9);
        plot(ax, sub.X_r, sub.F_costo_fisso, '-', 'Color', [col 0.30], 'LineWidth', 0.9);
        plot(ax, sub.X_r, sub.F_viaggio,     '-', 'Color', [col 0.25], 'LineWidth', 0.9);

        bm = sub.is_best == 1;
        if any(bm)
            plot(ax, sub.X_r(bm), sub.F_total(bm), ...
                 'p', 'MarkerSize', 11, ...
                 'MarkerFaceColor', 'yellow', 'MarkerEdgeColor', col, ...
                 'LineWidth', 1.4);
            
            if a == 1
                va = 'bottom';
                y_shift = max(sub.F_total)*0.03;
            else
                va = 'top';
                y_shift = -max(sub.F_total)*0.03;
            end
             
            text(sub.X_r(bm), sub.F_total(bm) + y_shift, ...
                 sprintf('%s\nX^*=%.1f  V=%d', lbl, sub.X_r(bm), sub.n_vehicles(bm)), ...
                 'FontSize', 7, 'Color', col*0.9, 'VerticalAlignment', va, ...
                 'HorizontalAlignment', 'center', 'Parent', ax);
        end
    end

    title(ax, upper(r), 'FontSize', 10, 'FontWeight', 'bold');
    xlabel(ax, 'X_r  (ritiri/settimana)', 'FontSize', 8);
    ylabel(ax, 'F.O.  (€)', 'FontSize', 8);
    if ~isempty(leg_h)
        legend(ax, leg_h, leg_txt, 'Location', 'best', 'FontSize', 7);
    end
    xlim(ax, [0.3, 6.2]);
end

ax6 = subplot(2, 3, 6);
axis(ax6, 'off');
y0 = 0.75;
for a = 1:n_algos
    ak  = algo_keys{a};
    col = ALGO_COLOR(ak);
    lbl = algo_labels(ak);
    t_s = algo_times.(matlab.lang.makeValidName(ak));
    text(0.15, y0, sprintf('— %s  (%.4f s)', lbl, t_s), ...
         'Color', col, 'FontSize', 10, 'FontWeight', 'bold', ...
         'Units', 'normalized', 'Parent', ax6);
    y0 = y0 - 0.20;
end
text(0.15, y0 - 0.05, '★ = soluzione ottimale', ...
     'FontSize', 9, 'Units', 'normalized', 'Parent', ax6);

sgtitle(fig1, 'F_{total} vs X_r — Curve per tipologia di rifiuto e algoritmo', ...
        'FontSize', 13, 'FontWeight', 'bold');

% =========================================================================
%  FIGURA 2 — Pareto: 5 subplot, Assi Invertiti e Palette Specifica
% =========================================================================

fig2 = figure('Name', 'Pareto: Insoddisfazione vs Costi Operativi', ...
              'NumberTitle', 'off', 'Position', [80 80 1400 680]);

for k = 1:n_types
    r    = waste_types{k};
    r_low = lower(r);
    rKey = matlab.lang.makeValidName(r);

    if isKey(pareto_palette, r_low)
        p_cols = pareto_palette(r_low);
    else
        p_cols = [0.5 0.5 0.5; 0.2 0.2 0.2]; % Fallback
    end

    ax = subplot(2, 3, k);
    hold(ax, 'on'); grid(ax, 'on'); box(ax, 'on');

    leg_h2   = gobjects(0);
    leg_txt2 = {};

    for a = 1:n_algos
        ak   = algo_keys{a};
        aKey = matlab.lang.makeValidName(ak);
        sub  = D.(aKey).(rKey);
        if isempty(sub), continue; end
        
        % Determina l'indice (1 per Greedy, 2 per CW) per estrarre il colore
        algo_idx = find(strcmp({'greedy', 'clarke_wright'}, ak));
        if isempty(algo_idx), algo_idx = 1; end

        sub = sortrows(sub, 'X_r'); 
        mk  = ALGO_MARKER(ak);
        lbl = algo_labels(ak);
        col = p_cols(algo_idx, :); % Colore specifico estratto dalla matrice

        F_costi = sub.F_costo_fisso + sub.F_viaggio + sub.F_lavoro;

        % SCAMBIO ASSI: F_costi sulle X, F_insoddis sulle Y
        h = plot(ax, F_costi, sub.F_insoddis, ['-', mk], ...
            'Color', col, 'LineWidth', 1.4, 'MarkerSize', 5, ...
            'MarkerFaceColor', col, 'MarkerEdgeColor', 'w');

        leg_h2(end+1)   = h;                          
        leg_txt2{end+1} = lbl;                   

        % Etichette X_r scambiate coerentemente
        for i = 1:height(sub)
            text(ax, F_costi(i), sub.F_insoddis(i), ...
                 sprintf(' %.1f', sub.X_r(i)), ...
                 'FontSize', 6, 'Color', col * 0.85, ...
                 'VerticalAlignment', 'bottom');
        end

        % Best point stella scambiato coerentemente
        bm = sub.is_best == 1;
        if any(bm)
            plot(ax, F_costi(bm), sub.F_insoddis(bm), ...
                'p', 'MarkerSize', 11, 'MarkerFaceColor', 'yellow', ...
                'MarkerEdgeColor', col, 'LineWidth', 1.2);
        end
    end
    
    title(ax, upper(r), 'FontSize', 10, 'FontWeight', 'bold');
    xlabel(ax, 'F_{costi} (€)', 'FontSize', 8);
    ylabel(ax, 'F_{insoddisfazione} (penalità)', 'FontSize', 8);
    if ~isempty(leg_h2)
        legend(ax, leg_h2, leg_txt2, 'Location', 'best', 'FontSize', 7);
    end
end

sgtitle(fig2, 'Frontiera di Pareto — Costi Operativi vs Insoddisfazione per Rifiuto', ...
        'FontSize', 13, 'FontWeight', 'bold');

% =========================================================================
%  FIGURA 3 — Bar chart grouped+stacked: scomposizione best solution
% =========================================================================

fig3 = figure('Name', 'Scomposizione F_total — Best Solution', ...
              'NumberTitle', 'off', 'Position', [130 130 1050 520]);
hold on; grid on; box on;

bar_width  = 0.35;
group_gap  = 1.0;   
group_centers = (1:n_types) * group_gap;

if n_algos == 1
    algo_offsets = 0;
else
    algo_offsets = linspace(-bar_width*0.55, bar_width*0.55, n_algos);
end

best_data = struct();   
for a = 1:n_algos
    ak   = algo_keys{a};
    aKey = matlab.lang.makeValidName(ak);
    best_data.(aKey) = struct();
    for k = 1:n_types
        r    = waste_types{k};
        rKey = matlab.lang.makeValidName(r);
        sub  = D.(aKey).(rKey);
        bm   = sub.is_best == 1;
        if any(bm)
            best_data.(aKey).(rKey) = [sub.F_insoddis(bm), sub.F_costo_fisso(bm), ...
                                       sub.F_viaggio(bm),   sub.F_lavoro(bm)];
            best_data.([aKey '_xstar_' rKey]) = sub.X_r(bm);
            best_data.([aKey '_nveh_'  rKey]) = sub.n_vehicles(bm);
        else
            best_data.(aKey).(rKey) = zeros(1, 4);
            best_data.([aKey '_xstar_' rKey]) = NaN;
            best_data.([aKey '_nveh_'  rKey]) = NaN;
        end
    end
end

bar_handles = gobjects(4, 1);   

for a = 1:n_algos
    ak    = algo_keys{a};
    aKey  = matlab.lang.makeValidName(ak);
    col_a = ALGO_COLOR(ak);
    x_pos = group_centers + algo_offsets(a);

    Y_mat = zeros(n_types, 4);
    for k = 1:n_types
        r    = waste_types{k};
        rKey = matlab.lang.makeValidName(r);
        Y_mat(k, :) = best_data.(aKey).(rKey);
    end

    b = bar(x_pos, Y_mat, bar_width, 'stacked', 'EdgeColor', col_a*0.7, 'LineWidth', 0.8);

    for c = 1:4
        face_col = COMP_COLORS(c,:) * 0.65 + col_a * 0.35;
        b(c).FaceColor = face_col;
        if a == 1   
            bar_handles(c) = b(c);
        end
    end

    for k = 1:n_types
        r    = waste_types{k};
        rKey = matlab.lang.makeValidName(r);
        tot  = sum(Y_mat(k,:));
        xs   = best_data.([aKey '_xstar_' rKey]);
        nv   = best_data.([aKey '_nveh_'  rKey]);
        if ~isnan(xs) && tot > 0
            text(x_pos(k), tot + max(sum(Y_mat,2))*0.03, ...
                 sprintf('X^*=%.1f\nV=%d', xs, nv), ...
                 'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom', ...
                 'FontSize', 7, 'Color', col_a * 0.9);
        end
    end
end

xticks(group_centers);
xticklabels(cellfun(@upper, waste_types, 'UniformOutput', false));
ylabel('F  (€)', 'FontSize', 11);
title('Scomposizione F_{total} — Soluzione ottimale per algoritmo', ...
      'FontSize', 13, 'FontWeight', 'bold');

legend(bar_handles, comp_labels, 'Location', 'northeast', 'FontSize', 9);

for a = 1:n_algos
    ak  = algo_keys{a};
    col = ALGO_COLOR(ak);
    lbl = algo_labels(ak);
    patch(NaN, NaN, col, 'EdgeColor', col*0.7, 'DisplayName', lbl);
end
legend('show', 'Location', 'northeast', 'FontSize', 9);

% =========================================================================
%  FIGURA 4 — Bar chart tempi di esecuzione
% =========================================================================

fig4 = figure('Name', 'Tempi di esecuzione', ...
              'NumberTitle', 'off', 'Position', [200 200 560 420]);
hold on; grid on; box on;

t_vals   = zeros(1, n_algos);
t_colors = zeros(n_algos, 3);
t_labels = cell(1, n_algos);

for a = 1:n_algos
    ak            = algo_keys{a};
    aKey          = matlab.lang.makeValidName(ak);
    t_vals(a)     = algo_times.(aKey);
    t_colors(a,:) = ALGO_COLOR(ak);
    t_labels{a}   = algo_labels(ak);
end

for a = 1:n_algos
    bar(a, t_vals(a), 0.5, 'FaceColor', t_colors(a,:), ...
            'EdgeColor', t_colors(a,:)*0.7, 'LineWidth', 1.2);
    text(a, t_vals(a) * 1.03, sprintf('%.4f s', t_vals(a)), ...
         'HorizontalAlignment', 'center', 'FontSize', 10, 'FontWeight', 'bold');
end

% Speedup annotation posizionata in alto a destra con formattazione visibile
if n_algos == 2
    ratio = max(t_vals) / max(min(t_vals), 1e-9);
    [~, faster_idx] = min(t_vals);
    faster_lbl = t_labels{faster_idx};
    
    text(0.95, 0.95, ...
         sprintf('%s è %.2fx più veloce', faster_lbl, ratio), ...
         'Units', 'normalized', 'HorizontalAlignment', 'right', 'VerticalAlignment', 'top', ...
         'FontSize', 11, 'Color', 'k', 'BackgroundColor', [0.96 0.96 0.96], ...
         'EdgeColor', 'k', 'Margin', 4);
end

xticks(1:n_algos);
xticklabels(t_labels);
ylabel('Tempo di esecuzione  (s)', 'FontSize', 11);
title('Confronto tempi — Greedy vs Clarke-Wright', ...
      'FontSize', 13, 'FontWeight', 'bold');
xlim([0.3, n_algos + 0.7]);
ylim([0, max(t_vals) * 1.25]);

% =========================================================================
%  Console: tabella riepilogativa dettagliata
% =========================================================================

fprintf('%-14s %-16s %6s %6s %10s %10s %10s %10s %10s\n', ...
        'Rifiuto','Algoritmo','X*','Veic.','F_total','F_insoddis', ...
        'F_fisso','F_viaggio','F_lavoro');
fprintf('%s\n', repmat('-', 1, 100));

for a = 1:n_algos
    ak   = algo_keys{a};
    aKey = matlab.lang.makeValidName(ak);
    lbl  = algo_labels(ak);

    for k = 1:n_types
        r    = waste_types{k};
        rKey = matlab.lang.makeValidName(r);
        sub  = D.(aKey).(rKey);
        bm   = sub.is_best == 1;
        if any(bm)
            fprintf('%-14s %-16s %6.1f %6d %10.1f %10.1f %10.1f %10.1f %10.1f\n', ...
                r, lbl, sub.X_r(bm), sub.n_vehicles(bm), ...
                sub.F_total(bm), sub.F_insoddis(bm), ...
                sub.F_costo_fisso(bm), sub.F_viaggio(bm), sub.F_lavoro(bm));
        end
    end
    fprintf('%s\n', repmat('-', 1, 100));
end

for a = 1:n_algos
    ak  = algo_keys{a};
    lbl = algo_labels(ak);
    fprintf('Tempo %-16s: %.4f s\n', lbl, algo_times.(matlab.lang.makeValidName(ak)));
end

% =========================================================================
%  FIGURA 5 — Tabella riepilogativa testuale (figure separata)
% =========================================================================

fig5 = figure('Name', 'Tabella Riepilogativa', ...
              'NumberTitle', 'off', 'Position', [250 250 900 420]);
axis off;

col_headers = {'Rifiuto','Algoritmo','X*','Veicoli', ...
               'F total','F insoddis','F fisso','F viaggio','F lavoro'};
n_rows = n_types * n_algos;
cell_data = cell(n_rows, numel(col_headers));

row = 0;
for a = 1:n_algos
    ak   = algo_keys{a};
    aKey = matlab.lang.makeValidName(ak);
    lbl  = algo_labels(ak);
    for k = 1:n_types
        row  = row + 1;
        r    = waste_types{k};
        rKey = matlab.lang.makeValidName(r);
        sub  = D.(aKey).(rKey);
        bm   = sub.is_best == 1;
        if any(bm)
            cell_data(row,:) = { ...
                upper(r), lbl, ...
                sprintf('%.1f', sub.X_r(bm)), ...
                sprintf('%d',   sub.n_vehicles(bm)), ...
                sprintf('%.0f', sub.F_total(bm)), ...
                sprintf('%.0f', sub.F_insoddis(bm)), ...
                sprintf('%.0f', sub.F_costo_fisso(bm)), ...
                sprintf('%.0f', sub.F_viaggio(bm)), ...
                sprintf('%.0f', sub.F_lavoro(bm)) };
        end
    end
end

t_ui = uitable(fig5, ...
    'Data',               cell_data, ...
    'ColumnName',         col_headers, ...
    'RowName',            {}, ...
    'Units',              'normalized', ...
    'Position',           [0.02 0.15 0.96 0.80], ...
    'FontSize',           10, ...
    'ColumnWidth',        {120,110,40,55,75,80,70,80,75});

y_t = 0.10;
for a = 1:n_algos
    ak  = algo_keys{a};
    col = ALGO_COLOR(ak);
    lbl = algo_labels(ak);
    annotation(fig5, 'textbox', [0.02 y_t 0.96 0.06], ...
        'String', sprintf('Tempo %s: %.4f s', lbl, algo_times.(matlab.lang.makeValidName(ak))), ...
        'Color', col, 'FontSize', 10, 'FontWeight', 'bold', ...
        'EdgeColor', 'none', 'FitBoxToText', 'off');
    y_t = y_t - 0.08;
end

% --- Estrazione del numero utenti dal nome file per il Titolo ---
[~, fname_no_ext, ~] = fileparts(CSV_FILE);
tokens = regexp(fname_no_ext, '(\d+)_utenti', 'tokens');
if ~isempty(tokens)
    n_utenti_str = tokens{1}{1};
    title_str = sprintf('Riepilogo: %s utenti', n_utenti_str);
else
    title_str = 'Riepilogo';
end

annotation(fig5, 'textbox', [0.02 0.96 0.96 0.04], ...
    'String', title_str, 'FontSize', 12, 'FontWeight', 'bold', ...
    'EdgeColor', 'none', 'HorizontalAlignment', 'center', 'Interpreter', 'none');