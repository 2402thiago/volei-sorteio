from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import List

FUNDS = [
    {"key": "attack", "name": "Ataque", "weight": 2.0},
    {"key": "setting", "name": "Levantamento", "weight": 2.0},
    {"key": "defense", "name": "Defesa", "weight": 1.0},
    {"key": "pass", "name": "Passe", "weight": 1.0},
    {"key": "block", "name": "Bloqueio", "weight": 1.0},
    {"key": "serve", "name": "Saque", "weight": 0.5},
]
TOTAL_WEIGHT = sum(f["weight"] for f in FUNDS)
POT_NAMES = ["Ataque", "Levantamento", "Defesa", "Passe", "Bloqueio", "Saque"]
NUM_TEAMS = 6

@dataclass
class Player:
    name: str
    gender: str  # 'M' or 'F'
    scores: dict = field(default_factory=dict)

    def weighted_score(self) -> float:
        s = 0.0
        for f in FUNDS:
            val = self.scores.get(f["key"], 5)
            s += val * f["weight"]
        return s / TOTAL_WEIGHT


@dataclass
class Pot:
    fund: dict
    players: list = field(default_factory=list)


@dataclass
class Team:
    id: int
    players: list = field(default_factory=list)
    total: float = 0.0

    @property
    def avg(self) -> float:
        return self.total / len(self.players) if self.players else 0.0


def assign_pots(players: List[Player]) -> List[Pot]:
    rank_map = {p.name: {} for p in players}
    for f in FUNDS:
        sorted_players = sorted(players, key=lambda p: p.scores.get(f["key"], 5), reverse=True)
        for rank, p in enumerate(sorted_players, 1):
            rank_map[p.name][f["key"]] = rank

    pots = [Pot(fund=f) for f in FUNDS]
    unassigned = {p.name for p in players}

    while unassigned:
        best_player = None
        best_pot_idx = -1
        best_rank = float("inf")

        for p in players:
            if p.name not in unassigned:
                continue
            for fi, f in enumerate(FUNDS):
                if len(pots[fi].players) >= 4:
                    continue
                r = rank_map[p.name][f["key"]]
                if r < best_rank:
                    best_rank = r
                    best_player = p
                    best_pot_idx = fi

        if not best_player:
            break
        unassigned.discard(best_player.name)
        fund_key = FUNDS[best_pot_idx]["key"]
        pots[best_pot_idx].players.append(
            Player(
                name=best_player.name,
                gender=best_player.gender,
                scores=best_player.scores,
            )
        )

    for i, pot in enumerate(pots):
        fund_key = FUNDS[i]["key"]
        pot.players.sort(key=lambda p: p.scores.get(fund_key, 5), reverse=True)
    return pots


def build_teams(players: List[Player], pots: List[Pot]) -> List[Team]:
    pot_of = {}
    for pi, pot in enumerate(pots):
        for p in pot.players:
            pot_of[p.name] = pi

    women = [p for p in players if p.gender == "F"]
    men = sorted(
        [p for p in players if p.gender == "M"],
        key=lambda p: p.weighted_score(),
        reverse=True,
    )

    random.shuffle(women)
    teams = [Team(id=i + 1) for i in range(NUM_TEAMS)]

    for i, w in enumerate(women):
        idx = i % NUM_TEAMS
        teams[idx].players.append(w)
        teams[idx].total += w.weighted_score()

    for man in men:
        t = min(teams, key=lambda t: t.total)
        t.players.append(man)
        t.total += man.weighted_score()

    return teams
