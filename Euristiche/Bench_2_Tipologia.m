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

% =========================================================================
% 1. PARSING E LETTURA DATI
% =========================================================================
VarTypes = {'string','double','string','double','double','double','double','double','double'};
VarNames = {'Scenario','Gamma','Algoritmo','F_insoddis','F_logistica','F_tot','Sat_Fisica','Sat_Tempo','N_Serviti'};
ResTable = table('Size', [0, length(VarNames)], 'VariableTypes', VarTypes, 'VariableNames', VarNames);

for i = 1:length(files)
    filename = files(i).name;

    % Regex: tutto tra 'tipo_' e '_gamma', poi gamma senza punto finale
    scen_str  = regexp(filename, 'tipo_(.+)_gamma',  'tokens');
    gamma_str = regexp(filename, 'gamma(\d+\.\d+)', 'tokens');

    if isempty(scen_str) || isempty(gamma_str), continue; end

    % Sostituisce underscore con spazio per le etichette degli assi
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

% Gamma di riferimento per i grafici a singolo pannello
gv_ref = 0.50;
[~, idx_ref] = min(abs(g_unique - gv_ref));
gv_ref = g_unique(idx_ref);

% =========================================================================
% GRAFICO 1: Scomposizione F_tot per Tipologia (gamma = 0.50)
% Mostra quanto pesa la componente utente vs logistica per ogni scenario
% =========================================================================
T_gref = ResTable(ResTable.Gamma == gv_ref, :);

fig1 = figure('Name', 'Scomposizione per Tipologia', 'Position', [50, 50, 950, 500]);
sgtitle(sprintf('B2 — Scomposizione F_{tot} per Tipologia (\\gamma = %.2f)', gv_ref), 'FontWeight', 'bold');

algo_keys   = {'greedy', 'clarke_wright'};
algo_titles = {'Greedy', 'Clarke-Wright'};

for a = 1:2
    subplot(1, 2, a);
    sub_T = sortrows(T_gref(strcmp(T_gref.Algoritmo, algo_keys{a}), :), 'Scenario');
    yData = [sub_T.F_insoddis, sub_T.F_logistica];
    b = bar(sub_T.Scenario, yData, 'stacked');
    b(1).FaceColor = [0.47, 0.67, 0.19];  % Verde — componente utente
    b(2).FaceColor = [0.30, 0.30, 0.30];  % Grigio — componente azienda
    title(algo_titles{a}, 'FontWeight', 'bold');
    ylabel('F_{tot} (valore assoluto)');
    legend('F_{insoddis} \times k_{scala}', 'F_{logistica}', 'Location', 'best');
    grid on; box on; xtickangle(35);
end

% =========================================================================
% GRAFICO 2: F_tot vs Tipologia — entrambi gli algoritmi, tutti i gamma
% =========================================================================
fig2 = figure('Name', 'F_tot vs Tipologia', 'Position', [100, 100, 950, 420]);
sgtitle('B2 — Funzione Obiettivo vs Tipologia', 'FontWeight', 'bold');

gamma_styles = {'-o', '-s', '-^'};

subplot(1, 2, 1); hold on;
for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Scenario');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Scenario');
    plot(subG.Scenario, subG.F_tot, gamma_styles{g}, 'Color', colorGreedy, 'LineWidth', 1.6, ...
        'MarkerFaceColor', colorGreedy, 'DisplayName', sprintf('Greedy \\gamma=%.2f', gv));
    plot(subC.Scenario, subC.F_tot, gamma_styles{g}, 'Color', colorCW,     'LineWidth', 1.6, ...
        'MarkerFaceColor', colorCW,     'DisplayName', sprintf('CW \\gamma=%.2f',     gv));
end
ylabel('F_{tot}'); title('F_{tot} per tipologia e \gamma');
legend('Location', 'best', 'NumColumns', 2, 'FontSize', 7);
grid on; box on; xtickangle(35);

% F_insoddis isolata — rivela quanto conta il mix utenza indipendentemente dal routing
subplot(1, 2, 2); hold on;
for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Scenario');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Scenario');
    if g == 1
        dnG = 'Greedy'; dnC = 'CW';
    else
        dnG = ''; dnC = '';
    end
    plot(subG.Scenario, subG.F_insoddis, gamma_styles{g}, 'Color', colorGreedy, 'LineWidth', 1.6, ...
        'MarkerFaceColor', colorGreedy, 'DisplayName', dnG);
    plot(subC.Scenario, subC.F_insoddis, gamma_styles{g}, 'Color', colorCW,     'LineWidth', 1.6, ...
        'MarkerFaceColor', colorCW,     'DisplayName', dnC);
end
ylabel('F_{insoddis} (scalata)');
title('Insoddisfazione per tipologia e \gamma');
legend('Location', 'best'); grid on; box on; xtickangle(35);

% =========================================================================
% GRAFICO 3: Saturazione Fisica e Temporale vs Tipologia (pannello 2×n_g)
% =========================================================================
fig3 = figure('Name', 'Saturazione vs Tipologia', 'Position', [150, 150, 1050, 620]);
sgtitle('B2 — Saturazione Fisica e Temporale vs Tipologia Utenza', 'FontWeight', 'bold');

for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Scenario');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Scenario');

    % Riga 1 — Saturazione Fisica
    subplot(2, n_g, g);
    yFis = [subG.Sat_Fisica, subC.Sat_Fisica];
    b = bar(categorical(scenarios), yFis, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f — Fisica', gv), 'FontWeight', 'bold');
    ylabel('Saturazione fisica (%)'); ylim([0 100]);
    grid on; box on; xtickangle(35);
    if g == 1, legend('Greedy', 'CW', 'Location', 'northwest'); end

    % Riga 2 — Saturazione Temporale
    subplot(2, n_g, g + n_g);
    yTem = [subG.Sat_Tempo, subC.Sat_Tempo];
    b = bar(categorical(scenarios), yTem, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f — Temporale', gv), 'FontWeight', 'bold');
    ylabel('Saturazione temporale (%)'); ylim([0 100]);
    grid on; box on; xtickangle(35);
end

% =========================================================================
% GRAFICO 4: Gap relativo Greedy–CW per Tipologia
% =========================================================================
fig4 = figure('Name', 'Gap Greedy vs CW per Tipologia', 'Position', [200, 200, 750, 420]);
sgtitle('B2 — Gap Relativo F_{tot}: Greedy vs Clarke-Wright per Tipologia', 'FontWeight', 'bold');
hold on;

for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'Scenario');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Scenario');

    if height(subG) ~= height(subC) || height(subG) == 0, continue; end

    gap_pct = (subG.F_tot - subC.F_tot) ./ min(subG.F_tot, subC.F_tot) * 100;
    plot(subG.Scenario, gap_pct, gamma_styles{g}, 'Color', [0.2 0.2 0.2], 'LineWidth', 2, ...
        'MarkerFaceColor', [0.5 0.5 0.5], 'DisplayName', sprintf('\\gamma = %.2f', gv));
end

yline(0, '--k', 'LineWidth', 1, 'DisplayName', 'Pareggio');
ylabel('Gap % = (F_{Greedy} - F_{CW}) / min \times 100');
title('Gap positivo → CW migliore; negativo → Greedy migliore');
legend('Location', 'best'); grid on; box on; xtickangle(35);