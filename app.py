from __future__ import annotations
import random
import streamlit as st

from logic import Player, FUNDS, TOTAL_WEIGHT, POT_NAMES, assign_pots, build_teams, NUM_TEAMS
from gsheets_db import (
    init_gsheets,
    disconnect_gsheets,
    load_players_from_sheets,
    save_players_to_sheets,
    load_scores_from_sheets,
    save_scores_to_sheets,
    save_history_to_sheets,
)

st.set_page_config(
    page_title="Vôlei 4x4 — Sorteio de Times",
    page_icon="🏐",
    layout="wide",
)

if "players" not in st.session_state:
    st.session_state.players = [
        Player(name="INGRA", gender="F"),
        Player(name="PATRICIA", gender="F"),
        Player(name="THAIS", gender="F"),
        Player(name="ELDA", gender="F"),
        Player(name="MILENA", gender="F"),
        Player(name="MARIA", gender="F"),
        Player(name="MATHEUS", gender="M"),
        Player(name="DOUGLAS", gender="M"),
        Player(name="THIAGO", gender="M"),
        Player(name="LIND", gender="M"),
        Player(name="KELVIS", gender="M"),
        Player(name="JOÃO", gender="M"),
        Player(name="RAMON", gender="M"),
        Player(name="TON", gender="M"),
        Player(name="ELIAS", gender="M"),
        Player(name="MAURICIO", gender="M"),
        Player(name="RYAN", gender="M"),
        Player(name="ROBERTO", gender="M"),
        Player(name="FRANKMAR", gender="M"),
        Player(name="WARLLEY", gender="M"),
        Player(name="MARCELO", gender="M"),
        Player(name="JAN", gender="M"),
        Player(name="FEIJÓ", gender="M"),
        Player(name="FABRICIO", gender="M"),
    ]

if "last_pots" not in st.session_state:
    st.session_state.last_pots = None

if "tab" not in st.session_state:
    st.session_state.tab = "atletas"

FUND_NAMES = {f["key"]: f["name"] for f in FUNDS}
FUND_WEIGHTS = {f["key"]: f["weight"] for f in FUNDS}
TEAM_COLORS = [
    "#1a56db", "#dc2626", "#059669",
    "#d97706", "#7c3aed", "#db2777",
]

sh = None
if st.secrets and not st.session_state.get("gsheets_no_auto"):
    sh = init_gsheets()
    if sh is not None:
        loaded = load_players_from_sheets(sh)
        if loaded:
            db_scores = load_scores_from_sheets(sh)
            if db_scores is None:
                db_scores = {}
            for p in loaded:
                if p.name in db_scores:
                    p.scores = db_scores[p.name]
            st.session_state.players = loaded


def tab_btn(label, key, icon=""):
    active = st.session_state.tab == key
    btn = st.button(
        f"{icon} {label}",
        type="primary" if active else "secondary",
        use_container_width=True,
        on_click=lambda k=key: st.session_state.update(tab=k),
    )
    return active


def get_all_players():
    """Build Player list with current scores from session state."""
    players = []
    for p in st.session_state.players:
        scores = {}
        for f in FUNDS:
            skey = f"score_{p.name}_{f['key']}"
            val = st.session_state.get(skey, 5)
            try:
                scores[f["key"]] = max(1, min(10, int(val)))
            except (ValueError, TypeError):
                scores[f["key"]] = 5
        players.append(Player(name=p.name, gender=p.gender, scores=scores))
    return players


def on_score_input():
    st.session_state.last_pots = None


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("## 🏐")
    st.markdown(
        "<h3 style='text-align:center;margin-bottom:0'>Vôlei 4x4</h3>"
        "<p style='text-align:center;color:#64748b;font-size:.85rem'>Sorteio de Times</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    tab_btn("Atletas", "atletas", "👥")
    tab_btn("Notas", "notas", "📝")
    tab_btn("Potes", "potes", "🎯")
    tab_btn("Times", "times", "🏆")

    st.divider()

    with st.expander("☁️ Google Sheets", expanded=False):
        if sh is not None:
            st.success("✅ Conectado")
            if st.button("Desconectar"):
                disconnect_gsheets()
                st.rerun()
        else:
            st.info("Configure no .streamlit/secrets.toml:")
            st.code("""
[google_credentials]
type = "service_account"
project_id = "..."
...

[google_sheet_url]
url = "https://docs.google.com/..."
""")
            if st.button("Tentar reconectar"):
                st.rerun()

    st.divider()
    st.markdown(
        "<p style='text-align:center;color:#94a3b8;font-size:.75rem'>"
        "6 times · 24 atletas · 6 potes</p>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────
# TAB: ATLETAS
# ─────────────────────────────────────────────
if st.session_state.tab == "atletas":
    st.header("👥 Atletas", divider="blue")
    st.caption("Gerencie os atletas cadastrados no sistema.")

    col_add, col_count = st.columns([3, 1])
    with col_add:
        with st.expander("➕ Novo Atleta", expanded=False):
            new_name = st.text_input("Nome", key="new_name", placeholder="Nome do atleta")
            new_gender = st.selectbox("Gênero", ["M", "F"], key="new_gender")
            if st.button("Adicionar", type="primary", use_container_width=True):
                name = new_name.strip().upper()
                if name and not any(p.name == name for p in st.session_state.players):
                    st.session_state.players.append(Player(name=name, gender=new_gender))
                    if sh:
                        save_players_to_sheets(sh, st.session_state.players)
                    st.rerun()
                elif not name:
                    st.error("Nome inválido.")
                else:
                    st.error("Atleta já existe.")

    with col_count:
        st.metric("Total", len(st.session_state.players))
        m_count = sum(1 for p in st.session_state.players if p.gender == "M")
        f_count = sum(1 for p in st.session_state.players if p.gender == "F")
        st.caption(f"⚦ {m_count} · ♀ {f_count}")

    if st.session_state.players:
        st.subheader("Lista de Atletas")
        for i, p in enumerate(st.session_state.players):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1:
                gender_icon = "♀" if p.gender == "F" else "⚦"
                st.markdown(f"**{p.name}** {gender_icon}")
            with c2:
                if st.button("✏️", key=f"edit_{i}", help="Editar"):
                    st.session_state.edit_idx = i
                    st.rerun()
            with c3:
                if st.button("🗑️", key=f"del_{i}", help="Remover"):
                    st.session_state.players.pop(i)
                    if sh:
                        save_players_to_sheets(sh, st.session_state.players)
                    st.rerun()

        if "edit_idx" in st.session_state:
            idx = st.session_state.edit_idx
            p = st.session_state.players[idx]
            with st.form("edit_form"):
                new_name = st.text_input("Nome", value=p.name)
                new_gender = st.selectbox("Gênero", ["M", "F"], index=0 if p.gender == "M" else 1)
                c1, c2 = st.columns(2)
                with c1:
                    if st.form_submit_button("Salvar", type="primary", use_container_width=True):
                        p.name = new_name.strip().upper()
                        p.gender = new_gender
                        if sh:
                            save_players_to_sheets(sh, st.session_state.players)
                        del st.session_state.edit_idx
                        st.rerun()
                with c2:
                    if st.form_submit_button("Cancelar", use_container_width=True):
                        del st.session_state.edit_idx
                        st.rerun()
    else:
        st.info("Nenhum atleta cadastrado. Adicione atletas para começar.")

# ─────────────────────────────────────────────
# TAB: NOTAS
# ─────────────────────────────────────────────
elif st.session_state.tab == "notas":
    st.header("📝 Avaliação dos Atletas", divider="blue")
    st.caption(
        "Avalie cada atleta de **1 a 10** em cada fundamento. "
        "**Nota Ponderada** = (Ataque×2 + Levantamento×2 + Defesa×1 + Passe×1 + Bloqueio×1 + Saque×0,5) ÷ 7,5"
    )

    players = st.session_state.players
    if not players:
        st.warning("Cadastre atletas primeiro na aba 'Atletas'.")
    else:
        cols_per_row = 4
        rows_needed = (len(players) + cols_per_row - 1) // cols_per_row

        for row_idx in range(rows_needed):
            cols = st.columns(cols_per_row)
            for col_idx in range(cols_per_row):
                p_idx = row_idx * cols_per_row + col_idx
                if p_idx >= len(players):
                    break
                p = players[p_idx]
                with cols[col_idx]:
                    with st.container(border=True):
                        gender_icon = "♀" if p.gender == "F" else "⚦"
                        st.markdown(f"**{p.name}** {gender_icon}")
                        for f in FUNDS:
                            skey = f"score_{p.name}_{f['key']}"
                            if skey not in st.session_state:
                                st.session_state[skey] = 5
                            st.session_state[skey] = st.number_input(
                                f"{f['name']} (×{f['weight']})",
                                min_value=1,
                                max_value=10,
                                value=st.session_state[skey],
                                key=skey + "_input",
                                on_change=on_score_input,
                                label_visibility="collapsed",
                                placeholder=f["name"],
                            )

                        scores = {}
                        for f in FUNDS:
                            val = st.session_state.get(f"score_{p.name}_{f['key']}", 5)
                            try:
                                scores[f["key"]] = max(1, min(10, int(val)))
                            except (ValueError, TypeError):
                                scores[f["key"]] = 5
                        ws = sum(scores[f["key"]] * f["weight"] for f in FUNDS) / TOTAL_WEIGHT
                        st.metric("Média", f"{ws:.2f}")

        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("🎲 Preencher aleatório", use_container_width=True, type="secondary"):
                for p in players:
                    for f in FUNDS:
                        skey = f"score_{p.name}_{f['key']}"
                        st.session_state[skey] = random.randint(1, 10)
                st.rerun()
        with c2:
            if st.button("⚡ Calcular & Ver Times", use_container_width=True, type="primary"):
                st.session_state.tab = "potes"
                st.rerun()

# ─────────────────────────────────────────────
# TAB: POTES
# ─────────────────────────────────────────────
elif st.session_state.tab == "potes":
    st.header("🎯 Potes por Fundamento", divider="blue")
    st.caption(
        "Cada **Pote** reúne os **4 atletas** mais destacados no fundamento "
        "que ainda não foram alocados em potes anteriores."
    )

    players_list = get_all_players()
    if len(players_list) < 4:
        st.warning("Cadastre e avalie pelo menos 4 atletas.")
    else:
        pots = assign_pots(players_list)
        st.session_state.last_pots = pots

        cols = st.columns(3)
        for i, pot in enumerate(pots):
            with cols[i % 3]:
                fund = pot.fund
                bg = ["#fef2f2", "#eff6ff", "#f0fdf4", "#fffbeb", "#f5f3ff", "#fdf2f8"][i]
                grad = ["#ef4444", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"][i]
                with st.container(border=True):
                    st.markdown(
                        f"<div style='background:{grad};padding:.5rem .75rem;border-radius:.5rem;"
                        f"color:#fff;font-weight:700;font-size:.9rem;display:flex;"
                        f"justify-content:space-between;align-items:center'>"
                        f"<span>Pote {i+1} — {fund['name']}</span>"
                        f"<span style='font-size:.75rem;opacity:.8'>×{fund['weight']}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if not pot.players:
                        st.caption("Vazio")
                    else:
                        for rank, p in enumerate(pot.players, 1):
                            g_icon = "♀" if p.gender == "F" else "⚦"
                            score_val = p.scores.get(fund["key"], 5)
                            st.markdown(
                                f"<div style='display:flex;justify-content:space-between;"
                                f"padding:.4rem .5rem;background:{bg};border-radius:.35rem;"
                                f"margin-top:.25rem;font-size:.85rem'>"
                                f"<span><strong>#{rank}</strong> {p.name} {g_icon}</span>"
                                f"<span><strong>{score_val}</strong>/10</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )

        if st.button("🏆 Ver Times →", type="primary", use_container_width=True):
            st.session_state.tab = "times"
            st.rerun()

# ─────────────────────────────────────────────
# TAB: TIMES
# ─────────────────────────────────────────────
elif st.session_state.tab == "times":
    st.header("🏆 Times Sorteados", divider="blue")

    players_list = get_all_players()
    if len(players_list) < 2:
        st.warning("Cadastre e avalie pelo menos 2 atletas.")
    else:
        pots = st.session_state.last_pots or assign_pots(players_list)
        teams = build_teams(players_list, pots)

        avgs = [t.avg for t in teams]
        mean_avg = sum(avgs) / len(avgs)
        variance = sum((v - mean_avg) ** 2 for v in avgs) / len(avgs)
        std_dev = variance ** 0.5
        max_diff = max(avgs) - min(avgs)

        if std_dev < 0.15:
            quality = ("Excelente", "#10b981")
        elif std_dev < 0.35:
            quality = ("Bom", "#f59e0b")
        else:
            quality = ("Regular", "#ef4444")

        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Média Geral", f"{mean_avg:.2f}")
        b2.metric("Desvio Padrão", f"{std_dev:.3f}")
        b3.metric("Diferença Max-Min", f"{max_diff:.3f}")
        b4.markdown(
            f"<div style='background:{quality[1]};color:#fff;padding:.5rem;"
            f"border-radius:.5rem;text-align:center'>"
            f"<span style='font-size:.7rem'>Nivelamento</span><br>"
            f"<strong>{quality[0]}</strong></div>",
            unsafe_allow_html=True,
        )

        c1, c2, _ = st.columns([1, 1, 2])
        with c1:
            if st.button("🔀 Novo Sorteio", type="primary", use_container_width=True):
                st.session_state.last_pots = None
                st.rerun()
        with c2:
            if sh and st.button("💾 Salvar histórico", use_container_width=True):
                save_history_to_sheets(sh, players_list, teams)
                st.success("Salvo!")

        st.divider()

        max_avg = max(avgs) if avgs else 1
        team_cols = st.columns(3)
        for i, team in enumerate(teams):
            with team_cols[i % 3]:
                bar_w = (team.avg / max_avg * 100) if max_avg > 0 else 0
                color = TEAM_COLORS[i]
                with st.container(border=True):
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;"
                        f"align-items:center'>"
                        f"<h4 style='margin:0'>Time {team.id}</h4>"
                        f"<span style='color:{color};font-weight:700'>{team.avg:.2f}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div style='height:5px;background:#f1f5f9;border-radius:3px;"
                        f"margin:.5rem 0'>"
                        f"<div style='height:100%;width:{bar_w:.1f}%;background:{color};"
                        f"border-radius:3px;transition:width .4s'></div></div>",
                        unsafe_allow_html=True,
                    )
                    for p in team.players:
                        g_icon = "♀" if p.gender == "F" else "⚦"
                        pot_label = ""
                        for pi, pot in enumerate(pots):
                            if any(pp.name == p.name for pp in pot.players):
                                pot_label = f"P{pi+1}"
                                break
                        st.markdown(
                            f"<div style='display:flex;justify-content:space-between;"
                            f"padding:.3rem 0;font-size:.85rem;"
                            f"border-bottom:1px solid #f1f5f9'>"
                            f"<span>{g_icon} <strong>{p.name}</strong> "
                            f"<span style='color:#94a3b8;font-size:.7rem'>{pot_label}</span></span>"
                            f"<span style='color:#64748b'>{p.weighted_score():.2f}</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
