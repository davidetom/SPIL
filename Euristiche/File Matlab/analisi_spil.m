% =========================================================================
%  SPIL — Analisi Risultati
%
%  Legge i CSV generati da main.py e produce 4 figure:
%
%    Fig 1 — F_insoddis e F_costi separati  (Greedy vs CW, per rifiuto)
%    Fig 2 — Curva di trade-off pesi A/B/C  (F_insoddis vs F_costi)
%    Fig 3 — Utilizzo veicoli               (n_vehicles per rifiuto)
%    Fig 4 — F_total per scenario pesi      (grouped bar A/B/C)
%
%  Come usare:
%    1. Imposta CSV_DIR con il percorso alla cartella risultati_csv/
%    2. Imposta TAG_BASE con il prefisso del file (es. 'mappa_reale' o
%       'std_seed42')
%    3. Lancia lo script
%
%  Convenzione nomi file attesa:
%    risultati_<N>u_<TAG_BASE>_espl.csv          (run esplorativa)
%    risultati_<N>u_<TAG_BASE>_A_bilanciato.csv
%    risultati_<N>u_<TAG_BASE>_B_pro_costi.csv
%    risultati_<N>u_<TAG_BASE>_C_pro_insoddisfaz.csv
%
% =========================================================================

%% ── 0. Configurazione ────────────────────────────────────────────────────

clearvars; clc; close all;

CSV_DIR  = 'risultati_csv';   % cartella con i CSV
TAG_BASE = 'mappa_reale';     % prefisso senza N e senza suffisso scenario
N_USERS  = 3932;              % numero utenti (per costruire il nome file)

% ── Palette colori ────────────────────────────────────────────────────────

COL_GREEDY = [0.13 0.47 0.71];
COL_CW     = [0.84 0.37 0.05];

COL_INS    = [0.29 0.67 0.31];   % verde  — insoddisfazione
COL_COST   = [0.17 0.45 0.70];   % blu    — costi

SCENARIO_COLORS = [
    0.50 0.50 0.50;   % A bilanciato  — grigio
    0.84 0.37 0.05;   % B pro-costi   — arancio
    0.13 0.47 0.71;   % C pro-insod.  — blu
];

WASTE_COLORS = [
    0.20 0.63 0.17;
    0.12 0.47 0.71;
    1.00 0.50 0.05;
    0.58 0.40 0.74;
    0.84 0.15 0.16;
];

%% ── 1. Lettura file CSV ───────────────────────────────────────────────────

% Tag dei 4 file attesi
scenario_tags   = {'', '_A_bilanciato', '_B_pro_costi', '_C_pro_insoddisfaz'};
scenario_labels = {'Esplorativa (1/1)', 'A — Bilanciato', ...
                   'B — Pro-costi', 'C — Pro-insoddisfaz.'};
n_scenarios = numel(scenario_tags);

all_data = cell(n_scenarios, 1);
found    = false(n_scenarios, 1);

for s = 1:n_scenarios
    fname = sprintf('risultati_%du_%s%s.csv', N_USERS, TAG_BASE, scenario_tags{s});
    fpath = fullfile(CSV_DIR, fname);
    if ~isfile(fpath)
        warning('File non trovato: %s', fname);
        continue
    end
    opts = detectImportOptions(fpath);
    opts.VariableNamesLine = 1;
    T = readtable(fpath, opts);
    if ~iscell(T.rifiuto),   T.rifiuto   = cellstr(T.rifiuto);   end
    if ~iscell(T.algoritmo), T.algoritmo = cellstr(T.algoritmo); end
    all_data{s} = T;
    found(s)    = true;
    fprintf('  Letto: %s\n', fname);
end

if ~any(found)
    error(['Nessun file trovato in ''%s'' con TAG_BASE=''%s'' e N=%d.\n' ...
           'Controlla CSV_DIR, TAG_BASE e N_USERS.'], CSV_DIR, TAG_BASE, N_USERS);
end

% Struttura comune da primo file disponibile
T_ref       = all_data{find(found,1)};
waste_types = unique(T_ref.rifiuto,   'stable');
algo_keys   = unique(T_ref.algoritmo, 'stable');
n_waste     = numel(waste_types);
n_algos     = numel(algo_keys);

fprintf('\n  Rifiuti  : %s\n', strjoin(waste_types, ', '));
fprintf('  Algoritmi: %s\n\n', strjoin(algo_keys, ', '));

%% ── Funzione locale di lettura best ──────────────────────────────────────
%  Restituisce struct best.(aKey).(rKey) con i campi F_*  e n_vehicles,
%  e tempi.(aKey).

function S = estrai_best(T, algo_keys, waste_types)
    S.best  = struct();
    S.tempi = struct();
    S.pesi  = struct();
    for a = 1:numel(algo_keys)
        ak   = algo_keys{a};
        aKey = matlab.lang.makeValidName(ak);
        amask = strcmp(T.algoritmo, ak);
        idx_first = find(amask, 1);
        if isempty(idx_first), continue; end
        S.tempi.(aKey) = T.algo_time_sec(idx_first);
        if ismember('alpha', T.Properties.VariableNames)
            S.pesi.(aKey).alpha      = T.alpha(idx_first);
            S.pesi.(aKey).scala_ins  = T.scala_ins(idx_first);
            S.pesi.(aKey).scala_cost = T.scala_cost(idx_first);
        else
            S.pesi.(aKey).alpha      = 0.5;
            S.pesi.(aKey).scala_ins  = 1.0;
            S.pesi.(aKey).scala_cost = 1.0;
        end
        S.best.(aKey) = struct();
        for k = 1:numel(waste_types)
            r    = waste_types{k};
            rKey = matlab.lang.makeValidName(r);
            mask = amask & strcmp(T.rifiuto, r) & (T.is_best == 1);
            if ~any(mask), continue; end
            idx = find(mask, 1);
            S.best.(aKey).(rKey).F_total       = T.F_total(idx);
            S.best.(aKey).(rKey).F_insoddis    = T.F_insoddis(idx);
            S.best.(aKey).(rKey).F_costi       = T.F_costo_fisso(idx) ...
                                                + T.F_viaggio(idx) ...
                                                + T.F_lavoro(idx);
            S.best.(aKey).(rKey).F_costo_fisso = T.F_costo_fisso(idx);
            S.best.(aKey).(rKey).F_viaggio     = T.F_viaggio(idx);
            S.best.(aKey).(rKey).F_lavoro      = T.F_lavoro(idx);
            S.best.(aKey).(rKey).n_vehicles    = T.n_vehicles(idx);
            S.best.(aKey).(rKey).X_r           = T.X_r(idx);
        end
    end
end

% Estrai strutture per ogni scenario
scenario_structs = cell(n_scenarios, 1);
for s = 1:n_scenarios
    if ~found(s), continue; end
    scenario_structs{s} = estrai_best(all_data{s}, algo_keys, waste_types);
end

%% ══════════════════════════════════════════════════════════════════════════
%  FIGURA 1 — F_insoddis vs F_costi separati  (run esplorativa)
%  Mostra i due termini della F.O. per ogni rifiuto e algoritmo.
%  Questo è il grafico che risponde alla domanda della prof:
%  "quanto vale la soddisfazione e quanto valgono i costi — il numero"
%% ══════════════════════════════════════════════════════════════════════════

if found(1)
    S_espl = scenario_structs{1};

    fig1 = figure('Name','SPIL — F_insoddis vs F_costi (run esplorativa)', ...
                  'NumberTitle','off','Position',[50 50 1200 500]);

    for a = 1:n_algos
        ak   = algo_keys{a};
        aKey = matlab.lang.makeValidName(ak);
        if ~isfield(S_espl.best, aKey), continue; end

        ax = subplot(1, n_algos, a);
        hold(ax,'on'); grid(ax,'on'); box(ax,'on');

        ins_vals  = zeros(n_waste,1);
        cost_vals = zeros(n_waste,1);

        for k = 1:n_waste
            rKey = matlab.lang.makeValidName(waste_types{k});
            if ~isfield(S_espl.best.(aKey), rKey), continue; end
            ins_vals(k)  = S_espl.best.(aKey).(rKey).F_insoddis;
            cost_vals(k) = S_espl.best.(aKey).(rKey).F_costi;
        end

        x = 1:n_waste;
        b1 = bar(ax, x - 0.2, ins_vals,  0.35, 'FaceColor', COL_INS,  'EdgeColor','none');
        b2 = bar(ax, x + 0.2, cost_vals, 0.35, 'FaceColor', COL_COST, 'EdgeColor','none');

        % Etichette valore
        for k = 1:n_waste
            text(ax, k-0.2, ins_vals(k)*1.02,  sprintf('%.0f',ins_vals(k)), ...
                 'HorizontalAlignment','center','FontSize',7,'Color',COL_INS*0.7);
            text(ax, k+0.2, cost_vals(k)*1.02, sprintf('%.0f',cost_vals(k)), ...
                 'HorizontalAlignment','center','FontSize',7,'Color',COL_COST*0.7);
        end

        col_algo = COL_GREEDY;
        if contains(ak,'clarke'), col_algo = COL_CW; end

        title(ax, upper(strrep(ak,'_',' ')), ...
              'FontSize',12,'FontWeight','bold','Color',col_algo);
        xlabel(ax,'Tipo rifiuto','FontSize',10);
        ylabel(ax,'Valore funzione obiettivo','FontSize',10);
        xticks(ax, x);
        xticklabels(ax, upper(waste_types));
        legend(ax, [b1 b2], {'F insoddisfazione','F costi logistici'}, ...
               'Location','northeast','FontSize',9);

        % Annotazione rapporto
        ratio = mean(cost_vals(cost_vals>0)) / mean(ins_vals(ins_vals>0));
        text(ax, 0.98, 0.97, sprintf('F_{costi}/F_{ins} = %.1fx', ratio), ...
             'Units','normalized','HorizontalAlignment','right', ...
             'VerticalAlignment','top','FontSize',9, ...
             'BackgroundColor',[1 1 0.85],'EdgeColor',[0.7 0.7 0.4]);
    end
    
    % Forza stessa scala Y su entrambi i subplot
    all_axes = findobj(fig1, 'Type', 'Axes');
    y_max = max(arrayfun(@(ax) ax.YLim(2), all_axes));
    for ax = all_axes'
        ylim(ax, [0, y_max * 1.08]);
    end

    sgtitle(fig1, ...
        'Termini della F.O.: Insoddisfazione vs Costi logistici — run esplorativa (α=0.5)', ...
        'FontSize',13,'FontWeight','bold');
end

%% ══════════════════════════════════════════════════════════════════════════
%  FIGURA 2 — Trade-off pesi A/B/C  (F_insoddis vs F_costi)
%  Curva di Pareto empirica: ogni punto è uno scenario di pesi.
%  Separato per algoritmo, con frecce che indicano la direzione del trade-off.
%% ══════════════════════════════════════════════════════════════════════════

fig2 = figure('Name','SPIL — Trade-off pesi A/B/C', ...
              'NumberTitle','off','Position',[80 80 900 520]);
hold on; grid on; box on;

leg_h2 = gobjects(0); leg_t2 = {};

% Offset per separare visivamente le etichette di Greedy e CW
label_offset_x = [+0.005, -0.005];
label_offset_y = [+0.008, -0.008];

% Colori fissi per scenario (indipendenti dall'algoritmo)
sc_point_colors = [
    0.50 0.50 0.50;   % Esplorativa — grigio
    0.20 0.70 0.30;   % A bilanciato — verde
    0.99 0.56 0.05;   % B pro-costi  — arancio
    0.13 0.47 0.71;   % C pro-insod. — blu
];

for a = 1:n_algos
    ak   = algo_keys{a};
    aKey = matlab.lang.makeValidName(ak);

    col_algo = COL_GREEDY;
    if contains(ak,'clarke'), col_algo = COL_CW; end
    lbl_algo = upper(strrep(ak,'_',' '));

    pts_ins  = [];
    pts_cost = [];
    pts_lbl  = {};
    pts_alpha = [];

    for s = 1:n_scenarios
        if ~found(s) || isempty(scenario_structs{s}), continue; end
        SS = scenario_structs{s};
        if ~isfield(SS.best, aKey), continue; end

        tot_ins = 0; tot_cost = 0;
        for k = 1:n_waste
            rKey = matlab.lang.makeValidName(waste_types{k});
            if ~isfield(SS.best.(aKey), rKey), continue; end
            r_data = SS.best.(aKey).(rKey);
            tot_ins  = tot_ins  + r_data.F_insoddis;
            tot_cost = tot_cost + r_data.F_costi;
        end
        pts_ins(end+1)   = tot_ins;            %#ok<AGROW>
        pts_cost(end+1)  = tot_cost;           %#ok<AGROW>
        pts_lbl{end+1}   = scenario_labels{s}; %#ok<AGROW>
        % Leggi alpha dal CSV se disponibile
        if isfield(SS.pesi, aKey) && isfield(SS.pesi.(aKey), 'alpha')
            pts_alpha(end+1) = SS.pesi.(aKey).alpha; %#ok<AGROW>
        else
            pts_alpha(end+1) = NaN; %#ok<AGROW>
        end
    end

    if isempty(pts_ins), continue; end

    % Ordina i punti per F_insoddis crescente per una curva Pareto corretta
    [pts_ins_sorted, sort_idx] = sort(pts_ins);
    pts_cost_sorted  = pts_cost(sort_idx);
    pts_lbl_sorted   = pts_lbl(sort_idx);
    pts_alpha_sorted = pts_alpha(sort_idx);

    % Segmenti di retta tra punti consecutivi (niente frecce)
    plot(pts_ins_sorted, pts_cost_sorted, '-', ...
         'Color', col_algo * 0.7, 'LineWidth', 1.8);

    % Punti scatter con colore fisso per scenario
    for i = 1:numel(pts_ins_sorted)
        % Ritrova l'indice originale per il colore scenario
        orig_idx = sort_idx(i);
        sc_col = sc_point_colors(min(orig_idx, size(sc_point_colors,1)), :);
        scatter(pts_ins_sorted(i), pts_cost_sorted(i), 140, sc_col, 'filled', ...
                'MarkerEdgeColor', 'w', 'LineWidth', 1.2);

        if ~isnan(pts_alpha_sorted(i))
            lbl_str = sprintf('%s\nα=%.2f (%s)', ...
                pts_lbl_sorted{i}, pts_alpha_sorted(i), lbl_algo);
        else
            lbl_str = sprintf('%s\n(%s)', pts_lbl_sorted{i}, lbl_algo);
        end
        ox = pts_ins_sorted(i) * (1 + label_offset_x(a));
        oy = pts_cost_sorted(i) * (1 + label_offset_y(a));
        halign = 'left';
        if a == 2, halign = 'right'; end
        text(ox, oy, lbl_str, ...
             'FontSize', 7, 'Color', col_algo * 0.8, ...
             'HorizontalAlignment', halign, ...
             'VerticalAlignment', 'middle');
    end

    % Handle per legenda algoritmo
    h = scatter(NaN, NaN, 100, col_algo, 'filled', 'MarkerEdgeColor', 'w');
    leg_h2(end+1) = h;   %#ok<AGROW>
    leg_t2{end+1} = lbl_algo; %#ok<AGROW>
end

% Legenda scenari (colori punti)
sc_labels_leg = scenario_labels;
for i = 1:n_scenarios
    if ~found(i), continue; end
    h = scatter(NaN, NaN, 80, sc_point_colors(min(i,size(sc_point_colors,1)),:), ...
                'filled', 'MarkerEdgeColor','w');
    leg_h2(end+1) = h;   %#ok<AGROW>
    leg_t2{end+1} = sc_labels_leg{i}; %#ok<AGROW>
end

xlabel('F_{insoddisfazione}  (penalità totale)', 'FontSize',12);
ylabel('F_{costi logistici}  (€)', 'FontSize',12);
title('Trade-off Insoddisfazione vs Costi — Combinazione convessa α', ...
      'FontSize',13,'FontWeight','bold');
if ~isempty(leg_h2)
    legend(leg_h2, leg_t2, 'Location','best','FontSize',9);
end

%% ══════════════════════════════════════════════════════════════════════════
%  FIGURA 3 — Utilizzo veicoli (n_vehicles e X_r per rifiuto)
%  Risponde alla domanda della prof: "quanto è utilizzato il camion
%  rispetto alla sua capacità/tempo?"
%% ══════════════════════════════════════════════════════════════════════════

if found(1)
    S_espl = scenario_structs{1};

    fig3 = figure('Name','SPIL — Utilizzo veicoli', ...
                  'NumberTitle','off','Position',[110 110 1100 500]);

    % Subplot sx: n_vehicles per rifiuto
    ax3a = subplot(1,2,1);
    hold(ax3a,'on'); grid(ax3a,'on'); box(ax3a,'on');

    bar_width = 0.35;
    offsets   = [-bar_width/2, bar_width/2];
    leg_h3a = gobjects(0); leg_t3a = {};

    for a = 1:n_algos
        ak   = algo_keys{a};
        aKey = matlab.lang.makeValidName(ak);
        if ~isfield(S_espl.best, aKey), continue; end

        col_algo = COL_GREEDY;
        if contains(ak,'clarke'), col_algo = COL_CW; end

        veh_vals = zeros(n_waste,1);
        for k = 1:n_waste
            rKey = matlab.lang.makeValidName(waste_types{k});
            if ~isfield(S_espl.best.(aKey), rKey), continue; end
            veh_vals(k) = S_espl.best.(aKey).(rKey).n_vehicles;
        end

        x_pos = (1:n_waste) + offsets(a);
        b = bar(ax3a, x_pos, veh_vals, bar_width, ...
                'FaceColor', col_algo, 'EdgeColor','none');
        leg_h3a(end+1) = b; %#ok<AGROW>
        leg_t3a{end+1} = upper(strrep(ak,'_',' ')); %#ok<AGROW>

        for k = 1:n_waste
            text(ax3a, x_pos(k), veh_vals(k)+0.3, sprintf('%d',veh_vals(k)), ...
                 'HorizontalAlignment','center','FontSize',8, ...
                 'Color',col_algo*0.7,'FontWeight','bold');
        end
    end

    xticks(ax3a, 1:n_waste);
    xticklabels(ax3a, upper(waste_types));
    ylabel(ax3a,'Veicoli attivati (best X_r)','FontSize',10);
    title(ax3a,'Flotta attiva per tipo rifiuto','FontSize',11,'FontWeight','bold');
    legend(ax3a, leg_h3a, leg_t3a, 'Location','northeast','FontSize',9);

    % Subplot dx: X_r ottimale per rifiuto
    ax3b = subplot(1,2,2);
    hold(ax3b,'on'); grid(ax3b,'on'); box(ax3b,'on');

    leg_h3b = gobjects(0); leg_t3b = {};

    for a = 1:n_algos
        ak   = algo_keys{a};
        aKey = matlab.lang.makeValidName(ak);
        if ~isfield(S_espl.best, aKey), continue; end

        col_algo = COL_GREEDY;
        if contains(ak,'clarke'), col_algo = COL_CW; end

        xr_vals = zeros(n_waste,1);
        for k = 1:n_waste
            rKey = matlab.lang.makeValidName(waste_types{k});
            if ~isfield(S_espl.best.(aKey), rKey), continue; end
            xr_vals(k) = S_espl.best.(aKey).(rKey).X_r;
        end

        x_pos = (1:n_waste) + offsets(a);
        b = bar(ax3b, x_pos, xr_vals, bar_width, ...
                'FaceColor', col_algo, 'EdgeColor','none');
        leg_h3b(end+1) = b; %#ok<AGROW>
        leg_t3b{end+1} = upper(strrep(ak,'_',' ')); %#ok<AGROW>

        for k = 1:n_waste
            text(ax3b, x_pos(k), xr_vals(k)+0.02, sprintf('%.1f',xr_vals(k)), ...
                 'HorizontalAlignment','center','FontSize',8, ...
                 'Color',col_algo*0.7,'FontWeight','bold');
        end
    end

    xticks(ax3b, 1:n_waste);
    xticklabels(ax3b, upper(waste_types));
    ylabel(ax3b,'Frequenza ottimale X_r (pass/settimana)','FontSize',10);
    title(ax3b,'Frequenza di raccolta ottimale','FontSize',11,'FontWeight','bold');
    legend(ax3b, leg_h3b, leg_t3b, 'Location','northeast','FontSize',9);

    sgtitle(fig3,'Utilizzo della flotta — run esplorativa', ...
            'FontSize',13,'FontWeight','bold');
end

%% ══════════════════════════════════════════════════════════════════════════
%  FIGURA 4 — F_total per scenario pesi (Grouped & Stacked bar)
%  Risponde alla domanda: come cambia la F.O. totale al variare dei pesi?
%  Mostra le componenti F_insoddis + F_costi impilate, divise per algoritmo.
%% ══════════════════════════════════════════════════════════════════════════

fig4 = figure('Name','SPIL — F_total per scenario pesi', ...
              'NumberTitle','off','Position',[140 140 1000 500]);
hold on; grid on; box on;

valid_sc  = find(found);
n_valid   = numel(valid_sc);

% Colori specifici: Chiaro = Insoddisfazione, Scuro = Costi
COL_GREEDY_INS  = [0.40, 0.75, 0.95]; % Azzurro
COL_GREEDY_COST = [0.00, 0.45, 0.74]; % Blu scuro
COL_CW_INS      = [0.95, 0.65, 0.35]; % Arancio chiaro
COL_CW_COST     = [0.85, 0.33, 0.10]; % Arancio scuro

% Impostazioni larghezza e distanza tra barre
bar_width = 0.30;
if n_algos == 1
    offsets = 0;
else
    offsets = linspace(-bar_width*0.6, bar_width*0.6, n_algos);
end
x_base = 1:n_valid;

leg_handles = [];
leg_labels  = {};

for a = 1:n_algos
    ak   = algo_keys{a};
    aKey = matlab.lang.makeValidName(ak);
    
    % Prepara i dati [F_insoddis, F_costi] per questo specifico algoritmo
    data_stack = zeros(n_valid, 2); 
    
    for si = 1:n_valid
        s  = valid_sc(si);
        SS = scenario_structs{s};
        if ~isfield(SS.best, aKey), continue; end
        
        tot_ins = 0; tot_cost = 0;
        for k = 1:n_waste
            rKey = matlab.lang.makeValidName(waste_types{k});
            if ~isfield(SS.best.(aKey), rKey), continue; end
            tot_ins  = tot_ins  + SS.best.(aKey).(rKey).F_insoddis;
            tot_cost = tot_cost + SS.best.(aKey).(rKey).F_costi;
        end
        data_stack(si, 1) = tot_ins;
        data_stack(si, 2) = tot_cost;
    end
    
    % Disegna il grafico 'stacked' spostato sull'asse X per non sovrapporsi
    x_pos = x_base + offsets(a);
    b = bar(x_pos, data_stack, bar_width, 'stacked', 'EdgeColor', 'w', 'LineWidth', 0.5);
    
    % Assegna i colori in base all'algoritmo
    nome_algo_legenda = upper(strrep(ak,'_',' '));
    if contains(ak, 'clarke')
        b(1).FaceColor = COL_CW_INS;
        b(2).FaceColor = COL_CW_COST;
    else
        b(1).FaceColor = COL_GREEDY_INS;
        b(2).FaceColor = COL_GREEDY_COST;
    end
    
    % Salva i riferimenti per la legenda
    leg_handles = [leg_handles, b(1), b(2)]; %#ok<AGROW>
    leg_labels  = [leg_labels, ...
                   {sprintf('%s - Insoddisfazione', nome_algo_legenda)}, ...
                   {sprintf('%s - Costi', nome_algo_legenda)}]; %#ok<AGROW>
               
    % Aggiungi il valore totale in cima alla colonna impilata
    for si = 1:n_valid
        tot = data_stack(si, 1) + data_stack(si, 2);
        if tot > 0
            text(x_pos(si), tot * 1.02, sprintf('%.0f', tot), ...
                 'HorizontalAlignment', 'center', ...
                 'VerticalAlignment', 'bottom', ...
                 'FontSize', 9, 'FontWeight', 'bold', ...
                 'Color', b(2).FaceColor * 0.8); % Usa il colore scuro per il testo
        end
    end
end

% Formattazione finale assi e legenda
xticks(x_base);
xticklabels(scenario_labels(valid_sc));
xtickangle(15);
ylabel('F_{total} — componenti F_{ins} e F_{costi}', 'FontSize', 11);
title('F_{total} per scenario pesi — Composizione e Confronto', ...
      'FontSize', 13, 'FontWeight', 'bold');
legend(leg_handles, leg_labels, 'Location', 'northeast', 'FontSize', 9);

%% ── Console: riepilogo numerico ──────────────────────────────────────────

fprintf('\n%s\n', repmat('=',1,72));
fprintf('  RIEPILOGO NUMERICO\n');
fprintf('%s\n', repmat('=',1,72));

for s = 1:n_scenarios
    if ~found(s) || isempty(scenario_structs{s}), continue; end
    SS = scenario_structs{s};
    % Leggi alpha dal primo algoritmo disponibile
    alpha_val = NaN; scala_ins_val = NaN; scala_cost_val = NaN;
    for a = 1:n_algos
        aKey_tmp = matlab.lang.makeValidName(algo_keys{a});
        if isfield(SS.pesi, aKey_tmp) && isfield(SS.pesi.(aKey_tmp),'alpha')
            alpha_val      = SS.pesi.(aKey_tmp).alpha;
            scala_ins_val  = SS.pesi.(aKey_tmp).scala_ins;
            scala_cost_val = SS.pesi.(aKey_tmp).scala_cost;
            break;
        end
    end
    if ~isnan(alpha_val)
        fprintf('\n  Scenario: %s  (α=%.2f, scala_ins=%.1f, scala_cost=%.1f)\n', ...
                scenario_labels{s}, alpha_val, scala_ins_val, scala_cost_val);
    else
        fprintf('\n  Scenario: %s\n', scenario_labels{s});
    end
    fprintf('  %-20s  %-14s  %-14s  %-14s\n', ...
            'Rifiuto','F_insoddis','F_costi','F_total');
    fprintf('  %s\n', repmat('-',1,66));
    for a = 1:n_algos
        ak   = algo_keys{a};
        aKey = matlab.lang.makeValidName(ak);
        SS   = scenario_structs{s};
        if ~isfield(SS.best, aKey), continue; end
        fprintf('  [%s]\n', upper(strrep(ak,'_',' ')));
        tot_ins=0; tot_cost=0; tot_tot=0;
        for k = 1:n_waste
            rKey = matlab.lang.makeValidName(waste_types{k});
            if ~isfield(SS.best.(aKey), rKey), continue; end
            r = SS.best.(aKey).(rKey);
            fprintf('  %-20s  %14.2f  %14.2f  %14.2f\n', ...
                    waste_types{k}, r.F_insoddis, r.F_costi, r.F_total);
            tot_ins=tot_ins+r.F_insoddis; tot_cost=tot_cost+r.F_costi;
            tot_tot=tot_tot+r.F_total;
        end
        fprintf('  %-20s  %14.2f  %14.2f  %14.2f\n', ...
                'TOTALE', tot_ins, tot_cost, tot_tot);
    end
end

fprintf('\n%s\n', repmat('=',1,72));
fprintf('  Script completato.\n\n');