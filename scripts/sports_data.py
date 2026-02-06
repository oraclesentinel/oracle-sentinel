#!/usr/bin/env python3
"""
Sports Data v2 - Layer 2b: Sports Intelligence via SofaSport API
All sports in one API ($0 free / $10 pro per month)
20+ sports, 5000+ leagues, current season data

Endpoints used:
- seasons/standings     → League table
- teams/near-events     → Previous + next match
- teams/recent-form     → Last 5 results
- teams/events          → Match history (paginated)
- events/form           → Both teams form + rating + position
- events/h2h-events     → Head-to-head history
- events/h2h-stats      → H2H summary (wins/draws/losses)
- events/streaks        → Betting streaks (over 2.5, clean sheets, etc)
- events/predict        → Fan voting prediction
- events/lineups        → Starting XI
- events/best-players   → Top rated players
- tournaments/seasons   → Get current season ID
"""

import os
import json
import re
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'polymarket.db')
SOFASPORT_KEY = os.getenv('SOFASPORT_API_KEY', '')
SOFASPORT_HOST = 'sofasport.p.rapidapi.com'

# ─── TOURNAMENT & TEAM ID MAPPINGS ──────────────────────────
# unique_tournament_id from SofaSport
TOURNAMENT_MAP = {
    # Football
    'premier league':      {'ut_id': 17, 'sport': 'football'},
    'english premier league': {'ut_id': 17, 'sport': 'football'},
    'champions league':    {'ut_id': 7,  'sport': 'football'},
    'la liga':             {'ut_id': 8,  'sport': 'football'},
    'serie a':             {'ut_id': 23, 'sport': 'football'},
    'bundesliga':          {'ut_id': 35, 'sport': 'football'},
    'ligue 1':             {'ut_id': 34, 'sport': 'football'},
    'europa league':       {'ut_id': 679, 'sport': 'football'},
    'eredivisie':          {'ut_id': 37, 'sport': 'football'},
    'fa cup':              {'ut_id': 45, 'sport': 'football'},
    'efl cup':             {'ut_id': 17, 'sport': 'football'},
    'copa america':        {'ut_id': 133, 'sport': 'football'},
    'world cup':           {'ut_id': 16, 'sport': 'football'},
    # Basketball / NBA
    'nba':                 {'ut_id': 132, 'sport': 'basketball'},
    'nba championship':    {'ut_id': 132, 'sport': 'basketball'},
    'nba finals':          {'ut_id': 132, 'sport': 'basketball'},
    # American Football / NFL
    'nfl':                 {'ut_id': 9464, 'sport': 'american-football'},
    'super bowl':          {'ut_id': 9464, 'sport': 'american-football'},
    # Ice Hockey / NHL
    'nhl':                 {'ut_id': 234, 'sport': 'ice-hockey'},
    'stanley cup':         {'ut_id': 234, 'sport': 'ice-hockey'},
    # MMA
    'ufc':                 {'ut_id': 11585, 'sport': 'mma'},
    'mma':                 {'ut_id': 11585, 'sport': 'mma'},
    # Formula 1
    'formula 1':           {'ut_id': 70, 'sport': 'motorsport'},
    'f1':                  {'ut_id': 70, 'sport': 'motorsport'},
    # MLB
    'mlb':                 {'ut_id': 11205, 'sport': 'baseball'},
    'world series':        {'ut_id': 11205, 'sport': 'baseball'},
}

# Known team IDs (Sofascore) - 310 teams across 12 leagues
# Auto-generated from standings dump + common short aliases
TEAM_ID_CACHE = {
    # ─── EPL (20 teams) ─────────────────────────────────────
    'wolverhampton': 3, 'wolves': 3,
    'burnley': 6,
    'crystal palace': 7,
    'nottingham forest': 14, 'nottm forest': 14,
    'manchester city': 17, 'man city': 17,
    'brighton & hove albion': 30, 'brighton': 30,
    'tottenham hotspur': 33, 'tottenham': 33, 'spurs': 33,
    'leeds united': 34, 'leeds': 34,
    'manchester united': 35, 'man united': 35, 'man utd': 35,
    'west ham united': 37, 'west ham': 37,
    'chelsea': 38,
    'newcastle united': 39, 'newcastle': 39,
    'aston villa': 40,
    'sunderland': 41,
    'arsenal': 42,
    'fulham': 43,
    'liverpool': 44,
    'everton': 48,
    'brentford': 50,
    'bournemouth': 60,
    # ─── La Liga (20 teams) ─────────────────────────────────
    'espanyol': 2814,
    'real betis': 2816,
    'barcelona': 2817, 'barca': 2817,
    'rayo vallecano': 2818,
    'villarreal': 2819,
    'osasuna': 2820,
    'celta vigo': 2821,
    'real sociedad': 2824,
    'athletic club': 2825, 'athletic bilbao': 2825,
    'mallorca': 2826,
    'valencia': 2828,
    'real madrid': 2829,
    'sevilla': 2833,
    'atletico madrid': 2836, 'atlético madrid': 2836,
    'elche': 2846,
    'levante ud': 2849, 'levante': 2849,
    'real oviedo': 2851,
    'getafe': 2859,
    'deportivo alavés': 2885, 'alaves': 2885,
    'girona fc': 24264, 'girona': 24264,
    # ─── Serie A (20 teams) ─────────────────────────────────
    'bologna': 2685,
    'atalanta': 2686,
    'juventus': 2687, 'juve': 2687,
    'lecce': 2689,
    'parma': 2690,
    'milan': 2692, 'ac milan': 2692,
    'fiorentina': 2693,
    'udinese': 2695,
    'torino': 2696,
    'inter': 2697, 'inter milan': 2697,
    'lazio': 2699,
    'hellas verona': 2701, 'verona': 2701,
    'roma': 2702, 'as roma': 2702,
    'como': 2704,
    'genoa': 2713,
    'napoli': 2714,
    'cagliari': 2719,
    'pisa': 2737,
    'cremonese': 2761,
    'sassuolo': 2793,
    # ─── Bundesliga (18 teams) ──────────────────────────────
    'vfl wolfsburg': 2524, 'wolfsburg': 2524,
    'fc st. pauli': 2526, 'st. pauli': 2526,
    "borussia m'gladbach": 2527, 'gladbach': 2527, 'monchengladbach': 2527,
    'sv werder bremen': 2534, 'werder bremen': 2534,
    'sc freiburg': 2538, 'freiburg': 2538,
    '1. fc union berlin': 2547, 'union berlin': 2547,
    '1. fsv mainz 05': 2556, 'mainz': 2556,
    'tsg hoffenheim': 2569, 'hoffenheim': 2569,
    'fc augsburg': 2600, 'augsburg': 2600,
    '1. fc köln': 2671, 'koln': 2671, 'cologne': 2671,
    'fc bayern münchen': 2672, 'bayern munich': 2672, 'bayern': 2672,
    'borussia dortmund': 2673, 'dortmund': 2673,
    'eintracht frankfurt': 2674, 'frankfurt': 2674,
    'hamburger sv': 2676, 'hamburg': 2676,
    'vfb stuttgart': 2677, 'stuttgart': 2677,
    'bayer 04 leverkusen': 2681, 'leverkusen': 2681,
    '1. fc heidenheim': 5885, 'heidenheim': 5885,
    'rb leipzig': 36360, 'leipzig': 36360,
    # ─── Ligue 1 (18 teams) ─────────────────────────────────
    'olympique de marseille': 1641, 'marseille': 1641,
    'lille': 1643,
    'paris saint-germain': 1644, 'psg': 1644,
    'auxerre': 1646,
    'nantes': 1647,
    'rc lens': 1648, 'lens': 1648,
    'olympique lyonnais': 1649, 'lyon': 1649,
    'metz': 1651,
    'as monaco': 1653, 'monaco': 1653,
    'lorient': 1656,
    'stade rennais': 1658, 'rennes': 1658,
    'rc strasbourg': 1659, 'strasbourg': 1659,
    'nice': 1661,
    'le havre': 1662,
    'toulouse': 1681,
    'angers': 1684,
    'stade brestois': 1715, 'brest': 1715,
    'paris fc': 6070,
    # ─── Eredivisie (18 teams) ──────────────────────────────
    'nac breda': 2947,
    'fc utrecht': 2948, 'utrecht': 2948,
    'az alkmaar': 2950, 'az': 2950,
    'fc groningen': 2951, 'groningen': 2951,
    'psv eindhoven': 2952, 'psv': 2952,
    'afc ajax': 2953, 'ajax': 2953,
    'fc twente': 2955, 'twente': 2955,
    'fortuna sittard': 2957,
    'feyenoord': 2959,
    'sparta rotterdam': 2960,
    'nec nijmegen': 2962, 'nec': 2962,
    'sc heerenveen': 2964, 'heerenveen': 2964,
    'excelsior': 2967,
    'fc volendam': 2968,
    'pec zwolle': 2971,
    'sc telstar': 2972, 'telstar': 2972,
    'heracles almelo': 2977, 'heracles': 2977,
    'go ahead eagles': 2979,
    # ─── Champions League extras ─────────────────────────────
    'bodø/glimt': 656,
    'fc københavn': 1284,
    'sk slavia praha': 2216, 'slavia prague': 2216,
    'club brugge kv': 2888, 'club brugge': 2888,
    'sporting cp': 3001, 'sporting': 3001,
    'benfica': 3006,
    'galatasaray': 3061,
    'olympiacos fc': 3245, 'olympiacos': 3245,
    'royale union saint-gilloise': 4860,
    'qarabağ fk': 5962,
    'pafos fc': 171626,
    # ─── Europa League extras ────────────────────────────────
    'sk brann': 1159,
    'fc midtjylland': 1289,
    'malmö ff': 1892,
    'ferencváros tc': 1925, 'ferencvaros': 1925,
    'gnk dinamo zagreb': 2032, 'dinamo zagreb': 2032,
    'red bull salzburg': 2046, 'salzburg': 2046,
    'sk sturm graz': 2051,
    'rangers': 2351,
    'celtic': 2352,
    'young boys': 2445,
    'basel': 2501,
    'krc genk': 2890, 'genk': 2890,
    'sporting braga': 2999, 'braga': 2999,
    'fc porto': 3002, 'porto': 3002,
    'fenerbahçe': 3052, 'fenerbahce': 3052,
    'panathinaikos fc': 3248, 'panathinaikos': 3248,
    'paok': 3251,
    'fcsb': 3301,
    'viktoria plzeň': 4502, 'plzen': 4502,
    'fk crvena zvezda': 5149, 'red star belgrade': 5149,
    'maccabi tel aviv': 5198,
    'ludogorets': 43840,
    # ─── NBA (30 teams) ─────────────────────────────────────
    'chicago bulls': 3409, 'bulls': 3409,
    'milwaukee bucks': 3410, 'bucks': 3410,
    'dallas mavericks': 3411, 'mavericks': 3411, 'mavs': 3411,
    'houston rockets': 3412, 'rockets': 3412,
    'sacramento kings': 3413, 'kings': 3413,
    'portland trail blazers': 3414, 'trail blazers': 3414, 'blazers': 3414,
    'memphis grizzlies': 3415, 'grizzlies': 3415,
    'phoenix suns': 3416, 'suns': 3416,
    'denver nuggets': 3417, 'nuggets': 3417,
    'oklahoma city thunder': 3418, 'thunder': 3418,
    'indiana pacers': 3419, 'pacers': 3419,
    'philadelphia 76ers': 3420, '76ers': 3420, 'sixers': 3420,
    'new york knicks': 3421, 'knicks': 3421,
    'boston celtics': 3422, 'celtics': 3422,
    'atlanta hawks': 3423, 'hawks': 3423,
    'detroit pistons': 3424, 'pistons': 3424,
    'los angeles clippers': 3425, 'clippers': 3425,
    'minnesota timberwolves': 3426, 'timberwolves': 3426, 'wolves': 3426,
    'los angeles lakers': 3427, 'lakers': 3427,
    'golden state warriors': 3428, 'warriors': 3428,
    'san antonio spurs': 3429,
    'charlotte hornets': 3430, 'hornets': 3430,
    'washington wizards': 3431, 'wizards': 3431,
    'cleveland cavaliers': 3432, 'cavaliers': 3432, 'cavs': 3432,
    'toronto raptors': 3433, 'raptors': 3433,
    'utah jazz': 3434, 'jazz': 3434,
    'miami heat': 3435, 'heat': 3435,
    'brooklyn nets': 3436, 'nets': 3436,
    'orlando magic': 3437, 'magic': 3437,
    'new orleans pelicans': 5539, 'pelicans': 5539,
    # ─── NFL (32 teams) ─────────────────────────────────────
    'miami dolphins': 4287, 'dolphins': 4287,
    'houston texans': 4324, 'texans': 4324,
    'pittsburgh steelers': 4345, 'steelers': 4345,
    'jacksonville jaguars': 4386, 'jaguars': 4386, 'jags': 4386,
    'los angeles rams': 4387, 'rams': 4387,
    'tampa bay buccaneers': 4388, 'buccaneers': 4388, 'bucs': 4388,
    'san francisco 49ers': 4389, '49ers': 4389, 'niners': 4389,
    'las vegas raiders': 4390, 'raiders': 4390,
    'chicago bears': 4391, 'bears': 4391,
    'dallas cowboys': 4392, 'cowboys': 4392,
    'atlanta falcons': 4393, 'falcons': 4393,
    'arizona cardinals': 4412, 'cardinals': 4412,
    'baltimore ravens': 4413, 'ravens': 4413,
    'buffalo bills': 4414, 'bills': 4414,
    'carolina panthers': 4415, 'panthers': 4415,
    'cincinnati bengals': 4416, 'bengals': 4416,
    'cleveland browns': 4417, 'browns': 4417,
    'denver broncos': 4418, 'broncos': 4418,
    'detroit lions': 4419, 'lions': 4419,
    'green bay packers': 4420, 'packers': 4420,
    'indianapolis colts': 4421, 'colts': 4421,
    'kansas city chiefs': 4422, 'chiefs': 4422,
    'minnesota vikings': 4423, 'vikings': 4423,
    'new england patriots': 4424, 'patriots': 4424, 'pats': 4424,
    'new orleans saints': 4425, 'saints': 4425,
    'new york giants': 4426, 'giants': 4426,
    'new york jets': 4427, 'jets': 4427,
    'philadelphia eagles': 4428, 'eagles': 4428,
    'los angeles chargers': 4429, 'chargers': 4429,
    'seattle seahawks': 4430, 'seahawks': 4430,
    'tennessee titans': 4431, 'titans': 4431,
    'washington commanders': 4432, 'commanders': 4432,
    # ─── NHL (32 teams) ─────────────────────────────────────
    'anaheim ducks': 3675, 'ducks': 3675,
    'winnipeg jets': 3676,
    'boston bruins': 3677, 'bruins': 3677,
    'buffalo sabres': 3678, 'sabres': 3678,
    'calgary flames': 3679, 'flames': 3679,
    'carolina hurricanes': 3680, 'hurricanes': 3680, 'canes': 3680,
    'chicago blackhawks': 3681, 'blackhawks': 3681,
    'colorado avalanche': 3682, 'avalanche': 3682, 'avs': 3682,
    'columbus blue jackets': 3683, 'blue jackets': 3683,
    'dallas stars': 3684, 'stars': 3684,
    'detroit red wings': 3685, 'red wings': 3685,
    'edmonton oilers': 3686, 'oilers': 3686,
    'florida panthers': 3687,
    'los angeles kings': 3688,
    'minnesota wild': 3689, 'wild': 3689,
    'montréal canadiens': 3690, 'montreal canadiens': 3690, 'canadiens': 3690, 'habs': 3690,
    'washington capitals': 3691, 'capitals': 3691, 'caps': 3691,
    'vancouver canucks': 3692, 'canucks': 3692,
    'toronto maple leafs': 3693, 'maple leafs': 3693,
    'tampa bay lightning': 3694, 'lightning': 3694,
    'st. louis blues': 3695, 'blues': 3695,
    'san jose sharks': 3696, 'sharks': 3696,
    'pittsburgh penguins': 3697, 'penguins': 3697, 'pens': 3697,
    'philadelphia flyers': 3699, 'flyers': 3699,
    'ottawa senators': 3700, 'senators': 3700, 'sens': 3700,
    'new york rangers': 3701,
    'new york islanders': 3703, 'islanders': 3703,
    'new jersey devils': 3704, 'devils': 3704,
    'nashville predators': 3705, 'predators': 3705, 'preds': 3705,
    'vegas golden knights': 257523, 'golden knights': 257523,
    'seattle kraken': 381707, 'kraken': 381707,
    'utah mammoth': 530472,
    # ─── MLB (30 teams) ─────────────────────────────────────
    'chicago cubs': 3627, 'cubs': 3627,
    'colorado rockies': 3628, 'rockies': 3628,
    'new york mets': 3629, 'mets': 3629,
    'milwaukee brewers': 3630, 'brewers': 3630,
    'st. louis cardinals': 3632,
    'cincinnati reds': 3633, 'reds': 3633,
    'san francisco giants': 3634,
    'philadelphia phillies': 3635, 'phillies': 3635,
    'san diego padres': 3636, 'padres': 3636,
    'pittsburgh pirates': 3637, 'pirates': 3637,
    'los angeles dodgers': 3638, 'dodgers': 3638,
    'miami marlins': 3639, 'marlins': 3639,
    'arizona diamondbacks': 3640, 'diamondbacks': 3640, 'dbacks': 3640,
    'seattle mariners': 3641, 'mariners': 3641,
    'toronto blue jays': 3642, 'blue jays': 3642,
    'chicago white sox': 3644, 'white sox': 3644,
    'athletics': 3645,
    'boston red sox': 3646, 'red sox': 3646,
    'texas rangers': 3647,
    'detroit tigers': 3648, 'tigers': 3648,
    'minnesota twins': 3649, 'twins': 3649,
    'cleveland guardians': 3650, 'guardians': 3650,
    'kansas city royals': 3651, 'royals': 3651,
    'baltimore orioles': 3652, 'orioles': 3652,
    'tampa bay rays': 3653, 'rays': 3653,
    'new york yankees': 3654, 'yankees': 3654,
    'houston astros': 3655, 'astros': 3655,
    'atlanta braves': 3656, 'braves': 3656,
    'los angeles angels': 5929, 'angels': 5929,
    'washington nationals': 5930, 'nationals': 5930, 'nats': 5930,
}

# ─── SPORT DETECTION ────────────────────────────────────────
SPORT_KEYWORDS = {
    'football': [
        'premier league', 'champions league', 'la liga', 'serie a',
        'bundesliga', 'ligue 1', 'europa league', 'world cup',
        'fa cup', 'copa america', 'eredivisie', 'efl cup',
    ],
    'basketball': ['nba', 'nba championship', 'nba finals', 'nba mvp'],
    'american-football': ['nfl', 'super bowl'],
    'ice-hockey': ['nhl', 'stanley cup'],
    'mma': ['ufc', 'mma', 'bellator'],
    'motorsport': ['formula 1', 'f1', 'grand prix'],
    'baseball': ['mlb', 'world series'],
}

TEAM_KEYWORDS = list(TEAM_ID_CACHE.keys())

# Auto-build sport & league lookup from TEAM_ID_CACHE comments/ranges
# Maps team keyword → sport and league
_NFL_TEAMS = {k for k, v in TEAM_ID_CACHE.items() if v in range(4287, 4433)}
_NBA_TEAMS = {k for k, v in TEAM_ID_CACHE.items() if v in [3409,3410,3411,3412,3413,3414,3415,3416,3417,3418,3419,3420,3421,3422,3423,3424,3425,3426,3427,3428,3429,3430,3431,3432,3433,3434,3435,3436,3437,5539]}
_NHL_TEAMS = {k for k, v in TEAM_ID_CACHE.items() if v in [3675,3676,3677,3678,3679,3680,3681,3682,3683,3684,3685,3686,3687,3688,3689,3690,3691,3692,3693,3694,3695,3696,3697,3699,3700,3701,3703,3704,3705,257523,381707,530472]}
_MLB_TEAMS = {k for k, v in TEAM_ID_CACHE.items() if v in [3627,3628,3629,3630,3632,3633,3634,3635,3636,3637,3638,3639,3640,3641,3642,3644,3645,3646,3647,3648,3649,3650,3651,3652,3653,3654,3655,3656,5929,5930]}

TEAM_SPORT_MAP = {}
TEAM_LEAGUE_MAP = {}
for t in _NFL_TEAMS:
    TEAM_SPORT_MAP[t] = 'american-football'
    TEAM_LEAGUE_MAP[t] = 'nfl'
for t in _NBA_TEAMS:
    TEAM_SPORT_MAP[t] = 'basketball'
    TEAM_LEAGUE_MAP[t] = 'nba'
for t in _NHL_TEAMS:
    TEAM_SPORT_MAP[t] = 'ice-hockey'
    TEAM_LEAGUE_MAP[t] = 'nhl'
for t in _MLB_TEAMS:
    TEAM_SPORT_MAP[t] = 'baseball'
    TEAM_LEAGUE_MAP[t] = 'mlb'
# Everything else defaults to football (soccer)


class SportsData:
    """Fetch sports data from SofaSport RapidAPI for AI analysis"""

    def __init__(self):
        self.api_key = SOFASPORT_KEY
        if not self.api_key:
            raise ValueError("SOFASPORT_API_KEY not set in config/.env")
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': SOFASPORT_HOST,
        }
        self.requests_made = 0
        self._season_cache = {}

    def _log(self, level, message):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] [{level}] {message}")
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                'INSERT INTO system_logs (level, component, message) VALUES (?, ?, ?)',
                (level, 'sports_data', message)
            )
            conn.commit()
            conn.close()
        except:
            pass

    def _api(self, endpoint: str, params: dict) -> dict:
        """Make API call to SofaSport"""
        url = f"https://{SOFASPORT_HOST}/v1/{endpoint}"
        try:
            r = requests.get(url, headers=self.headers, params=params, timeout=15)
            self.requests_made += 1
            if r.status_code == 200:
                data = r.json()
                if 'does not exist' in str(data.get('message', '')):
                    self._log('WARN', f'  Endpoint not found: {endpoint}')
                    return None
                return data
            else:
                self._log('ERROR', f'  API {r.status_code}: {r.text[:100]}')
                return None
        except Exception as e:
            self._log('ERROR', f'  API failed: {e}')
            return None

    # =========================================================
    # SPORT & MARKET DETECTION
    # =========================================================
    def detect_sport(self, question: str) -> dict:
        """Detect sport, market type, teams from Polymarket question"""
        q = question.lower()

        # Find sport + league
        sport = None
        league = None
        for sport_type, keywords in SPORT_KEYWORDS.items():
            for kw in keywords:
                if kw in q:
                    sport = sport_type
                    league = kw
                    break
            if sport:
                break

        # Try team keywords if no sport found
        if not sport:
            # Sort by length descending so "seahawks" matches before "hawks"
            sorted_keywords = sorted(TEAM_KEYWORDS, key=len, reverse=True)
            for team_kw in sorted_keywords:
                if team_kw in q:
                    if team_kw in TEAM_ID_CACHE:
                        # Lookup sport from TEAM_SPORT_MAP
                        sport = TEAM_SPORT_MAP.get(team_kw, 'football')
                        league = TEAM_LEAGUE_MAP.get(team_kw, team_kw)
                        break

        if not sport:
            return None

        # Market type
        market_type = self._detect_market_type(question)

        # Extract teams
        team, team_vs = self._extract_teams(question, market_type)

        # Get tournament config
        tournament = TOURNAMENT_MAP.get(league, {})

        return {
            'sport': sport,
            'market_type': market_type,
            'league': league,
            'tournament': tournament,
            'team': team,
            'team_vs': team_vs,
            'question': question,
        }

    def _detect_market_type(self, question: str) -> str:
        q = question.lower()
        match_patterns = [r'\bvs\.?\b', r'\bversus\b', r'\bbeat\b', r'\bdefeat\b',
                          r'\bwin .+? (game|match|fight)\b', r'\bmoneyline\b']
        for p in match_patterns:
            if re.search(p, q):
                return 'daily_match'
        player_patterns = [r'\bscore \d+', r'\bmvp\b', r'\btop scorer\b',
                           r'\bover \d+\.?\d* (points|goals)\b']
        for p in player_patterns:
            if re.search(p, q):
                return 'player_prop'
        return 'season_winner'

    def _extract_teams(self, question: str, market_type: str) -> tuple:
        team, team_vs = '', ''
        if market_type == 'daily_match':
            vs = re.search(r'(.+?)\s+(?:vs\.?|versus|to beat|to defeat)\s+(.+?)(?:\?|$|\s+in\s+)', question, re.I)
            if vs:
                team = re.sub(r'^Will\s+', '', vs.group(1).strip(), flags=re.I)
                team_vs = vs.group(2).strip()
        else:
            m = re.search(r'Will\s+(?:the\s+)?(.+?)\s+win\s+(?:the\s+)?', question, re.I)
            if m:
                team = m.group(1).strip()
                team = re.sub(r'^the\s+', '', team, flags=re.I)
                team = re.sub(r'\s+the$', '', team, flags=re.I)
        return team, team_vs

    def _resolve_team_id(self, team_name: str) -> int:
        """Resolve team name to SofaSport team_id"""
        key = team_name.lower().strip()
        if key in TEAM_ID_CACHE:
            return TEAM_ID_CACHE[key]
        # Try partial match
        for cached_name, tid in TEAM_ID_CACHE.items():
            if cached_name in key or key in cached_name:
                return tid
        self._log('WARN', f'  Team ID not found for: {team_name}')
        return None

    # =========================================================
    # GET CURRENT SEASON ID
    # =========================================================
    def _get_season_id(self, ut_id: int) -> int:
        """Get current season ID for a unique tournament"""
        if ut_id in self._season_cache:
            return self._season_cache[ut_id]

        d = self._api('unique-tournaments/seasons', {'unique_tournament_id': ut_id})
        if not d:
            return None

        # Response can be {'data': [list of seasons]} 
        data = d.get('data', d)
        seasons = None
        if isinstance(data, list) and data:
            seasons = data
        elif isinstance(data, dict) and 'seasons' in data:
            seasons = data['seasons']

        if seasons and len(seasons) > 0:
            season_id = seasons[0].get('id')
            self._season_cache[ut_id] = season_id
            self._log('INFO', f'  Season: {seasons[0].get("name","?")} (id:{season_id})')
            return season_id
        return None

    # =========================================================
    # DATA FETCHING
    # =========================================================
    def get_standings(self, ut_id: int, season_id: int) -> list:
        """Get league standings"""
        d = self._api('seasons/standings', {
            'seasons_id': season_id,
            'unique_tournament_id': ut_id,
            'standing_type': 'total'
        })
        standings = []
        if d and isinstance(d.get('data'), list):
            for group in d['data'][:1]:
                for row in group.get('rows', []):
                    standings.append({
                        'pos': row.get('position'),
                        'team': row.get('team', {}).get('name', '?'),
                        'team_id': row.get('team', {}).get('id'),
                        'pts': row.get('points'),
                        'played': row.get('matches'),
                        'wins': row.get('wins'),
                        'draws': row.get('draws'),
                        'losses': row.get('losses'),
                    })
        return standings

    def get_team_form(self, team_id: int) -> list:
        """Get team recent form (last matches)"""
        d = self._api('teams/recent-form', {'team_id': team_id})
        matches = []
        if d and d.get('data', {}).get('events'):
            for e in d['data']['events']:
                ht = e.get('homeTeam', {})
                at = e.get('awayTeam', {})
                hs = e.get('homeScore', {}).get('current', 0)
                as_ = e.get('awayScore', {}).get('current', 0)
                is_home = ht.get('id') == team_id
                if is_home:
                    result = 'W' if hs > as_ else ('D' if hs == as_ else 'L')
                else:
                    result = 'W' if as_ > hs else ('D' if hs == as_ else 'L')
                matches.append({
                    'home': ht.get('name', '?'),
                    'away': at.get('name', '?'),
                    'score': f"{hs}-{as_}",
                    'result': result,
                })
        return matches

    def get_event_form(self, event_id: int) -> dict:
        """Get pre-match form for both teams (rating, position, form)"""
        d = self._api('events/form', {'event_id': event_id})
        if d and d.get('data'):
            return d['data']
        return {}

    def get_h2h(self, event_id: int) -> dict:
        """Get H2H stats and recent meetings"""
        stats = self._api('events/h2h-stats', {'event_id': event_id})
        events = self._api('events/h2h-events', {'event_id': event_id})

        h2h = {}
        if stats and stats.get('data'):
            h2h['stats'] = stats['data']
        if events and isinstance(events.get('data'), list):
            meetings = []
            for e in events['data'][:5]:
                ht = e.get('homeTeam', {}).get('name', '?')
                at = e.get('awayTeam', {}).get('name', '?')
                hs = e.get('homeScore', {}).get('current', '?')
                as_ = e.get('awayScore', {}).get('current', '?')
                meetings.append(f"{ht} {hs}-{as_} {at}")
            h2h['meetings'] = meetings
        return h2h

    def get_streaks(self, event_id: int) -> list:
        """Get betting streaks (over 2.5 goals, clean sheets, etc)"""
        d = self._api('events/streaks', {'event_id': event_id})
        streaks = []
        if d and d.get('data', {}).get('general'):
            for s in d['data']['general']:
                streaks.append({
                    'name': s.get('name', '?'),
                    'value': s.get('value', '?'),
                    'team': s.get('team', '?'),
                })
        return streaks

    def get_prediction(self, event_id: int) -> dict:
        """Get fan prediction votes"""
        d = self._api('events/predict', {'event_id': event_id})
        if d and d.get('data'):
            v1 = d['data'].get('vote1') or 0
            vx = d['data'].get('voteX') or 0
            v2 = d['data'].get('vote2') or 0
            total = v1 + vx + v2
            if total > 0:
                return {
                    'home_win': round(v1 / total * 100, 1),
                    'draw': round(vx / total * 100, 1),
                    'away_win': round(v2 / total * 100, 1),
                    'total_votes': total,
                }
        return {}

    def get_event_data(self, event_id: int) -> dict:
        """Get event details (date, venue, teams)"""
        d = self._api('events/data', {'event_id': event_id})
        if d and d.get('data'):
            e = d['data']
            return {
                'home': e.get('homeTeam', {}).get('name', '?'),
                'away': e.get('awayTeam', {}).get('name', '?'),
                'tournament': e.get('tournament', {}).get('name', '?'),
                'start_timestamp': e.get('startTimestamp'),
            }
        return {}

    def get_lineups(self, event_id: int) -> dict:
        """Get starting lineups for both teams"""
        d = self._api('events/lineups', {'event_id': event_id})
        if not d or not d.get('data'):
            return {}
        data = d['data']
        lineups = {'confirmed': data.get('confirmed', False)}
        for side in ['home', 'away']:
            players = []
            for p in data.get(side, {}).get('players', []):
                pi = p.get('player', {})
                players.append({
                    'name': pi.get('name', '?'),
                    'position': pi.get('position', '?'),
                    'shirt': p.get('shirtNumber', '?'),
                    'substitute': p.get('substitute', False),
                })
            lineups[side] = players
        return lineups

    def get_statistics(self, event_id: int) -> list:
        """Get match statistics (possession, shots, etc) from previous match"""
        d = self._api('events/statistics', {'event_id': event_id})
        stats = []
        if d and isinstance(d.get('data'), list):
            for period in d['data']:
                if period.get('period') == 'ALL':
                    for group in period.get('groups', []):
                        for item in group.get('statisticsItems', []):
                            stats.append({
                                'name': item.get('name', '?'),
                                'home': item.get('home', '?'),
                                'away': item.get('away', '?'),
                            })
                    break
        return stats

    def get_best_players(self, event_id: int) -> dict:
        """Get best rated players from previous match"""
        d = self._api('events/best-players', {'event_id': event_id})
        if not d or not d.get('data'):
            return {}
        data = d['data']
        result = {}
        for key in ['bestHomeTeamPlayer', 'bestAwayTeamPlayer']:
            if data.get(key):
                p = data[key]
                result[key] = {
                    'name': p.get('player', {}).get('name', '?'),
                    'rating': p.get('value', '?'),
                }
        return result

    # =========================================================
    # FORMAT FOR AI PROMPT
    # =========================================================
    def format_for_ai_prompt(self, sport_info: dict, data: dict) -> str:
        """Format all collected data into text for AI analysis"""
        team = sport_info.get('team', 'Unknown')
        team_vs = sport_info.get('team_vs', '')
        sport = sport_info.get('sport', 'Unknown')
        league = sport_info.get('league', 'Unknown')
        market_type = sport_info.get('market_type', 'unknown')

        lines = []
        lines.append(f"\n{'='*50}")
        lines.append(f"SPORTS DATA ({sport.upper()} - {league.upper()})")
        lines.append(f"Market Type: {market_type.replace('_', ' ').title()}")
        lines.append(f"Team: {team}")
        if team_vs:
            lines.append(f"Opponent: {team_vs}")
        lines.append(f"Source: SofaSport API (live data)")
        lines.append(f"{'='*50}")

        # Upcoming match
        if data.get('next_event'):
            e = data['next_event']
            lines.append(f"\nUPCOMING MATCH:")
            lines.append(f"  {e.get('home', '?')} vs {e.get('away', '?')}")
            lines.append(f"  Competition: {e.get('tournament', '?')}")

        # Standings
        if data.get('standings'):
            show_count = 20 if market_type == 'season_winner' else 10
            lines.append(f"\nLEAGUE STANDINGS (Top {show_count}):")
            for s in data['standings'][:show_count]:
                marker = " ◄" if team.lower() in s['team'].lower() else ""
                # NFL/NBA don't use points/draws
                if s.get('pts') is not None and s.get('draws', 0) is not None:
                    lines.append(f"  #{s['pos']} {s['team']:20s} Pts:{s['pts']} P:{s['played']} W:{s['wins']} D:{s['draws']} L:{s['losses']}{marker}")
                else:
                    lines.append(f"  #{s['pos']} {s['team']:20s} W:{s['wins']} L:{s['losses']} P:{s['played']}{marker}")

        # Team form
        if data.get('team_form'):
            form_str = ''.join([m['result'] for m in data['team_form']])
            lines.append(f"\nRECENT FORM ({team}) — {form_str}")
            for m in data['team_form']:
                lines.append(f"  {m['home']} {m['score']} {m['away']} [{m['result']}]")

        # Opponent form
        if data.get('opponent_form'):
            opp_form_str = ''.join([m['result'] for m in data['opponent_form']])
            lines.append(f"\nOPPONENT FORM ({team_vs}) — {opp_form_str}")
            for m in data['opponent_form']:
                lines.append(f"  {m['home']} {m['score']} {m['away']} [{m['result']}]")

        # Event form (pre-match ratings)
        if data.get('event_form'):
            ef = data['event_form']
            ht = ef.get('homeTeam', {})
            at = ef.get('awayTeam', {})
            lines.append(f"\nPRE-MATCH RATINGS:")
            lines.append(f"  Home — Avg Rating: {ht.get('avgRating','?')} | Position: {ht.get('position','?')} | Form: {','.join(ht.get('form',[]))}")
            lines.append(f"  Away — Avg Rating: {at.get('avgRating','?')} | Position: {at.get('position','?')} | Form: {','.join(at.get('form',[]))}")

        # H2H
        if data.get('h2h'):
            h2h = data['h2h']
            if h2h.get('stats', {}).get('teamDuel'):
                d = h2h['stats']['teamDuel']
                lines.append(f"\nHEAD-TO-HEAD RECORD:")
                lines.append(f"  Home wins: {d.get('homeWins',0)} | Draws: {d.get('draws',0)} | Away wins: {d.get('awayWins',0)}")
            if h2h.get('stats', {}).get('managerDuel'):
                md = h2h['stats']['managerDuel']
                lines.append(f"  Manager duel — Home: {md.get('homeWins',0)}W | Draw: {md.get('draws',0)} | Away: {md.get('awayWins',0)}W")
            if h2h.get('meetings'):
                lines.append(f"  Recent meetings:")
                for m in h2h['meetings']:
                    lines.append(f"    {m}")

        # Streaks
        if data.get('streaks'):
            lines.append(f"\nBETTING STREAKS:")
            for s in data['streaks'][:8]:
                lines.append(f"  [{s['team']:4s}] {s['name']}: {s['value']}")

        # Fan prediction
        if data.get('prediction'):
            p = data['prediction']
            lines.append(f"\nFAN PREDICTION ({p.get('total_votes',0):,} votes):")
            lines.append(f"  Home win: {p.get('home_win',0)}% | Draw: {p.get('draw',0)}% | Away win: {p.get('away_win',0)}%")

        # Lineups (upcoming match)
        if data.get('lineups') and data['lineups'].get('confirmed'):
            lines.append(f"\nCONFIRMED LINEUPS:")
            for side in ['home', 'away']:
                starters = [p for p in data['lineups'].get(side, []) if not p.get('substitute')]
                subs = [p for p in data['lineups'].get(side, []) if p.get('substitute')]
                side_label = data.get('next_event', {}).get(side.replace('home','home').replace('away','away'), side.upper())
                lines.append(f"  {side.upper()} XI: {', '.join([p['name'] for p in starters[:11]])}")
                if subs:
                    lines.append(f"  {side.upper()} BENCH: {', '.join([p['name'] for p in subs[:7]])}")

        # Previous match statistics
        if data.get('prev_statistics'):
            lines.append(f"\nPREVIOUS MATCH STATS:")
            for s in data['prev_statistics'][:10]:
                lines.append(f"  {s['name']:25s} {s['home']:>6s} - {s['away']:<6s}")

        # Best players from previous match
        if data.get('best_players'):
            bp = data['best_players']
            lines.append(f"\nBEST PLAYERS (prev match):")
            if bp.get('bestHomeTeamPlayer'):
                p = bp['bestHomeTeamPlayer']
                lines.append(f"  Home: {p['name']} (rating: {p['rating']})")
            if bp.get('bestAwayTeamPlayer'):
                p = bp['bestAwayTeamPlayer']
                lines.append(f"  Away: {p['name']} (rating: {p['rating']})")

        return '\n'.join(lines)

    # =========================================================
    # MASTER: Get Data for Market
    # =========================================================
    def get_data_for_market(self, question: str) -> dict:
        """Main entry: detect sport → fetch data → format for AI"""
        self.requests_made = 0

        # Detect
        sport_info = self.detect_sport(question)
        if not sport_info:
            self._log('WARN', f'  Could not detect sport: {question[:60]}')
            return None

        self._log('INFO', f'  Detected: {sport_info["sport"]} / {sport_info["market_type"]} / Team: {sport_info["team"]}')

        team = sport_info['team']
        team_vs = sport_info.get('team_vs', '')
        tournament = sport_info.get('tournament', {})
        ut_id = tournament.get('ut_id')
        market_type = sport_info.get('market_type', 'season_winner')

        data = {}
        team_id = self._resolve_team_id(team) if team else None

        # ─── STANDINGS (for season_winner) ────────────────────
        if ut_id:
            season_id = self._get_season_id(ut_id)
            if season_id:
                data['standings'] = self.get_standings(ut_id, season_id)

        # ─── TEAM FORM ───────────────────────────────────────
        if team_id:
            data['team_form'] = self.get_team_form(team_id)

            # Get near events for H2H and event-specific data
            ne = self._api('teams/near-events', {'team_id': team_id})
            if ne and ne.get('data'):
                next_event = ne['data'].get('nextEvent') or {}
                prev_event = ne['data'].get('previousEvent') or {}

                next_id = next_event.get('id') if next_event else None
                prev_id = prev_event.get('id') if prev_event else None

                # Use next event for upcoming match data
                if next_id:
                    data['next_event'] = self.get_event_data(next_id)
                    data['event_form'] = self.get_event_form(next_id)
                    data['prediction'] = self.get_prediction(next_id)
                    data['streaks'] = self.get_streaks(next_id)
                    data['lineups'] = self.get_lineups(next_id)

                    if market_type == 'daily_match':
                        data['h2h'] = self.get_h2h(next_id)

                # Previous match stats (always useful for context)
                if prev_id:
                    data['prev_statistics'] = self.get_statistics(prev_id)
                    data['best_players'] = self.get_best_players(prev_id)

                # For season_winner without next event, use previous for form
                if not next_id and prev_id and market_type == 'season_winner':
                    data['event_form'] = self.get_event_form(prev_id)
                    data['streaks'] = self.get_streaks(prev_id)

        # ─── OPPONENT FORM (daily match) ─────────────────────
        if team_vs and market_type == 'daily_match':
            opp_id = self._resolve_team_id(team_vs)
            if opp_id:
                data['opponent_form'] = self.get_team_form(opp_id)

        if not data:
            self._log('WARN', f'  No data returned for: {team}')
            return None

        # Format
        prompt_text = self.format_for_ai_prompt(sport_info, data)
        self._log('INFO', f'  API requests used: {self.requests_made}')

        return {
            'sport_info': sport_info,
            'data': data,
            'prompt_text': prompt_text,
            'api_requests': self.requests_made,
        }

    @staticmethod
    def is_sports_market(question: str) -> bool:
        """Check if a market question is sports-related"""
        q = question.lower()
        for sport, keywords in SPORT_KEYWORDS.items():
            for kw in keywords:
                if kw in q:
                    return True
        for team_kw in TEAM_KEYWORDS:
            if team_kw in q:
                return True
        return False


# =========================================================
# CLI Test
# =========================================================
if __name__ == '__main__':
    print("=" * 60)
    print("⚽ Oracle Sentinel - Sports Data v2 (SofaSport)")
    print("=" * 60)

    sd = SportsData()

    test_questions = [
        "Will Tottenham win the 2025-26 English Premier League?",
        "Will Atletico Madrid win the 2025-26 Champions League?",
        "Will the New England Patriots win Super Bowl 2026?",
    ]

    for q in test_questions:
        print(f"\n{'─'*60}")
        print(f"Q: {q}")
        result = sd.get_data_for_market(q)
        if result:
            print(result['prompt_text'])
            print(f"\n  [API requests: {result['api_requests']}]")
        else:
            print("  ❌ No data available")

    print(f"\n{'='*60}")
    print("Done!")
