% =========================================================================
% BENCH 3: Analisi Distribuzione (Uniforme vs Cluster)
% =========================================================================
clear; clc; close all;

dataDir = 'risultati_csv';
files = dir(fullfile(dataDir, '*_distrib_*_gamma*.csv'));

if isempty(files)
    error('Nessun file trovato per l''analisi distrib. Controlla la cartella.');
end

VarTypes = {'string', 'double', 'string', 'double', 'double', 'double', 'double', 'double', 'double'};
VarNames = {'Modalita', 'Gamma', 'Algoritmo', 'F_insoddis', 'F_viaggio', 'F_tot', 'Sat_Fisica', 'Sat_Tempo', 'Vehicles'};
ResTable = table('Size', [0, length(VarNames)], 'VariableTypes', VarTypes, 'VariableNames', VarNames);

% 1. PARSING E LETTURA DATI
for i = 1:length(files)
    filename = files(i).name;
    
    mod_str = regexp(filename, 'distrib_(.*)_gamma', 'tokens');
    gamma_str = regexp(filename, 'gamma([\d.]+)', 'tokens');
    
    if isempty(mod_str) || isempty(gamma_str), continue; end
    
    mod_val = string(mod_str{1}{1}); 
    gamma_val = str2double(gamma_str{1}{1});
    
    filepath = fullfile(dataDir, filename);
    T = readtable(filepath, detectImportOptions(filepath));
    T_best = T(T.is_best == 1, :);
    
    algos = {'greedy', 'clarke_wright'};
    for a = 1:length(algos)
        T_algo = T_best(strcmp(T_best.algoritmo, algos{a}), :);
        if isempty(T_algo), continue; end
        
        f_ins = sum(T_algo.F_insoddis);
        f_via = sum(T_algo.F_viaggio); % Focus sul puro costo di viaggio (distanza)
        f_tot = sum(T_algo.F_total);
        s_fis = mean(T_algo.sat_fisica);
        s_tem = mean(T_algo.sat_tempo);
        v_tot = sum(T_algo.n_vehicles);
        
        ResTable = [ResTable; {mod_val, gamma_val, algos{a}, f_ins, f_via, f_tot, s_fis, s_tem, v_tot}];
    end
end

ResTable.Modalita = categorical(ResTable.Modalita);
modalita = categories(ResTable.Modalita);
gamma_unique = unique(ResTable.Gamma);

colorGreedy = [0.0, 0.45, 0.74]; 
colorCW = [0.85, 0.33, 0.10]; 

% =========================================================================
% GRAFICO 1: Abbattimento dei costi di viaggio (F_viaggio) vs Modalità
% =========================================================================
figure('Name', 'Impatto Cluster sui Viaggi', 'Position', [100, 100, 800, 400]);

subplot(1,2,1); hold on;
for g = 1:length(gamma_unique)
    sub_C = sortrows(ResTable(ResTable.Gamma == gamma_unique(g) & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Modalita');
    plot(modalita, sub_C.F_viaggio, '-o', 'LineWidth', 2, 'DisplayName', sprintf('\\gamma=%.2f', gamma_unique(g)));
end
title('Costo Puro di Viaggio (CW)');
ylabel('F_{viaggio} (Costo \propto Distanza)'); grid on; legend('Location', 'best');

subplot(1,2,2); hold on;
for g = 1:length(gamma_unique)
    sub_C = sortrows(ResTable(ResTable.Gamma == gamma_unique(g) & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'Modalita');
    plot(modalita, sub_C.Vehicles, '-s', 'LineWidth', 2, 'DisplayName', sprintf('\\gamma=%.2f', gamma_unique(g)));
end
title('Numero Veicoli Utilizzati (CW)');
ylabel('Camion (n)'); grid on;

% =========================================================================
% GRAFICO 2 & 3: Saturazioni a confronto
% =========================================================================
figure('Name', 'Saturazioni: Uniforme vs Cluster', 'Position', [150, 150, 1000, 600]);
sgtitle('Come l''aggregazione migliora la Saturazione (Uniforme vs Cluster)');

for g = 1:length(gamma_unique)
    g_val = gamma_unique(g);
    sub_T = sortrows(ResTable(ResTable.Gamma == g_val, :), {'Modalita', 'Algoritmo'});
    
    subplot(2, 3, g);
    yDataFis = reshape(sub_T.Sat_Fisica, 2, [])'; 
    b = bar(modalita, yDataFis, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f (Fisica)', g_val));
    ylabel('Sat. Fisica (%)'); ylim([0 100]); grid on;
    
    subplot(2, 3, g+3);
    yDataTem = reshape(sub_T.Sat_Tempo, 2, [])';
    b = bar(modalita, yDataTem, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f (Tempo)', g_val));
    ylabel('Sat. Tempo (%)'); ylim([0 100]); grid on;
    
    if g == 1, legend('Greedy', 'CW', 'Location', 'northwest'); end
end