% =========================================================================
% BENCH 2: Analisi Tipologia (Scenari Residenziali, Villette, etc.)
% =========================================================================
clear; clc; close all;

dataDir = 'risultati_csv';
files = dir(fullfile(dataDir, '*_tipo_*_gamma*.csv'));

if isempty(files)
    error('Nessun file trovato per l''analisi tipo. Controlla la cartella.');
end

VarTypes = {'string', 'double', 'string', 'double', 'double', 'double', 'double', 'double'};
VarNames = {'Scenario', 'Gamma', 'Algoritmo', 'F_insoddis', 'F_logistica', 'F_tot', 'Sat_Fisica', 'Sat_Tempo'};
ResTable = table('Size', [0, length(VarNames)], 'VariableTypes', VarTypes, 'VariableNames', VarNames);

% 1. PARSING E LETTURA DATI
for i = 1:length(files)
    filename = files(i).name;
    
    % Regex robusta: prende tutto tra 'tipo_' e '_gamma'
    scen_str = regexp(filename, 'tipo_(.*)_gamma', 'tokens');
    gamma_str = regexp(filename, 'gamma([\d.]+)', 'tokens');
    
    if isempty(scen_str) || isempty(gamma_str), continue; end
    
    scenario_val = string(strrep(scen_str{1}{1}, '_', ' ')); % Rimuove underscore per i plot
    gamma_val = str2double(gamma_str{1}{1});
    
    filepath = fullfile(dataDir, filename);
    opts = detectImportOptions(filepath);
    T = readtable(filepath, opts);
    T_best = T(T.is_best == 1, :);
    
    algos = {'greedy', 'clarke_wright'};
    for a = 1:length(algos)
        T_algo = T_best(strcmp(T_best.algoritmo, algos{a}), :);
        if isempty(T_algo), continue; end
        
        f_ins = sum(T_algo.F_insoddis);
        f_log = sum(T_algo.F_costo_fisso + T_algo.F_viaggio + T_algo.F_lavoro);
        f_tot = sum(T_algo.F_total);
        s_fis = mean(T_algo.sat_fisica);
        s_tem = mean(T_algo.sat_tempo);
        
        ResTable = [ResTable; {scenario_val, gamma_val, algos{a}, f_ins, f_log, f_tot, s_fis, s_tem}];
    end
end

ResTable.Scenario = categorical(ResTable.Scenario);
scenarios = categories(ResTable.Scenario);
gamma_unique = unique(ResTable.Gamma);

colorGreedy = [0.0, 0.45, 0.74]; 
colorCW = [0.85, 0.33, 0.10];    

% =========================================================================
% GRAFICO 1: Scomposizione per Scenario (Fisso a Gamma 0.50 per pulizia)
% =========================================================================
gamma_target = 0.50; 
T_g50 = ResTable(ResTable.Gamma == gamma_target, :);

figure('Name', 'Scomposizione per Tipologia', 'Position', [100, 100, 800, 500]);
sgtitle(sprintf('Scomposizione Costi vs Tipologia (\\gamma = %.2f)', gamma_target));

algos = {'greedy', 'clarke_wright'};
titles = {'Greedy', 'Clarke-Wright'};
for a = 1:2
    subplot(1, 2, a);
    sub_T = T_g50(strcmp(T_g50.Algoritmo, algos{a}), :);
    
    yData = [sub_T.F_insoddis, sub_T.F_logistica];
    b = bar(sub_T.Scenario, yData, 'stacked');
    b(1).FaceColor = [0.47, 0.67, 0.19]; 
    b(2).FaceColor = [0.30, 0.30, 0.30]; 
    
    title(titles{a}); ylabel('Valore Assoluto'); grid on;
    xtickangle(45);
    if a == 1, legend('F_{insoddis}', 'Costi Logistici'); end
end

% =========================================================================
% GRAFICO 2: Saturazione vs Tipologia
% =========================================================================
figure('Name', 'Saturazione vs Tipologia', 'Position', [150, 150, 1000, 600]);
sgtitle('Saturazione Fisica e Temporale vs Tipologia Utenza');

for g = 1:length(gamma_unique)
    g_val = gamma_unique(g);
    sub_T = sortrows(ResTable(ResTable.Gamma == g_val, :), {'Scenario', 'Algoritmo'});
    
    subplot(2, 3, g);
    yDataFis = reshape(sub_T.Sat_Fisica, 2, [])'; 
    b = bar(scenarios, yDataFis, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f (Fisica)', g_val));
    ylabel('Sat. Fisica (%)'); ylim([0 100]); grid on; xtickangle(45);
    
    subplot(2, 3, g+3);
    yDataTem = reshape(sub_T.Sat_Tempo, 2, [])';
    b = bar(scenarios, yDataTem, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f (Tempo)', g_val));
    ylabel('Sat. Tempo (%)'); ylim([0 100]); grid on; xtickangle(45);
    
    if g == 1, legend('Greedy', 'CW'); end
end

% =========================================================================
% GRAFICO 3: Costi vs Tipologia
% =========================================================================
figure('Name', 'Costi vs Tipologia', 'Position', [200, 200, 800, 400]);

hold on;
for g = 1:length(gamma_unique)
    sub_C = sortrows(ResTable(ResTable.Gamma == gamma_unique(g) & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Scenario');
    plot(scenarios, sub_C.F_tot, '-o', 'LineWidth', 2, 'DisplayName', sprintf('CW (\\gamma=%.2f)', gamma_unique(g)));
end
title('Funzione Obiettivo Totale (CW) vs Tipologia');
ylabel('F_{tot}'); grid on; legend('Location', 'best');