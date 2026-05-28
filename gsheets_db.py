from __future__ import annotations
import json
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from logic import Player, FUNDS


def get_sheet_by_name(sh, name):
    """Get worksheet by name, create it if it doesn't exist."""
    try:
        return sh.worksheet(name)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=name, rows=100, cols=20)


def init_sheets_structure(sh):
    """Create all required worksheets if they don't exist."""
    for sheet_name in ["atletas", "notas", "historico"]:
        try:
            get_sheet_by_name(sh, sheet_name)
        except Exception:
            pass


def init_gsheets() -> gspread.Spreadsheet | None:
    if "gsheets_connected" in st.session_state and st.session_state.gsheets_connected:
        return st.session_state.get("gsheets_client")

    if "google_sheet_url" not in st.secrets or "google_credentials" not in st.secrets:
        return None

    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds_dict = json.loads(st.secrets["google_credentials"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        url = st.secrets["google_sheet_url"]
        sh = client.open_by_url(url)

        st.session_state.gsheets_client = sh
        st.session_state.gsheets_connected = True
        return sh
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Sheets: {e}")
        return None




def disconnect_gsheets():
    st.session_state.gsheets_connected = False
    st.session_state.pop("gsheets_client", None)


def load_players_from_sheets(sh) -> list[Player] | None:
    try:
        ws = sh.worksheet("atletas")
        records = ws.get_all_records()
        players = []
        for r in records:
            name = r.get("nome", "").strip().upper()
            gender = r.get("genero", "").strip().upper()
            if name and gender in ("M", "F"):
                players.append(Player(name=name, gender=gender))
        return players
    except gspread.WorksheetNotFound:
        return []
    except Exception as e:
        st.error(f"Erro ao carregar atletas: {e}")
        return None


def save_players_to_sheets(sh, players: list[Player]) -> bool:
    try:
        ws = get_sheet_by_name(sh, "atletas")
        ws.clear()
        ws.append_row(["nome", "genero"])
        for p in players:
            ws.append_row([p.name, p.gender])
        return True
    except Exception as e:
        st.error(f"Erro ao salvar atletas: {e}")
        return False


def load_scores_from_sheets(sh) -> dict[str, dict] | None:
    try:
        ws = sh.worksheet("notas")
        records = ws.get_all_records()
        scores = {}
        for r in records:
            name = r.get("nome", "").strip().upper()
            if not name:
                continue
            scores[name] = {}
            for f in FUNDS:
                key = f["key"]
                val = r.get(key)
                try:
                    scores[name][key] = max(1, min(10, int(val)))
                except (ValueError, TypeError):
                    scores[name][key] = 5
        return scores
    except gspread.WorksheetNotFound:
        return {}
    except Exception as e:
        st.error(f"Erro ao carregar notas: {e}")
        return None


def save_scores_to_sheets(sh, players: list[Player]) -> bool:
    try:
        ws = get_sheet_by_name(sh, "notas")
        ws.clear()
        headers = ["nome"] + [f["key"] for f in FUNDS]
        ws.append_row(headers)
        for p in players:
            row = [p.name] + [p.scores.get(f["key"], 5) for f in FUNDS]
            ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar notas: {e}")
        return False


def save_history_to_sheets(sh, players: list[Player], teams: list) -> bool:
    try:
        ws = get_sheet_by_name(sh, "historico")
        row = []
        for t in teams:
            for p in t.players:
                row.extend([p.name, f"{p.weighted_score():.2f}", t.id])
        ws.append_row(
            ["sorteio"] + row,
        )
        return True
    except Exception as e:
        st.error(f"Erro ao salvar histórico: {e}")
        return False
