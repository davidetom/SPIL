% =========================================================================
% BENCH 4: Analisi Mappa Reale (Fabriano)
% =========================================================================
clear; clc; close all;

dataDir = 'risultati_csv';
files = dir(fullfile(dataDir, '*_mappa_reale_gamma*.csv'));

if isempty(files)
    error('Nessun file trovato per l''analisi mappa reale. Controlla la cartella.');
end

colorGreedy = [0.13, 0.47, 0.71];
colorCW     = [0.84, 0.37, 0.05];

gamma_colors = [
    0.20, 0.63, 0.86;
    0.50, 0.18, 0.56;
    0.18, 0.63, 0.33;
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
VarTypes = {'double','string','double','double','double','double','double','double','double'};
VarNames = {'Gamma','Algoritmo','F_insoddis','F_logistica','F_tot','Sat_Fisica','Sat_Tempo','Vehicles','N_Serviti'};
ResTable = table('Size', [0, length(VarNames)], 'VariableTypes', VarTypes, 'VariableNames', VarNames);

n_users_reale = NaN;

for i = 1:length(files)
    filename = files(i).name;

    gamma_str = regexp(filename, 'gamma(\d+\.\d+)', 'tokens');
    if isempty(gamma_str), continue; end

    gamma_val = str2double(gamma_str{1}{1});

    filepath = fullfile(dataDir, filename);
    T        = readtable(filepath, detectImportOptions(filepath));
    T_best   = T(T.is_best == 1, :);

    if ismember('n_users', T.Properties.VariableNames)
        n_users_reale = T.n_users(1);
    end

    algos = {'greedy', 'clarke_wright'};
    for a = 1:length(algos)
        T_algo = T_best(strcmp(T_best.algoritmo, algos{a}), :);
        if isempty(T_algo), continue; end

        f_ins  = sum(T_algo.F_insoddis);
        f_log  = sum(T_algo.F_costo_fisso + T_algo.F_viaggio + T_algo.F_lavoro);
        f_tot  = sum(T_algo.F_total);
        s_fis  = mean(T_algo.sat_fisica);
        s_tem  = mean(T_algo.sat_tempo);
        v_tot  = sum(T_algo.n_vehicles);
        n_serv = sum(T_algo.n_utenti_serviti);

        ResTable = [ResTable; {gamma_val, algos{a}, f_ins, f_log, f_tot, s_fis, s_tem, v_tot, n_serv}];
    end
end

if height(ResTable) == 0
    error('Nessun dato valido estratto. Controlla i nomi file e le colonne CSV.');
end

ResTable = sortrows(ResTable, {'Gamma', 'Algoritmo'});
g_unique = unique(ResTable.Gamma);
n_g      = length(g_unique);
g_cat    = categorical(g_unique);

label_map = containers.Map([0.10, 0.50, 0.90], ...
    {'Pro-Az. (0.10)', 'Neutro (0.50)', 'Pro-Cit. (0.90)'});

g_labels = cell(1, n_g);
for g = 1:n_g
    gv = g_unique(g);
    if isKey(label_map, gv), g_labels{g} = label_map(gv);
    else, g_labels{g} = sprintf('\\gamma=%.2f', gv); end
end

subG_all = sortrows(ResTable(strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Gamma');
subC_all = sortrows(ResTable(strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Gamma');

% =========================================================================
% GRAFICO 1: Scomposizione F_tot per politica
% =========================================================================
fig1 = figure('Name', 'Transizione Politiche (Reale)', 'Position', [50, 50, 950, 520]);
sgtitle('B4 — Fabriano: Scomposizione F_{tot} per Politica', ...
        'FontWeight', 'bold', 'FontSize', 11);

algo_tables = {subG_all, subC_all};
algo_titles = {'Greedy', 'Clarke-Wright'};

for a = 1:2
    subplot(1, 2, a);
    sub_T = algo_tables{a};
    yData = [sub_T.F_logistica, sub_T.F_insoddis];
    b = bar(g_cat, yData, 'stacked');
    b(1).FaceColor = [0.30, 0.30, 0.30];
    b(2).FaceColor = [0.47, 0.67, 0.19];
    title(algo_titles{a}, 'FontWeight', 'bold');
    ylabel('F_{tot} (valore assoluto)');
    xlabel('Politica (\gamma)');
    set(gca, 'XTickLabel', g_labels); xtickangle(20);
    legend('F_{logistica}', 'F_{insoddis} \times k_{scala}', 'Location', 'northeast');
    grid on; box on;
end

exportgraphics(fig1, fullfile(outDir, 'B4 Scomposizione Ftot per Politica.png'), 'Resolution', 300);

% =========================================================================
% GRAFICO 2: Saturazione Fisica e Temporale vs Politica
% =========================================================================
fig2 = figure('Name', 'Saturazioni (Reale)', 'Position', [100, 100, 950, 460]);
sgtitle('B4 — Fabriano: Saturazione dei Veicoli per Politica', ...
        'FontWeight', 'bold', 'FontSize', 11);

subplot(1, 2, 1);
yFis = [subG_all.Sat_Fisica, subC_all.Sat_Fisica];
b = bar(g_cat, yFis, 'grouped');
b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
title('Saturazione Fisica', 'FontWeight', 'bold');
ylabel('Capacità sfruttata (%)'); ylim([0 100]);
set(gca, 'XTickLabel', g_labels); xtickangle(20);
legend('Greedy', 'CW', 'Location', 'northeast'); grid on; box on;

subplot(1, 2, 2);
yTem = [subG_all.Sat_Tempo, subC_all.Sat_Tempo];
b = bar(g_cat, yTem, 'grouped');
b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
title('Saturazione Temporale', 'FontWeight', 'bold');
ylabel('Turno sfruttato (%)'); ylim([0 100]);
set(gca, 'XTickLabel', g_labels); xtickangle(20);
grid on; box on;

exportgraphics(fig2, fullfile(outDir, 'B4 Saturazione Veicoli per Politica.png'), 'Resolution', 300);

% =========================================================================
% GRAFICO 3: Flotta e Utenti Serviti vs Politica
% =========================================================================
fig3 = figure('Name', 'Flotta e Servizio (Reale)', 'Position', [150, 150, 950, 460]);
sgtitle('B4 — Fabriano: Flotta e Copertura Utenti per Politica', ...
        'FontWeight', 'bold', 'FontSize', 11);

subplot(1, 2, 1); hold on;
yVeh = [subG_all.Vehicles, subC_all.Vehicles];
b = bar(g_cat, yVeh, 'grouped');
b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
title('Veicoli Totali', 'FontWeight', 'bold');
ylabel('Numero veicoli (tutti i rifiuti)');
set(gca, 'XTickLabel', g_labels); xtickangle(20);
legend('Greedy', 'CW', 'Location', 'northeast'); grid on; box on;

subplot(1, 2, 2); hold on;
if ~isnan(n_users_reale) && n_users_reale > 0
    ftot_per_u_G = subG_all.F_tot / n_users_reale;
    ftot_per_u_C = subC_all.F_tot / n_users_reale;
else
    ftot_per_u_G = subG_all.F_tot;
    ftot_per_u_C = subC_all.F_tot;
end
plot(g_cat, ftot_per_u_G, '-o', 'Color', colorGreedy, 'LineWidth', 2, ...
     'MarkerFaceColor', colorGreedy, 'MarkerSize', 8, 'DisplayName', 'Greedy');
plot(g_cat, ftot_per_u_C, '-s', 'Color', colorCW, 'LineWidth', 2, ...
     'MarkerFaceColor', 'w', 'MarkerEdgeColor', colorCW, 'MarkerSize', 8, 'DisplayName', 'CW');
title('Costo per Utente', 'FontWeight', 'bold');
ylabel('F_{tot} / N_{utenti}');
set(gca, 'XTickLabel', g_labels); xtickangle(20);
legend('Location', 'northeast'); grid on; box on;

exportgraphics(fig3, fullfile(outDir, 'B4 Flotta e Copertura Utenti per Politica.png'), 'Resolution', 300);

% =========================================================================
% GRAFICO 4: Gap relativo Greedy–CW vs Politica (barre con annotazioni)
% =========================================================================
fig4 = figure('Name', 'Gap Greedy vs CW (Reale)', 'Position', [200, 200, 650, 460]);
sgtitle('B4 — Gap Relativo F_{tot}: Greedy vs CW  (Fabriano)', ...
        'FontWeight', 'bold', 'FontSize', 11);
hold on;

if height(subG_all) == height(subC_all) && height(subG_all) > 0
    gap_pct = (subG_all.F_tot - subC_all.F_tot) ./ min(subG_all.F_tot, subC_all.F_tot) * 100;
    b = bar(g_cat, gap_pct, 'FaceColor', [0.20, 0.40, 0.75], 'EdgeColor', [0.10, 0.20, 0.50], 'LineWidth', 1.2);
    y_range = max(gap_pct) - min([gap_pct; 0]);
    ylim([0, max(gap_pct) + y_range * 0.20]);
    for g = 1:n_g
        text(g, gap_pct(g) + y_range * 0.06, sprintf('%.1f%%', gap_pct(g)), ...
             'HorizontalAlignment', 'center', 'FontSize', 10, 'FontWeight', 'bold');
    end
end

yline(0, '--k', 'LineWidth', 1);
set(gca, 'XTickLabel', g_labels); xtickangle(20);
ylabel('Gap %  =  (F_{Greedy} - F_{CW}) / min \times 100');
grid on; box on;

exportgraphics(fig4, fullfile(outDir, 'B4 Gap Prestazionale tra Greedy e CW.png'), 'Resolution', 300);