% =========================================================================
% BENCH 1: Analisi Variazione N (Utenti Attivi)
% =========================================================================
clear; clc; close all;

dataDir = 'risultati_csv';
files = dir(fullfile(dataDir, '*_varN_*.csv'));

if isempty(files)
    error('Nessun file trovato per l''analisi varN. Controlla la cartella.');
end

% Colori standard (invariati in tutti i Bench)
colorGreedy = [0.13, 0.47, 0.71];   % Blu profondo
colorCW     = [0.84, 0.37, 0.05];   % Arancio bruciato

% =========================================================================
% 1. PARSING E LETTURA DATI
% =========================================================================
VarTypes = {'double','double','string','double','double','double','double','double','double','double','double'};
VarNames = {'N','Gamma','Algoritmo','F_insoddis','F_logistica','F_tot','Sat_Fisica','Sat_Tempo','Time_sec','Vehicles','N_Serviti'};
ResTable = table('Size', [0, length(VarNames)], 'VariableTypes', VarTypes, 'VariableNames', VarNames);

for i = 1:length(files)
    filename = files(i).name;

    % Regex robusti: fix punto finale e cattura N attivi
    n_str     = regexp(filename, 'Nact(\d+)',         'tokens');
    gamma_str = regexp(filename, 'gamma(\d+\.\d+)',   'tokens');

    if isempty(n_str) || isempty(gamma_str), continue; end

    N_val     = str2double(n_str{1}{1});
    gamma_val = str2double(gamma_str{1}{1});

    filepath = fullfile(dataDir, filename);
    T = readtable(filepath, detectImportOptions(filepath));
    T_best = T(T.is_best == 1, :);

    algos = {'greedy', 'clarke_wright'};
    for a = 1:length(algos)
        T_algo = T_best(strcmp(T_best.algoritmo, algos{a}), :);
        if isempty(T_algo), continue; end

        f_ins    = sum(T_algo.F_insoddis);
        f_log    = sum(T_algo.F_costo_fisso + T_algo.F_viaggio + T_algo.F_lavoro);
        f_tot    = sum(T_algo.F_total);
        s_fis    = mean(T_algo.sat_fisica);
        s_tem    = mean(T_algo.sat_tempo);
        t_sec    = mean(T_algo.algo_time_sec);
        v_tot    = sum(T_algo.n_vehicles);
        n_serv   = sum(T_algo.n_utenti_serviti);  % somma su tutti i rifiuti

        ResTable = [ResTable; {N_val, gamma_val, algos{a}, f_ins, f_log, f_tot, s_fis, s_tem, t_sec, v_tot, n_serv}];
    end
end

if height(ResTable) == 0
    error('Nessun dato valido estratto. Controlla i nomi file e le colonne CSV.');
end

ResTable  = sortrows(ResTable, {'N', 'Gamma', 'Algoritmo'});
N_unique  = unique(ResTable.N);
g_unique  = unique(ResTable.Gamma);
n_g       = length(g_unique);

% =========================================================================
% GRAFICO 1: Scomposizione F_tot per il massimo N (Transizione Politiche)
% =========================================================================
N_max  = max(N_unique);
T_maxN = ResTable(ResTable.N == N_max, :);

fig1 = figure('Name', sprintf('Scomposizione Costi (N=%d)', N_max), 'Position', [50, 50, 900, 520]);
sgtitle(sprintf('B1 — Scomposizione F_{tot} per Politica  (N = %d)', N_max), ...
        'FontWeight', 'bold', 'FontSize', 11);

algo_keys   = {'greedy', 'clarke_wright'};
algo_titles = {'Greedy', 'Clarke-Wright'};

for a = 1:2
    subplot(1, 2, a);
    sub_T  = sortrows(T_maxN(strcmp(T_maxN.Algoritmo, algo_keys{a}), :), 'Gamma');
    % F_logistica prima (sotto), F_insoddis sopra — legenda dall'alto verso il basso
    yData  = [sub_T.F_logistica, sub_T.F_insoddis];
    b      = bar(categorical(sub_T.Gamma), yData, 'stacked');
    b(1).FaceColor = [0.30, 0.30, 0.30];  % Grigio — componente azienda (sotto)
    b(2).FaceColor = [0.47, 0.67, 0.19];  % Verde  — componente utente  (sopra)
    title(algo_titles{a}, 'FontWeight', 'bold');
    ylabel('F_{tot} (valore assoluto)');
    xlabel('Parametro \gamma');
    legend('F_{logistica}', 'F_{insoddis} \times k_{scala}', 'Location', 'best');
    grid on; box on;
end

% =========================================================================
% GRAFICO 2: F_tot vs N per entrambi gli algoritmi e tutti i gamma
% =========================================================================
fig2 = figure('Name', 'F_tot vs N', 'Position', [100, 100, 950, 460]);
sgtitle('B1 — Scalabilità: F_{tot} e Tempo al variare di N', ...
        'FontWeight', 'bold', 'FontSize', 11);

subplot(1, 2, 1); hold on;
% Un colore per gamma, cerchio per Greedy, quadrato per CW
gamma_colors = [
    0.20, 0.63, 0.86;   % gamma 0.10 — celeste
    0.50, 0.18, 0.56;   % gamma 0.50 — viola
    0.18, 0.63, 0.33;   % gamma 0.90 — verde
];

for g = 1:n_g
    gv   = g_unique(g);
    col  = gamma_colors(mod(g-1, size(gamma_colors,1)) + 1, :);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'N');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'N');
    plot(subG.N, subG.F_tot, '-o', 'Color', col, 'LineWidth', 1.6, ...
         'MarkerFaceColor', col, 'MarkerSize', 7, ...
         'DisplayName', sprintf('Greedy  \\gamma=%.2f', gv));
    plot(subC.N, subC.F_tot, '-s', 'Color', col, 'LineWidth', 1.6, ...
         'MarkerFaceColor', 'w', 'MarkerEdgeColor', col, 'MarkerSize', 7, ...
         'DisplayName', sprintf('CW  \\gamma=%.2f', gv));
end
xlabel('Utenti attivi (N)'); ylabel('F_{tot}');
title('Funzione Obiettivo');
legend('Location', 'best', 'NumColumns', 2, 'FontSize', 7);
grid on; box on;

subplot(1, 2, 2); hold on;
% Stesso schema colori del pannello F_tot — gamma colore, algoritmo marker
% Legenda: solo 2 voci (Greedy / CW), le curve per gamma extra sono invisibili in legenda
for g = 1:n_g
    gv   = g_unique(g);
    col  = gamma_colors(mod(g-1, size(gamma_colors,1)) + 1, :);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'N');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'N');
    if g == 1
        hvG = 'on'; hvC = 'on';
        dnG = 'Greedy'; dnC = 'Clarke-Wright';
    else
        hvG = 'off'; hvC = 'off';
        dnG = ''; dnC = '';
    end
    plot(subG.N, subG.Time_sec, '-o', 'Color', col, 'LineWidth', 1.6, ...
         'MarkerFaceColor', col, 'MarkerSize', 7, ...
         'DisplayName', dnG, 'HandleVisibility', hvG);
    plot(subC.N, subC.Time_sec, '-s', 'Color', col, 'LineWidth', 1.6, ...
         'MarkerFaceColor', 'w', 'MarkerEdgeColor', col, 'MarkerSize', 7, ...
         'DisplayName', dnC, 'HandleVisibility', hvC);
end
xlabel('Utenti attivi (N)'); ylabel('Secondi (log)');
title('Tempo di Calcolo');
legend('Location', 'northwest'); grid on; box on;
set(gca, 'YScale', 'log');   % DOPO i plot, altrimenti MATLAB resetta la scala

% =========================================================================
% GRAFICO 3: Saturazione Fisica e Temporale vs N (pannello 2×n_g)
% =========================================================================
fig3 = figure('Name', 'Saturazione vs N', 'Position', [150, 150, 1100, 660]);
sgtitle('B1 — Saturazione Fisica (riga 1) e Temporale (riga 2) vs N', ...
        'FontWeight', 'bold', 'FontSize', 11);

for g = 1:n_g
    gv    = g_unique(g);
    subG  = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'N');
    subC  = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'N');

    % Riga 1 — Saturazione Fisica
    ax = subplot(2, n_g, g);
    yFis = [subG.Sat_Fisica, subC.Sat_Fisica];
    b = bar(categorical(N_unique), yFis, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f', gv), 'FontWeight', 'bold', 'FontSize', 10);
    ylabel('Fisica (%)'); ylim([0 100]); grid on; box on;
    if g == 1, legend('Greedy', 'CW', 'Location', 'northwest'); end

    % Riga 2 — Saturazione Temporale
    subplot(2, n_g, g + n_g);
    yTem = [subG.Sat_Tempo, subC.Sat_Tempo];
    b = bar(categorical(N_unique), yTem, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f', gv), 'FontWeight', 'bold', 'FontSize', 10);
    ylabel('Temporale (%)'); ylim([0 100]); grid on; box on;
end

% =========================================================================
% GRAFICO 4: Utenti Serviti vs N — cambio vincolo attivo
% =========================================================================
fig4 = figure('Name', 'Utenti Serviti vs N', 'Position', [200, 200, 700, 440]);
sgtitle('B1 — Utenti Serviti vs N', 'FontWeight', 'bold', 'FontSize', 11);
hold on;

% Usiamo gamma=0.50 (neutro) come riferimento per questa analisi
gv_ref = 0.50;
[~, idx_ref] = min(abs(g_unique - gv_ref));
gv_ref = g_unique(idx_ref);

subG_ref = sortrows(ResTable(ResTable.Gamma == gv_ref & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'N');
subC_ref = sortrows(ResTable(ResTable.Gamma == gv_ref & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'N');

% Linea teorica: N_attivi × n_rifiuti (tutti i rifiuti, tutti serviti)
n_rifiuti = 5;
plot(N_unique, N_unique * n_rifiuti, '--k', 'LineWidth', 1.2, 'DisplayName', 'Teorico (tutti serviti)');
plot(subG_ref.N, subG_ref.N_Serviti, '-o', 'Color', colorGreedy, 'LineWidth', 2, ...
     'MarkerFaceColor', colorGreedy, 'DisplayName', sprintf('Greedy (\\gamma=%.2f)', gv_ref));
plot(subC_ref.N, subC_ref.N_Serviti, '-s', 'Color', colorCW,     'LineWidth', 2, ...
     'MarkerFaceColor', colorCW,     'DisplayName', sprintf('CW (\\gamma=%.2f)',     gv_ref));

xlabel('Utenti attivi (N)'); ylabel('n\_utenti\_serviti (somma 5 rifiuti)');
legend('Location', 'northwest'); grid on; box on;

% =========================================================================
% GRAFICO 5: Gap relativo Greedy–CW vs N
% =========================================================================
fig5 = figure('Name', 'Gap Greedy vs CW', 'Position', [250, 250, 700, 440]);
sgtitle('B1 — Gap Relativo F_{tot}: Greedy vs CW', 'FontWeight', 'bold', 'FontSize', 11);
hold on;

for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'N');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'N');

    if height(subG) ~= height(subC) || height(subG) == 0, continue; end

    gap_pct = (subG.F_tot - subC.F_tot) ./ min(subG.F_tot, subC.F_tot) * 100;
    col = gamma_colors(mod(g-1, size(gamma_colors,1)) + 1, :);
    plot(subG.N, gap_pct, '-o', 'Color', col, 'LineWidth', 2, ...
         'MarkerFaceColor', col, 'MarkerSize', 7, 'DisplayName', sprintf('\\gamma = %.2f', gv));
end

yline(0, '--k', 'LineWidth', 1, 'DisplayName', 'Pareggio');
xlabel('Utenti attivi (N)');
ylabel('Gap %  =  (F_{Greedy} - F_{CW}) / min \times 100');
legend('Location', 'best'); grid on; box on;