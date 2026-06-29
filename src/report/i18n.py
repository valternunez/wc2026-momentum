"""Bilingual string catalog for the editorial site (English + Spanish).

Single source of truth for every human-readable string on the report page — the long-form
prose, UI labels, modal / tooltip / share-card text, stage names and month abbreviations.
`build_site` selects a language, fills the `{{TOKEN}}` placeholders in `editorial_copy.TEMPLATE`
and injects the JS `T` object. The English values are the originals lifted from the template;
the Spanish values are a natural (neutral / international) translation. To edit copy, change the
`en`/`es` value side by side here — the structure stays single-source.

Values may embed *data* tokens (e.g. `{{N_MATCHES}}`); build_site substitutes tokens in a few
passes so one level of nesting resolves. HTML inside a value is inserted verbatim.
"""

from __future__ import annotations

LANGS = ("en", "es")

# Country/national-team names: FotMob's English string → Mexican Spanish. Applied to displayed
# team names on the ES build only (cards, extremes, modal/share). Anything not listed falls back
# to the original string, so an unmapped team just shows its English name (safe degradation).
COUNTRIES = {
    # nations currently in the data
    "Algeria": "Argelia", "Argentina": "Argentina", "Australia": "Australia", "Austria": "Austria",
    "Belgium": "Bélgica", "Bosnia and Herzegovina": "Bosnia y Herzegovina", "Brazil": "Brasil",
    "Canada": "Canadá", "Cape Verde": "Cabo Verde", "Colombia": "Colombia", "Croatia": "Croacia",
    "Curacao": "Curazao", "Czechia": "Chequia", "DR Congo": "RD Congo", "Ecuador": "Ecuador",
    "Egypt": "Egipto", "England": "Inglaterra", "France": "Francia", "Germany": "Alemania",
    "Ghana": "Ghana", "Haiti": "Haití", "Iran": "Irán", "Iraq": "Irak", "Ivory Coast": "Costa de Marfil",
    "Japan": "Japón", "Jordan": "Jordania", "Mexico": "México", "Morocco": "Marruecos",
    "Netherlands": "Países Bajos", "New Zealand": "Nueva Zelanda", "Norway": "Noruega",
    "Panama": "Panamá", "Paraguay": "Paraguay", "Portugal": "Portugal", "Qatar": "Qatar",
    "Saudi Arabia": "Arabia Saudita", "Scotland": "Escocia", "Senegal": "Senegal",
    "South Africa": "Sudáfrica", "South Korea": "Corea del Sur", "Spain": "España", "Sweden": "Suecia",
    "Switzerland": "Suiza", "Tunisia": "Túnez", "Turkiye": "Turquía", "USA": "Estados Unidos",
    "Uruguay": "Uruguay", "Uzbekistan": "Uzbekistán",
    # other likely WC2026 nations not yet seen in the data (future-proofing)
    "Italy": "Italia", "Denmark": "Dinamarca", "Poland": "Polonia", "Serbia": "Serbia",
    "Nigeria": "Nigeria", "Mali": "Malí", "Costa Rica": "Costa Rica", "Honduras": "Honduras",
    "Jamaica": "Jamaica", "Venezuela": "Venezuela", "Peru": "Perú", "Chile": "Chile", "Wales": "Gales",
    "Greece": "Grecia", "Bolivia": "Bolivia", "Ukraine": "Ucrania", "Nicaragua": "Nicaragua",
    "El Salvador": "El Salvador", "Guatemala": "Guatemala", "Trinidad and Tobago": "Trinidad y Tobago",
    "Türkiye": "Turquía",
}

# Masthead date month abbreviations (1-indexed; [0] unused). Output is upper-cased downstream.
MONTHS = {
    "en": ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "es": ["", "ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
}

# Stage labels for the match grid. {letter} is filled per group. Knockout keys mirror FotMob rounds.
STAGE = {
    "en": {"1/16": "Round of 32", "1/8": "Round of 16", "1/4": "Quarter-finals",
           "1/2": "Semi-finals", "bronze": "Third-place play-off", "final": "Final",
           "group": "Group {letter}", "other": "Other matches"},
    "es": {"1/16": "Dieciseisavos de final", "1/8": "Octavos de final", "1/4": "Cuartos de final",
           "1/2": "Semifinales", "bronze": "Tercer puesto", "final": "Final",
           "group": "Grupo {letter}", "other": "Otros partidos"},
}

# Stoppage-type labels (money chart + mechanism cards).
LABELS = {
    "en": {"hydration": "Hydration break", "var": "VAR review",
           "injury_huddle": "Injury · with sub", "injury_no_huddle": "Injury · no sub"},
    "es": {"hydration": "Pausa de hidratación", "var": "Revisión del VAR",
           "injury_huddle": "Lesión · con cambio", "injury_no_huddle": "Lesión · sin cambio"},
}

# Short stoppage-type words used inside running text / tooltips (lower-case).
TYPES = {
    "en": {"hydration": "hydration", "var": "VAR", "injury_huddle": "injury with sub",
           "injury_no_huddle": "injury no sub", "other": "other"},
    "es": {"hydration": "hidratación", "var": "VAR", "injury_huddle": "lesión con cambio",
           "injury_no_huddle": "lesión sin cambio", "other": "otra"},
}

# JS runtime strings, injected as `var T = {...}`. %H / %A are replaced with the team names in JS.
JS = {
    "en": {
        "svgTitle": "%H v %A momentum",
        "svgSummary": "%H versus %A per-minute momentum. Wave above the line means %H on top, below means %A. Dashed lines mark stoppages; dots mark goals.",
        "goal": "Goal",
        "miss": "Missed penalty",
        "penMiss": "pen miss",
        "minutesTracked": "minutes tracked",
        "stoppagesDetected": "stoppages detected",
        "shareKicker": "WC2026 · STOPPAGE MOMENTUM",
        "shareMinutes": "minutes",
        "shareStoppages": "stoppages",
        "onTop": "on top",
        "legHydration": "HYDRATION",
        "legVar": "VAR",
        "legInjury": "INJURY",
        "legGoal": "GOAL",
        "shareFoot": "FotMob per-minute momentum",
        "shareBtn": "↓&nbsp;SHARE IMAGE",
        "rendering": "RENDERING…",
        "shareNavTitle": "%H %A · momentum",
        "dataLabel": "Chart data",
        "thMin": "Min",
        "thEvent": "Event",
        "thMomentum": "Momentum",
        "thLeader": "On top",
        "types": {"hydration": "hydration", "var": "VAR", "injury_huddle": "injury with sub",
                  "injury_no_huddle": "injury no sub", "other": "other"},
    },
    "es": {
        "svgTitle": "%H v %A · momentum",
        "svgSummary": "Momentum por minuto de %H frente a %A. La onda por encima de la línea significa que %H domina; por debajo, %A. Las líneas discontinuas marcan pausas; los puntos, goles.",
        "goal": "Gol",
        "miss": "Penal fallado",
        "penMiss": "penal fallado",
        "minutesTracked": "minutos registrados",
        "stoppagesDetected": "pausas detectadas",
        "shareKicker": "WC2026 · MOMENTUM EN PAUSAS",
        "shareMinutes": "minutos",
        "shareStoppages": "pausas",
        "onTop": "dominando",
        "legHydration": "HIDRATACIÓN",
        "legVar": "VAR",
        "legInjury": "LESIÓN",
        "legGoal": "GOL",
        "shareFoot": "Momentum por minuto de FotMob",
        "shareBtn": "↓&nbsp;COMPARTIR IMAGEN",
        "rendering": "GENERANDO…",
        "shareNavTitle": "%H %A · momentum",
        "dataLabel": "Datos del gráfico",
        "thMin": "Min",
        "thEvent": "Evento",
        "thMomentum": "Momentum",
        "thLeader": "Domina",
        "types": {"hydration": "hidratación", "var": "VAR", "injury_huddle": "lesión con cambio",
                  "injury_no_huddle": "lesión sin cambio", "other": "otra"},
    },
}

# Fragment strings used by build_site's HTML-builder functions (not direct template tokens).
# Several carry {placeholders} filled with str.format / .replace in build_site.
FRAG = {
    "en": {
        "tab_all": "All",
        "tab_group": "Group stage",
        "tab_knockout": "Knockouts",
        "tabs_aria": "Filter matches by stage",
        "cards_pending": "Match panels render on the next local update.",
        "open_chart_aria": "{h} v {a} · open chart",
        "card_img_alt": "{h} v {a} · per-minute momentum",
        "extremes_biggest": "Biggest swings",
        "extremes_quietest": "Quietest breaks",
        "extremes_vs": "v",
        "extremes_from": "from",
        "info_aria": "What does this mean?",
        "compare_not_enough": "Not enough data yet to compare stoppage types.",
        "compare_var_ratio": "about {ratio}× a VAR review",
        "compare_ratio": "roughly {ratio}× an injury stoppage with no sub",
        "compare_default": "the largest swing of any stoppage type",
        "compare_and": " and ",
        "compare_sentence": "A hydration break costs the leading side {comp}. Based on {n} breaks logged so far.",
        "cc_hyd_label": "Hydration break",
        "cc_hyd_sub": "World Cup 2026 · the headline",
        "cc_p26_label": "No break: same 2026 matches",
        "cc_p26_sub": "the same teams, at quiet minutes · the cleanest control",
        "cc_euro_label": "No break: Euro 2024",
        "cc_euro_sub": "European national teams · at the 22′/67′ marks",
        "cc_copa_label": "No break: Copa América 2024",
        "cc_copa_sub": "S. American NT, US summer · noisy (CI nearly touches zero)",
        "cc_gold_label": "No break: Gold Cup 2025",
        "cc_gold_sub": "CONCACAF national teams, same US/Canada hosts · at the 22′/67′ marks",
        "cc_cwc_label": "No break: Club World Cup 2025",
        "cc_cwc_sub": "clubs, not national teams · the high outlier",
        "cc_wc22_label": "No break: World Cup 2022",
        "cc_wc22_sub": "national teams, cooler Qatar · at the 22′/67′ marks",
        "cc_matches": " · {m} matches",
        "cc_leg_break": "filled = a mandated break",
        "cc_leg_ctrl": "hollow = no break (control)",
        "cc_leg_2026": "same 2026 teams",
        "cc_leg_nt": "other national teams",
        "cc_leg_club": "club football",
        "cc_axis_dir": "← further left = the leader sheds more momentum after the break",
        "tip_copa": "Copa América 2024: national teams in the same US summer, a similar size to the Gold Cup baseline ({{COPA_N}} windows, one per break, counting only the side that was ahead, so an odd number is normal). Of the no-break baselines, its −{{COPA_DELTA}} is the lowest and least stable: the interval nearly touches zero. Read it next to the others, not on its own.",
        "tip_gold": "CONCACAF Gold Cup 2025: the closest match to WC2026. National teams in the same US/Canada host region and June heat, many of them 2026 sides too, measured at quiet minutes ({{GOLD_N}} windows). It lands at −{{GOLD_DELTA}}, right with the other no-break baselines. (2023 is left out: FotMob has no minute-by-minute momentum for it.)",
        "tip_read": "How to read this: the dot is the average momentum drop for the team that was on top; the faint bar around it is the 95% range, where the true value very likely sits given how few matches there are so far. When two bars overlap a lot, those numbers aren't meaningfully different yet.",
        "tip_placebo": "The exact same 2026 matches, but measured at random quiet minutes with no break (around 10', 35', 55' and 80'). It shows how much the leading team fades with no whistle at all: the pure cool-off baseline, i.e. regression to the mean.",
        "tip_bootstrap": "The 95% interval is the margin of error. We build it by rebuilding the dataset thousands of times, each time drawing whole matches at random (with replacement) and re-taking the average, then keeping the middle 95% of those averages. We resample whole matches, not single breaks, because two breaks in the same game aren't independent evidence. Counting matches as the unit keeps the band honestly wide instead of falsely narrow.",
        "trend_label": "Live analysis",
        "trend_sentence": '''Recomputed every matchday from the committed dataset. As of {updated}, the hydration swing sits at <strong style="font-weight:600">{est}</strong> across {n} on-top breaks. Watch it as the knockouts arrive: more matches should tighten the interval.''',
        "exp_no_df": "Per-minute momentum for {home} (home, blue) vs {away} (away, orange).",
        "exp_no_stop": "Per-minute momentum for {home} vs {away}. No stoppages detected.",
        "exp_lead_marginal": "play was roughly even, with {leader} a shade ahead",
        "exp_lead_moderate": "{leader} had the upper hand",
        "exp_lead_strong": "{leader} were well on top",
        "exp_lost": '''In the five minutes before the <span class="ev-min">{m}'</span> hydration break, {lead}; in the five after, they gave up <span class="ev-mom">{x}</span> momentum.''',
        "exp_pushed": '''In the five minutes before the <span class="ev-min">{m}'</span> hydration break, {lead}; in the five after, they pushed <span class="ev-mom">{x}</span> further ahead.''',
        "exp_held": '''In the five minutes before the <span class="ev-min">{m}'</span> hydration break, {lead}; in the five after, momentum held roughly steady.''',
        "exp_swing": '''Biggest post-stoppage swing: <span class="ev-mom">{x}</span> at the <span class="ev-min">{m}'</span> {type}.''',
        "exp_fallback": "Per-minute momentum for {home} vs {away}.",
    },
    "es": {
        "tab_all": "Todos",
        "tab_group": "Fase de grupos",
        "tab_knockout": "Eliminatorias",
        "tabs_aria": "Filtrar partidos por fase",
        "cards_pending": "Los paneles de partidos se generarán en la próxima actualización local.",
        "open_chart_aria": "{h} vs {a} · abrir gráfico",
        "card_img_alt": "{h} vs {a} · momentum por minuto",
        "extremes_biggest": "Mayores caídas",
        "extremes_quietest": "Pausas más tranquilas",
        "extremes_vs": "vs",
        "extremes_from": "desde",
        "info_aria": "¿Qué significa esto?",
        "compare_not_enough": "Aún no hay datos suficientes para comparar tipos de interrupción.",
        "compare_var_ratio": "alrededor de {ratio}× una revisión del VAR",
        "compare_ratio": "aproximadamente {ratio}× una pausa por lesión sin cambio",
        "compare_default": "la mayor variación de cualquier tipo de interrupción",
        "compare_and": " y ",
        "compare_sentence": "Una pausa de hidratación le cuesta al equipo que domina {comp}. Con base en {n} pausas registradas hasta ahora.",
        "cc_hyd_label": "Pausa de hidratación",
        "cc_hyd_sub": "Mundial 2026 · el titular",
        "cc_p26_label": "Sin pausa: mismos partidos de 2026",
        "cc_p26_sub": "los mismos equipos, en minutos tranquilos · el control más limpio",
        "cc_euro_label": "Sin pausa: Euro 2024",
        "cc_euro_sub": "selecciones europeas · en los minutos 22′/67′",
        "cc_copa_label": "Sin pausa: Copa América 2024",
        "cc_copa_sub": "selecciones sudamericanas, verano de EE. UU. · ruidoso (su IC casi toca el cero)",
        "cc_gold_label": "Sin pausa: Copa Oro 2025",
        "cc_gold_sub": "selecciones de CONCACAF, mismas sedes de EE. UU./Canadá · en los minutos 22′/67′",
        "cc_cwc_label": "Sin pausa: Mundial de Clubes 2025",
        "cc_cwc_sub": "clubes, no selecciones · el valor atípico alto",
        "cc_wc22_label": "Sin pausa: Mundial 2022",
        "cc_wc22_sub": "selecciones, invierno más fresco de Qatar · en los minutos 22′/67′",
        "cc_matches": " · {m} partidos",
        "cc_leg_break": "relleno = pausa obligatoria",
        "cc_leg_ctrl": "hueco = sin pausa (control)",
        "cc_leg_2026": "mismos equipos de 2026",
        "cc_leg_nt": "otras selecciones",
        "cc_leg_club": "futbol de clubes",
        "cc_axis_dir": "← más a la izquierda = el líder pierde más momentum tras la pausa",
        "tip_copa": "Copa América 2024: selecciones en el mismo verano de EE. UU., de un tamaño parecido a la línea base de la Copa Oro ({{COPA_N}} ventanas, una por pausa, contando solo al equipo que iba arriba, así que un número impar es normal). De las líneas base sin pausa, su −{{COPA_DELTA}} es el más bajo y el menos estable: su intervalo casi toca el cero. Léelo junto a los demás, no por sí solo.",
        "tip_gold": "Copa Oro 2025 de CONCACAF: lo más parecido al Mundial 2026. Selecciones en la misma región sede de EE. UU./Canadá y el calor de junio, varias también equipos de 2026, medidas en minutos tranquilos ({{GOLD_N}} ventanas). Queda en −{{GOLD_DELTA}}, justo con las demás líneas base sin pausa. (2023 se excluye: FotMob no tiene su momentum minuto a minuto.)",
        "tip_read": "Cómo leer esto: el punto es la caída media de momentum para el equipo que dominaba; la barra tenue a su alrededor es el rango del 95%, donde muy probablemente está el valor real dado los pocos partidos que hay hasta ahora. Cuando dos barras se solapan mucho, esos números todavía no son significativamente distintos.",
        "tip_placebo": "Exactamente los mismos partidos de 2026, pero medidos en minutos tranquilos al azar sin pausa (alrededor de los 10', 35', 55' y 80'). Muestra cuánto se desinfla el equipo que domina sin ningún silbatazo: la línea base pura de enfriamiento, es decir, regresión a la media.",
        "tip_bootstrap": "El intervalo del 95% es el margen de error. Lo construimos reconstruyendo los datos miles de veces: cada vez tomamos partidos enteros al azar (con reemplazo), volvemos a promediar, y nos quedamos con el 95% central de esos promedios. Remuestreamos partidos enteros, no pausas sueltas, porque dos pausas del mismo partido no son evidencia independiente. Tomar el partido como unidad mantiene la banda honestamente ancha en vez de falsamente estrecha.",
        "trend_label": "Análisis en vivo",
        "trend_sentence": '''Se recalcula cada jornada a partir del conjunto de datos versionado. Al {updated}, la variación por hidratación se sitúa en <strong style="font-weight:600">{est}</strong> a lo largo de {n} pausas con un equipo dominando. Síguela a medida que llegan las eliminatorias: más partidos deberían ajustar el intervalo.''',
        "exp_no_df": "Momentum por minuto de {home} (local, azul) vs {away} (visitante, naranja).",
        "exp_no_stop": "Momentum por minuto de {home} vs {away}. No se detectaron pausas.",
        "exp_lead_marginal": "el juego estaba parejo, con {leader} apenas al frente",
        "exp_lead_moderate": "{leader} llevaba la iniciativa",
        "exp_lead_strong": "{leader} dominaba con claridad",
        "exp_lost": '''En los cinco minutos previos a la pausa de hidratación del minuto <span class="ev-min">{m}'</span>, {lead}; en los cinco siguientes, perdió <span class="ev-mom">{x}</span> de momentum.''',
        "exp_pushed": '''En los cinco minutos previos a la pausa de hidratación del minuto <span class="ev-min">{m}'</span>, {lead}; en los cinco siguientes, sacó <span class="ev-mom">{x}</span> más de ventaja.''',
        "exp_held": '''En los cinco minutos previos a la pausa de hidratación del minuto <span class="ev-min">{m}'</span>, {lead}; en los cinco siguientes, el momentum se mantuvo casi igual.''',
        "exp_swing": '''Mayor variación tras una pausa: <span class="ev-mom">{x}</span> en el minuto <span class="ev-min">{m}'</span> ({type}).''',
        "exp_fallback": "Momentum por minuto de {home} vs {away}.",
    },
}

# Static template tokens (UPPERCASE keys == {{TOKEN}} names in editorial_copy.TEMPLATE).
STRINGS = {
    "en": {
        "META_TITLE": "Do hydration breaks really kill momentum? · WC2026",
        "META_DESC": "Do FIFA's mandatory hydration breaks shift in-match momentum at the 2026 World Cup? A live, data-driven analysis, updated every matchday.",
        "OG_SITENAME": "WC2026 Stoppage Momentum",
        "OG_TITLE": "Do hydration breaks really kill momentum?",
        "OG_DESC": "FIFA made hydration breaks mandatory at the 2026 World Cup. The team on top drops ~{{HERO_DELTA}} momentum points after one, but the same teams drop ~{{P26_DELTA}} with no break. Mostly regression to the mean, with an ~{{GAP}}-point gap left to explain. A live, data-driven analysis.",
        "OG_ALT": "Do hydration breaks really kill momentum? -{{HERO_DELTA}} after a break vs about -{{P26_DELTA}} for the same teams with no break.",
        "TW_DESC": "The team on top drops ~{{HERO_DELTA}} momentum points after a hydration break, but the same teams drop ~{{P26_DELTA}} with no break. Mostly regression to the mean, with a gap left over.",
        "MAST_TITLE": "WC2026",
        "NAV_METHOD": "Methodology",
        "NAV_METHOD_FOOT": "Methodology &amp; the full report",
        "LIVE_UPDATED": "LIVE · UPDATED",
        "FRESH_NOTE": "The live scraper hasn't refreshed in a while; this data was last updated",
        "HERO_KICKER": "The Hydration-Break Momentum Study",
        "HERO_H1": "Do hydration breaks really kill momentum?",
        "HERO_LEDE": "FIFA made in-match hydration breaks mandatory at the 2026 World Cup. Coaches and pundits call them momentum killers. Through {{N_MATCHES}} matches the team on top really does sag after a break, but it sags nearly as much with no break at all.",
        "HERO_BYLINE": "BY VALTER NUNEZ",
        "HERO_META": "{{N_MATCHES}} MATCHES · {{N_STOPPAGES}} STOPPAGES",
        "BAND_CAPTION": '''momentum points: the average swing <em style="font-style:italic;color:#E5C9A0">away</em> from the team on top in the five minutes after a hydration break, though the same teams sag about {{P26_DELTA}} with no break at all.''',
        "BAND_SUB1": "MEAN OF {{HYD_N}} BREAKS WHERE A TEAM HELD THE EDGE",
        "S01_HEAD": "01 — The claim: hydration breaks change the game",
        "S01_LEAD": "Every match it's the same beat. The referee blows for the mandated break midway through each half, both sides jog to the touchline for three minutes of water and instructions. Plenty of people have an opinion about it — players, pundits, fans — but almost no one has measured whether it actually moves the game.",
        "S01_QUOTE": '''"Hydration breaks are a bit interesting … every time going to a commercial is a bit — not really that I like it. If it's really hot it would be good to put them in. But you have to look at it in every game, separately."''',
        "S01_ATTR": '''Virgil van Dijk · Netherlands captain, after the 2–2 draw with Japan · <a class="src" href="https://www.espn.com/soccer/story/_/id/49071612/virgil-van-dijk-criticises-world-cup-hydration-breaks">ESPN</a>''',
        "S01_FOLLOW": '''Van Dijk's gripe is flow and ad breaks. The real debate, however, is tactical, and even the TV booth has a name for it: Emma Hayes (the USWNT head coach, on ITV) calls them <em style="font-style:italic">momentum breaks</em>: <span style="color:#1A1813">"advantageous for the team losing momentum … when you're on top, you don't want it; when you're losing, you do."</span> <a class="src" href="https://www.espn.com/soccer/story/_/id/48945011/why-there-drinks-breaks-2026-world-cup-fifa-criticised">[ESPN]</a> The data is where that claim gets tested.''',
        "S02_HEAD": "02 — What every stoppage does",
        "S02_MOMLABEL": 'What "momentum" means here',
        "S02_MOMDEF": '''An index of which side is on top, built from the flow of attacks, shots and dangerous moves, not the scoreline. Positive means the home team is pressing, negative the away team. The project <em style="font-style:italic">reads</em> the number from <strong style="font-weight:600">FotMob's</strong> per-minute momentum, it doesn't compute one; all it does is measure how it moves in the five minutes either side of a stoppage.''',        "S02_LEAD": "Take the team on top before a break and track what it loses over the next five minutes, split by what kind of stoppage cut in. Every stoppage type leans the same way, though the hydration break leans the furthest.",
        "S02_CHARTLABEL": "MEAN MOMENTUM CHANGE FOR THE TEAM ON TOP",
        "S03_HEAD": "03 — Match by match",
        "S03_LEAD": '''The result is built from every match, all filterable by stage. The wave rises when the <strong style="font-weight:600">home</strong> side is on top, drops when the <strong style="font-weight:600">away</strong> side takes over, and dashed lines mark detected stoppages. <span style="color:#6B6557">Click any match for the full interactive chart.</span>''',
        "S03_EXTREMES_HEAD": "The extremes",
        "S03_EXTREMES_LEAD": 'Where a hydration break landed hardest, and where it barely registered. Each row is a match\'s biggest swing for the side that was on top; the figure after "from" is how high they were riding when the whistle blew. Click any to open the chart.',
        "LEG_HOME": "HOME ON TOP",
        "LEG_AWAY": "AWAY ON TOP",
        "LEG_HYDRATION": "HYDRATION",
        "LEG_VAR": "VAR",
        "LEG_INJURY": "INJURY",
        "LEG_GOAL": "GOAL",
        "S03_FOOTNOTE": "Per-minute momentum rendered from FotMob (derived analysis only; raw payloads not redistributed). One panel per scraped match; stoppage markers from the reconciled FotMob + ESPN commentary feed.",
        "S04_HEAD": "04 — How is it different from other stoppages?",
        "S04_LEAD": "Line the stoppages up by how much of a coaching window they create, and the momentum swing roughly tracks them. The more a break looks like a timeout, the harder the leading team tends to fall.",
        "MECH_HYD_LABEL": "Hydration break",
        "MECH_HYD_DESC": "Three scheduled minutes. Full organised huddle, water, tactical reset.",
        "MECH_VAR_LABEL": "VAR review",
        "MECH_VAR_DESC": "A long pause, players idle, but no formal touchline instruction.",
        "MECH_IH_LABEL": "Injury · with sub",
        "MECH_IH_DESC": "Unscheduled, but a substitution was made: fresh legs and a word from the bench.",
        "MECH_INH_LABEL": "Injury · no sub",
        "MECH_INH_DESC": "Quick stoppage, play resumes before anyone regroups.",
        "S04_DURATION": '''ESPN times every break from the whistle to the resume: a median of <strong style="font-weight:600;color:#EFEBDF">{{DUR_MEDIAN}}</strong> (from {{DUR_MIN}} to {{DUR_MAX}}), two to three times longer than a typical injury stoppage, and remarkably consistent. Does a <em style="font-style:italic">longer</em> break hit the leader harder? Here the data can't say: the long breaks dip a little deeper (about −{{DUR_LONG}} vs −{{DUR_SHORT}} for the short ones), but that gap is too small to separate from noise. So what seems to matter is <strong style="font-weight:600;color:#EFEBDF">that there's a long break at all</strong>, not small differences in how long it runs.''',
        "S04_CONCL": '''If a hydration break were only about <em style="font-style:italic">rest</em>, a long VAR pause should match it. So far it doesn't quite, which hints at the <strong style="font-weight:600;color:#EFEBDF">coaching window</strong> a break creates. Belgium's Rudi Garcia put it plainly: <span style="color:#EFEBDF">"for me, it's a coaching break more than a cooling break."</span> <a class="src" href="https://www.aljazeera.com/sports/2026/6/20/hydration-break-boos-how-fifa-united-players-fans-coaches-at-world-cup">[Al Jazeera]</a> The comparison is by stoppage type rather than perfectly duration-matched (the breaks themselves are timed, but VAR and injury timings are patchier), and the "with sub" injury split is confounded by the substitution itself. Once pre-break momentum is controlled for, the hydration and VAR intervals <strong style="font-weight:600;color:#EFEBDF">overlap</strong>. Not a verdict, but suggestive. And a VAR pause still lets a coach shout instructions from the touchline, so at most this comparison understates the coaching window rather than inventing it.''',
        "S05_HEAD": "05 — The catch",
        "S05_LEAD1": '''A team that just had a blazing five minutes tends to cool off <em style="font-style:italic">anyway</em>, break or no break. This is called regression to the mean<button type="button" class="info" aria-label="What does this mean?" data-tip="Regression to the mean: a team that just had a hot five minutes tends to cool off in the next five anyway, break or no break. It's a natural pull back toward average, not something the break caused.">i</button>, and it's the single biggest threat to reading too much into the results above.''',
        "S05_LEAD2": "So run the <em style=\"font-style:italic\">exact same measurement</em> where no break was mandated (on the same FotMob scale) and put the −{{HERO_DELTA}} next to it. The cleanest control is the very same 2026 matches at quiet minutes: −{{P26_DELTA}}. Add national-team football with no breaks at all (World Cup 2022 at −{{WC22_DELTA}}, Euro 2024 at −{{EURO_DELTA}}, the same-host Gold Cup 2025 at −{{GOLD_DELTA}}, the noisier Copa América 2024 at −{{COPA_DELTA}}), and the no-break baseline lands around −{{NOBREAK_LO}} to −{{NOBREAK_HI}}. So most of the −{{HERO_DELTA}} is the team cooling off anyway. But not all of it: the break still sits about {{GAP}} {{GAP_PTS}} below the same teams with no whistle, {{GAP_CLAUSE}}.",
        "S05_CAVEAT_BOX": '''Same statistic, same scale. The gold-standard control is the same 2026 teams at quiet minutes (−{{P26_DELTA}}), and Euro 2024, World Cup 2022 and the same-host Gold Cup 2025 land right with it (−{{EURO_DELTA}}, −{{WC22_DELTA}}, −{{GOLD_DELTA}}): national-team football regresses about −{{NOBREAK_LO}} to −{{NOBREAK_HI}} on its own. Clubs swing more (the Club World Cup drops −{{CWC_DELTA}}), which is why an earlier club-only comparison flattered the "same drop" read. The break (−{{HERO_DELTA}}) sits about {{GAP}} {{GAP_PTS}} below the same-teams control once their pre-break level is matched, {{GAP_CLAUSE}}. The sample is small, so it's suggestive, not proven. <span style="color:#5A5547">(An event-xT cross-check on 2022 agrees the slide is real.)</span>''',
        "S05_CONCL": '''That's why the model controls for pre-break momentum and clusters its errors by match, and why there's no causal headline yet: the live sample is still small and the signed-off fixed-effects test finds no break-vs-rest difference so far. The break-vs-no-break gap is the ~{{GAP}}-point question the project keeps watching. The full model is in the <a class="src" href="method.html#findings">methodology</a>.''',
        "GAP_CLAUSE_OPEN": "but with the matches logged so far, that gap's 95% interval ({{GAP_LO}} to {{GAP_HI}} points) still includes zero, not yet distinguishable from no effect",
        "GAP_CLAUSE_SIG": "and that gap's 95% interval ({{GAP_LO}} to {{GAP_HI}} points) now sits clear of zero",
        "GAP_PTS_ONE": "point",
        "GAP_PTS_MANY": "points",
        "TWFE_CLAUSE_NULL": '''The signed-off fixed-effects model agrees there is nothing to call yet: the hydration&#215;pre-momentum interaction (the "momentum killer" term) is <strong>{{TWFE_COEF}}</strong> (95% CI {{TWFE_CI}}, p&nbsp;=&nbsp;{{TWFE_P}}, n&nbsp;=&nbsp;{{TWFE_N}}), indistinguishable from zero. That is the honest current state, not a held-back result.''',
        "TWFE_CLAUSE_SIG": '''The signed-off fixed-effects model now estimates the hydration&#215;pre-momentum interaction (the "momentum killer" term) at <strong>{{TWFE_COEF}}</strong> (95% CI {{TWFE_CI}}, p&nbsp;=&nbsp;{{TWFE_P}}, n&nbsp;=&nbsp;{{TWFE_N}}).''',
        "TWFE_CLAUSE_HELD": "The signed-off fixed-effects model is held until the live sample is large enough for a stable estimate.",
        "S06_HEAD": "06 — Did they even need them?",
        "S06_LEAD": '''If the momentum case against the breaks is thin, the heat case <em style="font-style:italic">for</em> them is barely there. FIFA mandates a break in every match. But cooling breaks were built for genuine heat stress, and most of these games never came close.''',
        "HEAT_DESC32": 'matches reached <strong style="font-weight:600">WBGT 32°C</strong>, the level that traditionally triggers a cooling break',
        "HEAT_DESC_DOME": 'were played in <strong style="font-weight:600">air-conditioned domes</strong>, climate already controlled',
        "HEAT_DESC_MEDIAN": 'median match WBGT, short of the <strong style="font-weight:600">28°C</strong> high-risk line ({{HEAT_HOT28}} cleared it)',
        "S06_CONCL": "So most matches got a mandatory three-minute interruption with neither a momentum effect nor a heat reason. The breaks may still be worth it for the handful of genuinely brutal afternoons. But a fixed, every-match rule is hard to justify as a heat measure in most matches. And even this WBGT, estimated in the shade, runs cooler than the pitch.",
        "S06_ALT": '''And altitude is a different argument: {{HEAT_ALT}} matches sat above 1,500 m (Mexico City, Guadalajara), where thinner air is its own fatigue load. That might justify a breather, but it's a separate stressor this momentum analysis doesn't measure, and it isn't what a <em style="font-style:italic">cooling</em> break is for.''',
        "S06_ACCL": '''A different objection is the heat itself: maybe momentum swings more because players from cool leagues wilt in the US summer, not because of any whistle. So the project checked, mapping every player to his club's home city and comparing that heat to match day. Teams furthest from their home climate didn't drop harder; across clubs and across national teams alike, the link came out flat or slightly backwards. The big drops aren't acclimatization. They're regression to the mean. <a class="src" href="method.html#heat">How it was tested →</a>''',
        "S06_FOOTNOTE": "WBGT (wet-bulb globe temperature) approximated from Open-Meteo temperature + humidity at each venue and kickoff. Altitude (Mexico City and Guadalajara sit above 1,500 m) shapes fatigue, not hydration need; the signal for a cooling break is heat and humidity.",
        "BOTTOM_HEAD": "The bottom line, so far",
        "BOTTOM_LEAD_OPEN": "On the surface it's a momentum killer. But it's mostly regression to the mean, and the break's extra bite isn't proven yet.",
        "BOTTOM_LEAD_SIG": "Most of it is regression to the mean, but the break's extra bite is now real, not just noise.",
        "BOTTOM_T1_LABEL": "Momentum",
        "BOTTOM_T1": "The leader sags about −{{HERO_DELTA}} after a break, yet the same teams sag −{{P26_DELTA}} at quiet minutes with no whistle. That leaves a gap of about {{GAP}} (95% CI {{GAP_LO}} to {{GAP_HI}}).",
        "BOTTOM_T2_LABEL": "Heat",
        "BOTTOM_T2": "Most matches never reached the heat a cooling break is built for, so a mandatory break in every game is hard to justify on heat alone.",
        "BOTTOM_T3_LABEL": "What's next",
        "BOTTOM_T3": "The knockouts decide whether that gap firms up or fades. The verdict stays open until the July 19 final.",
        "FOOT_OUTCOME_H": "OUTCOME",
        "FOOT_OUTCOME_T": "FotMob's per-minute momentum index: their model of which side is on top, from the flow of attacks and chances. Read here, not computed. Reframed per team, windowed 5 minutes either side of each stoppage.",
        "FOOT_ID_H": "IDENTIFICATION",
        "FOOT_ID_T": "Type-contrast of hydration vs VAR vs injury stoppages. Stoppages detected from ESPN commentary (not a hardcoded clock), with break durations now measured from ESPN's start/end-delay timestamps (hydration well-covered; VAR/injury patchier).",
        "FOOT_CAV_H": "CAVEATS HANDLED",
        "FOOT_CAV_T": "Regression to the mean (2022 historical placebo), score-state asymmetry, substitutions at the break, match-clustered confidence intervals.",
        "FOOT_REPRO_H": "REPRODUCE",
        "FOOT_REPRO_T": "Daily-updating dataset and live report regenerate from the committed parquet through the July 19 final.",
        "FOOT_REPRO_LINK": "github.com/valternunez/wc2026-momentum ↗",
        "FOOT_STAMP1": "WC2026 STOPPAGE MOMENTUM STUDY · SNAPSHOT {{SNAPSHOT_DATE}}",
        "FOOT_STAMP2": "LIVE ANALYSIS · NUMBERS COMPUTED FROM THE COMMITTED DATASET",
        "CI_CAPTION": "95% INTERVAL (CLUSTER BOOTSTRAP)",
        "INTERVAL_NOTE": "The bars show the 95% margin of error, computed match by match; all of them fall on the negative side. The effect doesn't hinge on the window we picked (it shows up the same at 4, 5, or 6 minutes), but with few matches so far, read it as a signal, not proof. And looking only at the team that was on top doesn't rule out that team simply drifting back to its normal level on its own; that's what the no-break comparison below controls for. The causal claim waits for more matches.",
        "MODAL_KICKER": "Match momentum",
        "MODAL_CLOSE": "CLOSE ✕",
        "MODAL_CLOSE_ARIA": "Close",
        "MODAL_HOME": "Home",
        "MODAL_AWAY": "Away",
        "MODAL_ONTOP": "on top",
        "CTL_COLOURS": "COLOURS",
        "CTL_EDITORIAL": "EDITORIAL",
        "CTL_KITS": "TEAM KITS",
        "CTL_MODE": "MODE",
        "CTL_LIGHT": "LIGHT",
        "CTL_DARK": "DARK",
        "CTL_SHARE": "&#8595;&nbsp;SHARE IMAGE",
        "MODAL_CHARTNOTE": "Per-minute momentum, FotMob (home-positive). Hover the chart for values.",
        # --- Story mode (vertical 9:16 share slideshow) ---
        "STORY_META_TITLE": "The story: do hydration breaks kill momentum? · WC2026",
        "STORY_META_DESC": "A swipe-through visual story of the WC2026 hydration-break momentum finding.",
        "STORY_KICKER": "WC2026 · STOPPAGE MOMENTUM",
        "STORY_ENTRY": "Story",
        "STORY_BACK": "Read the full analysis",
        "STORY_OPEN": "Open story mode",
        "STORY_HINT": "Tap to advance · swipe back",
        "STORY_SAVE": "Save image",
        "STORY_VIDEO": "Download video",
        "STORY_REPLAY": "Replay",
        "STORY_NEXT": "Next",
        "STORY_PREV": "Previous",
        "STORY_OF": "of",
        # slide 1 — hook
        "STORY_HOOK_H": "Do hydration breaks really kill momentum?",
        "STORY_HOOK_SUB": "FIFA made them mandatory at the 2026 World Cup. Coaches call them momentum killers. Here's what {{N_MATCHES}} matches of data actually say.",
        # slide 2 — the claim
        "STORY_CLAIM_LABEL": "THE CLAIM",
        "STORY_CLAIM_H": "Stop a team that's flying, and the spell breaks.",
        "STORY_CLAIM_SUB": "Coaches and pundits call the breaks momentum killers. It's the conventional wisdom, so we measured it.",
        # slide 3 — the drop
        "STORY_DROP_LABEL": "AFTER A HYDRATION BREAK",
        "STORY_DROP_UNIT": "momentum, team on top",
        "STORY_DROP_SUB": "The leading side really does sag after a break. On the surface, the momentum killer looks real.",
        # slide 4 — the catch
        "STORY_CATCH_LABEL": "…BUT WITH NO BREAK",
        "STORY_CATCH_UNIT": "same teams, quiet minutes",
        "STORY_CATCH_SUB": "The same teams sag at break-free minutes too. Most of the drop is just regression to the mean: a hot spell cooling off on its own.",
        # slide 5 — the verdict
        "STORY_VERDICT_LABEL": "WHAT'S LEFT OVER",
        "STORY_VERDICT_UNIT": "points below no break",
        "STORY_VERDICT_SUB": "The break still sits about {{GAP}} {{GAP_PTS}} below the same teams with no whistle, {{GAP_CLAUSE}}.",
        # slide 6 — CTA
        "STORY_CTA_H": "A live analysis.",
        "STORY_CTA_SUB": "Updated daily through the July 19 final. Every number traces to the committed dataset.",
        "STORY_CTA_URL": "valternunez.github.io/wc2026-momentum",
        # --- Share bar ---
        "SHARE_LABEL": "Share",
        "SHARE_WHATSAPP": "WhatsApp",
        "SHARE_X": "X",
        "SHARE_TELEGRAM": "Telegram",
        "SHARE_COPY": "Copy link",
        "SHARE_COPIED": "Copied!",
        "SHARE_NATIVE": "Share…",
        "SHARE_TITLE": "WC2026 · Stoppage Momentum",
        "SHARE_TEXT": "Do hydration breaks really kill momentum? A live, data-driven look at the 2026 World Cup:",
        # --- Reel / TikTok (~15s kinetic myth-buster video) ---
        "REEL_META_TITLE": "Reel · WC2026 Stoppage Momentum",
        "REEL_KICKER": "WC2026 · STOPPAGE MOMENTUM",
        "REEL_HOOK1": "Hydration breaks",
        "REEL_HOOK_KILL": "kill",
        "REEL_HOOK2": "momentum.",
        "REEL_HOOK_TAG": "— every coach, ever",
        "REEL_PROOF_LABEL": "after a break",
        "REEL_PROOF_TAG": "the team on top sags. case closed?",
        "REEL_TWIST_KICKER": "except…",
        "REEL_TWIST_LABEL": "with NO break",
        "REEL_TWIST_LINE": "it's mostly regression to the mean.",
        "REEL_VERDICT_KICKER": "the real gap",
        "REEL_VERDICT_OPEN": "still includes zero, not proven yet.",
        "REEL_VERDICT_SIG": "now clear of zero: the break really bites.",
        "REEL_CTA": "{{N_MATCHES}} matches · updated daily",
        "REEL_CTA_URL": "valternunez.github.io/wc2026-momentum",
        "REEL_LINK": "Reel",
        # --- Methodology / full-report page ---
        "METHOD_META_TITLE": "Methodology & full report · WC2026 Stoppage Momentum",
        "METHOD_META_DESC": "How the WC2026 hydration-break momentum analysis is built: the data, how a stoppage becomes a momentum number, the no-break baselines, regression to the mean, the heat / acclimatization check, and the honest limits.",
        "METHOD_KICKER": "Methodology & the full report",
        "METHOD_H1": "How this was built",
        "METHOD_LEDE": "Every number on the main page comes from one committed dataset and the code in this repository. Here is what that dataset is, how a stoppage becomes a momentum number, what the comparisons control for, and where the honest limits are.",
        "METHOD_BACK": "← The story",
        "METHOD_PDF_LABEL": "Download the full report (PDF)",
        "METHOD_FOOT": "WC2026 STOPPAGE MOMENTUM STUDY · METHODOLOGY · EVERY FIGURE COMPUTED FROM THE COMMITTED DATASET",
        "METHOD_FINDINGS": '''<h2>00 — Findings in brief</h2>
<p>The team on top of momentum loses about <strong>−{{HERO_DELTA}}</strong> momentum points in the five minutes after a mandatory hydration break. But the <em style="font-style:italic">same</em> teams lose about <strong>−{{P26_DELTA}}</strong> at quiet, break-free minutes, so most of the drop is regression to the mean, the natural cool-off after a hot spell, not the whistle.</p>
<p>What is left is a gap of about <strong>{{GAP}}</strong> {{GAP_PTS}} between a break and no break for the same teams; {{GAP_CLAUSE}}, and the sample is still small, so it is suggestive, not proven. A separate look at the weather suggests most matches never reached the heat a cooling break is designed for. None of this is a causal verdict yet. The knockouts will sharpen it.</p>''',
        "METHOD_WHAT": '''<h2>01 — What this measures</h2>
<p>The question is narrow and testable: do FIFA's mandatory in-match hydration breaks shift momentum away from the team that was on top? The outcome is <strong>FotMob's</strong> per-minute momentum index, their model of which side is on top, built from the flow of attacks and chances, not the scoreline. The project <em style="font-style:italic">reads</em> that number; it does not compute one. Positive means the home side is pressing, negative the away side.</p>
<p>It is a live analysis: the page rebuilds from the committed dataset every matchday through the July 19 final, so the figures move as data accrues.</p>''',
        "METHOD_DATA": '''<h2>02 — Where the data comes from</h2>
<p>Three sources, each doing one job:</p>
<ul>
<li><strong>FotMob</strong>: the per-minute momentum series, and match lineups (used for the heat check).</li>
<li><strong>ESPN</strong>: text commentary, which gives the exact timing of stoppages (and VAR / injury events), so breaks are detected from what actually happened, not a hardcoded clock.</li>
<li><strong>Open-Meteo</strong>: temperature and humidity at each venue and kickoff for WBGT, and the historical climate of clubs' home cities for the acclimatization check.</li>
</ul>
<p>The project publishes <em style="font-style:italic">derived</em> data only: the processed dataset and dated summaries are committed to the repo, but raw scraped payloads are never redistributed, out of respect for the sources' terms. Scraping runs locally on a home connection; the public site is rebuilt by CI from the committed dataset and never scrapes. Git history is the snapshot system; each day's estimate is a commit.</p>''',
        "METHOD_PIPE": '''<h2>03 — From a stoppage to a number</h2>
<p>For every detected stoppage, two five-minute windows of momentum are taken: the <strong>pre</strong> window (the five minutes before the whistle) and the <strong>post</strong> window (the five minutes after), excluding the stoppage minute itself. The outcome is the change between them: <code>momentum_delta = post mean − pre mean</code>.</p>
<p>Momentum is home-positive, so each stoppage produces <em style="font-style:italic">two</em> rows, one from each team's perspective (the away row is just the negative). Because they mirror each other, the pooled average is zero by construction. So the project always reports the team that was <strong>on top</strong> before the break. The "momentum killer" claim is specifically that a break pushes momentum away from whoever was ahead.</p>''',
        "METHOD_BASELINES": '''<h2>04 — The comparison baselines</h2>
<p>A team that just had a blazing five minutes tends to cool off anyway, break or no break. That regression to the mean is the single biggest threat to reading the raw drop as an effect. So the project runs the <em style="font-style:italic">exact same measurement</em> where no break was mandated, on the same FotMob scale, and compares:</p>
<ul>
<li><strong>The same 2026 teams at quiet minutes</strong> (−{{P26_DELTA}}): the cleanest control, identical teams, identical tournament, just no whistle. Anything fixed about a team (its quality, its heat, its altitude) is differenced out here.</li>
<li><strong>World Cup 2022</strong> (−{{WC22_DELTA}}) and <strong>Euro 2024</strong> (−{{EURO_DELTA}}): national-team football in cooler settings, no mandated breaks.</li>
<li><strong>Copa América 2024</strong> (−{{COPA_DELTA}}): national teams in US summer heat, but a noisier single edition.</li>
<li><strong>CONCACAF Gold Cup 2025</strong> (−{{GOLD_DELTA}}): national teams in the same US/Canada host region and June heat as 2026, many of them 2026 sides too. The closest no-break analog. The 2023 edition is excluded because FotMob carries no per-minute momentum for it.</li>
<li><strong>Club World Cup 2025</strong> (−{{CWC_DELTA}}): clubs, which regress harder than national teams; a contrast, not a like-for-like.</li>
</ul>
<p>National-team football regresses about −{{NOBREAK_LO}} to −{{NOBREAK_HI}} on its own. The break (−{{HERO_DELTA}}) sits about {{GAP}} {{GAP_PTS}} below the same-teams control once their pre-break level is matched, {{GAP_CLAUSE}}.</p>''',
        "METHOD_CI": '''<h2>05 — Confidence intervals</h2>
<p>Several stoppages within one match are not independent, so intervals are bootstrapped by resampling <em style="font-style:italic">matches</em>, not rows (a cluster bootstrap). Early in the tournament there are few match-clusters, so the 95% interval is wide; read it as indicative, not a precise p-value. The effect holds whether the window is 4, 5 or 6 minutes long. The headline currently rests on {{HYD_N}} on-top hydration breaks, and the estimate-over-time chart on the main page shows whether it is stabilizing or fading.</p>
<p>{{TWFE_CLAUSE}}</p>''',
        "METHOD_HEAT": '''<h2>06 — The heat &amp; acclimatization check</h2>
<p>The intuitive objection is that the swings are about heat, not the whistle: players from cool leagues wilting in the US summer. The project tested it directly. For every team it built an <em style="font-style:italic">acclimatization gap</em>: the WBGT on match day minus the WBGT the squad is used to back home, mapping each player to his club's home city ({{ACCL_CLUBS}} clubs placed). If heat-displacement drove the drops, teams further from home should fall harder.</p>
<p>They do not. Across tournaments the biggest gap goes with the <em style="font-style:italic">smallest</em> drop, not the largest:</p>
<table><thead><tr><th>Tournament</th><th>heat gap</th><th>drop</th></tr></thead><tbody>
<tr><td>Copa América 2024</td><td>{{ACCL_COPA_GAP}}°C</td><td>{{ACCL_COPA_DROP}}</td></tr>
<tr><td>Club World Cup 2025</td><td>{{ACCL_CWC_GAP}}°C</td><td>{{ACCL_CWC_DROP}}</td></tr>
<tr><td>World Cup 2026</td><td>{{ACCL_WC26_GAP}}°C</td><td>{{ACCL_WC26_DROP}}</td></tr>
<tr><td>Euro 2024</td><td>{{ACCL_EURO_GAP}}°C</td><td>{{ACCL_EURO_DROP}}</td></tr>
</tbody></table>
<p>Within groups it is the same story. Among the Club World Cup clubs the gap→drop slope is {{ACCL_SLOPE_CWC}} per °C [{{ACCL_CWC_LO}}, {{ACCL_CWC_HI}}]; if anything, clubs further from home dropped <em style="font-style:italic">less</em>. Pooled across national teams it is {{ACCL_SLOPE_NAT}} per °C [{{ACCL_NAT_LO}}, {{ACCL_NAT_HI}}], essentially flat. So the big drops are not an acclimatization effect, and the high Club World Cup figure is structural (clubs regress more), not heat.</p>
<p>One honest caveat: the heat gap is tangled up with continent, league and fixture congestion, so this rules out the simple heat story rather than proving a precise null. And it never threatened the headline anyway: the same-teams control already holds a team's heat fixed.</p>''',
        "METHOD_ALT": '''<h2>07 — Altitude</h2>
<p>Altitude is a different stressor from heat (thin air, not thermoregulation), and only two venues are high (Mexico City and Guadalajara, both above 1,500 m). That is too few to test, and a cooling break is not built for it, so it is noted and left alone.</p>''',
        "METHOD_LIMITS": '''<h2>08 — What this can and cannot say</h2>
<ul>
<li><strong>Small sample, for now.</strong> Early in the tournament the intervals are wide; the estimate-over-time chart shows whether the effect stabilizes or fades.</li>
<li><strong>Break durations, now measured.</strong> ESPN's start/end-delay timestamps give an exact length for {{DUR_N}} of {{DUR_N_ALL}} on-top hydration breaks (median {{DUR_MEDIAN}}, {{DUR_MIN}}–{{DUR_MAX}}); VAR and injury coverage is thinner. Whether <em style="font-style:italic">longer</em> breaks bite harder is inconclusive on the current sample (the slope's interval includes zero), so the analysis doesn't lean on it.</li>
<li><strong>WBGT is a shade estimate</strong> from temperature and humidity; true on-pitch heat under sun runs higher.</li>
<li><strong>The acclimatization gap is collinear</strong> with continent, league and schedule, so it is suggestive, not a clean instrument.</li>
<li><strong>No causal headline yet.</strong> The agreed causal model (a two-way fixed-effects regression with match-clustered errors and the hydration×pre-momentum interaction) is held until the live sample is large enough for stable estimates.</li>
</ul>''',
        "METHOD_REPRO": '''<h2>09 — Reproducibility</h2>
<p>Every figure here and on the main page is computed deterministically from one file (the committed processed dataset) by the code in the repository. Nothing is hand-entered. The full source, the dataset, and this report are public.</p>
<p><a class="src" href="{{PAGES_URL}}">github.com/valternunez/wc2026-momentum ↗</a></p>''',
    },
    "es": {
        "META_TITLE": "¿Las pausas de hidratación matan el momentum? · WC2026",
        "META_DESC": "¿Las pausas de hidratación obligatorias de la FIFA cambian el momentum durante los partidos del Mundial 2026? Un análisis en vivo, basado en datos, actualizado cada jornada.",
        "OG_SITENAME": "WC2026 Momentum en Pausas",
        "OG_TITLE": "¿Las pausas de hidratación matan el momentum?",
        "OG_DESC": "La FIFA volvió obligatorias las pausas de hidratación en el Mundial 2026. El equipo dominante pierde ~{{HERO_DELTA}} puntos de momentum tras una, pero los mismos equipos pierden ~{{P26_DELTA}} sin pausa. Sobre todo regresión a la media, con una brecha de ~{{GAP}} {{GAP_PTS}} por explicar. Un análisis en vivo, basado en datos.",
        "OG_ALT": "¿Las pausas de hidratación matan el momentum? -{{HERO_DELTA}} tras una pausa vs aproximadamente -{{P26_DELTA}} para los mismos equipos sin pausa.",
        "TW_DESC": "El equipo dominante pierde ~{{HERO_DELTA}} puntos de momentum tras una pausa de hidratación, pero los mismos equipos pierden ~{{P26_DELTA}} sin pausa. Sobre todo regresión a la media, con una brecha por explicar.",
        "MAST_TITLE": "WC2026",
        "NAV_METHOD": "Metodología",
        "NAV_METHOD_FOOT": "Metodología e informe completo",
        "LIVE_UPDATED": "EN VIVO · ACTUALIZADO",
        "FRESH_NOTE": "El recolector en vivo no se actualiza desde hace un tiempo; estos datos se actualizaron por última vez el",
        "HERO_KICKER": "Estudio de momentum en pausas de hidratación",
        "HERO_H1": "¿Las pausas de hidratación matan el momentum?",
        "HERO_LEDE": "La FIFA volvió obligatorias las pausas de hidratación en el Mundial 2026. Técnicos y comentaristas las llaman asesinas del momentum. A lo largo de {{N_MATCHES}} partidos, el equipo que domina sí se desinfla tras una pausa, pero lo hace casi la misma cantidad sin pausa alguna.",
        "HERO_BYLINE": "POR VALTER NÚÑEZ",
        "HERO_META": "{{N_MATCHES}} PARTIDOS · {{N_STOPPAGES}} PAUSAS",
        "BAND_CAPTION": '''puntos de momentum: la caída media que <em style="font-style:italic;color:#E5C9A0">se aleja</em> del equipo dominante en los cinco minutos posteriores a una pausa de hidratación, aunque los mismos equipos caen unos {{P26_DELTA}} sin pausa alguna.''',
        "BAND_SUB1": "PROMEDIO DE {{HYD_N}} PAUSAS EN LAS QUE UN EQUIPO DOMINABA",
        "S01_HEAD": "01 — La afirmación: las pausas cambian el partido",
        "S01_LEAD": "Cada partido es lo mismo: el árbitro hace una pausa obligatoria hacia la mitad de cada tiempo y ambos equipos trotan hacia la banda para tres minutos de agua e instrucciones. Mucha gente opina al respecto —jugadores, comentaristas, aficionados—, pero casi nadie ha medido si de verdad cambia el partido.",
        "S01_QUOTE": '''«Las pausas de hidratación son un poco curiosas… cada vez que se va a una tanda de comerciales es un poco — no es que me guste demasiado. Si hace mucho calor estaría bien ponerlas. Pero hay que mirarlo en cada partido, por separado.»''',
        "S01_ATTR": '''Virgil van Dijk · capitán de Países Bajos, tras el empate 2–2 con Japón · <a class="src" href="https://www.espn.com/soccer/story/_/id/49071612/virgil-van-dijk-criticises-world-cup-hydration-breaks">ESPN</a>''',
        "S01_FOLLOW": '''La queja de Van Dijk es sobre el ritmo y los cortes comerciales. El verdadero debate, sin embargo, es táctico, y hasta en la cabina de TV tienen un nombre para ello: Emma Hayes (directora técnica de la selección femenina de Estados Unidos, como comentarista en ITV) las llama <em style="font-style:italic">pausas de momentum</em>: <span style="color:#1A1813">«ventajosas para el equipo que está perdiendo el momentum… cuando dominas, no las quieres; cuando vas cayendo, sí.»</span> <a class="src" href="https://www.espn.com/soccer/story/_/id/48945011/why-there-drinks-breaks-2026-world-cup-fifa-criticised">[ESPN]</a> Y es esta misma idea la que los datos de este proyecto ponen a prueba.''',
        "S02_HEAD": "02 — Qué hace cada interrupción",
        "S02_MOMLABEL": "Qué significa «momentum» aquí",
        "S02_MOMDEF": '''Un índice sobre qué equipo domina, construido a partir del flujo de ataques, remates y jugadas de peligro, no del marcador. Positivo significa que presiona el equipo local; negativo, el visitante. Este proyecto <em style="font-style:italic">lee</em> el número del momentum por minuto de <strong style="font-weight:600">FotMob</strong>, no calcula uno nuevo; lo único que hace es medir cómo se mueve en los cinco minutos a cada lado de una interrupción.''',        "S02_LEAD": "Toma al equipo que dominaba antes de una pausa y mira qué pierde en los cinco minutos siguientes, según el tipo de interrupción que lo cortó. Todas las interrupciones se inclinan igual, aunque la de hidratación es la que más lo hace.",
        "S02_CHARTLABEL": "CAMBIO MEDIO DE MOMENTUM PARA EL EQUIPO DOMINANTE",
        "S03_HEAD": "03 — Partido a partido",
        "S03_LEAD": '''El resultado se construye a partir de cada partido, todos filtrables por fase. La onda sube cuando domina el <strong style="font-weight:600">local</strong>, baja cuando toma el control el <strong style="font-weight:600">visitante</strong>, y las líneas discontinuas marcan las pausas detectadas. <span style="color:#6B6557">Da clic en cualquier partido para ver el gráfico interactivo completo.</span>''',
        "S03_EXTREMES_HEAD": "Los extremos",
        "S03_EXTREMES_LEAD": "Dónde una pausa de hidratación golpeó más fuerte, y dónde apenas se hizo notar. Cada fila es la mayor variación de un partido para el equipo que dominaba; la cifra después de «desde» es qué tan alto venía cuando sonó el silbatazo. Toca cualquiera para abrir el gráfico.",
        "LEG_HOME": "LOCAL DOMINA",
        "LEG_AWAY": "VISITANTE DOMINA",
        "LEG_HYDRATION": "HIDRATACIÓN",
        "LEG_VAR": "VAR",
        "LEG_INJURY": "LESIÓN",
        "LEG_GOAL": "GOL",
        "S03_FOOTNOTE": "Momentum por minuto generado a partir de FotMob (solo análisis derivado; no se redistribuyen los datos crudos). Un panel por partido recolectado; los marcadores de pausas provienen del cruce de FotMob + el relato de ESPN.",
        "S04_HEAD": "04 — ¿En qué se diferencia de otras pausas?",
        "S04_LEAD": "Al ordenar las interrupciones según cuánto espacio para dar indicaciones técnicas crean, se ve que la variación de momentum las acompaña a grandes rasgos. Cuanto más se parece una pausa a un tiempo muerto, más fuerte tiende a caer el equipo que dominaba.",
        "MECH_HYD_LABEL": "Pausa de hidratación",
        "MECH_HYD_DESC": "Tres minutos programados. Indicaciones técnicas completas, agua, reinicio táctico.",
        "MECH_VAR_LABEL": "Revisión del VAR",
        "MECH_VAR_DESC": "Una pausa larga, jugadores parados, pero sin instrucción formal desde la banda.",
        "MECH_IH_LABEL": "Lesión · con cambio",
        "MECH_IH_DESC": "No programada, pero hubo un cambio: piernas nuevas y un mensaje desde la banca.",
        "MECH_INH_LABEL": "Lesión · sin cambio",
        "MECH_INH_DESC": "Interrupción breve, el juego se reanuda antes de que nadie se reagrupe.",
        "S04_DURATION": '''ESPN cronometra cada pausa, del silbatazo a la reanudación: una mediana de <strong style="font-weight:600;color:#EFEBDF">{{DUR_MEDIAN}}</strong> (de {{DUR_MIN}} a {{DUR_MAX}}), dos o tres veces más larga que una pausa por lesión típica, y notablemente constante. ¿Una pausa <em style="font-style:italic">más larga</em> golpea más fuerte al que va arriba? Aquí los datos no alcanzan a decirlo: las pausas largas lo enfrían un poco más que las cortas (cerca de −{{DUR_LONG}} frente a −{{DUR_SHORT}}), pero esa diferencia es demasiado chica para distinguirla del ruido. Así que lo que parece pesar es <strong style="font-weight:600;color:#EFEBDF">que haya una pausa larga</strong>, no las pequeñas diferencias en cuánto dura.''',
        "S04_CONCL": '''Si una pausa de hidratación fuera solo cuestión de <em style="font-style:italic">descanso</em>, una pausa del VAR igual de larga debería igualarla. Por ahora no lo hace del todo, lo que apunta a la <strong style="font-weight:600;color:#EFEBDF">ventana de indicaciones técnicas</strong> que crea una pausa. El técnico de Bélgica, Rudi García, lo dijo: <span style="color:#EFEBDF">«para mí, es más una pausa de instrucción que una pausa de enfriamiento.»</span> <a class="src" href="https://www.aljazeera.com/sports/2026/6/20/hydration-break-boos-how-fifa-united-players-fans-coaches-at-world-cup">[Al Jazeera]</a> Se compara por tipo de interrupción más que de forma perfectamente emparejada por duración (se cronometran las pausas, pero los tiempos de VAR y lesión son más irregulares), y la división de lesión «con cambio» está confundida por el propio cambio. Al controlar por el momentum previo, los intervalos de la hidratación y del VAR <strong style="font-weight:600;color:#EFEBDF">se solapan</strong>. Esto no es un veredicto, aunque sí sugerente. Y en una pausa del VAR el técnico igual puede gritar indicaciones desde la banda, así que esta comparación, a lo mucho, subestima la ventana de indicaciones técnicas en lugar de inventarla.''',
        "S05_HEAD": "05 — La trampa",
        "S05_LEAD1": '''Un equipo que acaba de tener cinco minutos brillantes tiende a enfriarse <em style="font-style:italic">de todos modos</em>, con pausa o sin pausa. Esto se llama regresión a la media<button type="button" class="info" aria-label="¿Qué significa esto?" data-tip="Regresión a la media: un equipo que acaba de tener cinco minutos calientes tiende a enfriarse en los cinco siguientes de todos modos, con pausa o sin pausa. Es un retorno natural hacia el promedio, no algo que la pausa haya causado.">i</button>, y es la mayor amenaza para no leer de más en los resultados antes mostrados.''',
        "S05_LEAD2": "Así que se hace exactamente la misma medición donde no hubo pausa obligatoria (en la misma escala de FotMob) y se pone el −{{HERO_DELTA}} al lado. El control más limpio son los mismos partidos de 2026 en minutos tranquilos: −{{P26_DELTA}}. Súmale futbol de selecciones sin pausa alguna (Mundial 2022 en −{{WC22_DELTA}}, Euro 2024 en −{{EURO_DELTA}}, la Copa Oro 2025 en la misma región sede en −{{GOLD_DELTA}}, la más ruidosa Copa América 2024 en −{{COPA_DELTA}}), y la línea base sin pausa queda alrededor de −{{NOBREAK_LO}} a −{{NOBREAK_HI}}. Así que la mayor parte del −{{HERO_DELTA}} es el equipo enfriándose de todos modos. Pero no todo: la pausa todavía queda unos {{GAP}} {{GAP_PTS}} por debajo de los mismos equipos sin silbato, {{GAP_CLAUSE}}.",
        "S05_CAVEAT_BOX": '''Misma estadística, misma escala. El control de referencia son los mismos equipos de 2026 en minutos tranquilos (−{{P26_DELTA}}), y Euro 2024, el Mundial 2022 y la Copa Oro 2025 de la misma región sede caen justo ahí (−{{EURO_DELTA}}, −{{WC22_DELTA}}, −{{GOLD_DELTA}}): el futbol de selecciones regresa por sí solo alrededor de −{{NOBREAK_LO}} a −{{NOBREAK_HI}}. Los clubes oscilan más (el Mundial de Clubes cae −{{CWC_DELTA}}), y por eso una comparación previa solo con clubes inflaba la idea de «la misma caída». La pausa (−{{HERO_DELTA}}) queda unos {{GAP}} {{GAP_PTS}} por debajo del control con los mismos equipos una vez igualado su nivel previo, {{GAP_CLAUSE}}. La muestra es chica, así que es sugerente, no probado. <span style="color:#5A5547">(Un cruce con xT por evento en 2022 coincide en que la caída es real.)</span>''',
        "S05_CONCL": '''Por eso el modelo controla por el momentum previo y agrupa sus errores por partido, y por eso todavía no hay un titular causal: la muestra en vivo aún es chica y la prueba de efectos fijos acordada aún no detecta diferencia entre pausa y el resto. La brecha entre pausa y no-pausa, de unos ~{{GAP}} {{GAP_PTS}}, es la pregunta que el proyecto sigue observando. El modelo completo está en la <a class="src" href="method.es.html#findings">metodología</a>.''',
        "GAP_CLAUSE_OPEN": "pero con los partidos disponibles hasta ahora, el intervalo del 95% de esa brecha ({{GAP_LO}} a {{GAP_HI}} puntos) todavía incluye el cero, aún no se distingue de un efecto nulo",
        "GAP_CLAUSE_SIG": "y el intervalo del 95% de esa brecha ({{GAP_LO}} a {{GAP_HI}} puntos) ya queda lejos del cero",
        "GAP_PTS_ONE": "punto",
        "GAP_PTS_MANY": "puntos",
        "TWFE_CLAUSE_NULL": '''El modelo de efectos fijos acordado coincide en que aún no hay nada que declarar: la interacción hidratación&#215;momentum-previo (el término «asesino del momentum») es <strong>{{TWFE_COEF}}</strong> (IC 95% {{TWFE_CI}}, p&nbsp;=&nbsp;{{TWFE_P}}, n&nbsp;=&nbsp;{{TWFE_N}}), indistinguible de cero. Es el estado honesto actual, no un resultado guardado.''',
        "TWFE_CLAUSE_SIG": '''El modelo de efectos fijos acordado ahora estima la interacción hidratación&#215;momentum-previo (el término «asesino del momentum») en <strong>{{TWFE_COEF}}</strong> (IC 95% {{TWFE_CI}}, p&nbsp;=&nbsp;{{TWFE_P}}, n&nbsp;=&nbsp;{{TWFE_N}}).''',
        "TWFE_CLAUSE_HELD": "El modelo de efectos fijos acordado se mantiene en pausa hasta que la muestra en vivo sea lo bastante grande para una estimación estable.",
        "S06_HEAD": "06 — ¿Acaso hacían falta?",
        "S06_LEAD": '''Si el argumento del momentum en contra de las pausas es flojo, el del calor <em style="font-style:italic">a favor</em> es casi inexistente. La FIFA exige una pausa en cada partido, pero las pausas de hidratación se diseñaron para un estrés térmico real, y la mayoría de estos partidos no se acercan a ese nivel de estrés.''',
        "HEAT_DESC32": 'partidos alcanzaron <strong style="font-weight:600">WBGT 32°C</strong>, el nivel que tradicionalmente justifica una pausa de enfriamiento',
        "HEAT_DESC_DOME": 'se jugaron en <strong style="font-weight:600">estadios techados con aire acondicionado</strong>, clima ya controlado',
        "HEAT_DESC_MEDIAN": 'WBGT mediano por partido, por debajo de la línea de alto riesgo de <strong style="font-weight:600">28°C</strong> ({{HEAT_HOT28}} la superaron)',
        "S06_CONCL": "Así que la mayoría de los partidos tuvieron una interrupción obligatoria de tres minutos, sin efecto sobre el momentum, sin razón climatológica. Las pausas pueden seguir valiendo la pena para el puñado de tardes realmente brutales, pero una regla fija, para cada partido, es difícil de justificar como medida contra el calor en la mayoría de los partidos. Y hasta este WBGT, estimado a la sombra, queda por debajo del calor en la cancha.",
        "S06_ALT": '''Y la altitud es otro argumento: {{HEAT_ALT}} partidos se jugaron por encima de los 1,500 m (Ciudad de México, Guadalajara), donde el aire más delgado es su propia carga de fatiga. Eso quizá justifique un respiro, pero es un factor aparte que este análisis de momentum no mide, y no es para lo que sirve una pausa de <em style="font-style:italic">enfriamiento</em>.''',
        "S06_ACCL": '''Otra objeción es el calor mismo: tal vez el momentum se mueve tanto porque jugadores de ligas frescas se derriten en el verano de Estados Unidos, y no por un silbatazo. Así que se revisó, ligando a cada jugador con la ciudad de su club y comparando ese calor con el del partido. Los equipos más lejos de su clima de casa no cayeron más; entre clubes y entre selecciones, la relación salió plana o ligeramente al revés. Las caídas grandes no son aclimatación: son regresión a la media. <a class="src" href="method.es.html#heat">Cómo se probó →</a>''',
        "S06_FOOTNOTE": "El WBGT (temperatura de globo y bulbo húmedo) se aproxima a partir de la temperatura + humedad de Open-Meteo en cada sede y horario de inicio. La altitud (Ciudad de México y Guadalajara están por encima de los 1,500 m) moldea la fatiga, no la necesidad de hidratación; la señal para una pausa de enfriamiento son el calor y la humedad.",
        "BOTTOM_HEAD": "La conclusión, por ahora",
        "BOTTOM_LEAD_OPEN": "En la superficie parece matar el momentum. Pero es sobre todo regresión a la media, y el plus de la pausa aún no está probado.",
        "BOTTOM_LEAD_SIG": "Casi todo es regresión a la media, pero el plus de la pausa ya es real, no solo ruido.",
        "BOTTOM_T1_LABEL": "Momentum",
        "BOTTOM_T1": "El líder se desinfla unos −{{HERO_DELTA}} tras una pausa, pero los mismos equipos caen −{{P26_DELTA}} en minutos tranquilos, sin silbatazo. Eso deja una brecha de {{GAP}} (IC 95% {{GAP_LO}} a {{GAP_HI}}).",
        "BOTTOM_T2_LABEL": "Calor",
        "BOTTOM_T2": "La mayoría de los partidos nunca alcanzó el calor para el que sirve una pausa de enfriamiento, así que una pausa obligatoria en cada juego es difícil de justificar solo por el calor.",
        "BOTTOM_T3_LABEL": "Lo que sigue",
        "BOTTOM_T3": "Las eliminatorias dirán si esa brecha se afirma o se desvanece. El veredicto sigue abierto hasta la final del 19 de julio.",
        "FOOT_OUTCOME_H": "RESULTADO MEDIDO",
        "FOOT_OUTCOME_T": "El índice de momentum por minuto de FotMob: su modelo de qué equipo domina, a partir del flujo de ataques y ocasiones. Se lee, no se calcula. Reformulado por equipo, en ventanas de 5 minutos a cada lado de cada pausa.",
        "FOOT_ID_H": "IDENTIFICACIÓN",
        "FOOT_ID_T": "Contraste por tipo entre pausas de hidratación, VAR y lesión. Las pausas se detectan a partir del relato de ESPN (no de un reloj fijo), y ahora se cronometra su duración con las marcas de inicio/fin de ESPN (la hidratación bien cubierta; VAR y lesión más irregulares).",
        "FOOT_CAV_H": "ADVERTENCIAS CONTROLADAS",
        "FOOT_CAV_T": "Regresión a la media (placebo histórico de 2022), asimetría según el marcador, sustituciones en la pausa, intervalos de confianza agrupados por partido.",
        "FOOT_REPRO_H": "REPRODUCIR",
        "FOOT_REPRO_T": "El conjunto de datos se actualiza a diario y el informe en vivo se regenera a partir del parquet versionado, hasta la final del 19 de julio.",
        "FOOT_REPRO_LINK": "github.com/valternunez/wc2026-momentum ↗",
        "FOOT_STAMP1": "ESTUDIO WC2026 DE MOMENTUM EN PAUSAS · INSTANTÁNEA {{SNAPSHOT_DATE}}",
        "FOOT_STAMP2": "ANÁLISIS EN VIVO · CIFRAS CALCULADAS A PARTIR DEL CONJUNTO DE DATOS VERSIONADO",
        "CI_CAPTION": "INTERVALO 95% (BOOTSTRAP POR PARTIDO)",
        "INTERVAL_NOTE": "Las barras muestran el margen de error del 95%, calculado partido por partido; todas caen del lado negativo. El efecto no depende de la ventana elegida (aparece igual con 4, 5 o 6 minutos), pero con pocos partidos hasta ahora conviene leerlo como una señal, no como una prueba. Y mirar solo al equipo que dominaba no descarta que ese equipo simplemente volviera a su nivel normal por sí solo; eso lo controla la comparación sin pausa de abajo. La conclusión causal espera a tener más partidos.",
        "MODAL_KICKER": "Momentum del partido",
        "MODAL_CLOSE": "CERRAR ✕",
        "MODAL_CLOSE_ARIA": "Cerrar",
        "MODAL_HOME": "Local",
        "MODAL_AWAY": "Visitante",
        "MODAL_ONTOP": "dominando",
        "CTL_COLOURS": "COLORES",
        "CTL_EDITORIAL": "EDITORIAL",
        "CTL_KITS": "UNIFORMES",
        "CTL_MODE": "MODO",
        "CTL_LIGHT": "CLARO",
        "CTL_DARK": "OSCURO",
        "CTL_SHARE": "&#8595;&nbsp;COMPARTIR IMAGEN",
        "MODAL_CHARTNOTE": "Momentum por minuto, FotMob (local en positivo). Pasa el cursor por el gráfico para ver los valores.",
        # --- Modo historia (presentación vertical 9:16 para compartir) ---
        "STORY_META_TITLE": "La historia: ¿las pausas de hidratación matan el momentum? · WC2026",
        "STORY_META_DESC": "Una historia visual, deslizable, del hallazgo sobre el momentum en las pausas de hidratación del Mundial 2026.",
        "STORY_KICKER": "WC2026 · MOMENTUM EN PAUSAS",
        "STORY_ENTRY": "Historia",
        "STORY_BACK": "Leer el análisis completo",
        "STORY_OPEN": "Abrir modo historia",
        "STORY_HINT": "Toca para avanzar · desliza para volver",
        "STORY_SAVE": "Guardar imagen",
        "STORY_VIDEO": "Descargar video",
        "STORY_REPLAY": "Repetir",
        "STORY_NEXT": "Siguiente",
        "STORY_PREV": "Anterior",
        "STORY_OF": "de",
        # diapositiva 1 — gancho
        "STORY_HOOK_H": "¿Las pausas de hidratación de verdad matan el momentum?",
        "STORY_HOOK_SUB": "La FIFA las volvió obligatorias en el Mundial 2026. Los técnicos las llaman asesinas del momentum. Esto es lo que dicen los datos de {{N_MATCHES}} partidos.",
        # diapositiva 2 — la afirmación
        "STORY_CLAIM_LABEL": "LA AFIRMACIÓN",
        "STORY_CLAIM_H": "Frena a un equipo que vuela y se rompe el hechizo.",
        "STORY_CLAIM_SUB": "Técnicos y comentaristas llaman a las pausas asesinas del momentum. Es la idea popular, así que se midió.",
        # diapositiva 3 — la caída
        "STORY_DROP_LABEL": "TRAS UNA PAUSA DE HIDRATACIÓN",
        "STORY_DROP_UNIT": "momentum, equipo que domina",
        "STORY_DROP_SUB": "El equipo que domina sí se desinfla tras una pausa. En la superficie, la muerte del momentum parece real.",
        # diapositiva 4 — el detalle
        "STORY_CATCH_LABEL": "…PERO SIN PAUSA",
        "STORY_CATCH_UNIT": "mismos equipos, minutos tranquilos",
        "STORY_CATCH_SUB": "Los mismos equipos se desinflan también en minutos sin pausa. La mayor parte es regresión a la media: una racha que se enfría sola.",
        # diapositiva 5 — el veredicto
        "STORY_VERDICT_LABEL": "LO QUE SOBRA",
        "STORY_VERDICT_UNIT": "puntos por debajo de no tener pausa",
        "STORY_VERDICT_SUB": "La pausa todavía queda unos {{GAP}} {{GAP_PTS}} por debajo de los mismos equipos sin silbatazo, {{GAP_CLAUSE}}.",
        # diapositiva 6 — CTA
        "STORY_CTA_H": "Un análisis en vivo.",
        "STORY_CTA_SUB": "Se actualiza a diario hasta la final del 19 de julio. Cada cifra se rastrea al conjunto de datos versionado.",
        "STORY_CTA_URL": "valternunez.github.io/wc2026-momentum",
        # --- Barra de compartir ---
        "SHARE_LABEL": "Compartir",
        "SHARE_WHATSAPP": "WhatsApp",
        "SHARE_X": "X",
        "SHARE_TELEGRAM": "Telegram",
        "SHARE_COPY": "Copiar enlace",
        "SHARE_COPIED": "¡Copiado!",
        "SHARE_NATIVE": "Compartir…",
        "SHARE_TITLE": "WC2026 · Momentum en Pausas",
        "SHARE_TEXT": "¿Las pausas de hidratación de verdad matan el momentum? Un análisis en vivo, basado en datos, del Mundial 2026:",
        # --- Reel / TikTok (video kinético de ~15s, derribando el mito) ---
        "REEL_META_TITLE": "Reel · WC2026 Momentum en Pausas",
        "REEL_KICKER": "WC2026 · MOMENTUM EN PAUSAS",
        "REEL_HOOK1": "Las pausas de hidratación",
        "REEL_HOOK_KILL": "matan",
        "REEL_HOOK2": "el momentum.",
        "REEL_HOOK_TAG": "— dicen todos los técnicos",
        "REEL_PROOF_LABEL": "tras una pausa",
        "REEL_PROOF_TAG": "el que domina se desinfla. ¿caso cerrado?",
        "REEL_TWIST_KICKER": "pero…",
        "REEL_TWIST_LABEL": "SIN pausa",
        "REEL_TWIST_LINE": "es casi toda regresión a la media.",
        "REEL_VERDICT_KICKER": "la brecha real",
        "REEL_VERDICT_OPEN": "aún incluye el cero, sin probar todavía.",
        "REEL_VERDICT_SIG": "ya lejos del cero: la pausa sí pega.",
        "REEL_CTA": "{{N_MATCHES}} partidos · actualizado a diario",
        "REEL_CTA_URL": "valternunez.github.io/wc2026-momentum",
        "REEL_LINK": "Reel",
        # --- Página de metodología / informe completo ---
        "METHOD_META_TITLE": "Metodología e informe completo · WC2026 Momentum en Pausas",
        "METHOD_META_DESC": "Cómo se construye el análisis del momentum en las pausas de hidratación del Mundial 2026: los datos, cómo una pausa se vuelve un número de momentum, las referencias sin pausa, la regresión a la media, la prueba de calor / aclimatación y los límites honestos.",
        "METHOD_KICKER": "Metodología y el informe completo",
        "METHOD_H1": "Cómo se construyó esto",
        "METHOD_LEDE": "Cada número de la página principal sale de un solo conjunto de datos versionado y del código de este repositorio. Aquí está qué es ese conjunto de datos, cómo una pausa se convierte en un número de momentum, qué controlan las comparaciones y dónde están los límites honestos.",
        "METHOD_BACK": "← El reportaje",
        "METHOD_PDF_LABEL": "Descarga el informe completo (PDF)",
        "METHOD_FOOT": "WC2026 ESTUDIO DE MOMENTUM EN PAUSAS · METODOLOGÍA · CADA CIFRA SE CALCULA DESDE EL CONJUNTO DE DATOS VERSIONADO",
        "METHOD_FINDINGS": '''<h2>00 — Los hallazgos, en breve</h2>
<p>El equipo que va arriba en el momentum pierde alrededor de <strong>−{{HERO_DELTA}}</strong> puntos en los cinco minutos después de una pausa de hidratación obligatoria. Pero los <em style="font-style:italic">mismos</em> equipos pierden alrededor de <strong>−{{P26_DELTA}}</strong> en minutos tranquilos, sin pausa, así que la mayor parte de la caída es regresión a la media, el enfriamiento natural tras un buen rato, no el silbatazo.</p>
<p>Lo que queda es una diferencia de unos <strong>{{GAP}}</strong> {{GAP_PTS}} entre pausa y no pausa para los mismos equipos; {{GAP_CLAUSE}}, y la muestra todavía es chica, así que es sugerente, no comprobado. Una mirada aparte al clima sugiere que la mayoría de los partidos nunca llegó al calor para el que sirve una pausa de enfriamiento. Nada de esto es todavía un veredicto causal. La eliminatoria lo afinará.</p>''',
        "METHOD_WHAT": '''<h2>01 — Qué se mide aquí</h2>
<p>La pregunta es acotada y comprobable: ¿las pausas de hidratación obligatorias de la FIFA mueven el momentum en contra del equipo que iba arriba? La variable es el índice de momentum por minuto de <strong>FotMob</strong>, su modelo de qué lado domina, armado con el flujo de ataques y ocasiones, no con el marcador. Aquí se <em style="font-style:italic">lee</em> ese número; no se calcula uno propio. Positivo es que el local aprieta, negativo el visitante.</p>
<p>Es un análisis en vivo: la página se reconstruye desde el conjunto de datos versionado cada jornada hasta la final del 19 de julio, así que las cifras se mueven conforme entran datos.</p>''',
        "METHOD_DATA": '''<h2>02 — De dónde salen los datos</h2>
<p>Tres fuentes, cada una con un trabajo:</p>
<ul>
<li><strong>FotMob</strong>: la serie de momentum por minuto y las alineaciones (que se usan en la prueba de calor).</li>
<li><strong>ESPN</strong>: la narración de texto, que da el momento exacto de las pausas (y de eventos de VAR / lesión), así que las pausas se detectan por lo que de verdad pasó, no por un reloj fijo.</li>
<li><strong>Open-Meteo</strong>: temperatura y humedad en cada sede y horario de inicio para el WBGT, y el clima histórico de las ciudades de los clubes para la prueba de aclimatación.</li>
</ul>
<p>Solo se publican datos <em style="font-style:italic">derivados</em>: el conjunto de datos procesado y los resúmenes con fecha quedan versionados en el repo, pero los datos crudos nunca se redistribuyen, por respeto a los términos de las fuentes. El scraping corre localmente en una conexión de casa; el sitio público lo reconstruye CI desde el conjunto de datos versionado y nunca hace scraping. El historial de git es el sistema de instantáneas; la estimación de cada día es un commit.</p>''',
        "METHOD_PIPE": '''<h2>03 — De una pausa a un número</h2>
<p>Por cada pausa detectada se toman dos ventanas de cinco minutos de momentum: la ventana <strong>previa</strong> (los cinco minutos antes del silbatazo) y la <strong>posterior</strong> (los cinco minutos después), excluyendo el minuto mismo de la pausa. La variable es el cambio entre ambas: <code>momentum_delta = media posterior − media previa</code>.</p>
<p>El momentum es local-en-positivo, así que cada pausa produce <em style="font-style:italic">dos</em> filas, una desde la perspectiva de cada equipo (la del visitante es solo el negativo). Como se reflejan, el promedio agrupado es cero por construcción. Por eso siempre se reporta al equipo que iba <strong>arriba</strong> antes de la pausa. La acusación de "matar el momentum" es justamente que la pausa empuja el momentum lejos de quien iba ganándolo.</p>''',
        "METHOD_BASELINES": '''<h2>04 — Las referencias de comparación</h2>
<p>Un equipo que acaba de tener cinco minutos ardientes tiende a enfriarse de todos modos, con pausa o sin ella. Esa regresión a la media es la mayor amenaza para leer la caída cruda como un efecto. Así que se corre la <em style="font-style:italic">misma medición exacta</em> donde no había pausa obligatoria, en la misma escala de FotMob, y se compara:</p>
<ul>
<li><strong>Los mismos equipos de 2026 en minutos tranquilos</strong> (−{{P26_DELTA}}): el control más limpio, mismos equipos, mismo torneo, solo que sin silbatazo. Todo lo fijo de un equipo (su nivel, su calor, su altitud) se cancela aquí.</li>
<li><strong>Mundial 2022</strong> (−{{WC22_DELTA}}) y <strong>Euro 2024</strong> (−{{EURO_DELTA}}): futbol de selecciones en climas más frescos, sin pausas obligatorias.</li>
<li><strong>Copa América 2024</strong> (−{{COPA_DELTA}}): selecciones en el calor del verano de Estados Unidos, pero una sola edición más ruidosa.</li>
<li><strong>Copa Oro 2025 de CONCACAF</strong> (−{{GOLD_DELTA}}): selecciones en la misma región sede de EE. UU./Canadá y el calor de junio que 2026, varias también equipos de 2026. El análogo sin pausa más cercano. La edición de 2023 se excluye porque FotMob no tiene su momentum minuto a minuto.</li>
<li><strong>Mundial de Clubes 2025</strong> (−{{CWC_DELTA}}): clubes, que regresan más fuerte que las selecciones; un contraste, no una comparación pareja.</li>
</ul>
<p>El futbol de selecciones regresa por su cuenta alrededor de −{{NOBREAK_LO}} a −{{NOBREAK_HI}}. La pausa (−{{HERO_DELTA}}) queda unos {{GAP}} {{GAP_PTS}} por debajo del control de mismos equipos una vez igualado su nivel previo, {{GAP_CLAUSE}}.</p>''',
        "METHOD_CI": '''<h2>05 — Intervalos de confianza</h2>
<p>Varias pausas dentro de un mismo partido no son independientes, así que los intervalos se calculan por bootstrap remuestreando <em style="font-style:italic">partidos</em>, no filas (un bootstrap por conglomerados). Temprano en el torneo hay pocos conglomerados, así que el intervalo del 95% es ancho; léelo como indicativo, no como un valor p preciso. El efecto se sostiene con ventanas de 4, 5 o 6 minutos. Por ahora el titular descansa en {{HYD_N}} pausas de hidratación con equipo arriba, y la gráfica de la estimación a lo largo del torneo, en la página principal, muestra si se está estabilizando o desvaneciendo.</p>
<p>{{TWFE_CLAUSE}}</p>''',
        "METHOD_HEAT": '''<h2>06 — La prueba de calor y aclimatación</h2>
<p>La objeción intuitiva es que los vaivenes son por el calor, no por el silbatazo: jugadores de ligas frescas derritiéndose en el verano de Estados Unidos. Se probó directo. Para cada equipo se armó una <em style="font-style:italic">brecha de aclimatación</em>: el WBGT del día del partido menos el WBGT al que está acostumbrado el plantel en casa, ligando a cada jugador con la ciudad de su club ({{ACCL_CLUBS}} clubes ubicados). Si el calor por desplazamiento moviera las caídas, los equipos más lejos de casa deberían caer más fuerte.</p>
<p>No lo hacen. Entre torneos, la mayor brecha va con la <em style="font-style:italic">menor</em> caída, no con la mayor:</p>
<table><thead><tr><th>Torneo</th><th>brecha</th><th>caída</th></tr></thead><tbody>
<tr><td>Copa América 2024</td><td>{{ACCL_COPA_GAP}}°C</td><td>{{ACCL_COPA_DROP}}</td></tr>
<tr><td>Mundial de Clubes 2025</td><td>{{ACCL_CWC_GAP}}°C</td><td>{{ACCL_CWC_DROP}}</td></tr>
<tr><td>Mundial 2026</td><td>{{ACCL_WC26_GAP}}°C</td><td>{{ACCL_WC26_DROP}}</td></tr>
<tr><td>Euro 2024</td><td>{{ACCL_EURO_GAP}}°C</td><td>{{ACCL_EURO_DROP}}</td></tr>
</tbody></table>
<p>Dentro de cada grupo es la misma historia. Entre los clubes del Mundial de Clubes la pendiente brecha→caída es {{ACCL_SLOPE_CWC}} por °C [{{ACCL_CWC_LO}}, {{ACCL_CWC_HI}}]; si acaso, los clubes más lejos de casa cayeron <em style="font-style:italic">menos</em>. Agrupando las selecciones es {{ACCL_SLOPE_NAT}} por °C [{{ACCL_NAT_LO}}, {{ACCL_NAT_HI}}], prácticamente plana. Así que las caídas grandes no son aclimatación, y la cifra alta del Mundial de Clubes es estructural (los clubes regresan más), no calor.</p>
<p>Un matiz honesto: la brecha de calor está enredada con el continente, la liga y la carga de partidos, así que esto descarta la versión simple del calor más que probar un cero exacto. Y de todos modos nunca amenazó al titular: el control de mismos equipos ya deja fijo el calor de cada equipo.</p>''',
        "METHOD_ALT": '''<h2>07 — Altitud</h2>
<p>La altitud es un factor distinto del calor (aire delgado, no termorregulación), y solo dos sedes son altas (Ciudad de México y Guadalajara, ambas por encima de los 1,500 m). Son muy pocas para probarlo, y una pausa de enfriamiento no es para eso, así que se anota y se deja.</p>''',
        "METHOD_LIMITS": '''<h2>08 — Lo que se puede y no se puede decir</h2>
<ul>
<li><strong>Muestra chica, por ahora.</strong> Temprano en el torneo los intervalos son anchos; la gráfica de la estimación a lo largo del tiempo muestra si el efecto se estabiliza o se desvanece.</li>
<li><strong>Duraciones de pausa, ahora medidas.</strong> Las marcas de inicio/fin de ESPN dan una duración exacta para {{DUR_N}} de {{DUR_N_ALL}} pausas de hidratación con equipo arriba (mediana {{DUR_MEDIAN}}, {{DUR_MIN}}–{{DUR_MAX}}); la cobertura de VAR y lesión es más delgada. Si las pausas <em style="font-style:italic">más largas</em> pegan más fuerte es inconcluso con la muestra actual (el intervalo de la pendiente incluye el cero), así que el análisis no se apoya en eso.</li>
<li><strong>El WBGT es una estimación a la sombra</strong> a partir de temperatura y humedad; el calor real en la cancha bajo el sol es mayor.</li>
<li><strong>La brecha de aclimatación es colineal</strong> con el continente, la liga y el calendario, así que es sugerente, no un instrumento limpio.</li>
<li><strong>Todavía no hay titular causal.</strong> El modelo causal acordado (una regresión de efectos fijos a dos vías, con errores por conglomerado de partido y la interacción hidratación×momentum-previo) se mantiene en pausa hasta que la muestra viva sea lo bastante grande para estimaciones estables.</li>
</ul>''',
        "METHOD_REPRO": '''<h2>09 — Reproducibilidad</h2>
<p>Cada cifra de aquí y de la página principal se calcula de forma determinista desde un solo archivo (el conjunto de datos procesado y versionado) con el código del repositorio. Nada se captura a mano. El código completo, los datos y este informe son públicos.</p>
<p><a class="src" href="{{PAGES_URL}}">github.com/valternunez/wc2026-momentum ↗</a></p>''',
    },
}


def strings(lang: str) -> dict:
    return STRINGS[lang]
