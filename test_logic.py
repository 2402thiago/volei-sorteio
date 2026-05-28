"""Test core logic functions."""
from logic import Player, FUNDS, assign_pots, build_teams, TOTAL_WEIGHT


def make_player(name, gender, **scores):
    return Player(name=name, gender=gender, scores=scores)


def test_weighted_score():
    p = make_player("TESTE", "M", **{"attack":10, "setting":10, "defense":1, "pass":1, "block":1, "serve":1})
    expected = (10*2 + 10*2 + 1*1 + 1*1 + 1*1 + 1*0.5) / TOTAL_WEIGHT
    assert abs(p.weighted_score() - expected) < 0.001, f"{p.weighted_score()} != {expected}"
    print(f"✅ weighted_score: {p.weighted_score():.2f}")


def test_assign_pots():
    players = []
    for i in range(24):
        g = "F" if i < 6 else "M"
        scores = {"attack":10-i%7, "setting":10-i%7, "defense":10-i%7, "pass":10-i%7, "block":10-i%7, "serve":10-i%7}
        players.append(make_player(f"J{i+1}", g, **scores))
    pots = assign_pots(players)
    assert len(pots) == 6, f"Expected 6 pots, got {len(pots)}"
    for i, pot in enumerate(pots):
        assert len(pot.players) == 4, f"Pot {i} has {len(pot.players)} players"
        print(f"✅ Pot {i+1} ({pot.fund['name']}): {[p.name for p in pot.players]}")
    # Check no duplicate across pots
    all_names = []
    for pot in pots:
        all_names.extend(p.name for p in pot.players)
    assert len(all_names) == len(set(all_names)), "Duplicate players across pots!"
    print("✅ No duplicates across pots")


def test_build_teams():
    players = []
    for i in range(6):
        scores = {f["key"]: 8 for f in FUNDS}
        players.append(make_player(f"F{i+1}", "F", **scores))
    for i in range(18):
        scores = {"attack":5, "setting":5, "defense":5, "pass":5, "block":5, "serve":5}
        players.append(make_player(f"M{i+1}", "M", **scores))
    pots = assign_pots(players)
    teams = build_teams(players, pots)
    assert len(teams) == 6, f"Expected 6 teams, got {len(teams)}"
    total_team_players = sum(len(t.players) for t in teams)
    assert total_team_players == 24, f"Expected 24 total players, got {total_team_players}"
    # Check each team has at least 3 and at most 5 players
    for t in teams:
        assert 3 <= len(t.players) <= 5, f"Team {t.id} has {len(t.players)} players"
        print(f"✅ Team {t.id}: {len(t.players)} players, avg={t.avg:.2f}")
    print("✅ All teams valid")


if __name__ == "__main__":
    test_weighted_score()
    test_assign_pots()
    test_build_teams()
    print("\n🎉 All tests passed!")
