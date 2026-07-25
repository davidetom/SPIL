% =========================================================================
% BENCH 4: Analisi Mappa Reale (Fabriano)
% =========================================================================
clear; clc; close all;

dataDir = 'risultati_csv';
% Cerca i file generati dall'analisi mappa_reale
files = dir(fullfile(dataDir, '*_mappa_reale_gamma*.csv'));

if isempty(files)
    error('Nessun file trovato per l''analisi mappa reale. Controlla la cartella.');
end

VarTypes = {'double', 'string', 'double', 'double', 'double', 'double', 'double', 'double'};
VarNames = {'Gamma', 'Algoritmo', 'F_insoddis', 'F_logistica', 'F_tot', 'Sat_Fisica', 'Sat_Tempo', 'Vehicles'};
ResTable = table('Size', [0, length(VarNames)], 'VariableTypes', VarTypes, 'VariableNames', VarNames);

% 1. PARSING E LETTURA DATI
for i = 1:length(files)
    filename = files(i).name;
    
    % Estraiamo solo il gamma, essendo un'istanza singola
    gamma_str = regexp(filename, 'gamma(\d+\.\d+)', 'tokens');
    if isempty(gamma_str), continue; end
    
    gamma_val = str2double(gamma_str{1}{1});
    
    filepath = fullfile(dataDir, filename);
    T = readtable(filepath, detectImportOptions(filepath));
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
        v_tot = sum(T_algo.n_vehicles);
        
        ResTable = [ResTable; {gamma_val, algos{a}, f_ins, f_log, f_tot, s_fis, s_tem, v_tot}];
    end
end

% Ordinamento e creazione label personalizzate per l'asse X
ResTable = sortrows(ResTable, {'Gamma', 'Algoritmo'});
gamma_unique = unique(ResTable.Gamma);
gamma_labels = categorical(gamma_unique);
% Rinomina le categorie per maggior chiarezza
gamma_labels = renamecats(gamma_labels, {'0.1', '0.5', '0.9'}, ...
    {'Pro-Azienda (\gamma=0.10)', 'Neutro (\gamma=0.50)', 'Pro-Cittadino (\gamma=0.90)'});

colorGreedy = [0.0, 0.45, 0.74]; 
colorCW = [0.85, 0.33, 0.10]; 

% =========================================================================
% GRAFICO 1: Transizione Politiche (Scomposizione FO)
% =========================================================================
figure('Name', 'Transizione Politiche (Reale)', 'Position', [100, 100, 900, 500]);
sgtitle('Mappa Reale: Scomposizione Funzione Obiettivo per Politica');

algos = {'greedy', 'clarke_wright'};
titles = {'Greedy', 'Clarke-Wright'};
for a = 1:2
    subplot(1, 2, a);
    sub_T = ResTable(strcmp(ResTable.Algoritmo, algos{a}), :);
    
    yData = [sub_T.F_insoddis, sub_T.F_logistica];
    b = bar(gamma_labels, yData, 'stacked');
    b(1).FaceColor = [0.47, 0.67, 0.19]; % Verde
    b(2).FaceColor = [0.30, 0.30, 0.30]; % Grigio
    
    title(titles{a}); ylabel('Costo FO (Assoluto)'); grid on;
    if a == 1, legend('F_{insoddis} (Scalata)', 'Costi Logistici', 'Location', 'northwest'); end
end

% =========================================================================
% GRAFICO 2: Saturazione Camion (Crollo al Gamma 0.90)
% =========================================================================
figure('Name', 'Saturazioni (Reale)', 'Position', [150, 150, 900, 400]);
sgtitle('Mappa Reale: Collasso della Saturazione verso politiche Pro-Cittadino');

subplot(1, 2, 1);
yDataFis = reshape(ResTable.Sat_Fisica, 2, [])'; 
b = bar(gamma_labels, yDataFis, 'grouped');
b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
title('Saturazione Fisica Media'); ylabel('Capacità sfruttata (%)'); ylim([0 100]); grid on;
legend('Greedy', 'CW', 'Location', 'southwest');

subplot(1, 2, 2);
yDataTem = reshape(ResTable.Sat_Tempo, 2, [])';
b = bar(gamma_labels, yDataTem, 'grouped');
b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
title('Saturazione Temporale Media'); ylabel('Turno sfruttato (%)'); ylim([0 100]); grid on;

% =========================================================================
% GRAFICO 3: Esplosione flotta veicoli
% =========================================================================
figure('Name', 'Flotta Veicoli (Reale)', 'Position', [200, 200, 600, 450]);

hold on;
sub_G = ResTable(strcmp(ResTable.Algoritmo, 'greedy'), :);
sub_C = ResTable(strcmp(ResTable.Algoritmo, 'clarke_wright'), :);

plot(gamma_labels, sub_G.Vehicles, '-o', 'Color', colorGreedy, 'LineWidth', 2, 'MarkerSize', 8, 'DisplayName', 'Greedy');
plot(gamma_labels, sub_C.Vehicles, '-s', 'Color', colorCW, 'LineWidth', 2, 'MarkerSize', 8, 'DisplayName', 'Clarke-Wright');

title('Mappa Reale: Aumento dei Camion Necessari');
ylabel('Numero Totale di Veicoli Utilizzati');
grid on; legend('Location', 'northwest');