% =========================================================================
% BENCH 2: Analisi Tipologia (Scenari Residenziali, Villette, etc.)
% =========================================================================
clear; clc; close all;

dataDir = 'risultati_csv';
files = dir(fullfile(dataDir, '*_tipo_*_gamma*.csv'));

if isempty(files)
    error('Nessun file trovato per l''analisi tipo. Controlla la cartella.');
end

% Colori standard
colorGreedy = [0.13, 0.47, 0.71];
colorCW     = [0.84, 0.37, 0.05];

% Colori per gamma (stesso schema di Bench_1)
gamma_colors = [
    0.20, 0.63, 0.86;   % gamma 0.10 — celeste
    0.50, 0.18, 0.56;   % gamma 0.50 — viola
    0.18, 0.63, 0.33;   % gamma 0.90 — verde
];

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
% 1. PARSING E LETTURA DATI
% =========================================================================
VarTypes = {'string','double','string','double','double','double','double','double','double'};
VarNames = {'Scenario','Gamma','Algoritmo','F_insoddis','F_logistica','F_tot','Sat_Fisica','Sat_Tempo','N_Serviti'};
ResTable = table('Size', [0, length(VarNames)], 'VariableTypes', VarTypes, 'VariableNames', VarNames);

for i = 1:length(files)
    filename = files(i).name;

    scen_str  = regexp(filename, 'tipo_(.+)_gamma',  'tokens');
    gamma_str = regexp(filename, 'gamma(\d+\.\d+)', 'tokens');

    if isempty(scen_str) || isempty(gamma_str), continue; end

    scenario_val = string(strrep(scen_str{1}{1}, '_', ' '));
    gamma_val    = str2double(gamma_str{1}{1});

    filepath = fullfile(dataDir, filename);
    T        = readtable(filepath, detectImportOptions(filepath));
    T_best   = T(T.is_best == 1, :);

    algos = {'greedy', 'clarke_wright'};
    for a = 1:length(algos)
        T_algo = T_best(strcmp(T_best.algoritmo, algos{a}), :);
        if isempty(T_algo), continue; end

        f_ins  = sum(T_algo.F_insoddis);
        f_log  = sum(T_algo.F_costo_fisso + T_algo.F_viaggio + T_algo.F_lavoro);
        f_tot  = sum(T_algo.F_total);
        s_fis  = mean(T_algo.sat_fisica);
        s_tem  = mean(T_algo.sat_tempo);
        n_serv = sum(T_algo.n_utenti_serviti);

        ResTable = [ResTable; {scenario_val, gamma_val, algos{a}, f_ins, f_log, f_tot, s_fis, s_tem, n_serv}];
    end
end

if height(ResTable) == 0
    error('Nessun dato valido estratto. Controlla i nomi file e le colonne CSV.');
end

ResTable.Scenario = categorical(ResTable.Scenario);
scenarios = categories(ResTable.Scenario);
n_scen    = length(scenarios);
g_unique  = unique(ResTable.Gamma);
n_g       = length(g_unique);

gv_ref = 0.50;
[~, idx_ref] = min(abs(g_unique - gv_ref));
gv_ref = g_unique(idx_ref);

% =========================================================================
% GRAFICO 1: Scomposizione F_tot per Tipologia (gamma = 0.50)
% =========================================================================
T_gref = ResTable(ResTable.Gamma == gv_ref, :);

fig1 = figure('Name', 'Scomposizione per Tipologia', 'Position', [50, 50, 950, 520]);
sgtitle(sprintf('B2 — Scomposizione F_{tot} per Tipologia  (\\gamma = %.2f)', gv_ref), ...
        'FontWeight', 'bold', 'FontSize', 11);

algo_keys   = {'greedy', 'clarke_wright'};
algo_titles = {'Greedy', 'Clarke-Wright'};

for a = 1:2
    subplot(1, 2, a);
    sub_T = sortrows(T_gref(strcmp(T_gref.Algoritmo, algo_keys{a}), :), 'Scenario');
    % F_logistica sotto (grigio), F_insoddis sopra (verde)
    yData = [sub_T.F_logistica, sub_T.F_insoddis];
    b = bar(sub_T.Scenario, yData, 'stacked');
    b(1).FaceColor = [0.30, 0.30, 0.30];
    b(2).FaceColor = [0.47, 0.67, 0.19];
    title(algo_titles{a}, 'FontWeight', 'bold');
    ylabel('F_{tot} (valore assoluto)');
    legend('F_{logistica}', 'F_{insoddis} \times k_{scala}', 'Location', 'northeast');
    grid on; box on; xtickangle(35);
end

exportgraphics(fig1, fullfile(outDir, 'ScomposizioneFtot2.png'), 'Resolution', 300);

% =========================================================================
% GRAFICO 2: F_tot e F_insoddis vs Tipologia — colore = gamma, marker = algoritmo
% =========================================================================
fig2 = figure('Name', 'F_tot vs Tipologia', 'Position', [100, 100, 1000, 460]);
sgtitle('B2 — Funzione Obiettivo vs Tipologia', 'FontWeight', 'bold', 'FontSize', 11);

subplot(1, 2, 1); hold on;
for g = 1:n_g
    gv   = g_unique(g);
    col  = gamma_colors(mod(g-1, size(gamma_colors,1)) + 1, :);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Scenario');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Scenario');
    plot(subG.Scenario, subG.F_tot, '-o', 'Color', col, 'LineWidth', 1.6, ...
         'MarkerFaceColor', col, 'MarkerSize', 7, ...
         'DisplayName', sprintf('Greedy  \\gamma=%.2f', gv));
    plot(subC.Scenario, subC.F_tot, '-s', 'Color', col, 'LineWidth', 1.6, ...
         'MarkerFaceColor', 'w', 'MarkerEdgeColor', col, 'MarkerSize', 7, ...
         'DisplayName', sprintf('CW  \\gamma=%.2f', gv));
end
ylabel('F_{tot}'); title('F_{tot} per Tipologia');
legend('Location', 'best', 'NumColumns', 2, 'FontSize', 7);
grid on; box on; xtickangle(35);

subplot(1, 2, 2); hold on;
for g = 1:n_g
    gv   = g_unique(g);
    col  = gamma_colors(mod(g-1, size(gamma_colors,1)) + 1, :);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Scenario');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Scenario');
    if g == 1
        hvG = 'on'; hvC = 'on'; dnG = 'Greedy'; dnC = 'CW';
    else
        hvG = 'off'; hvC = 'off'; dnG = ''; dnC = '';
    end
    plot(subG.Scenario, subG.F_insoddis, '-o', 'Color', col, 'LineWidth', 1.6, ...
         'MarkerFaceColor', col, 'MarkerSize', 7, ...
         'DisplayName', dnG, 'HandleVisibility', hvG);
    plot(subC.Scenario, subC.F_insoddis, '-s', 'Color', col, 'LineWidth', 1.6, ...
         'MarkerFaceColor', 'w', 'MarkerEdgeColor', col, 'MarkerSize', 7, ...
         'DisplayName', dnC, 'HandleVisibility', hvC);
end
ylabel('F_{insoddis} (scalata)');
title('Insoddisfazione per Tipologia');
legend('Location', 'northeast'); grid on; box on; xtickangle(35);

exportgraphics(fig2, fullfile(outDir, 'FtotperTipologia.png'), 'Resolution', 300);

% =========================================================================
% GRAFICO 3: Saturazione Fisica e Temporale vs Tipologia (pannello 2×n_g)
% =========================================================================
fig3 = figure('Name', 'Saturazione vs Tipologia', 'Position', [150, 150, 1100, 660]);
sgtitle('B2 — Saturazione Fisica (riga 1) e Temporale (riga 2) vs Tipologia', ...
        'FontWeight', 'bold', 'FontSize', 11);

ax_leg = [];
ax_leg3 = [];  % terzo subplot (γ=0.90)
for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Scenario');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Scenario');

    ax1 = subplot(2, n_g, g);
    yFis = [subG.Sat_Fisica, subC.Sat_Fisica];
    b = bar(categorical(scenarios), yFis, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f', gv), 'FontWeight', 'bold', 'FontSize', 10);
    ylabel('Fisica (%)'); ylim([0 100]);
    grid on; box on; xtickangle(35);
    if g == 1, ax_leg = ax1; end
    if g == n_g, ax_leg3 = ax1; end  % salva il terzo subplot

    subplot(2, n_g, g + n_g);
    yTem = [subG.Sat_Tempo, subC.Sat_Tempo];
    b = bar(categorical(scenarios), yTem, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f', gv), 'FontWeight', 'bold', 'FontSize', 10);
    ylabel('Temporale (%)'); ylim([0 100]);
    grid on; box on; xtickangle(35);
end

% Legenda ancorata al terzo subplot in alto a destra, dove c'è spazio libero
lgd = legend(ax_leg3, 'Greedy', 'CW', 'Location', 'northeast');
lgd.FontSize = 9;

exportgraphics(fig3, fullfile(outDir, 'SaturazioneFisicaTemporale.png'), 'Resolution', 300);

% =========================================================================
% GRAFICO 4: Gap relativo Greedy–CW per Tipologia
% =========================================================================
fig4 = figure('Name', 'Gap Greedy vs CW per Tipologia', 'Position', [200, 200, 780, 460]);
sgtitle('B2 — Gap Relativo F_{tot}: Greedy vs CW per Tipologia', ...
        'FontWeight', 'bold', 'FontSize', 11);
hold on;

for g = 1:n_g
    gv   = g_unique(g);
    col  = gamma_colors(mod(g-1, size(gamma_colors,1)) + 1, :);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Scenario');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Scenario');

    if height(subG) ~= height(subC) || height(subG) == 0, continue; end

    gap_pct = (subG.F_tot - subC.F_tot) ./ min(subG.F_tot, subC.F_tot) * 100;
    plot(subG.Scenario, gap_pct, '-o', 'Color', col, 'LineWidth', 2, ...
         'MarkerFaceColor', col, 'MarkerSize', 7, ...
         'DisplayName', sprintf('\\gamma = %.2f', gv));
end

yline(0, '--k', 'LineWidth', 1, 'DisplayName', 'Pareggio');
ylabel('Gap %  =  (F_{Greedy} - F_{CW}) / min \times 100');
lg = legend('FontSize', 8, 'Box', 'on');
% Posiziona la legenda in alto a sinistra (coordinate normalizzate figura)
lg.Units    = 'normalized';
lg.Position = [0.13, 0.72, 0.12, 0.18];  % [x, y, larghezza, altezza]
grid on; box on; xtickangle(35);

exportgraphics(fig4, fullfile(outDir, 'GapPrestazionale.png'), 'Resolution', 300);