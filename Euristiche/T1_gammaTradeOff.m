% =========================================================================
% T1: Analisi Trasversale — Effetto Gamma (Politica di Compromesso)
% Usa tutti i CSV disponibili, aggregati per gamma.
% Domanda: come si sposta il compromesso sociale/economico al variare di γ?
% =========================================================================
clear; clc; close all;

dataDir = 'risultati_csv';
files   = dir(fullfile(dataDir, '*.csv'));

if isempty(files)
    error('Nessun file CSV trovato in risultati_csv/');
end

colorGreedy = [0.13, 0.47, 0.71];
colorCW     = [0.84, 0.37, 0.05];

% =========================================================================
% 1. LETTURA DATI — tutte le righe is_best=1 di tutti i benchmark
%    Una riga per (benchmark × rifiuto × algoritmo × gamma)
% =========================================================================
VarTypes_raw = {'string','double','string','string','double','double','double','double','double'};
VarNames_raw = {'Benchmark','Gamma','Rifiuto','Algoritmo','F_insoddis','F_logistica','F_tot','Sat_Fisica','Sat_Tempo'};
RawTable = table('Size', [0, length(VarNames_raw)], ...
    'VariableTypes', VarTypes_raw, 'VariableNames', VarNames_raw);

% Tabella separata per X_r ottimo per rifiuto (G3)
VarTypes_xr = {'string','double','string','string','double'};
VarNames_xr = {'Benchmark','Gamma','Rifiuto','Algoritmo','X_r_best'};
XrTable = table('Size', [0, length(VarNames_xr)], ...
    'VariableTypes', VarTypes_xr, 'VariableNames', VarNames_xr);

for i = 1:length(files)
    filename  = files(i).name;
    gamma_str = regexp(filename, 'gamma(\d+\.\d+)', 'tokens');
    if isempty(gamma_str), continue; end

    gamma_val = str2double(gamma_str{1}{1});

    % Etichetta benchmark dal nome file (tutto prima di _gamma)
    bench_str = regexp(filename, '^(.+)_gamma', 'tokens');
    if isempty(bench_str)
        bench_label = filename;
    else
        bench_label = string(bench_str{1}{1});
    end

    filepath = fullfile(dataDir, filename);
    T        = readtable(filepath, detectImportOptions(filepath));
    T_best   = T(T.is_best == 1, :);
    if isempty(T_best), continue; end

    algos = {'greedy', 'clarke_wright'};
    for a = 1:length(algos)
        T_algo = T_best(strcmp(T_best.algoritmo, algos{a}), :);
        if isempty(T_algo), continue; end

        % Una riga per rifiuto (per X_r per rifiuto in G3)
        for r_idx = 1:height(T_algo)
            row     = T_algo(r_idx, :);
            rifiuto = string(row.rifiuto);
            f_log_r = row.F_costo_fisso + row.F_viaggio + row.F_lavoro;

            RawTable = [RawTable; {bench_label, gamma_val, rifiuto, algos{a}, ...
                row.F_insoddis, f_log_r, row.F_total, row.sat_fisica, row.sat_tempo}];

            XrTable = [XrTable; {bench_label, gamma_val, rifiuto, algos{a}, row.X_r}];
        end
    end
end

if height(RawTable) == 0
    error('Nessun dato valido estratto.');
end

% =========================================================================
% 2. AGGREGAZIONE per (Gamma × Algoritmo) — media su benchmark e rifiuti
%    Usiamo la media perché i valori assoluti variano tra benchmark
%    (N diversi, rete diversa). La forma della curva è ciò che conta.
% =========================================================================
AggTable = groupsummary(RawTable, {'Gamma','Algoritmo'}, 'mean', ...
    {'F_insoddis','F_logistica','F_tot','Sat_Fisica','Sat_Tempo'});
AggTable.Properties.VariableNames = strrep(AggTable.Properties.VariableNames, 'mean_', '');
AggTable = sortrows(AggTable, {'Algoritmo', 'Gamma'});

g_unique = unique(AggTable.Gamma);
n_g      = length(g_unique);

subG_agg = sortrows(AggTable(strcmp(AggTable.Algoritmo, 'greedy'),        :), 'Gamma');
subC_agg = sortrows(AggTable(strcmp(AggTable.Algoritmo, 'clarke_wright'), :), 'Gamma');

% =========================================================================
% GRAFICO 1: Curva di Trade-off F_insoddis vs F_logistica (Pareto empirica)
% Ogni punto è un valore di gamma; la freccia indica gamma crescente.
% =========================================================================
fig1 = figure('Name', 'Frontiera Pareto Empirica', 'Position', [50, 50, 750, 600]);
sgtitle('T1 — Frontiera di Pareto Empirica: Insoddisfazione vs Logistica', 'FontWeight', 'bold');
hold on;

% Curve
plot(subG_agg.F_logistica, subG_agg.F_insoddis, '-o', ...
    'Color', colorGreedy, 'LineWidth', 2, 'MarkerFaceColor', colorGreedy, ...
    'MarkerSize', 8, 'DisplayName', 'Greedy');
plot(subC_agg.F_logistica, subC_agg.F_insoddis, '-s', ...
    'Color', colorCW,     'LineWidth', 2, 'MarkerFaceColor', colorCW, ...
    'MarkerSize', 8, 'DisplayName', 'Clarke-Wright');

% Annotazione gamma su ogni punto Greedy
for g = 1:n_g
    gv = g_unique(g);
    row_g = subG_agg(subG_agg.Gamma == gv, :);
    if isempty(row_g), continue; end
    text(row_g.F_logistica + 0.01 * abs(row_g.F_logistica), row_g.F_insoddis, ...
        sprintf('  \\gamma=%.2f', gv), 'FontSize', 8, 'Color', colorGreedy);
end

% Freccia direzione gamma crescente (dal punto min al punto max gamma)
if height(subG_agg) >= 2
    x1 = subG_agg.F_logistica(1);   y1 = subG_agg.F_insoddis(1);
    x2 = subG_agg.F_logistica(2);   y2 = subG_agg.F_insoddis(2);
    annotation('arrow', ...
        [x1, x2] / (xlim * [0;1] + (xlim * [1;0] - xlim * [0;1])) + [0 0], ...
        [y1, y2] / (ylim * [0;1] + (ylim * [1;0] - ylim * [0;1])) + [0 0]);
end

xlabel('F_{logistica} (costi operativi medi)');
ylabel('F_{insoddis} \times k_{scala} (media)');
legend('Location', 'best'); grid on; box on;

% =========================================================================
% GRAFICO 2: F_insoddis e F_logistica separatamente vs gamma
% =========================================================================
fig2 = figure('Name', 'Componenti vs Gamma', 'Position', [100, 100, 950, 420]);
sgtitle('T1 — Componenti della Funzione Obiettivo al variare di \gamma', 'FontWeight', 'bold');

subplot(1, 2, 1); hold on;
plot(subG_agg.Gamma, subG_agg.F_insoddis, '-o', 'Color', colorGreedy, 'LineWidth', 2, ...
    'MarkerFaceColor', colorGreedy, 'DisplayName', 'Greedy');
plot(subC_agg.Gamma, subC_agg.F_insoddis, '-s', 'Color', colorCW,     'LineWidth', 2, ...
    'MarkerFaceColor', colorCW,     'DisplayName', 'CW');
xlabel('\gamma'); ylabel('F_{insoddis} \times k_{scala} (media)');
title('Insoddisfazione vs \gamma', 'FontWeight', 'bold');
legend('Location', 'best'); grid on; box on;

subplot(1, 2, 2); hold on;
plot(subG_agg.Gamma, subG_agg.F_logistica, '-o', 'Color', colorGreedy, 'LineWidth', 2, ...
    'MarkerFaceColor', colorGreedy, 'DisplayName', 'Greedy');
plot(subC_agg.Gamma, subC_agg.F_logistica, '-s', 'Color', colorCW,     'LineWidth', 2, ...
    'MarkerFaceColor', colorCW,     'DisplayName', 'CW');
xlabel('\gamma'); ylabel('F_{logistica} (media)');
title('Costi Logistici vs \gamma', 'FontWeight', 'bold');
legend('Location', 'best'); grid on; box on;

% =========================================================================
% GRAFICO 3: X*_r ottimo per rifiuto vs gamma
% Aggregato su benchmark (media), separato per rifiuto e algoritmo
% =========================================================================
rifiuti_list = unique(XrTable.Rifiuto);
n_rif        = length(rifiuti_list);

% Palette per i rifiuti (5 colori distinti)
colori_rif = [
    0.84, 0.15, 0.16;   % rosso    — organico
    0.17, 0.63, 0.17;   % verde    — carta
    0.12, 0.47, 0.71;   % blu      — plastica
    0.58, 0.40, 0.74;   % viola    — vetro
    0.55, 0.34, 0.29;   % marrone  — indifferenziata
    ];

fig3 = figure('Name', 'X_r ottimo vs Gamma', 'Position', [150, 150, 1050, 480]);
sgtitle('T1 — Frequenza Ottima X^*_r per Rifiuto al variare di \gamma', 'FontWeight', 'bold');

algo_keys   = {'greedy', 'clarke_wright'};
algo_titles = {'Greedy', 'Clarke-Wright'};

for a = 1:2
    subplot(1, 2, a); hold on;
    for r = 1:n_rif
        rif_name = rifiuti_list(r);
        sub_xr   = XrTable(strcmp(XrTable.Rifiuto, rif_name) & ...
            strcmp(XrTable.Algoritmo, algo_keys{a}), :);
        if isempty(sub_xr), continue; end

        % Media su benchmark per ogni gamma
        xr_agg = groupsummary(sub_xr, 'Gamma', 'mean', 'X_r_best');
        xr_agg = sortrows(xr_agg, 'Gamma');

        col_r = colori_rif(mod(r-1, size(colori_rif,1)) + 1, :);
        plot(xr_agg.Gamma, xr_agg.mean_X_r_best, '-o', ...
            'Color', col_r, 'LineWidth', 1.8, 'MarkerFaceColor', col_r, ...
            'DisplayName', char(rif_name));
    end
    xlabel('\gamma');
    ylabel('X^*_r ottimo (raccolta/settimana)');
    title(algo_titles{a}, 'FontWeight', 'bold');
    legend('Location', 'best', 'FontSize', 8);
    grid on; box on;
    ylim([0, max(cellfun(@str2double, {'6.5'}))]);  % adatta al tuo range X_VALUES
end

% =========================================================================
% GRAFICO 4: Saturazione media vs gamma
% =========================================================================
fig4 = figure('Name', 'Saturazione vs Gamma', 'Position', [200, 200, 950, 420]);
sgtitle('T1 — Saturazione Media dei Veicoli al variare di \gamma', 'FontWeight', 'bold');

subplot(1, 2, 1); hold on;
plot(subG_agg.Gamma, subG_agg.Sat_Fisica, '-o', 'Color', colorGreedy, 'LineWidth', 2, ...
    'MarkerFaceColor', colorGreedy, 'DisplayName', 'Greedy');
plot(subC_agg.Gamma, subC_agg.Sat_Fisica, '-s', 'Color', colorCW,     'LineWidth', 2, ...
    'MarkerFaceColor', colorCW,     'DisplayName', 'CW');
xlabel('\gamma'); ylabel('Saturazione fisica media (%)');
title('Saturazione Fisica vs \gamma', 'FontWeight', 'bold');
ylim([0 100]); legend('Location', 'best'); grid on; box on;

subplot(1, 2, 2); hold on;
plot(subG_agg.Gamma, subG_agg.Sat_Tempo, '-o', 'Color', colorGreedy, 'LineWidth', 2, ...
    'MarkerFaceColor', colorGreedy, 'DisplayName', 'Greedy');
plot(subC_agg.Gamma, subC_agg.Sat_Tempo, '-s', 'Color', colorCW,     'LineWidth', 2, ...
    'MarkerFaceColor', colorCW,     'DisplayName', 'CW');
xlabel('\gamma'); ylabel('Saturazione temporale media (%)');
title('Saturazione Temporale vs \gamma', 'FontWeight', 'bold');
ylim([0 100]); legend('Location', 'best'); grid on; box on;