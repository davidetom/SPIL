% =========================================================================
% BENCH 3: Analisi Distribuzione (Uniforme vs Cluster)
% =========================================================================
clear; clc; close all;

dataDir = 'risultati_csv';
files = dir(fullfile(dataDir, '*_distrib_*_gamma*.csv'));

if isempty(files)
    error('Nessun file trovato per l''analisi distrib. Controlla la cartella.');
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
modalita = categories(ResTable.Modalita);
g_unique = unique(ResTable.Gamma);
n_g      = length(g_unique);

gv_ref = 0.50;
[~, idx_ref] = min(abs(g_unique - gv_ref));
gv_ref = g_unique(idx_ref);

% =========================================================================
% GRAFICO 1: F_viaggio e Veicoli vs Modalità — colore = gamma, marker = algoritmo
% =========================================================================
fig1 = figure('Name', 'Costo Viaggio e Flotta vs Modalita', 'Position', [50, 50, 1000, 460]);
sgtitle('B3 — Impatto Distribuzione Spaziale su Costi di Viaggio e Flotta', ...
        'FontWeight', 'bold', 'FontSize', 11);

subplot(1, 2, 1); hold on;
for g = 1:n_g
    gv   = g_unique(g);
    col  = gamma_colors(mod(g-1, size(gamma_colors,1)) + 1, :);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Modalita');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Modalita');
    plot(subG.Modalita, subG.F_viaggio, '-o', 'Color', col, 'LineWidth', 1.6, ...
         'MarkerFaceColor', col, 'MarkerSize', 7, ...
         'DisplayName', sprintf('Greedy  \\gamma=%.2f', gv));
    plot(subC.Modalita, subC.F_viaggio, '-s', 'Color', col, 'LineWidth', 1.6, ...
         'MarkerFaceColor', 'w', 'MarkerEdgeColor', col, 'MarkerSize', 7, ...
         'DisplayName', sprintf('CW  \\gamma=%.2f', gv));
end
ylabel('F_{viaggio} (€)'); title('Costo di Viaggio');
legend('Location', 'northwest', 'NumColumns', 2, 'FontSize', 7);
grid on; box on;

subplot(1, 2, 2); hold on;
for g = 1:n_g
    gv   = g_unique(g);
    col  = gamma_colors(mod(g-1, size(gamma_colors,1)) + 1, :);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Modalita');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Modalita');
    if g == 1
        hvG = 'on'; hvC = 'on'; dnG = 'Greedy'; dnC = 'CW';
    else
        hvG = 'off'; hvC = 'off'; dnG = ''; dnC = '';
    end
    plot(subG.Modalita, subG.Vehicles, '-o', 'Color', col, 'LineWidth', 1.6, ...
         'MarkerFaceColor', col, 'MarkerSize', 7, ...
         'DisplayName', dnG, 'HandleVisibility', hvG);
    plot(subC.Modalita, subC.Vehicles, '-s', 'Color', col, 'LineWidth', 1.6, ...
         'MarkerFaceColor', 'w', 'MarkerEdgeColor', col, 'MarkerSize', 7, ...
         'DisplayName', dnC, 'HandleVisibility', hvC);
end
ylabel('Veicoli totali (n)'); title('Flotta Utilizzata');
legend('Location', 'northwest'); grid on; box on;

exportgraphics(fig1, fullfile(outDir, 'Costi di Viaggio e Flotta.png'), 'Resolution', 300);

% =========================================================================
% GRAFICO 2: Scomposizione F_tot per modalità (gamma = 0.50)
% =========================================================================
T_gref = ResTable(ResTable.Gamma == gv_ref, :);

fig2 = figure('Name', 'Scomposizione F_tot per Modalita', 'Position', [100, 100, 950, 520]);
sgtitle(sprintf('B3 — Scomposizione F_{tot} per Distribuzione Spaziale  (\\gamma = %.2f)', gv_ref), ...
        'FontWeight', 'bold', 'FontSize', 11);

algo_keys   = {'greedy', 'clarke_wright'};
algo_titles = {'Greedy', 'Clarke-Wright'};

for a = 1:2
    subplot(1, 2, a);
    sub_T = sortrows(T_gref(strcmp(T_gref.Algoritmo, algo_keys{a}), :), 'Modalita');
    yData = [sub_T.F_logistica, sub_T.F_insoddis];
    b = bar(sub_T.Modalita, yData, 'stacked');
    b(1).FaceColor = [0.30, 0.30, 0.30];
    b(2).FaceColor = [0.47, 0.67, 0.19];
    title(algo_titles{a}, 'FontWeight', 'bold');
    ylabel('F_{tot} (valore assoluto)');
    legend('F_{logistica}', 'F_{insoddis} \times k_{scala}', 'Location', 'northwest');
    grid on; box on;
end

exportgraphics(fig2, fullfile(outDir, 'Ftot vs Distribuzione Spaziale.png'), 'Resolution', 300);

% =========================================================================
% GRAFICO 3: Saturazione Fisica e Temporale vs Modalità (pannello 2×n_g)
% =========================================================================
fig3 = figure('Name', 'Saturazione vs Modalita', 'Position', [150, 150, 1100, 660]);
sgtitle('B3 — Saturazione Fisica (riga 1) e Temporale (riga 2): Uniforme vs Cluster', ...
        'FontWeight', 'bold', 'FontSize', 11);

for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Modalita');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Modalita');

    subplot(2, n_g, g);
    yFis = [subG.Sat_Fisica, subC.Sat_Fisica];
    b = bar(categorical(modalita), yFis, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f', gv), 'FontWeight', 'bold', 'FontSize', 10);
    ylabel('Fisica (%)'); ylim([0 100]); grid on; box on;
    if g == 1, legend('Greedy', 'CW', 'Location', 'northwest'); end

    subplot(2, n_g, g + n_g);
    yTem = [subG.Sat_Tempo, subC.Sat_Tempo];
    b = bar(categorical(modalita), yTem, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f', gv), 'FontWeight', 'bold', 'FontSize', 10);
    ylabel('Temporale (%)'); ylim([0 100]); grid on; box on;
end

exportgraphics(fig3, fullfile(outDir, 'Saturazione Fisica e Temporale.png'), 'Resolution', 300);

% =========================================================================
% GRAFICO 4: Gap relativo Greedy–CW per Modalità
% =========================================================================
fig4 = figure('Name', 'Gap Greedy vs CW per Modalita', 'Position', [200, 200, 700, 460]);
sgtitle('B3 — Gap Relativo F_{tot}: Greedy vs CW per Distribuzione', ...
        'FontWeight', 'bold', 'FontSize', 11);
hold on;

for g = 1:n_g
    gv   = g_unique(g);
    col  = gamma_colors(mod(g-1, size(gamma_colors,1)) + 1, :);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Modalita');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Modalita');

    if height(subG) ~= height(subC) || height(subG) == 0, continue; end

    gap_pct = (subG.F_tot - subC.F_tot) ./ min(subG.F_tot, subC.F_tot) * 100;
    plot(subG.Modalita, gap_pct, '-o', 'Color', col, 'LineWidth', 2, ...
         'MarkerFaceColor', col, 'MarkerSize', 7, ...
         'DisplayName', sprintf('\\gamma = %.2f', gv));
end

yline(0, '--k', 'LineWidth', 1, 'DisplayName', 'Pareggio');
ylabel('Gap %  =  (F_{Greedy} - F_{CW}) / min \times 100');
legend('Location', 'best'); grid on; box on;

exportgraphics(fig4, fullfile(outDir, 'Gap Prestazionale tra Greedy e CW.png'), 'Resolution', 300);