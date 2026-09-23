% =========================================================================
% T2: Analisi Trasversale — Profilo F(X_r)
% Usa TUTTE le righe dei CSV (non solo is_best) per mostrare la forma
% della funzione obiettivo sulla griglia X_r = [0.5, 1.0, ..., 6.0].
% Domanda: dove si trova il minimo? Perché? Cosa cambia col gamma?
% =========================================================================
clear; clc; close all;

dataDir = 'risultati_csv';
files   = dir(fullfile(dataDir, '*.csv'));

if isempty(files)
    error('Nessun file CSV trovato in risultati_csv/');
end

colorGreedy = [0.13, 0.47, 0.71];
colorCW     = [0.84, 0.37, 0.05];

% Cartella di output per l'export delle figure (creata se non esiste)
% NB: getenv('HOME') su Windows spesso e' vuoto -> path relativo sbagliato.
%     java.lang.System.getProperty('user.home') funziona su Win/Mac/Linux.
homeDir = char(java.lang.System.getProperty('user.home'));
outDir  = fullfile(homeDir, 'Desktop', 'immagini');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end
fprintf('  [INFO] Le figure verranno salvate in: %s\n', outDir);

% =========================================================================
% 1. LETTURA DATI — TUTTE le righe (is_best=0 e is_best=1)
%    Una riga per (benchmark × rifiuto × algoritmo × gamma × X_r)
% =========================================================================
VarTypes_raw = {'string','double','string','string','double', ...
                'double','double','double','double','double','double','double'};
VarNames_raw = {'Benchmark','Gamma','Rifiuto','Algoritmo','X_r', ...
                'F_insoddis','F_logistica','F_tot','Sat_Fisica','Sat_Tempo','N_Serviti','Vehicles'};
RawTable = table('Size', [0, length(VarNames_raw)], ...
                 'VariableTypes', VarTypes_raw, 'VariableNames', VarNames_raw);

for i = 1:length(files)
    filename  = files(i).name;
    gamma_str = regexp(filename, 'gamma(\d+\.\d+)', 'tokens');
    if isempty(gamma_str), continue; end

    gamma_val   = str2double(gamma_str{1}{1});
    bench_str   = regexp(filename, '^(.+)_gamma', 'tokens');
    bench_label = string(bench_str{1}{1});

    filepath = fullfile(dataDir, filename);
    T        = readtable(filepath, detectImportOptions(filepath));

    algos = {'greedy', 'clarke_wright'};
    for a = 1:length(algos)
        T_algo = T(strcmp(T.algoritmo, algos{a}), :);
        if isempty(T_algo), continue; end

        for row_idx = 1:height(T_algo)
            row     = T_algo(row_idx, :);
            f_log_r = row.F_costo_fisso + row.F_viaggio + row.F_lavoro;
            n_serv  = row.n_utenti_serviti;

            RawTable = [RawTable; {bench_label, gamma_val, string(row.rifiuto), ...
                algos{a}, row.X_r, row.F_insoddis, f_log_r, row.F_total, ...
                row.sat_fisica, row.sat_tempo, n_serv, row.n_vehicles}];
        end
    end
end

if height(RawTable) == 0
    error('Nessun dato valido estratto.');
end

g_unique  = unique(RawTable.Gamma);
n_g       = length(g_unique);
xr_unique = unique(RawTable.X_r);

% =========================================================================
% GRAFICO 1: Profilo F_tot(X_r) aggregato su tutti i benchmark e rifiuti
% Separato per gamma (colore) e algoritmo (subplot)
% Il minimo di ogni curva è evidenziato con un marker grande
% =========================================================================
fig1 = figure('Name', 'Profilo F(X_r)', 'Position', [50, 50, 1050, 480]);
sgtitle('T2 — Profilo della Funzione Obiettivo F_{tot}(X_r)', 'FontWeight', 'bold');

% Palette gamma: dal blu chiaro (gamma basso = Pro-Azienda) al verde (Pro-Cittadino)
gamma_colors = [
    0.20, 0.63, 0.86;   % gamma 0.10 — celeste
    0.50, 0.50, 0.50;   % gamma 0.50 — grigio
    0.18, 0.63, 0.33;   % gamma 0.90 — verde
];
gamma_styles = {'-', '--', ':'};

algo_keys   = {'greedy', 'clarke_wright'};
algo_titles = {'Greedy', 'Clarke-Wright'};
algo_colors = {colorGreedy, colorCW};

for a = 1:2
    subplot(1, 2, a); hold on;

    for g = 1:n_g
        gv    = g_unique(g);
        sub   = RawTable(strcmp(RawTable.Algoritmo, algo_keys{a}) & RawTable.Gamma == gv, :);
        if isempty(sub), continue; end

        % Media F_tot per X_r (aggrega su benchmark e rifiuti)
        agg = groupsummary(sub, 'X_r', 'mean', 'F_tot');
        agg = sortrows(agg, 'X_r');

        col_g = gamma_colors(mod(g-1, size(gamma_colors,1)) + 1, :);
        plot(agg.X_r, agg.mean_F_tot, gamma_styles{g}, ...
             'Color', col_g, 'LineWidth', 2, ...
             'DisplayName', sprintf('\\gamma = %.2f', gv));

        % Marca il minimo — testo a destra del punto, leggermente sotto
        [~, idx_min] = min(agg.mean_F_tot);
        yl = ylim;
        y_offset = (yl(2) - yl(1)) * 0.05;
        plot(agg.X_r(idx_min), agg.mean_F_tot(idx_min), 'v', ...
             'Color', col_g, 'MarkerFaceColor', col_g, 'MarkerSize', 10, ...
             'HandleVisibility', 'off');
        text(agg.X_r(idx_min) + 0.15, agg.mean_F_tot(idx_min) + y_offset, ...
             sprintf('X^*=%.1f', agg.X_r(idx_min)), ...
             'Color', col_g, 'FontSize', 8, 'FontWeight', 'bold');
    end

    xlabel('X_r (raccolta/settimana)');
    ylabel('F_{tot} medio (aggregato)');
    title(algo_titles{a}, 'FontWeight', 'bold');
    legend('Location', 'best', 'FontSize', 8);
    grid on; box on;
end

exportgraphics(fig1, fullfile(outDir, 't2 Ftot rispetto a Xr.png'), 'Resolution', 300);

% =========================================================================
% GRAFICO 2: Scomposizione F(X_r) — F_insoddis vs F_logistica
% Istanza std seed42, gamma=0.50, rifiuto di riferimento = organico
% Non si aggrega su tutti i rifiuti: ogni rifiuto ha X*_r diverso,
% la media non corrisponde all'ottimo di nessuno specifico.
% =========================================================================
gv_ref       = 0.50;
[~, idx_ref] = min(abs(g_unique - gv_ref));
gv_ref       = g_unique(idx_ref);
rif_ref      = "organico";  % rifiuto di riferimento — cambia qui se necessario

fig2 = figure('Name', 'Scomposizione F(X_r)', 'Position', [100, 100, 1050, 480]);
sgtitle(sprintf('T2 — Scomposizione F_{tot}(X_r): rifiuto "%s"  (\\gamma = %.2f, istanza std)', ...
        char(rif_ref), gv_ref), 'FontWeight', 'bold');

% Pre-calcola range Y condiviso
y_all2 = [];
for a = 1:2
    bench_ref = RawTable.Benchmark == "risultati_200u_std_seed42";
    sub_pre = RawTable(bench_ref & strcmp(RawTable.Algoritmo, algo_keys{a}) & ...
                       RawTable.Gamma == gv_ref & RawTable.Rifiuto == rif_ref, :);
    if isempty(sub_pre)
        sub_pre = RawTable(strcmp(RawTable.Algoritmo, algo_keys{a}) & ...
                           RawTable.Gamma == gv_ref & RawTable.Rifiuto == rif_ref, :);
    end
    if ~isempty(sub_pre)
        y_all2 = [y_all2; sub_pre.F_insoddis; sub_pre.F_logistica; ...
                  sub_pre.F_insoddis + sub_pre.F_logistica];
    end
end
y_min_shared = 0;
y_max_shared = max(y_all2) * 1.08;

for a = 1:2
    subplot(1, 2, a); hold on;

    bench_ref = RawTable.Benchmark == "risultati_200u_std_seed42";
    sub = RawTable(bench_ref & strcmp(RawTable.Algoritmo, algo_keys{a}) & ...
                   RawTable.Gamma == gv_ref & RawTable.Rifiuto == rif_ref, :);

    if isempty(sub)
        sub = RawTable(strcmp(RawTable.Algoritmo, algo_keys{a}) & ...
                       RawTable.Gamma == gv_ref & RawTable.Rifiuto == rif_ref, :);
        warning('Benchmark std seed42 non trovato per rifiuto %s, uso tutti.', char(rif_ref));
    end
    if isempty(sub)
        title(sprintf('%s — nessun dato', algo_titles{a})); continue;
    end

    sub = sortrows(sub, 'X_r');

    % Su singolo rifiuto + singolo benchmark non serve groupsummary —
    % una riga per X_r, prendo direttamente i valori
    plot(sub.X_r, sub.F_insoddis, '-o', ...
         'Color', [0.47, 0.67, 0.19], 'LineWidth', 2, 'MarkerFaceColor', [0.47, 0.67, 0.19], ...
         'DisplayName', 'F_{insoddis} \times k_{scala}');
    plot(sub.X_r, sub.F_logistica, '-s', ...
         'Color', [0.30, 0.30, 0.30], 'LineWidth', 2, 'MarkerFaceColor', [0.30, 0.30, 0.30], ...
         'DisplayName', 'F_{logistica}');
    f_tot_calc = sub.F_insoddis + sub.F_logistica;
    plot(sub.X_r, f_tot_calc, '-^', ...
         'Color', algo_colors{a}, 'LineWidth', 2.5, 'MarkerFaceColor', algo_colors{a}, ...
         'DisplayName', 'F_{tot}  =  F_{insoddis} + F_{logistica}');

    % Minimo di F_tot
    [~, idx_min] = min(f_tot_calc);
    xline(sub.X_r(idx_min), '--k', 'LineWidth', 1.2, 'HandleVisibility', 'off');
    yl = ylim;
    text(sub.X_r(idx_min) + 0.08, yl(1) + (yl(2)-yl(1))*0.04, ...
         sprintf('X^*=%.1f', sub.X_r(idx_min)), ...
         'FontSize', 8, 'FontWeight', 'bold', 'Color', [0.2 0.2 0.2]);

    xlabel('X_r (raccolta/settimana)');
    ylabel('Valore componente');
    title(algo_titles{a}, 'FontWeight', 'bold');
    ylim([y_min_shared, y_max_shared]);
    legend('Location', 'northeast', 'FontSize', 8);
    grid on; box on;
end

exportgraphics(fig2, fullfile(outDir, 't2 Scomposizione Ftot (Organico) rispetto a Xr.png'), 'Resolution', 300);

% =========================================================================
% GRAFICO 3: Profilo F(X_r) per singolo rifiuto — gamma=0.50, entrambi gli algoritmi
% Organico e vetro avranno comportamenti strutturalmente diversi
% =========================================================================
rifiuti_list = unique(RawTable.Rifiuto);
n_rif        = length(rifiuti_list);

colori_rif = [
    0.84, 0.15, 0.16;
    0.17, 0.63, 0.17;
    0.12, 0.47, 0.71;
    0.58, 0.40, 0.74;
    0.55, 0.34, 0.29;
];

fig3 = figure('Name', 'Profilo F(X_r) per Rifiuto', 'Position', [150, 150, 1050, 480]);
sgtitle(sprintf('T2 — Profilo F_{tot}(X_r) per Rifiuto (\\gamma = %.2f)', gv_ref), ...
        'FontWeight', 'bold');

for a = 1:2
    subplot(1, 2, a); hold on;

    for r = 1:n_rif
        rif_name = rifiuti_list(r);
        sub_r    = RawTable(strcmp(RawTable.Algoritmo, algo_keys{a}) & ...
                            RawTable.Gamma == gv_ref & ...
                            strcmp(RawTable.Rifiuto, rif_name), :);
        if isempty(sub_r), continue; end

        agg_r = groupsummary(sub_r, 'X_r', 'mean', 'F_tot');
        agg_r = sortrows(agg_r, 'X_r');

        col_r = colori_rif(mod(r-1, size(colori_rif,1)) + 1, :);
        plot(agg_r.X_r, agg_r.mean_F_tot, '-o', ...
             'Color', col_r, 'LineWidth', 1.8, 'MarkerFaceColor', col_r, ...
             'DisplayName', char(rif_name));

        % Minimo per rifiuto
        [~, idx_min] = min(agg_r.mean_F_tot);
        plot(agg_r.X_r(idx_min), agg_r.mean_F_tot(idx_min), 'v', ...
             'Color', col_r, 'MarkerFaceColor', col_r, 'MarkerSize', 9, ...
             'HandleVisibility', 'off');
    end

    xlabel('X_r (raccolta/settimana)');
    ylabel('F_{tot} medio');
    title(algo_titles{a}, 'FontWeight', 'bold');
    legend('Location', 'southeast', 'FontSize', 8);
    grid on; box on;
end

exportgraphics(fig3, fullfile(outDir, 't2 Ftot per Rifiuto rispetto a Xr.png'), 'Resolution', 300);

% =========================================================================
% GRAFICO 4: Veicoli(X_r) — relazione meccanica tra frequenza e flotta
% Al crescere di X_r i carichi Q_u=W/X_r diminuiscono → meno veicoli
% =========================================================================
fig4 = figure('Name', 'Veicoli vs X_r', 'Position', [200, 200, 1050, 480]);
sgtitle('T2 — Veicoli Utilizzati al variare di X_r', 'FontWeight', 'bold', 'FontSize', 11);

for a = 1:2
    subplot(1, 2, a); hold on;

    for g = 1:n_g
        gv  = g_unique(g);
        sub = RawTable(strcmp(RawTable.Algoritmo, algo_keys{a}) & RawTable.Gamma == gv, :);
        if isempty(sub), continue; end

        agg_v = groupsummary(sub, 'X_r', 'mean', 'Vehicles');
        agg_v = sortrows(agg_v, 'X_r');

        col_g = gamma_colors(mod(g-1, size(gamma_colors,1)) + 1, :);
        plot(agg_v.X_r, agg_v.mean_Vehicles, gamma_styles{g}, ...
             'Color', col_g, 'LineWidth', 2, ...
             'DisplayName', sprintf('\\gamma = %.2f', gv));
    end

    xlabel('X_r (raccolta/settimana)');
    ylabel('Veicoli medi (somma 5 rifiuti)');
    title(algo_titles{a}, 'FontWeight', 'bold');
    legend('Location', 'northeast', 'FontSize', 8);
    grid on; box on;
end

exportgraphics(fig4, fullfile(outDir, 't2 Veicoli rispetto a Xr.png'), 'Resolution', 300);