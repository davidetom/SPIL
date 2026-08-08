% =========================================================================
% BENCH 4: Analisi Mappa Reale (Fabriano)
% =========================================================================
clear; clc; close all;

dataDir = 'risultati_csv';
files = dir(fullfile(dataDir, '*_mappa_reale_gamma*.csv'));

if isempty(files)
    error('Nessun file trovato per l''analisi mappa reale. Controlla la cartella.');
end

% Colori standard
colorGreedy = [0.13, 0.47, 0.71];
colorCW     = [0.84, 0.37, 0.05];

% =========================================================================
% 1. PARSING E LETTURA DATI
% =========================================================================
VarTypes = {'double','string','double','double','double','double','double','double','double','double'};
VarNames = {'Gamma','Algoritmo','F_insoddis','F_logistica','F_viaggio','F_tot','Sat_Fisica','Sat_Tempo','Vehicles','N_Serviti'};
ResTable = table('Size', [0, length(VarNames)], 'VariableTypes', VarTypes, 'VariableNames', VarNames);

n_users_reale = NaN;  % sarà letto dal primo CSV valido

for i = 1:length(files)
    filename = files(i).name;

    gamma_str = regexp(filename, 'gamma(\d+\.\d+)', 'tokens');
    if isempty(gamma_str), continue; end

    gamma_val = str2double(gamma_str{1}{1});

    filepath = fullfile(dataDir, filename);
    T        = readtable(filepath, detectImportOptions(filepath));
    T_best   = T(T.is_best == 1, :);

    % Recupera n_users dalla colonna se presente, altrimenti dal nome file
    if ismember('n_users', T.Properties.VariableNames)
        n_users_reale = T.n_users(1);
    end

    algos = {'greedy', 'clarke_wright'};
    for a = 1:length(algos)
        T_algo = T_best(strcmp(T_best.algoritmo, algos{a}), :);
        if isempty(T_algo), continue; end

        f_ins  = sum(T_algo.F_insoddis);
        f_log  = sum(T_algo.F_costo_fisso + T_algo.F_viaggio + T_algo.F_lavoro);
        f_via  = sum(T_algo.F_viaggio);
        f_tot  = sum(T_algo.F_total);
        s_fis  = mean(T_algo.sat_fisica);
        s_tem  = mean(T_algo.sat_tempo);
        v_tot  = sum(T_algo.n_vehicles);
        n_serv = sum(T_algo.n_utenti_serviti);

        ResTable = [ResTable; {gamma_val, algos{a}, f_ins, f_log, f_via, f_tot, s_fis, s_tem, v_tot, n_serv}];
    end
end

if height(ResTable) == 0
    error('Nessun dato valido estratto. Controlla i nomi file e le colonne CSV.');
end

ResTable = sortrows(ResTable, {'Gamma', 'Algoritmo'});
g_unique = unique(ResTable.Gamma);
n_g      = length(g_unique);

% Costruzione label gamma robusta: rinomina solo le categorie presenti
g_labels_raw = arrayfun(@(x) sprintf('%.2f', x), g_unique, 'UniformOutput', false);
g_cat        = categorical(g_unique);

% Mappa nomi → etichette leggibili solo per i gamma effettivamente presenti
label_map = containers.Map([0.10, 0.50, 0.90], ...
    {'Pro-Azienda (\gamma=0.10)', 'Neutro (\gamma=0.50)', 'Pro-Cittadino (\gamma=0.90)'});

g_labels_pretty = cell(1, n_g);
for g = 1:n_g
    gv = g_unique(g);
    if isKey(label_map, gv)
        g_labels_pretty{g} = label_map(gv);
    else
        g_labels_pretty{g} = sprintf('\\gamma=%.2f', gv);
    end
end

% Sottotabelle per algoritmo (ordinate per Gamma)
subG_all = sortrows(ResTable(strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Gamma');
subC_all = sortrows(ResTable(strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Gamma');

% =========================================================================
% GRAFICO 1: Transizione Politiche — Scomposizione F_tot per politica
% =========================================================================
fig1 = figure('Name', 'Transizione Politiche (Reale)', 'Position', [50, 50, 950, 500]);
sgtitle('B4 — Mappa Reale Fabriano: Scomposizione F_{tot} per Politica', 'FontWeight', 'bold');

algo_keys   = {'greedy', 'clarke_wright'};
algo_tables = {subG_all, subC_all};
algo_titles = {'Greedy', 'Clarke-Wright'};

for a = 1:2
    subplot(1, 2, a);
    sub_T = algo_tables{a};
    yData = [sub_T.F_insoddis, sub_T.F_logistica];
    b = bar(g_cat, yData, 'stacked');
    b(1).FaceColor = [0.47, 0.67, 0.19];
    b(2).FaceColor = [0.30, 0.30, 0.30];
    title(algo_titles{a}, 'FontWeight', 'bold');
    ylabel('F_{tot} (valore assoluto)');
    xlabel('Politica (\gamma)');
    set(gca, 'XTickLabel', g_labels_pretty);
    xtickangle(20);
    legend('F_{insoddis} \times k_{scala}', 'F_{logistica}', 'Location', 'best');
    grid on; box on;
end

% =========================================================================
% GRAFICO 2: Saturazione Fisica e Temporale vs Politica
% =========================================================================
fig2 = figure('Name', 'Saturazioni (Reale)', 'Position', [100, 100, 950, 420]);
sgtitle('B4 — Mappa Reale: Saturazione dei Veicoli al variare della Politica', 'FontWeight', 'bold');

subplot(1, 2, 1);
yFis = [subG_all.Sat_Fisica, subC_all.Sat_Fisica];
b = bar(g_cat, yFis, 'grouped');
b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
title('Saturazione Fisica Media', 'FontWeight', 'bold');
ylabel('Capacità sfruttata (%)'); ylim([0 100]);
set(gca, 'XTickLabel', g_labels_pretty); xtickangle(20);
legend('Greedy', 'CW', 'Location', 'southwest'); grid on; box on;

subplot(1, 2, 2);
yTem = [subG_all.Sat_Tempo, subC_all.Sat_Tempo];
b = bar(g_cat, yTem, 'grouped');
b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
title('Saturazione Temporale Media', 'FontWeight', 'bold');
ylabel('Turno sfruttato (%)'); ylim([0 100]);
set(gca, 'XTickLabel', g_labels_pretty); xtickangle(20);
grid on; box on;

% =========================================================================
% GRAFICO 3: Flotta e Utenti Serviti vs Politica
% =========================================================================
fig3 = figure('Name', 'Flotta e Servizio (Reale)', 'Position', [150, 150, 950, 420]);
sgtitle('B4 — Mappa Reale: Espansione Flotta e Copertura Utenti', 'FontWeight', 'bold');

subplot(1, 2, 1); hold on;
plot(g_cat, subG_all.Vehicles, '-o', 'Color', colorGreedy, 'LineWidth', 2, ...
    'MarkerFaceColor', colorGreedy, 'MarkerSize', 8, 'DisplayName', 'Greedy');
plot(g_cat, subC_all.Vehicles, '-s', 'Color', colorCW,     'LineWidth', 2, ...
    'MarkerFaceColor', colorCW,     'MarkerSize', 8, 'DisplayName', 'Clarke-Wright');
title('Veicoli Totali per Politica', 'FontWeight', 'bold');
ylabel('Numero veicoli (tutti i rifiuti)');
set(gca, 'XTickLabel', g_labels_pretty); xtickangle(20);
legend('Location', 'northwest'); grid on; box on;

subplot(1, 2, 2); hold on;
% Linea teorica: n_users * 5 rifiuti (tutti serviti)
n_rifiuti = 5;
if ~isnan(n_users_reale)
    yline(n_users_reale * n_rifiuti, '--k', 'LineWidth', 1.2, 'DisplayName', 'Teorico (tutti serviti)');
end
plot(g_cat, subG_all.N_Serviti, '-o', 'Color', colorGreedy, 'LineWidth', 2, ...
    'MarkerFaceColor', colorGreedy, 'MarkerSize', 8, 'DisplayName', 'Greedy');
plot(g_cat, subC_all.N_Serviti, '-s', 'Color', colorCW,     'LineWidth', 2, ...
    'MarkerFaceColor', colorCW,     'MarkerSize', 8, 'DisplayName', 'Clarke-Wright');
title('Utenti Serviti per Politica', 'FontWeight', 'bold');
ylabel('n\_utenti\_serviti (somma 5 rifiuti)');
set(gca, 'XTickLabel', g_labels_pretty); xtickangle(20);
legend('Location', 'best'); grid on; box on;

% =========================================================================
% GRAFICO 4: Gap relativo Greedy–CW vs Politica
% =========================================================================
fig4 = figure('Name', 'Gap Greedy vs CW (Reale)', 'Position', [200, 200, 650, 420]);
sgtitle('B4 — Gap Relativo F_{tot}: Greedy vs Clarke-Wright (Mappa Reale)', 'FontWeight', 'bold');
hold on;

if height(subG_all) == height(subC_all) && height(subG_all) > 0
    gap_pct = (subG_all.F_tot - subC_all.F_tot) ./ min(subG_all.F_tot, subC_all.F_tot) * 100;
    bar(g_cat, gap_pct, 'FaceColor', [0.4 0.4 0.4], 'EdgeColor', 'k');
    for g = 1:n_g
        text(g, gap_pct(g) + sign(gap_pct(g)) * 0.3, sprintf('%.1f%%', gap_pct(g)), ...
            'HorizontalAlignment', 'center', 'FontSize', 9, 'FontWeight', 'bold');
    end
end

yline(0, '--k', 'LineWidth', 1);
set(gca, 'XTickLabel', g_labels_pretty); xtickangle(20);
ylabel('Gap % = (F_{Greedy} - F_{CW}) / min \times 100');
title('Gap positivo → CW migliore; negativo → Greedy migliore');
grid on; box on;