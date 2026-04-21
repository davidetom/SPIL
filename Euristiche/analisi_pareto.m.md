```
matlab ln:1 hl:43-70 hlt:F_Totale
% =========================================================================

% SPIL — Analisi Pareto e Visualizzazione Risultati

% Legge risultati_spil.csv generato da main.py e produce:

% 1. Curva F_total vs X_r per ogni rifiuto (subplot)

% 2. Scatter Pareto bi-obiettivo: F_insoddis vs F_costi per ogni rifiuto

% 3. Tabella riepilogativa (best per rifiuto) con tempo greedy

% =========================================================================

  

clear; clc; close all;

  

% ── Configurazione ────────────────────────────────────────────────────────

CSV_FILE = 'risultati_spil.csv'; % path relativo o assoluto al CSV

  

% Colori per i 5 rifiuti (in ordine: organico, carta, plastica, vetro, indiff.)

COLORS = [

0.20 0.63 0.17; % verde — organico

0.12 0.47 0.71; % blu — carta

1.00 0.50 0.05; % arancione — plastica

0.58 0.40 0.74; % viola — vetro

0.84 0.15 0.16; % rosso — indifferenziata

];

  

% ── 1. Lettura CSV ────────────────────────────────────────────────────────

opts = detectImportOptions(CSV_FILE);

opts.VariableNamesLine = 1;

T = readtable(CSV_FILE, opts);

  

waste_types = unique(T.rifiuto, 'stable'); % preserva ordine

n_types = numel(waste_types);

greedy_time = T.greedy_time_sec(1); % uguale per tutte le righe

  

fprintf('=== Riepilogo SPIL ===\n');

fprintf('Rifiuti: %d\n', n_types);

fprintf('Tempo greedy: %.4f s\n\n', greedy_time);

  

% ── 2. Pre-allocazione struttura dati per rifiuto ─────────────────────────

D = struct(); % D.(rifiuto) = tabella filtrata

  

for k = 1:n_types

r = waste_types{k};

mask = strcmp(T.rifiuto, r);

D.(matlab.lang.makeValidName(r)) = T(mask, :);

end

  

% =========================================================================

% FIGURA 1 — F_total vs X_r (curva completa + punto ottimale)

% =========================================================================

figure('Name', 'F\_total vs X\_r per rifiuto', 'NumberTitle', 'off', ...

'Position', [50 50 1400 650]);

  

for k = 1:n_types

r = waste_types{k};

rKey = matlab.lang.makeValidName(r);

sub = D.(rKey);

  

% Ordina per X_r

sub = sortrows(sub, 'X_r');

  

% Punto ottimale

best_mask = sub.is_best == 1;

  

subplot(2, 3, k);

hold on; grid on; box on;

  

% Curva totale

plot(sub.X_r, sub.F_total, '-o', ...

'Color', COLORS(k,:), 'LineWidth', 1.8, ...

'MarkerSize', 5, 'MarkerFaceColor', COLORS(k,:));

  

% Highlight componenti (area stacked opzionale — linee tratteggiate)

plot(sub.X_r, sub.F_insoddis, '--', 'Color', COLORS(k,:)*0.6, 'LineWidth', 1.0);

plot(sub.X_r, sub.F_costo_fisso, ':', 'Color', COLORS(k,:)*0.6, 'LineWidth', 1.0);

plot(sub.X_r, sub.F_viaggio, '-.', 'Color', COLORS(k,:)*0.7, 'LineWidth', 1.0);

  

% Punto ottimale (stella)

if any(best_mask)

plot(sub.X_r(best_mask), sub.F_total(best_mask), ...

'p', 'MarkerSize', 14, ...

'MarkerFaceColor', 'yellow', 'MarkerEdgeColor', 'k', 'LineWidth', 1.2);

text(sub.X_r(best_mask) + 0.05, sub.F_total(best_mask), ...

sprintf('X^*=%.1f\nF=%.0f\nV=%d', ...

sub.X_r(best_mask), sub.F_total(best_mask), sub.n_vehicles(best_mask)), ...

'FontSize', 7.5, 'VerticalAlignment', 'bottom');

end

  

title(upper(r), 'FontSize', 10, 'FontWeight', 'bold');

xlabel('X_r (ritiri/settimana)', 'FontSize', 8);

ylabel('Valore funzione obiettivo (€)', 'FontSize', 8);

legend({'F_{total}','F_{insoddis}','F_{fisso}','F_{viaggio}'}, ...

'Location','best', 'FontSize', 7);

xlim([min(sub.X_r)-0.2, max(sub.X_r)+0.2]);

end

  

% Cella vuota (6° subplot) usata per nota tempo

subplot(2, 3, 6);

axis off;

text(0.5, 0.6, sprintf('Tempo greedy totale\n%.4f s', greedy_time), ...

'HorizontalAlignment','center', 'FontSize', 12, 'FontWeight', 'bold');

text(0.5, 0.35, sprintf('★ = soluzione ottimale'), ...

'HorizontalAlignment','center', 'FontSize', 10);

  

sgtitle('F_{total} vs X_r — Curve complete per tipologia di rifiuto', ...

'FontSize', 13, 'FontWeight', 'bold');

  

% =========================================================================

% FIGURA 2 — Scatter bi-obiettivo: F_insoddis vs F_costi (Pareto frontier)

% F_costi = F_costo_fisso + F_viaggio + F_lavoro

% =========================================================================

figure('Name', 'Pareto: Insoddisfazione vs Costi Operativi', ...

'NumberTitle', 'off', 'Position', [100 100 900 650]);

hold on; grid on; box on;

  

legend_handles = gobjects(n_types, 1);

  

for k = 1:n_types

r = waste_types{k};

rKey = matlab.lang.makeValidName(r);

sub = D.(rKey);

  

F_costi = sub.F_costo_fisso + sub.F_viaggio + sub.F_lavoro;

  

% Tutti i punti

h = scatter(sub.F_insoddis, F_costi, 50, ...

'o', 'MarkerFaceColor', COLORS(k,:), ...

'MarkerEdgeColor', 'w', 'LineWidth', 0.8);

legend_handles(k) = h;

  

% Etichetta X_r su ogni punto

for i = 1:height(sub)

text(sub.F_insoddis(i) + 5, F_costi(i), ...

sprintf('%.1f', sub.X_r(i)), ...

'FontSize', 6, 'Color', COLORS(k,:)*0.7);

end

  

% Best point: stella

best_mask = sub.is_best == 1;

if any(best_mask)

scatter(sub.F_insoddis(best_mask), F_costi(best_mask), 200, ...

'p', 'MarkerFaceColor', 'yellow', 'MarkerEdgeColor', 'k', 'LineWidth', 1.2);

end

end

  

xlabel('F_{insoddisfazione} (penalità disservizio)', 'FontSize', 11);

ylabel('F_{costi operativi} (fisso + viaggio + lavoro) [€]', 'FontSize', 11);

title('Frontiera di Pareto — Insoddisfazione vs Costi Operativi', ...

'FontSize', 13, 'FontWeight', 'bold');

legend(legend_handles, cellfun(@upper, waste_types, 'UniformOutput', false), ...

'Location', 'best', 'FontSize', 9);

  

% =========================================================================

% FIGURA 3 — Bar chart: scomposizione F_total per rifiuto (best solution)

% =========================================================================

figure('Name', 'Scomposizione F\_total (best)', 'NumberTitle', 'off', ...

'Position', [150 150 900 500]);

  

comp_matrix = zeros(n_types, 4); % [insoddis, fisso, viaggio, lavoro]

x_best_vec = zeros(n_types, 1);

v_best_vec = zeros(n_types, 1);

  

for k = 1:n_types

r = waste_types{k};

rKey = matlab.lang.makeValidName(r);

sub = D.(rKey);

bm = sub.is_best == 1;

if any(bm)

comp_matrix(k,:) = [sub.F_insoddis(bm), sub.F_costo_fisso(bm), ...

sub.F_viaggio(bm), sub.F_lavoro(bm)];

x_best_vec(k) = sub.X_r(bm);

v_best_vec(k) = sub.n_vehicles(bm);

end

end

  

b = bar(comp_matrix, 'stacked');

comp_colors = [0.29 0.67 0.31; 0.17 0.45 0.70; 0.99 0.56 0.05; 0.60 0.40 0.74];

for i = 1:4

b(i).FaceColor = comp_colors(i,:);

end

  

xticks(1:n_types);

xticklabels(cellfun(@upper, waste_types, 'UniformOutput', false));

ylabel('F (€)', 'FontSize', 11);

title('Scomposizione F_{total} per rifiuto — Soluzione ottimale', ...

'FontSize', 13, 'FontWeight', 'bold');

legend({'Insoddisfazione','Costo fisso','Costo viaggio','Costo lavoro'}, ...

'Location', 'northeast', 'FontSize', 9);

grid on; box on;

  

% Annotazione X* e V* sopra ogni barra

for k = 1:n_types

tot_k = sum(comp_matrix(k,:));

text(k, tot_k + max(sum(comp_matrix,2))*0.01, ...

sprintf('X^*=%.1f\nV=%d', x_best_vec(k), v_best_vec(k)), ...

'HorizontalAlignment', 'center', 'FontSize', 8);

end

  

% =========================================================================

% Console: tabella riepilogativa

% =========================================================================

fprintf('%-18s %6s %6s %10s %10s %10s %10s %10s\n', ...

'Rifiuto','X*','Veic.','F_total','F_insoddis','F_fisso','F_viaggio','F_lavoro');

fprintf('%s\n', repmat('-',1,82));

  

for k = 1:n_types

r = waste_types{k};

rKey = matlab.lang.makeValidName(r);

sub = D.(rKey);

bm = sub.is_best == 1;

if any(bm)

fprintf('%-18s %6.1f %6d %10.1f %10.1f %10.1f %10.1f %10.1f\n', ...

r, sub.X_r(bm), sub.n_vehicles(bm), ...

sub.F_total(bm), sub.F_insoddis(bm), ...

sub.F_costo_fisso(bm), sub.F_viaggio(bm), sub.F_lavoro(bm));

end

end

fprintf('%s\n', repmat('-',1,82));

fprintf('Tempo greedy totale: %.4f s\n', greedy_time);
```
