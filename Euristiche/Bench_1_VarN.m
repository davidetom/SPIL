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

fig1 = figure('Name', sprintf('Scomposizione Costi (N=%d)', N_max), 'Position', [50, 50, 900, 500]);
sgtitle(sprintf('B1 — Transizione Politiche (\\gamma) a N = %d', N_max), 'FontWeight', 'bold');

algo_keys   = {'greedy', 'clarke_wright'};
algo_titles = {'Greedy', 'Clarke-Wright'};

for a = 1:2
    subplot(1, 2, a);
    sub_T  = sortrows(T_maxN(strcmp(T_maxN.Algoritmo, algo_keys{a}), :), 'Gamma');
    yData  = [sub_T.F_insoddis, sub_T.F_logistica];
    b      = bar(categorical(sub_T.Gamma), yData, 'stacked');
    b(1).FaceColor = [0.47, 0.67, 0.19];  % Verde — componente utente
    b(2).FaceColor = [0.30, 0.30, 0.30];  % Grigio — componente azienda
    title(algo_titles{a}, 'FontWeight', 'bold');
    ylabel('F_{tot} (valore assoluto)');
    xlabel('Parametro \gamma');
    legend('F_{insoddis} \times k_{scala}', 'F_{logistica}', 'Location', 'best');
    grid on; box on;
end

% =========================================================================
% GRAFICO 2: F_tot vs N per entrambi gli algoritmi e tutti i gamma
% =========================================================================
fig2 = figure('Name', 'F_tot vs N', 'Position', [100, 100, 950, 420]);
sgtitle('B1 — Funzione Obiettivo e Tempo di Calcolo vs N', 'FontWeight', 'bold');

subplot(1, 2, 1); hold on;
gamma_styles = {'-o', '-s', '-^'};  % un marker per gamma

for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'N');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'N');
    plot(subG.N, subG.F_tot, gamma_styles{g}, 'Color', colorGreedy, 'LineWidth', 1.6, ...
        'MarkerFaceColor', colorGreedy, 'DisplayName', sprintf('Greedy \\gamma=%.2f', gv));
    plot(subC.N, subC.F_tot, gamma_styles{g}, 'Color', colorCW,     'LineWidth', 1.6, ...
        'MarkerFaceColor', colorCW,     'DisplayName', sprintf('CW \\gamma=%.2f',     gv));
end
xlabel('Utenti attivi (N)'); ylabel('F_{tot}');
title('Funzione Obiettivo vs N');
legend('Location', 'best', 'NumColumns', 2, 'FontSize', 7);
grid on; box on;

subplot(1, 2, 2); hold on;
% Tempo medio sui gamma (il gamma non influenza il tempo di routing)
for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'N');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'N');
    if g == 1
        dnG = 'Greedy'; dnC = 'Clarke-Wright';
    else
        dnG = ''; dnC = '';
    end
    plot(subG.N, subG.Time_sec, gamma_styles{g}, 'Color', colorGreedy, 'LineWidth', 1.6, ...
        'MarkerFaceColor', colorGreedy, 'DisplayName', dnG);
    plot(subC.N, subC.Time_sec, gamma_styles{g}, 'Color', colorCW,     'LineWidth', 1.6, ...
        'MarkerFaceColor', colorCW,     'DisplayName', dnC);
end
xlabel('Utenti attivi (N)'); ylabel('Secondi');
title('Tempo di Calcolo vs N');
set(gca, 'YScale', 'log');
legend('Location', 'northwest'); grid on; box on;

% =========================================================================
% GRAFICO 3: Saturazione Fisica e Temporale vs N (pannello 2×n_g)
% =========================================================================
fig3 = figure('Name', 'Saturazione vs N', 'Position', [150, 150, 1050, 620]);
sgtitle('B1 — Saturazione Fisica e Temporale al variare di N e \gamma', 'FontWeight', 'bold');

for g = 1:n_g
    gv    = g_unique(g);
    subG  = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'N');
    subC  = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'N');

    % Riga 1 — Saturazione Fisica
    subplot(2, n_g, g);
    yFis = [subG.Sat_Fisica, subC.Sat_Fisica];
    b = bar(categorical(N_unique), yFis, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f — Fisica', gv), 'FontWeight', 'bold');
    ylabel('Saturazione fisica (%)'); ylim([0 100]); grid on; box on;
    if g == 1, legend('Greedy', 'CW', 'Location', 'northwest'); end

    % Riga 2 — Saturazione Temporale
    subplot(2, n_g, g + n_g);
    yTem = [subG.Sat_Tempo, subC.Sat_Tempo];
    b = bar(categorical(N_unique), yTem, 'grouped');
    b(1).FaceColor = colorGreedy; b(2).FaceColor = colorCW;
    title(sprintf('\\gamma = %.2f — Temporale', gv), 'FontWeight', 'bold');
    ylabel('Saturazione temporale (%)'); ylim([0 100]); grid on; box on;
end

% =========================================================================
% GRAFICO 4: Utenti Serviti vs N — cambio vincolo attivo
% =========================================================================
fig4 = figure('Name', 'Utenti Serviti vs N', 'Position', [200, 200, 700, 420]);
sgtitle('B1 — Utenti Effettivamente Serviti vs N', 'FontWeight', 'bold');
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
title(sprintf('Utenti serviti vs N (\\gamma = %.2f)', gv_ref));
legend('Location', 'northwest'); grid on; box on;

% =========================================================================
% GRAFICO 5: Gap relativo Greedy–CW vs N
% =========================================================================
fig5 = figure('Name', 'Gap Greedy vs CW', 'Position', [250, 250, 700, 420]);
sgtitle('B1 — Gap Relativo F_{tot}: Greedy vs Clarke-Wright', 'FontWeight', 'bold');
hold on;

for g = 1:n_g
    gv   = g_unique(g);
    subG = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'greedy'),        :), 'N');
    subC = sortrows(ResTable(ResTable.Gamma == gv & strcmp(ResTable.Algoritmo, 'clarke_wright'), :), 'N');

    if height(subG) ~= height(subC) || height(subG) == 0, continue; end

    gap_pct = (subG.F_tot - subC.F_tot) ./ min(subG.F_tot, subC.F_tot) * 100;
    plot(subG.N, gap_pct, gamma_styles{g}, 'Color', [0.2 0.2 0.2], 'LineWidth', 2, ...
        'MarkerFaceColor', [0.5 0.5 0.5], 'DisplayName', sprintf('\\gamma = %.2f', gv));
end

yline(0, '--k', 'LineWidth', 1, 'DisplayName', 'Pareggio');
xlabel('Utenti attivi (N)');
ylabel('Gap % = (F_{Greedy} - F_{CW}) / min \times 100');
title('Gap positivo → CW migliore; negativo → Greedy migliore');
legend('Location', 'best'); grid on; box on;