% =========================================================================
%  SPIL — Analisi Pareto e Visualizzazione Risultati (singola run)
%
%  Input  : un file CSV  risultati_<N>_utenti.csv  (generato da main.py)
%  Output : 5 figure
%    Fig 1 — F_total vs X_r per rifiuto (curve per algoritmo, colori distinti)
%    Fig 2 — Scatter Pareto bi-obiettivo (F_insoddis vs F_costi)
%    Fig 3 — Bar chart grouped+stacked: scomposizione best solution per algo
%    Fig 4 — Bar chart tempi di esecuzione (Greedy vs Clarke-Wright)
%    Fig 5 — Tabella riepilogativa testuale
%
%  Uso standalone:
%    >> analisi_pareto            % chiede il CSV via dialog
%    >> analisi_pareto('risultati_500_utenti.csv')   % path esplicito
%
%  Uso da RunPipeline.m:
%    Il pipeline passa CSV_FILE come variabile workspace prima di chiamare
%    questo script  (assignin / o semplicemente la imposta nel workspace).
% =========================================================================

%% ── 0. Acquisizione path CSV ─────────────────────────────────────────────

% Rileva se lo script è lanciato da solo (standalone) o da un altro script
stack_esecutivo = dbstack;
is_standalone = (length(stack_esecutivo) == 1);

% Chiedi il file SE è lanciato da solo, OPPURE se la variabile in memoria non esiste
% Chiedi il file SE è lanciato da solo, OPPURE se la variabile in memoria non esiste
if is_standalone || ~exist('CSV_FILE', 'var') || isempty(CSV_FILE)
    
    % Se la cartella esiste, apri il prompt direttamente lì dentro
    start_path = '*.csv';
    if exist('risultati_csv', 'dir')
        start_path = fullfile('risultati_csv', '*.csv');
    end
    
    [fname, fpath] = uigetfile(start_path, 'Seleziona il CSV della run');
    if isequal(fname, 0)
        error('Nessun file selezionato. Script interrotto.');
    end
    CSV_FILE = fullfile(fpath, fname);
end

% Se arriva da RunPipeline come stringa ("..."), convertiamo in char array
if isstring(CSV_FILE)
    CSV_FILE = char(CSV_FILE);
end

if ~isfile(CSV_FILE)
    error('File non trovato: %s', CSV_FILE);
end

% Pulisci il workspace, MA SALVA la variabile per il resto dello script
clearvars -except CSV_FILE; 
clc; 
close all;

%% ── 1. Lettura e partizionamento dati ────────────────────────────────────

opts = detectImportOptions(CSV_FILE);
opts.VariableNamesLine = 1;
T = readtable(CSV_FILE, opts);

% Converti colonne stringa (compatibilità R2019b+)
if ~iscell(T.rifiuto),    T.rifiuto    = cellstr(T.rifiuto);    end
if ~iscell(T.algoritmo),  T.algoritmo  = cellstr(T.algoritmo);  end

waste_types = unique(T.rifiuto,   'stable');   % ordine: organico, carta, ...
algo_keys   = unique(T.algoritmo, 'stable');   % {"greedy"} o {"greedy","clarke_wright"}
n_types     = numel(waste_types);
n_algos     = numel(algo_keys);

% Etichette leggibili per i plot
algo_labels = containers.Map( ...
    {'greedy','clarke_wright'}, ...
    {'Greedy','Clarke-Wright'} );

%% ── 2. Palette colori ────────────────────────────────────────────────────
%
%  COLORS_WASTE  : 1 colore per rifiuto  (usato in Fig 2 scatter Pareto)
%  COLORS_ALGO   : 1 colore per algoritmo (usato in Fig 1, 3, 4)
%
%  Fig 1 — curve: colore = algoritmo  (Greedy blu scuro, CW arancione)
%  Fig 2 — scatter: colore = rifiuto, marker = algoritmo (○ G, △ CW)

COLORS_WASTE = [
    0.20  0.63  0.17;   % verde     — organico
    0.12  0.47  0.71;   % blu       — carta
    1.00  0.50  0.05;   % arancione — plastica
    0.58  0.40  0.74;   % viola     — vetro
    0.84  0.15  0.16;   % rosso     — indifferenziata
];

% Colori fissi per gli algoritmi (indipendenti dal numero di rifiuti)
ALGO_COLOR = containers.Map( ...
    {'greedy','clarke_wright'}, ...
    {[0.13 0.47 0.71], [0.84 0.37 0.05]} );   % blu profondo / arancio bruciato

ALGO_MARKER = containers.Map( ...
    {'greedy','clarke_wright'}, ...
    {'o', '^'} );

ALGO_LINE = containers.Map( ...
    {'greedy','clarke_wright'}, ...
    {'-', '-'} );   % entrambe linee continue, distinte solo dal colore

COMP_COLORS = [   % colori per le 4 componenti della F.O.
    0.29 0.67 0.31;   % insoddisfazione — verde chiaro
    0.17 0.45 0.70;   % costo fisso     — blu
    0.99 0.56 0.05;   % costo viaggio   — arancione
    0.60 0.40 0.74;   % costo lavoro    — viola
];
comp_labels = {'Insoddisfazione','Costo fisso','Costo viaggio','Costo lavoro'};

%% ── 3. Struttura dati D.(algo).(rifiuto) ─────────────────────────────────

D = struct();
algo_times = struct();   % tempo per algoritmo (primo valore trovato)

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

    % Tempo di esecuzione (uguale per tutte le righe dello stesso algo)
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
%  FIGURA 1 — F_total vs X_r: 5 subplot, curve per algoritmo (colore)
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

        % Curva F_total
        h = plot(ax, sub.X_r, sub.F_total, ...
                 [ALGO_LINE(ak), mk], ...
                 'Color', col, 'LineWidth', 2.0, ...
                 'MarkerSize', 5, 'MarkerFaceColor', col);
        leg_h(end+1)   = h;                          %#ok<AGROW>
        leg_txt{end+1} = ['F_{total} ', lbl];        %#ok<AGROW>

        % Componenti con trasparenza (50% del colore base)
        plot(ax, sub.X_r, sub.F_insoddis,    '-', ...
             'Color', [col 0.40], 'LineWidth', 0.9);
        plot(ax, sub.X_r, sub.F_costo_fisso, '-', ...
             'Color', [col 0.30], 'LineWidth', 0.9);
        plot(ax, sub.X_r, sub.F_viaggio,     '-', ...
             'Color', [col 0.25], 'LineWidth', 0.9);

        % Stella punto ottimale
        bm = sub.is_best == 1;
        if any(bm)
            plot(ax, sub.X_r(bm), sub.F_total(bm), ...
                 'p', 'MarkerSize', 13, ...
                 'MarkerFaceColor', 'yellow', 'MarkerEdgeColor', col, ...
                 'LineWidth', 1.4);
            text(sub.X_r(bm) + 0.07, sub.F_total(bm), ...
                 sprintf('%s\nX^*=%.1f  V=%d', lbl, sub.X_r(bm), sub.n_vehicles(bm)), ...
                 'FontSize', 6.5, 'Color', col*0.85, 'VerticalAlignment', 'bottom');
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

% 6° cella: legenda algoritmi
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
%  FIGURA 2 — Scatter Pareto bi-obiettivo
%             Colore = rifiuto   |   Marker = algoritmo (○ G, △ CW)
% =========================================================================

fig2 = figure('Name', 'Pareto: Insoddisfazione vs Costi Operativi', ...
              'NumberTitle', 'off', 'Position', [80 80 950 680]);
hold on; grid on; box on;

% Prima passiamo tutti i punti, poi costruiamo la legenda a mano
leg_h2   = gobjects(0);
leg_txt2 = {};

for k = 1:n_types
    r    = waste_types{k};
    rKey = matlab.lang.makeValidName(r);
    col  = COLORS_WASTE(k, :);

    first_for_this_waste = true;

    for a = 1:n_algos
        ak   = algo_keys{a};
        aKey = matlab.lang.makeValidName(ak);
        sub  = D.(aKey).(rKey);
        if isempty(sub), continue; end

        mk  = ALGO_MARKER(ak);
        lbl = algo_labels(ak);

        F_costi = sub.F_costo_fisso + sub.F_viaggio + sub.F_lavoro;

        h = scatter(sub.F_insoddis, F_costi, 55, ...
            mk, 'MarkerFaceColor', col, ...
            'MarkerEdgeColor', 'w', 'LineWidth', 0.7);

        % Un handle per rifiuto in legenda (solo primo algo incontrato)
        if first_for_this_waste
            leg_h2(end+1)   = h;                          %#ok<AGROW>
            leg_txt2{end+1} = upper(r);                   %#ok<AGROW>
            first_for_this_waste = false;
        end

        % Etichette X_r
        for i = 1:height(sub)
            text(sub.F_insoddis(i) + max(sub.F_insoddis)*0.005, F_costi(i), ...
                 sprintf('%.1f', sub.X_r(i)), ...
                 'FontSize', 5.5, 'Color', col * 0.72);
        end

        % Best point stella
        bm = sub.is_best == 1;
        if any(bm)
            scatter(sub.F_insoddis(bm), F_costi(bm), 220, ...
                'p', 'MarkerFaceColor', 'yellow', ...
                'MarkerEdgeColor', col, 'LineWidth', 1.5);
        end
    end
end

% Legenda marker (algoritmi) — aggiunta manuale in basso a destra
for a = 1:n_algos
    ak  = algo_keys{a};
    mk  = ALGO_MARKER(ak);
    lbl = algo_labels(ak);
    h_tmp = scatter(NaN, NaN, 60, mk, ...
        'MarkerFaceColor', [0.4 0.4 0.4], 'MarkerEdgeColor', 'w');
    leg_h2(end+1)   = h_tmp;           %#ok<AGROW>
    leg_txt2{end+1} = lbl;             %#ok<AGROW>
end

xlabel('F_{insoddisfazione}  (penalità disservizio)', 'FontSize', 11);
ylabel('F_{costi operativi}  (fisso + viaggio + lavoro)  [€]', 'FontSize', 11);
title('Frontiera di Pareto — Insoddisfazione vs Costi Operativi', ...
      'FontSize', 13, 'FontWeight', 'bold');
legend(leg_h2, leg_txt2, 'Location', 'best', 'FontSize', 9);

% =========================================================================
%  FIGURA 3 — Bar chart grouped+stacked: scomposizione best solution
%             Gruppi = rifiuti  |  Coppia barre = algoritmi
%             Stacked per componente (insoddis, fisso, viaggio, lavoro)
% =========================================================================
%
%  Strategia: per n_algos algoritmi, ogni "gruppo rifiuto" occupa
%  n_algos posizioni X equidistanziate attorno al centro del gruppo.
%  Usiamo bar() con posizione X esplicita per ogni algoritmo.

fig3 = figure('Name', 'Scomposizione F_total — Best Solution', ...
              'NumberTitle', 'off', 'Position', [130 130 1050 520]);
hold on; grid on; box on;

bar_width  = 0.35;
group_gap  = 1.0;   % distanza tra centri gruppi
% centri dei gruppi
group_centers = (1:n_types) * group_gap;

% offset di ciascun algoritmo nel gruppo (simmetrico attorno al centro)
if n_algos == 1
    algo_offsets = 0;
else
    algo_offsets = linspace(-bar_width*0.55, bar_width*0.55, n_algos);
end

% Pre-raccolta dati best per ogni (algo, rifiuto)
best_data = struct();   % best_data.(aKey).(rKey) = [insoddis, fisso, viaggio, lavoro]
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

% Disegno barre stacked per ogni (algo, rifiuto)
bar_handles = gobjects(4, 1);   % un handle per componente (per legenda)

for a = 1:n_algos
    ak    = algo_keys{a};
    aKey  = matlab.lang.makeValidName(ak);
    col_a = ALGO_COLOR(ak);
    x_pos = group_centers + algo_offsets(a);

    bottom = zeros(1, n_types);
    for c = 1:4
        comp_vals = zeros(1, n_types);
        for k = 1:n_types
            r    = waste_types{k};
            rKey = matlab.lang.makeValidName(r);
            comp_vals(k) = best_data.(aKey).(rKey)(c);
        end

        % Mescola colore componente con colore algoritmo: media pesata
        face_col = COMP_COLORS(c,:) * 0.65 + col_a * 0.35;

        b = bar(x_pos, comp_vals, bar_width, 'stacked', ...
                'FaceColor', face_col, 'EdgeColor', col_a*0.7, ...
                'LineWidth', 0.8, 'BarWidth', 1.0);

        % Imposta bottom manuale (MATLAB bar stacked su posizioni esplicite
        % non gestisce il bottom automaticamente come in grouped)
        for kk = 1:n_types
            b(1).YData(kk) = comp_vals(kk);   % già ok — bar() accumula su stessa x
        end

        if a == 1   % salva handle solo una volta per la legenda componenti
            bar_handles(c) = b;
        end

        bottom = bottom + comp_vals;
    end

    % Annotazione X* e V* sopra ogni barra del gruppo
    for k = 1:n_types
        r    = waste_types{k};
        rKey = matlab.lang.makeValidName(r);
        tot  = sum(best_data.(aKey).(rKey));
        xs   = best_data.([aKey '_xstar_' rKey]);
        nv   = best_data.([aKey '_nveh_'  rKey]);
        if ~isnan(xs)
            text(x_pos(k), tot * 1.015, ...
                 sprintf('X^*=%.1f\nV=%d', xs, nv), ...
                 'HorizontalAlignment', 'center', 'FontSize', 6.5, ...
                 'Color', col_a * 0.8);
        end
    end
end

% Etichette gruppo (nome rifiuto centrato)
xticks(group_centers);
xticklabels(cellfun(@upper, waste_types, 'UniformOutput', false));
ylabel('F  (€)', 'FontSize', 11);
title('Scomposizione F_{total} — Soluzione ottimale per algoritmo', ...
      'FontSize', 13, 'FontWeight', 'bold');

% Legenda doppia: componenti + algoritmi
legend(bar_handles, comp_labels, 'Location', 'northeast', 'FontSize', 9);

% Aggiunta patch fittizie per identificare gli algoritmi nel grafico
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
    b = bar(a, t_vals(a), 0.5, 'FaceColor', t_colors(a,:), ...
            'EdgeColor', t_colors(a,:)*0.7, 'LineWidth', 1.2);
    text(a, t_vals(a) * 1.03, sprintf('%.4f s', t_vals(a)), ...
         'HorizontalAlignment', 'center', 'FontSize', 10, 'FontWeight', 'bold');
end

% Speedup annotation (solo se entrambi presenti)
if n_algos == 2
    ratio = max(t_vals) / max(min(t_vals), 1e-9);
    [~, faster_idx] = min(t_vals);
    faster_lbl = t_labels{faster_idx};
    text(1.5, max(t_vals) * 0.90, ...
         sprintf('%s è %.2fx più veloce', faster_lbl, ratio), ...
         'HorizontalAlignment', 'center', 'FontSize', 10, ...
         'BackgroundColor', [1 1 0.85], 'EdgeColor', [0.6 0.6 0.4]);
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
    'ColumnWidth',        {80,110,40,55,75,80,70,80,75});

% Testo tempi sotto la tabella
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

title_str = sprintf('Riepilogo SPIL — %s', CSV_FILE);
annotation(fig5, 'textbox', [0.02 0.96 0.96 0.04], ...
    'String', title_str, 'FontSize', 11, 'FontWeight', 'bold', ...
    'EdgeColor', 'none', 'HorizontalAlignment', 'center');