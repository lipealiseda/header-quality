"""Brazilian Portuguese text for the charts. Keys are the English templates used
in charts.py, so a missing or edited English string is caught when the Portuguese
charts are drawn."""

PT = {
    # shared
    "Data StatsBomb open data, 2,651 men's matches (mostly the 2015/16 top 4 leagues). Heights from Transfermarkt.":
        "Dados abertos da StatsBomb, 2.651 jogos (maioria das 4 grandes ligas, 2015/16). Alturas do Transfermarkt.",
    # a1
    "Where headers become goals": "Onde o cabeceio vira gol",
    "Share of headed shots that are scored, by location. Inside the six yard box about 1 in 5 go in,\n"
    "around the penalty spot about 1 in 16, from the edge of the box about 1 in 25.":
        "Porcentagem de finalizações de cabeça que viram gol, por local. Dentro da pequena área cerca de\n"
        "1 em 5 entra, perto da marca do pênalti cerca de 1 em 16, da entrada da área cerca de 1 em 25.",
    "Goal rate": "Taxa de gol",
    "{n} headed shots.\nCells with fewer than\n12 shots are hidden.":
        "{n} cabeceios.\nCélulas com menos\nde 12 não aparecem.",
    # a2
    "Flick on from a teammate": "Desvio de um companheiro", "Short pass": "Passe curto",
    "Cross in open play": "Cruzamento com bola rolando", "Free kick": "Cobrança de falta",
    "Corner": "Escanteio", "Long ball": "Bola longa",
    "Corners and long balls make the worst headed chances": "Escanteios e bolas longas geram as piores chances de cabeça",
    "Goal rate and on target rate of headed shots by how the ball arrived. Lines are 95% intervals.\n"
    "Corner headers face 8.6 defenders in the box on average (5.9 otherwise) and 63% are under pressure.":
        "Taxa de gol e de acerto no alvo dos cabeceios, pela origem da bola. Linhas são intervalos de 95%.\n"
        "Cabeceios de escanteio enfrentam 8,6 defensores na área (5,9 nos outros) e 63% saem sob pressão.",
    "Scored": "Gol", "On target": "No alvo",
    "Delivery type  (headed shots)": "Tipo de bola  (cabeceios)",
    # a3
    "Location decides goals, the delivery shapes accuracy": "O local decide o gol, a bola recebida define a pontaria",
    "Share of each model's accuracy lost when one factor is scrambled (permutation importance,\n"
    "gradient boosting, tested on held out matches). Height did not make either list.":
        "Parte da precisão de cada modelo perdida quando um fator é embaralhado (importância por permutação,\n"
        "gradient boosting, testado em jogos separados). A altura não entrou em nenhuma das listas.",
    "What makes a header a goal": "O que faz o cabeceio virar gol", "What puts it on target": "O que põe a bola no alvo",
    # a4
    "Headed finishing shows no clear skill signal": "Finalizar de cabeça não mostra sinal claro de talento",
    "Goals vs expected goals on headers for the {n} players with 25+ headed shots. Reliability is about\n"
    "zero (95% interval below 0 to {hi}), so with this few players moderate skill cannot be ruled out.":
        "Gols contra gols esperados de cabeça dos {n} jogadores com 25+ cabeceios. A confiabilidade é quase zero\n"
        "(intervalo de 95% de abaixo de 0 a {hi}), mas com tão poucos jogadores um talento moderado é possível.",
    "Expected headed goals (model)": "Gols de cabeça esperados (modelo)", "Actual headed goals": "Gols de cabeça marcados",
    "Gray band": "Faixa cinza",
    "Where 90% of players\nwould land if every\nheader were a coin flip\nat its xG.\n\n"
    "{out} of {n} players fall\noutside it. Luck alone\nwould put about {exp} there.":
        "Onde 90% dos jogadores\nficariam se cada\ncabeceio fosse um sorteio\ncom a chance do seu xG.\n\n"
        "{out} de {n} jogadores ficam\nfora dela. Só a sorte\ncolocaria cerca de {exp} ali.",
    "Dot size = headed shots": "Tamanho = finalizações de cabeça",
    # d1
    "Every few centimetres changes the aerial duel": "Poucos centímetros mudam o duelo aéreo",
    "Share of aerial duels won by the defending player, by how much taller he is than the attacker.\n"
    "Band is the 95% interval. Ends are capped at 20 cm.":
        "Porcentagem de duelos aéreos ganhos pelo defensor, pela diferença de altura para o atacante.\n"
        "A faixa é o intervalo de 95%. As pontas param em 20 cm.",
    "Defender height minus attacker height (cm)": "Altura do defensor menos a do atacante (cm)",
    "Defender wins the duel": "Defensor ganha o duelo", "coin flip": "cara ou coroa",
    "Same height: defender still wins {p}": "Mesma altura: o defensor ainda ganha {p}",
    "{n} duels with both heights known": "{n} duelos com as duas alturas conhecidas",
    # d2
    "Clear it far from your own goal": "Afaste a bola longe do seu gol",
    "Chance the opponent gets a shot within 10 seconds of a defensive header, by where the header\n"
    "was made. Own goal at the bottom.":
        "Chance de o adversário finalizar em até 10 segundos depois de um cabeceio defensivo, pelo local\n"
        "do cabeceio. O próprio gol fica embaixo.",
    "Opponent shot\nwithin 10 s": "Finalização rival\nem até 10 s",
    "{n} defensive headers\nCells with fewer than\n40 headers are hidden":
        "{n} cabeceios\nCélulas com menos\nde 40 não aparecem",
    # d3
    "Defenders who win more headers than their height says": "Defensores que ganham mais pelo alto do que a altura indica",
    "Aerial duels won above or below expected per 100, for {n} defenders with 100+ duels. Lines are\n"
    "95% ranges. The rank range shows where each could really sit among all {n}.":
        "Duelos aéreos ganhos acima ou abaixo do esperado a cada 100, para {n} defensores com 100+ duelos. Linhas\n"
        "são faixas de 95%. A faixa de posição mostra onde cada um pode estar de verdade entre os {n}.",
    "{lo} to {hi}": "{lo} a {hi}",
    "Duels won above expected per 100 (shrunk, line = 95% range)":
        "Duelos ganhos acima do esperado a cada 100 (ajustado, linha = faixa de 95%)",
    "95% rank\nrange": "Faixa de\nposição 95%",
    "Top 10": "10 melhores", "Bottom 5": "5 piores",
    # d4
    "Aerial duels won vs expected": "Duelos aéreos ganhos vs esperado",
    "Headers on target vs expected": "Cabeceios no alvo vs esperado",
    "Opponent shots prevented after clearing": "Finalizações rivais evitadas após afastar",
    "Next ball won after clearing": "Segunda bola ganha após afastar",
    "Headed goals minus xG": "Gols de cabeça menos xG",
    "Attack and defense": "Ataque e defesa", "Attack": "Ataque", "Defense": "Defesa",
    "Only one header skill clearly repeats": "Só um talento no jogo aéreo se repete com clareza",
    "Reliability of each metric, the average over 200 random match splits, corrected to the full sample.\n"
    "Lines are 95% intervals. 0 means pure luck, 1 means pure skill.":
        "Confiabilidade de cada métrica, média de 200 divisões aleatórias dos jogos, corrigida para a amostra toda.\n"
        "Linhas são intervalos de 95%. 0 quer dizer pura sorte, 1 quer dizer puro talento.",
    "below 0": "abaixo de 0", "{est}  ({lo} to {hi})": "{est}  ({lo} a {hi})",
    "{name}\n{side}, {p} players": "{name}\n{side}, {p} jogadores", "repeatable": "se repete",
    # m1
    "Header xG predictions match reality": "O xG de cabeça bate com a realidade",
    "Headed shots grouped into ten equal bins by predicted chance of a goal. Each dot compares the average\n"
    "prediction with the share that went in. Lines are 95% intervals from resampling matches.":
        "Finalizações de cabeça divididas em dez grupos iguais pela chance prevista de gol. Cada ponto compara a\n"
        "previsão média com a parte que entrou. Linhas são intervalos de 95% com reamostragem de jogos.",
    "This project's xG": "xG deste projeto", "StatsBomb xG": "xG da StatsBomb",
    "Predicted chance of a goal (bin average)": "Chance prevista de gol (média do grupo)",
    "Share of headers scored": "Cabeceios que viraram gol", "perfect calibration": "calibração perfeita",
    "Calibration slope": "Inclinação de calibração",
    "This project  {a}\n   95%  {b} to {c}\nStatsBomb  {d}\n   95%  {e} to {f}":
        "Este projeto  {a}\n   95%  {b} a {c}\nStatsBomb  {d}\n   95%  {e} a {f}",
    "1 is ideal. Below 1 means\npredictions are a bit too\nextreme, above 1 a bit too\ncautious.":
        "1 é o ideal. Abaixo de 1\nas previsões são extremas\ndemais, acima de 1 são\ncautelosas demais.",
    "Average prediction": "Previsão média",
    "This project  {a}\nStatsBomb  {b}\nActual goal rate  {c}": "Este projeto  {a}\nStatsBomb  {b}\nTaxa real de gol  {c}",
    # m2
    "Two methods, nearly the same ranking": "Dois métodos, quase o mesmo ranking",
    "Aerial duels above expected per 100 for {n} ranked players, from the empirical Bayes ranking and\n"
    "from a mixed effects model that also adjusts for opponents. Rank correlation {r} (95% interval {lo} to {hi}).":
        "Duelos aéreos acima do esperado a cada 100 para {n} jogadores, por Bayes empírico e por um modelo misto\n"
        "que também ajusta pelo adversário. Correlação de postos {r} (intervalo de 95% de {lo} a {hi}).",
    "Moved up 40+ places in the mixed model": "Subiu 40+ posições no modelo misto",
    "Empirical Bayes, duels above expected per 100": "Bayes empírico, duelos acima do esperado a cada 100",
    "Mixed model, duels above expected per 100": "Modelo misto, duelos acima do esperado a cada 100",
    "What differs": "O que muda",
    "The mixed model estimates\nevery player at once, so a win\nagainst a strong header of the\n"
    "ball counts for more. Players\nwho faced stronger opponents\nmove up (orange).\n\n"
    "Moving up and opponent\nstrength correlate {r}.":
        "O modelo misto estima todos\nos jogadores de uma vez, então\nganhar de um adversário forte\n"
        "pelo alto vale mais. Quem\nenfrentou adversários mais\nfortes sobe (laranja).\n\n"
        "Subir e a força do adversário\ntêm correlação de {r}.",
}

NICE_PT = {
    "dist": "Distância ao gol", "angle": "Ângulo para o gol", "gk_dist_shooter": "Distância do goleiro ao cabeceio",
    "gk_dist_goal": "Goleiro adiantado", "gk_in_cone": "Goleiro na linha do chute",
    "nearest_opp_dist": "Espaço até o defensor mais perto", "n_def_in_cone": "Defensores na linha do chute",
    "n_att_in_cone": "Companheiros na linha do chute", "n_opp_within_2m": "Defensores a até 2 jardas",
    "n_opp_in_box": "Defensores na área", "aerial_won": "Cabeceio após ganhar a disputa",
    "dlv_pace": "Velocidade da bola", "dlv_length": "Distância da bola",
    "dlv_flight_time": "Tempo de voo da bola", "dlv_technique": "Bola fechada, aberta ou reta",
    "dlv_type": "Tipo de bola", "dlv_height": "Altura da bola", "dlv_start_x": "Onde a bola saiu (profundidade)",
    "dlv_wide": "Quão aberta a bola saiu", "turn_angle": "Quanto o cabeceio desvia a bola",
    "diving": "Cabeceio de peixinho", "in_six": "Dentro da pequena área", "score_diff": "Diferença no placar",
    "height_cm": "Altura do jogador", "def_height_cm": "Altura do defensor", "att_height_cm": "Altura do atacante",
    "height_diff": "Diferença de altura", "x": "Distância da própria linha de fundo", "wide": "Quão aberto foi o cabeceio",
    "in_own_box": "Dentro da própria área", "def_pos": "Posição do defensor", "att_pos": "Posição do atacante",
    "play_pattern": "Fase do jogo", "f360_opp_within_3m": "Adversários a até 3 jardas (dados 360)",
    "dist_own_goal": "Distância do próprio gol", "under_pressure": "Sob pressão",
    "pos_group": "Posição do jogador", "f360_opp_within_10m": "Adversários a até 10 jardas (dados 360)",
    "f360_nearest_opp": "Adversário mais perto (dados 360)",
}
