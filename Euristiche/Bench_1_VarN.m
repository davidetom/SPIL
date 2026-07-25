% =========================================================================
% BENCH 1: Analisi Variazione N (Utenti Attivi)
% =========================================================================
clear; clc; close all;

dataDir = 'risultati_csv';
files = dir(fullfile(dataDir, '*_varN_*.csv'));

if isempty(files)
    error('Nessun file trovato per l''analisi varN. Controlla la cartella.');
end

% Preallocazione tabella risultati
VarTypes = {'double', 'double', 'string', 'double', 'double', 'double', 'double', 'double', 'double', 'double'};
VarNames = {'N', 'Gamma', 'Algoritmo', 'F_insoddis', 'F_logistica', 'F_tot', 'Sat_Fisica', 'Sat_Tempo', 'Time_sec', 'Vehicles'};
ResTable = table('Size', [0, length(VarNames)], 'VariableTypes', VarTypes, 'VariableNames', VarNames);

% 1. PARSING E LETTURA DATI
for i = 1:length(files)
    filename = files(i).name;
    
    % Estrazione N e Gamma tramite Regex
    n_str = regexp(filename, 'Nact(\d+)', 'tokens');
    gamma_str = regexp(filename, 'gamma(\d+\.\d+)', 'tokens');
    
    if isempty(n_str) || isempty(gamma_str), continue; end
    
    N_val = str2double(n_str{1}{1});
    gamma_val = str2double(gamma_str{1}{1});
    
    % Lettura CSV
    filepath = fullfile(dataDir, filename);
    opts = detectImportOptions(filepath);
    T = readtable(filepath, opts);
    
    % Filtro solo configurazioni migliori
    T_best = T(T.is_best == 1, :);
    
    algos = {'greedy', 'clarke_wright'};
    for a = 1:length(algos)
        algo = algos{a};
        T_algo = T_best(strcmp(T_best.algoritmo, algo), :);
        if isempty(T_algo), continue; end
        
        % Calcolo metriche aggregate per il run (somma dei costi, media delle saturazioni)
        f_ins = sum(T_algo.F_insoddis);
        f_log = sum(T_algo.F_costo_fisso + T_algo.F_viaggio + T_algo.F_lavoro);
        f_tot = sum(T_algo.F_total);
        s_fis = mean(T_algo.sat_fisica);
        s_tem = mean(T_algo.sat_tempo);
        t_sec = mean(T_algo.algo_time_sec); % Il tempo è lo stesso per tutte le righe di quel run
        v_tot = sum(T_algo.n_vehicles);
        
        ResTable = [ResTable; {N_val, gamma_val, algo, f_ins, f_log, f_tot, s_fis, s_tem, t_sec, v_tot}];
    end
end

% Ordinamento per plotting
ResTable = sortrows(ResTable, {'N', 'Gamma', 'Algoritmo'});
N_unique = unique(ResTable.N);
gamma_unique = unique(ResTable.Gamma);

% Colori standard
colorGreedy = [0.0, 0.45, 0.74]; % Blu
colorCW = [0.85, 0.33, 0.10];    % Arancio

% =========================================================================
% GRAFICO 1: Transizione Politiche (Scomposizione F_tot per il massimo N)
% =========================================================================
N_max = max(N_unique);
T_maxN = ResTable(ResTable.N == N_max, :);

figure('Name', sprintf('Scomposizione Costi (N=%d)', N_max), 'Position', [100, 100, 800, 500]);
sgtitle(sprintf('Transizione Politiche (\\gamma) a N = %d', N_max));

algos = {'greedy', 'clarke_wright'};
titles = {'Greedy', 'Clarke-Wright'};
for a = 1:2
    subplot(1, 2, a);
    sub_T = T_maxN(strcmp(T_maxN.Algoritmo, algos{a}), :);
    
    % Dati da impilare: Insoddisfazione vs Logistica
    yData = [sub_T.F_insoddis, sub_T.F_logistica];
    
    b = bar(categorical(sub_T.Gamma), yData, 'stacked');
    b(1).FaceColor = [0.47, 0.67, 0.19]; % Verde (Cittadino)
    b(2).FaceColor = [0.30, 0.30, 0.30]; % Grigio (Azienda)
    
    title(titles{a});
    ylabel('Valore Assoluto'); xlabel('Parametro \gamma');
    legend('F_{insoddis} (Scalata)', 'Costi Logistici', 'Location', 'northwest');
    grid on;
end

%% DIAGNOSTICA TEMPORANEA
fprintf('\n--- DIAGNOSTICA CONTEGGIO RIGHE ---\n');
fprintf('N_unique     : %s\n', mat2str(N_unique'));
fprintf('gamma_unique : %s\n', mat2str(gamma_unique'));
for g = 1:length(gamma_unique)
    g_val = gamma_unique(g);
    sub_T = ResTable(ResTable.Gamma == g_val, :);
    fprintf('  gamma=%.2f  ->  %d righe totali\n', g_val, height(sub_T));
    for a = 1:numel(algos)
        n_a = sum(strcmp(sub_T.Algoritmo, algos{a}));
        fprintf('      %-15s : %d righe (atteso %d)\n', algos{a}, n_a, length(N_unique));
    end
end
fprintf('-----------------------------------\n\n');

% =========================================================================
% GRAFICO 2: Saturazione Camion vs N (Il Focus)
% =========================================================================
figure('Name', 'Saturazione Camion vs N', 'Position', [150, 150, 1000, 600]);
sgtitle('Saturazione Fisica e Temporale al variare di N e \gamma');

for g = 1:length(gamma_unique)
    g_val = gamma_unique(g);
    sub_T = ResTable(ResTable.Gamma == g_val, :);
    
    % Saturazione Fisica
    subplot(2, 3, g);
    yDataFis = reshape(sub_T.Sat_Fisica, 2, [])'; % 2 algoritmi
    b = bar(categorical(N_unique), yDataFis, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f (Fisica)', g_val));
    ylabel('Sat. Fisica (%)'); ylim([0 100]); grid on;
    if g == 1, legend('Greedy', 'CW', 'Location', 'northwest'); end
    
    % Saturazione Temporale
    subplot(2, 3, g+3);
    yDataTem = reshape(sub_T.Sat_Tempo, 2, [])';
    b = bar(categorical(N_unique), yDataTem, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f (Tempo)', g_val));
    ylabel('Sat. Tempo (%)'); ylim([0 100]); grid on;
end

% =========================================================================
% GRAFICO 3: Costi e Tempi vs N
% =========================================================================
figure('Name', 'Prestazioni vs N', 'Position', [200, 200, 900, 400]);

subplot(1, 2, 1); hold on;
for g = 1:length(gamma_unique)
    sub_G = ResTable(ResTable.Gamma == gamma_unique(g) & strcmp(ResTable.Algoritmo, 'greedy'), :);
    sub_C = ResTable(ResTable.Gamma == gamma_unique(g) & strcmp(ResTable.Algoritmo, 'clarke_wright'), :);
    plot(sub_G.N, sub_G.F_tot, '-o', 'Color', colorGreedy, 'DisplayName', sprintf('Greedy (\\gamma=%.2f)', gamma_unique(g)));
    plot(sub_C.N, sub_C.F_tot, '-s', 'Color', colorCW, 'DisplayName', sprintf('CW (\\gamma=%.2f)', gamma_unique(g)));
end
title('Funzione Obiettivo Totale vs N');
xlabel('Utenti Attivi (N)'); ylabel('F_{tot}'); grid on;
legend('Location', 'best', 'NumColumns', 2);

subplot(1, 2, 2); hold on;
sub_G = ResTable(strcmp(ResTable.Algoritmo, 'greedy'), :);
sub_C = ResTable(strcmp(ResTable.Algoritmo, 'clarke_wright'), :);
% Il tempo di algo non varia molto col gamma in proporzione, plottiamo la media
g_mean_time = splitapply(@mean, sub_G.Time_sec, findgroups(sub_G.N));
c_mean_time = splitapply(@mean, sub_C.Time_sec, findgroups(sub_C.N));

plot(N_unique, g_mean_time, '-o', 'Color', colorGreedy, 'LineWidth', 2, 'DisplayName', 'Greedy (Media)');
plot(N_unique, c_mean_time, '-s', 'Color', colorCW, 'LineWidth', 2, 'DisplayName', 'Clarke-Wright (Media)');
title('Tempo di Calcolo vs N');
xlabel('Utenti Attivi (N)'); ylabel('Secondi'); grid on; set(gca, 'YScale', 'log'); legend('Location', 'northwest');