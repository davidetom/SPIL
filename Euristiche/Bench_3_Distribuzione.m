% =========================================================================
% BENCH 3: Analisi Distribuzione (Uniforme vs Cluster)
% =========================================================================
clear; clc; close all;

dataDir = 'risultati_csv';
files = dir(fullfile(dataDir, '*_distrib_*_gamma*.csv'));

if isempty(files)
    error('Nessun file trovato per l''analisi distrib. Controlla la cartella.');
end

% Colori standard
colorGreedy = [0.13, 0.47, 0.71];
colorCW     = [0.84, 0.37, 0.05];

% =========================================================================
% 1. PARSING E LETTURA DATI
% =========================================================================
VarTypes = {'string','double','string','double','double','double','double','double','double','double','double'};
VarNames = {'Modalita','Gamma','Algoritmo','F_insoddis','F_viaggio','F_logistica','F_tot','Sat_Fisica','Sat_Tempo','Vehicles','N_Serviti'};
ResTable = table('Size', [0, length(VarNames)], 'VariableTypes', VarTypes, 'VariableNames', VarNames);

for i = 1:length(files)
    filename = files(i).name;

    mod_str   = regexp(filename, 'distrib_(.+)_gamma',  'tokens');
    gamma_str = regexp(filename, 'gamma(\d+\.\d+)',     'tokens');

    if isempty(mod_str) || isempty(gamma_str), continue; end

    mod_val   = string(mod_str{1}{1});
    gamma_val = str2double(gamma_str{1}{1});

    filepath = fullfile(dataDir, filename);
    T        = readtable(filepath, detectImportOptions(filepath));
    T_best   = T(T.is_best == 1, :);

    algos = {'greedy', 'clarke_wright'};
    for a = 1:length(algos)
        T_algo = T_best(strcmp(T_best.algoritmo, algos{a}), :);
        if isempty(T_algo), continue; end

        f_ins  = sum(T_algo.F_insoddis);
        f_via  = sum(T_algo.F_viaggio);
        f_log  = sum(T_algo.F_costo_fisso + T_algo.F_viaggio + T_algo.F_lavoro);
        f_tot  = sum(T_algo.F_total);
        s_fis  = mean(T_algo.sat_fisica);
        s_tem  = mean(T_algo.sat_tempo);
        v_tot  = sum(T_algo.n_vehicles);
        n_serv = sum(T_algo.n_utenti_serviti);

        ResTable = [ResTable; {mod_val, gamma_val, algos{a}, f_ins, f_via, f_log, f_tot, s_fis, s_tem, v_tot, n_serv}];
    end
end

if height(ResTable) == 0
    error('Nessun dato valido estratto. Controlla i nomi file e le colonne CSV.');
end

ResTable.Modalita = categorical(ResTable.Modalita);
modalita = categories(ResTable.Modalita);   % es. {'cluster', 'uniform'}
n_mod    = length(modalita);
g_unique = unique(ResTable.Gamma);
n_g      = length(g_unique);

gamma_styles = {'-o', '-s', '-^'};

% Gamma di riferimento per i pannelli a singola politica
gv_ref = 0.50;
[~, idx_ref] = min(abs(g_unique - gv_ref));
gv_ref = g_unique(idx_ref);

% =========================================================================
% GRAFICO 1: F_viaggio e Veicoli vs Modalità — entrambi gli algoritmi
% Domanda chiave: il cluster riduce il costo di viaggio? Di quanto?
% =========================================================================
fig1 = figure('Name', 'Costo Viaggio e Flotta vs Modalita', 'Position', [50, 50, 1000, 420]);
sgtitle('B3 — Impatto della Distribuzione Spaziale su Costi di Viaggio e Flotta', 'FontWeight', 'bold');

subplot(1, 2, 1); hold on;
for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Modalita');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Modalita');
    plot(subG.Modalita, subG.F_viaggio, gamma_styles{g}, 'Color', colorGreedy, 'LineWidth', 1.6, ...
        'MarkerFaceColor', colorGreedy, 'DisplayName', sprintf('Greedy \\gamma=%.2f', gv));
    plot(subC.Modalita, subC.F_viaggio, gamma_styles{g}, 'Color', colorCW,     'LineWidth', 1.6, ...
        'MarkerFaceColor', colorCW,     'DisplayName', sprintf('CW \\gamma=%.2f',     gv));
end
ylabel('F_{viaggio} (€)');
title('Costo di Viaggio vs Distribuzione');
legend('Location', 'best', 'NumColumns', 2, 'FontSize', 7);
grid on; box on;

subplot(1, 2, 2); hold on;
for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Modalita');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Modalita');
    if g == 1
        dnG = 'Greedy'; dnC = 'CW';
    else
        dnG = ''; dnC = '';
    end
    plot(subG.Modalita, subG.Vehicles, gamma_styles{g}, 'Color', colorGreedy, 'LineWidth', 1.6, ...
        'MarkerFaceColor', colorGreedy, 'DisplayName', dnG);
    plot(subC.Modalita, subC.Vehicles, gamma_styles{g}, 'Color', colorCW,     'LineWidth', 1.6, ...
        'MarkerFaceColor', colorCW,     'DisplayName', dnC);
end
ylabel('Veicoli totali (n)');
title('Flotta Utilizzata vs Distribuzione');
legend('Location', 'best'); grid on; box on;

% =========================================================================
% GRAFICO 2: Scomposizione F_tot per modalità (gamma = 0.50)
% Isola quanto della differenza tra uniform e cluster è viaggio vs insoddisfazione
% =========================================================================
T_gref = ResTable(ResTable.Gamma == gv_ref, :);

fig2 = figure('Name', 'Scomposizione F_tot per Modalita', 'Position', [100, 100, 950, 500]);
sgtitle(sprintf('B3 — Scomposizione F_{tot} per Distribuzione Spaziale (\\gamma = %.2f)', gv_ref), 'FontWeight', 'bold');

algo_keys   = {'greedy', 'clarke_wright'};
algo_titles = {'Greedy', 'Clarke-Wright'};

for a = 1:2
    subplot(1, 2, a);
    sub_T = sortrows(T_gref(strcmp(T_gref.Algoritmo, algo_keys{a}), :), 'Modalita');
    yData = [sub_T.F_insoddis, sub_T.F_logistica];
    b = bar(sub_T.Modalita, yData, 'stacked');
    b(1).FaceColor = [0.47, 0.67, 0.19];
    b(2).FaceColor = [0.30, 0.30, 0.30];
    title(algo_titles{a}, 'FontWeight', 'bold');
    ylabel('F_{tot} (valore assoluto)');
    legend('F_{insoddis} \times k_{scala}', 'F_{logistica}', 'Location', 'best');
    grid on; box on;
end

% =========================================================================
% GRAFICO 3: Saturazione Fisica e Temporale vs Modalità (pannello 2×n_g)
% =========================================================================
fig3 = figure('Name', 'Saturazione vs Modalita', 'Position', [150, 150, 1050, 620]);
sgtitle('B3 — Saturazione Fisica e Temporale: Uniforme vs Cluster', 'FontWeight', 'bold');

for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Modalita');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Modalita');

    % Riga 1 — Saturazione Fisica
    subplot(2, n_g, g);
    yFis = [subG.Sat_Fisica, subC.Sat_Fisica];
    b = bar(categorical(modalita), yFis, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f — Fisica', gv), 'FontWeight', 'bold');
    ylabel('Saturazione fisica (%)'); ylim([0 100]);
    grid on; box on;
    if g == 1, legend('Greedy', 'CW', 'Location', 'northwest'); end

    % Riga 2 — Saturazione Temporale
    subplot(2, n_g, g + n_g);
    yTem = [subG.Sat_Tempo, subC.Sat_Tempo];
    b = bar(categorical(modalita), yTem, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f — Temporale', gv), 'FontWeight', 'bold');
    ylabel('Saturazione temporale (%)'); ylim([0 100]);
    grid on; box on;
end

% =========================================================================
% GRAFICO 4: Gap relativo Greedy–CW per Modalità
% =========================================================================
fig4 = figure('Name', 'Gap Greedy vs CW per Modalita', 'Position', [200, 200, 700, 420]);
sgtitle('B3 — Gap Relativo F_{tot}: Greedy vs Clarke-Wright per Distribuzione', 'FontWeight', 'bold');
hold on;

for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Modalita');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Modalita');

    if height(subG) ~= height(subC) || height(subG) == 0, continue; end

    gap_pct = (subG.F_tot - subC.F_tot) ./ min(subG.F_tot, subC.F_tot) * 100;
    plot(subG.Modalita, gap_pct, gamma_styles{g}, 'Color', [0.2 0.2 0.2], 'LineWidth', 2, ...
        'MarkerFaceColor', [0.5 0.5 0.5], 'DisplayName', sprintf('\\gamma = %.2f', gv));
end

yline(0, '--k', 'LineWidth', 1, 'DisplayName', 'Pareggio');
ylabel('Gap % = (F_{Greedy} - F_{CW}) / min \times 100');
title('Il cluster amplifica o riduce il vantaggio di CW?');
legend('Location', 'best'); grid on; box on;