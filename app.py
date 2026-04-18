import os
import sqlite3
import hashlib
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

APP_VERSION = "1.4.2"
DB_NAME = "workout_app.db"
SESSION_COOKIE_NAME = "workout_session_token"
SESSION_HOURS = 2
ORG_PASSWORD = "VASE"

CATEGORY_PLACEHOLDER = "選択してください"
EXERCISE_PLACEHOLDER = "選択してください"

EXERCISE_MASTER = {
    "胸": [
        "ベンチプレス",
        "ダンベルフライ",
        "チェストプレス",
        "インクラインダンベルプレス",
        "ケーブルクロスオーバー",
        "ディップス",
        "プッシュアップ",
        "デクラインベンチプレス",
        "ペックフライ",
        "プルオーバー",
    ],
    "脚": [
        "バーベルスクワット",
        "レッグプレス",
        "レッグエクステンション",
        "レッグカール",
        "ブルガリアンスクワット",
        "ランジ",
        "ハックスクワット",
        "スティフレッグデッドリフト",
        "カーフレイズ",
        "ヒップスラスト",
    ],
    "背中": [
        "デッドリフト",
        "懸垂",
        "ラットプルダウン",
        "ベントオーバーロウ",
        "ワンハンドダンベルロウ",
        "シーテッドロウ",
        "Tバーロウ",
        "ストレートアームプルダウン",
        "バックエクステンション",
        "フェイスプル",
    ],
    "肩": [
        "オーバーヘッドプレス",
        "サイドレイズ",
        "アーノルドプレス",
        "フロントレイズ",
        "リアレイズ",
        "アップライトロウ",
        "ショルダープレス",
        "ケーブルサイドレイズ",
        "シュラッグ",
        "ミリタリープレス",
    ],
    "腕": [
        "バーベルカール",
        "インクラインダンベルカール",
        "ハンマーカール",
        "プリチャーカール",
        "ケーブルカール",
        "スカルクラッシャー",
        "ケーブルプッシュダウン",
        "クローズグリップベンチプレス",
        "フレンチプレス",
        "リバースカール",
    ],
    "腹筋": [
        "クランチ",
        "レッグレイズ",
        "アブローラー",
        "ハンギングレッグレイズ",
        "シットアップ",
        "ロシアンツイスト",
        "ケーブルクランチ",
        "プランク",
        "サイドプランク",
        "バイシクルクランチ",
    ],
}

EXERCISE_METS = {
    "ベンチプレス": 6.0,
    "ダンベルフライ": 5.0,
    "チェストプレス": 5.5,
    "インクラインダンベルプレス": 6.0,
    "ケーブルクロスオーバー": 5.0,
    "ディップス": 6.0,
    "プッシュアップ": 4.5,
    "デクラインベンチプレス": 6.0,
    "ペックフライ": 5.0,
    "プルオーバー": 5.0,
    "バーベルスクワット": 6.0,
    "レッグプレス": 6.0,
    "レッグエクステンション": 5.0,
    "レッグカール": 5.0,
    "ブルガリアンスクワット": 6.0,
    "ランジ": 6.0,
    "ハックスクワット": 6.0,
    "スティフレッグデッドリフト": 6.0,
    "カーフレイズ": 4.5,
    "ヒップスラスト": 5.5,
    "デッドリフト": 6.5,
    "懸垂": 6.0,
    "ラットプルダウン": 5.5,
    "ベントオーバーロウ": 6.0,
    "ワンハンドダンベルロウ": 5.5,
    "シーテッドロウ": 5.5,
    "Tバーロウ": 6.0,
    "ストレートアームプルダウン": 5.0,
    "バックエクステンション": 4.5,
    "フェイスプル": 4.5,
    "オーバーヘッドプレス": 6.0,
    "サイドレイズ": 5.0,
    "アーノルドプレス": 5.5,
    "フロントレイズ": 5.0,
    "リアレイズ": 5.0,
    "アップライトロウ": 5.5,
    "ショルダープレス": 6.0,
    "ケーブルサイドレイズ": 5.0,
    "シュラッグ": 4.5,
    "ミリタリープレス": 6.0,
    "バーベルカール": 4.5,
    "インクラインダンベルカール": 4.5,
    "ハンマーカール": 4.5,
    "プリチャーカール": 4.5,
    "ケーブルカール": 4.5,
    "スカルクラッシャー": 5.0,
    "ケーブルプッシュダウン": 5.0,
    "クローズグリップベンチプレス": 6.0,
    "フレンチプレス": 5.0,
    "リバースカール": 4.5,
    "クランチ": 4.0,
    "レッグレイズ": 4.5,
    "アブローラー": 5.5,
    "ハンギングレッグレイズ": 5.5,
    "シットアップ": 4.5,
    "ロシアンツイスト": 4.5,
    "ケーブルクランチ": 5.0,
    "プランク": 3.5,
    "サイドプランク": 3.5,
    "バイシクルクランチ": 4.5,
}

CATEGORY_DEFAULT_MET = {
    "胸": 5.5,
    "脚": 5.8,
    "背中": 5.8,
    "肩": 5.3,
    "腕": 4.8,
    "腹筋": 4.5,
}


def get_cookie_password():
    try:
        if "cookie_password" in st.secrets:
            return st.secrets["cookie_password"]
    except Exception:
        pass
    return "change-this-cookie-password-before-serious-use-2026"


COOKIE_PASSWORD = get_cookie_password()


def render_app_title():
    st.markdown(
        f"""
        <div style="display:flex; align-items:flex-end; gap:10px; margin-bottom:0.5rem;">
            <h1 style="margin:0;">🏋️ 筋トレメモ</h1>
            <span style="font-size:0.9rem; color:#9aa0a6; margin-bottom:0.35rem;">ver.{APP_VERSION}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def utcnow():
    return datetime.utcnow()


def get_table_columns(table_name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    rows = cur.fetchall()
    conn.close()
    return [row["name"] for row in rows]


def column_exists(table_name, column_name):
    return column_name in get_table_columns(table_name)


def infer_category_from_exercise(exercise):
    exercise = (exercise or "").strip()
    for category, exercises in EXERCISE_MASTER.items():
        if exercise in exercises:
            return category
    return list(EXERCISE_MASTER.keys())[0]


def calculate_age(birthdate_str):
    if not birthdate_str:
        return None
    try:
        b = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
    except Exception:
        return None
    today = date.today()
    age = today.year - b.year - ((today.month, today.day) < (b.month, b.day))
    return age


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            height_cm REAL,
            body_weight_kg REAL,
            birthdate TEXT,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            workout_date TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '',
            exercise TEXT NOT NULL,
            rest_seconds INTEGER NOT NULL DEFAULT 90,
            rating TEXT NOT NULL DEFAULT '△',
            workout_note TEXT,
            body_weight_kg REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS workout_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER NOT NULL,
            set_no INTEGER NOT NULL,
            weight REAL NOT NULL,
            reps_unassisted INTEGER NOT NULL,
            reps_assisted INTEGER NOT NULL,
            is_warmup INTEGER NOT NULL DEFAULT 0,
            rest_seconds INTEGER NOT NULL DEFAULT 0,
            set_note TEXT DEFAULT '',
            FOREIGN KEY (workout_id) REFERENCES workouts (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS day_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            workout_date TEXT NOT NULL,
            day_note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, workout_date)
        )
        """
    )

    conn.commit()

    if not column_exists("users", "birthdate"):
        cur.execute("ALTER TABLE users ADD COLUMN birthdate TEXT")

    if not column_exists("workouts", "body_weight_kg"):
        cur.execute("ALTER TABLE workouts ADD COLUMN body_weight_kg REAL")

    conn.commit()
    conn.close()


def backfill_known_data():
    conn = get_conn()
    cur = conn.cursor()

    # iwasaki の生年月日を自動補正
    cur.execute(
        """
        UPDATE users
        SET birthdate = '1994-12-21'
        WHERE lower(username) = 'iwasaki'
          AND (birthdate IS NULL OR birthdate = '')
        """
    )

    # iwasaki の 2026-04-18 workout 体重を 84.00 に自動補正
    cur.execute(
        """
        UPDATE workouts
        SET body_weight_kg = 84.0
        WHERE workout_date = '2026-04-18'
          AND user_id IN (
              SELECT id FROM users WHERE lower(username) = 'iwasaki'
          )
          AND (body_weight_kg IS NULL OR body_weight_kg = 0)
        """
    )

    conn.commit()
    conn.close()


def cleanup_expired_sessions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE expires_at <= ?", (utcnow().isoformat(),))
    conn.commit()
    conn.close()


def create_session(user_id, hours=SESSION_HOURS):
    token = os.urandom(32).hex()
    expires_at = utcnow() + timedelta(hours=hours)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sessions (token, user_id, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            token,
            user_id,
            expires_at.isoformat(),
            utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return token


def delete_session(token):
    if not token:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def get_user_from_session(token):
    if not token:
        return None

    cleanup_expired_sessions()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT user_id, expires_at
        FROM sessions
        WHERE token = ?
        """,
        (token,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    try:
        expires_at = datetime.fromisoformat(row["expires_at"])
    except Exception:
        delete_session(token)
        return None

    if expires_at <= utcnow():
        delete_session(token)
        return None

    return get_user_by_id(row["user_id"])


def hash_password(password, salt_hex=None):
    salt = os.urandom(16) if salt_hex is None else bytes.fromhex(salt_hex)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200_000,
    )
    return salt.hex(), pwd_hash.hex()


def create_user(username, password, display_name, height_cm, body_weight_kg, birthdate):
    username = (username or "").strip()
    password = password or ""
    display_name = (display_name or "").strip() or username

    if not username or not password or not display_name:
        return False, "ID・PW・名前は必須です。"

    birthdate_str = None
    if birthdate:
        birthdate_str = birthdate.strftime("%Y-%m-%d")

    conn = get_conn()
    cur = conn.cursor()

    # 既存IDを大文字小文字を無視してチェック
    cur.execute(
        "SELECT 1 FROM users WHERE lower(username) = lower(?) LIMIT 1",
        (username,),
    )
    existing = cur.fetchone()
    if existing is not None:
        conn.close()
        return False, "そのIDは既に登録されています。"

    salt_hex, pwd_hash_hex = hash_password(password)

    try:
        cur.execute(
            """
            INSERT INTO users (
                username, display_name, height_cm, body_weight_kg, birthdate, password_salt, password_hash, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                display_name,
                float(height_cm) if height_cm and float(height_cm) > 0 else None,
                float(body_weight_kg) if body_weight_kg and float(body_weight_kg) > 0 else None,
                birthdate_str,
                salt_hex,
                pwd_hash_hex,
                utcnow().isoformat(),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False, "そのIDは既に登録されています。"

    conn.close()
    return True, "アカウントを作成しました。ログインしてください。"


def authenticate(username, password):
    username = (username or "").strip()
    password = password or ""

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE lower(username) = lower(?)", (username,))
    user = cur.fetchone()
    conn.close()

    if user is None:
        return None

    _, pwd_hash_hex = hash_password(password, salt_hex=user["password_salt"])
    if pwd_hash_hex == user["password_hash"]:
        return dict(user)

    return None


def get_user_by_id(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return dict(user) if user else None


def update_user_profile(user_id, display_name, height_cm, body_weight_kg, birthdate):
    display_name = (display_name or "").strip()

    height_value = None if height_cm is None or float(height_cm) <= 0 else float(height_cm)
    weight_value = None if body_weight_kg is None or float(body_weight_kg) <= 0 else float(body_weight_kg)
    birthdate_str = birthdate.strftime("%Y-%m-%d") if birthdate else None

    if not display_name:
        return False, "名前は必須です。"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET display_name = ?, height_cm = ?, body_weight_kg = ?, birthdate = ?
        WHERE id = ?
        """,
        (
            display_name,
            height_value,
            weight_value,
            birthdate_str,
            user_id,
        ),
    )
    conn.commit()
    conn.close()
    return True, "プロフィールを更新しました。"


def update_user_current_weight(user_id, body_weight_kg):
    if body_weight_kg is None or float(body_weight_kg) <= 0:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET body_weight_kg = ? WHERE id = ?",
        (float(body_weight_kg), user_id),
    )
    conn.commit()
    conn.close()


def get_workouts_for_user(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM workouts
        WHERE user_id = ?
        ORDER BY workout_date DESC, id DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_workout_by_id(workout_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM workouts WHERE id = ?", (workout_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_sets_for_workout(workout_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM workout_sets
        WHERE workout_id = ?
        ORDER BY set_no ASC
        """,
        (workout_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def save_workout(user_id, workout_date, category, exercise, rest_seconds, rating, workout_note, body_weight_kg, sets_data):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO workouts (
            user_id, workout_date, category, exercise, rest_seconds, rating, workout_note, body_weight_kg, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            str(workout_date),
            category.strip(),
            exercise.strip(),
            int(rest_seconds),
            rating,
            (workout_note or "").strip(),
            float(body_weight_kg) if body_weight_kg and float(body_weight_kg) > 0 else None,
            utcnow().isoformat(),
        ),
    )
    workout_id = cur.lastrowid

    for i, s in enumerate(sets_data, start=1):
        cur.execute(
            """
            INSERT INTO workout_sets (
                workout_id,
                set_no,
                weight,
                reps_unassisted,
                reps_assisted,
                is_warmup,
                rest_seconds,
                set_note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workout_id,
                i,
                float(s["weight"]),
                int(s["reps_unassisted"]),
                int(s["reps_assisted"]),
                1 if s["is_warmup"] else 0,
                0,
                "",
            ),
        )

    conn.commit()
    conn.close()


def update_workout(workout_id, workout_date, category, exercise, rest_seconds, rating, workout_note, body_weight_kg, sets_data):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE workouts
        SET workout_date = ?, category = ?, exercise = ?, rest_seconds = ?, rating = ?, workout_note = ?, body_weight_kg = ?
        WHERE id = ?
        """,
        (
            str(workout_date),
            category.strip(),
            exercise.strip(),
            int(rest_seconds),
            rating,
            (workout_note or "").strip(),
            float(body_weight_kg) if body_weight_kg and float(body_weight_kg) > 0 else None,
            workout_id,
        ),
    )

    cur.execute("DELETE FROM workout_sets WHERE workout_id = ?", (workout_id,))

    for i, s in enumerate(sets_data, start=1):
        cur.execute(
            """
            INSERT INTO workout_sets (
                workout_id,
                set_no,
                weight,
                reps_unassisted,
                reps_assisted,
                is_warmup,
                rest_seconds,
                set_note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workout_id,
                i,
                float(s["weight"]),
                int(s["reps_unassisted"]),
                int(s["reps_assisted"]),
                1 if s["is_warmup"] else 0,
                0,
                "",
            ),
        )

    conn.commit()
    conn.close()


def delete_workout(workout_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM workout_sets WHERE workout_id = ?", (workout_id,))
    cur.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
    conn.commit()
    conn.close()


def upsert_day_note(user_id, workout_date, day_note):
    conn = get_conn()
    cur = conn.cursor()
    now = utcnow().isoformat()
    cur.execute(
        """
        INSERT INTO day_notes (user_id, workout_date, day_note, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, workout_date)
        DO UPDATE SET day_note = excluded.day_note, updated_at = excluded.updated_at
        """,
        (user_id, str(workout_date), (day_note or "").strip(), now, now),
    )
    conn.commit()
    conn.close()


def delete_day_note(user_id, workout_date):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM day_notes WHERE user_id = ? AND workout_date = ?",
        (user_id, str(workout_date)),
    )
    conn.commit()
    conn.close()


def get_all_day_notes_map(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT workout_date, day_note
        FROM day_notes
        WHERE user_id = ?
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return {row["workout_date"]: row["day_note"] or "" for row in rows}


def get_latest_same_exercise(user_id, exercise, exclude_workout_id=None):
    exercise = (exercise or "").strip()
    if not exercise or exercise == EXERCISE_PLACEHOLDER:
        return None, []

    conn = get_conn()
    cur = conn.cursor()

    if exclude_workout_id is None:
        cur.execute(
            """
            SELECT *
            FROM workouts
            WHERE user_id = ?
              AND lower(trim(exercise)) = lower(trim(?))
            ORDER BY workout_date DESC, id DESC
            LIMIT 1
            """,
            (user_id, exercise),
        )
    else:
        cur.execute(
            """
            SELECT *
            FROM workouts
            WHERE user_id = ?
              AND lower(trim(exercise)) = lower(trim(?))
              AND id != ?
            ORDER BY workout_date DESC, id DESC
            LIMIT 1
            """,
            (user_id, exercise, exclude_workout_id),
        )

    workout = cur.fetchone()
    if workout is None:
        conn.close()
        return None, []

    cur.execute(
        """
        SELECT *
        FROM workout_sets
        WHERE workout_id = ?
        ORDER BY set_no ASC
        """,
        (workout["id"],),
    )
    sets_rows = cur.fetchall()
    conn.close()
    return workout, sets_rows


def estimate_1rm_brzycki(weight, reps_unassisted):
    if weight <= 0:
        return None
    if reps_unassisted < 1 or reps_unassisted > 10:
        return None

    denominator = 37 - reps_unassisted
    if denominator <= 0:
        return None

    return weight * (36 / denominator)


def best_estimated_1rm(sets_data):
    candidates = []
    for s in sets_data:
        if s["is_warmup"]:
            continue
        est = estimate_1rm_brzycki(float(s["weight"]), int(s["reps_unassisted"]))
        if est is not None:
            candidates.append((est, s))
    if not candidates:
        return None, None
    return max(candidates, key=lambda x: x[0])


def get_exercise_met(category, exercise):
    if exercise in EXERCISE_METS:
        return EXERCISE_METS[exercise]
    if category in CATEGORY_DEFAULT_MET:
        return CATEGORY_DEFAULT_MET[category]
    return 5.0


def calculate_workout_metrics(workout, sets_rows):
    total_load = 0.0
    main_load = 0.0
    total_sets = len(sets_rows)
    total_reps = 0
    active_seconds = 0

    for row in sets_rows:
        reps = int(row["reps_unassisted"]) + int(row["reps_assisted"])
        load = float(row["weight"]) * reps
        total_load += load
        total_reps += reps
        active_seconds += reps * 4
        if not bool(row["is_warmup"]):
            main_load += load

    rest_intervals = max(total_sets - 1, 0)
    total_seconds = active_seconds + int(workout["rest_seconds"]) * rest_intervals

    met = get_exercise_met(
        workout["category"] or infer_category_from_exercise(workout["exercise"]),
        workout["exercise"],
    )

    est_kcal = None
    bw = workout["body_weight_kg"]
    if bw is not None and float(bw) > 0:
        est_kcal = met * float(bw) * (total_seconds / 3600)

    return {
        "total_load": total_load,
        "main_load": main_load,
        "total_sets": total_sets,
        "total_reps": total_reps,
        "est_kcal": est_kcal,
    }


def calculate_daily_summary(entries):
    summary = {
        "total_load": 0.0,
        "main_load": 0.0,
        "total_sets": 0,
        "total_reps": 0,
        "est_kcal": 0.0,
        "has_kcal": True,
    }

    for entry in entries:
        metrics = entry["metrics"]
        summary["total_load"] += metrics["total_load"]
        summary["main_load"] += metrics["main_load"]
        summary["total_sets"] += metrics["total_sets"]
        summary["total_reps"] += metrics["total_reps"]

        if metrics["est_kcal"] is None:
            summary["has_kcal"] = False
        else:
            summary["est_kcal"] += metrics["est_kcal"]

    return summary


def default_set_model():
    return {
        "is_warmup": False,
        "weight": 0.0,
        "reps_unassisted": 0,
        "reps_assisted": 0,
    }


def ensure_app_state():
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "page" not in st.session_state:
        st.session_state.page = "入力"
    if "editing_workout_id" not in st.session_state:
        st.session_state.editing_workout_id = None
    if "org_gate_passed" not in st.session_state:
        st.session_state.org_gate_passed = False
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0
    if "flash_message" not in st.session_state:
        st.session_state.flash_message = None


def entry_key(name):
    return f"{name}_{st.session_state.form_version}"


def model_key():
    return f"sets_model_{st.session_state.form_version}"


def set_widget_key(field, index):
    return f"set_{field}_{st.session_state.form_version}_{index}"


def get_current_header():
    return {
        "workout_date": st.session_state.get(entry_key("workout_date"), date.today()),
        "category": st.session_state.get(entry_key("category"), CATEGORY_PLACEHOLDER),
        "exercise": st.session_state.get(entry_key("exercise"), EXERCISE_PLACEHOLDER),
        "rest_seconds": st.session_state.get(entry_key("rest_seconds"), 90),
        "rating": st.session_state.get(entry_key("rating"), "△"),
        "workout_note": st.session_state.get(entry_key("workout_note"), ""),
        "body_weight_kg": st.session_state.get(entry_key("body_weight_kg"), 0.0),
    }


def hydrate_set_widgets_from_model():
    model = st.session_state[model_key()]
    for i, row in enumerate(model):
        wk = set_widget_key("is_warmup", i)
        wtk = set_widget_key("weight", i)
        ruk = set_widget_key("reps_unassisted", i)
        rak = set_widget_key("reps_assisted", i)

        if wk not in st.session_state:
            st.session_state[wk] = bool(row["is_warmup"])
        if wtk not in st.session_state:
            st.session_state[wtk] = float(row["weight"])
        if ruk not in st.session_state:
            st.session_state[ruk] = int(row["reps_unassisted"])
        if rak not in st.session_state:
            st.session_state[rak] = int(row["reps_assisted"])


def sync_set_field(index, field):
    model = st.session_state[model_key()]
    if index >= len(model):
        return
    widget_key = set_widget_key(field, index)
    model[index][field] = st.session_state[widget_key]


def ensure_form_defaults(user=None):
    if entry_key("workout_date") not in st.session_state:
        st.session_state[entry_key("workout_date")] = date.today()
    if entry_key("category") not in st.session_state:
        st.session_state[entry_key("category")] = CATEGORY_PLACEHOLDER
    if entry_key("exercise") not in st.session_state:
        st.session_state[entry_key("exercise")] = EXERCISE_PLACEHOLDER
    if entry_key("rest_seconds") not in st.session_state:
        st.session_state[entry_key("rest_seconds")] = 90
    if entry_key("rating") not in st.session_state:
        st.session_state[entry_key("rating")] = "△"
    if entry_key("workout_note") not in st.session_state:
        st.session_state[entry_key("workout_note")] = ""
    if entry_key("body_weight_kg") not in st.session_state:
        if user and user.get("body_weight_kg") is not None:
            st.session_state[entry_key("body_weight_kg")] = float(user["body_weight_kg"])
        else:
            st.session_state[entry_key("body_weight_kg")] = 0.0

    if model_key() not in st.session_state:
        st.session_state[model_key()] = [default_set_model()]

    hydrate_set_widgets_from_model()


def load_form_state(header, sets_model, editing_id=None):
    st.session_state.form_version += 1
    st.session_state.editing_workout_id = editing_id

    st.session_state[entry_key("workout_date")] = header["workout_date"]
    st.session_state[entry_key("category")] = header["category"]
    st.session_state[entry_key("exercise")] = header["exercise"]
    st.session_state[entry_key("rest_seconds")] = header["rest_seconds"]
    st.session_state[entry_key("rating")] = header["rating"]
    st.session_state[entry_key("workout_note")] = header["workout_note"]
    st.session_state[entry_key("body_weight_kg")] = header["body_weight_kg"]

    st.session_state[model_key()] = sets_model
    hydrate_set_widgets_from_model()


def reset_entry_form(user=None, preserve_date=None, preserve_rest=None):
    body_weight = 0.0
    if user and user.get("body_weight_kg") is not None:
        body_weight = float(user["body_weight_kg"])

    header = {
        "workout_date": preserve_date if preserve_date is not None else date.today(),
        "category": CATEGORY_PLACEHOLDER,
        "exercise": EXERCISE_PLACEHOLDER,
        "rest_seconds": int(preserve_rest) if preserve_rest is not None else 90,
        "rating": "△",
        "workout_note": "",
        "body_weight_kg": body_weight,
    }
    load_form_state(header, [default_set_model()], editing_id=None)


def current_sets_model():
    return st.session_state[model_key()]


def current_sets_payload():
    return [dict(row) for row in current_sets_model()]


def append_blank_set():
    header = get_current_header()
    new_sets = current_sets_payload()
    new_sets.append(default_set_model())
    load_form_state(header, new_sets, st.session_state.editing_workout_id)


def append_copy_set(index):
    header = get_current_header()
    new_sets = current_sets_payload()
    if 0 <= index < len(new_sets):
        new_sets.append(dict(new_sets[index]))
    else:
        new_sets.append(default_set_model())
    load_form_state(header, new_sets, st.session_state.editing_workout_id)


def remove_set(index):
    header = get_current_header()
    new_sets = current_sets_payload()
    if len(new_sets) <= 1:
        return
    new_sets = [row for i, row in enumerate(new_sets) if i != index]
    load_form_state(header, new_sets, st.session_state.editing_workout_id)


def copy_previous_full_entry(user_id, current_header):
    workout, sets_rows = get_latest_same_exercise(
        user_id,
        current_header["exercise"],
        st.session_state.editing_workout_id,
    )
    if workout is None:
        return False

    sets_model = []
    for row in sets_rows:
        sets_model.append(
            {
                "is_warmup": bool(row["is_warmup"]),
                "weight": float(row["weight"]),
                "reps_unassisted": int(row["reps_unassisted"]),
                "reps_assisted": int(row["reps_assisted"]),
            }
        )

    header = dict(current_header)
    header["rest_seconds"] = int(workout["rest_seconds"])
    header["rating"] = workout["rating"] if workout["rating"] in ["〇", "△", "×"] else "△"
    header["workout_note"] = workout["workout_note"] or ""

    load_form_state(header, sets_model or [default_set_model()], st.session_state.editing_workout_id)
    return True


def load_workout_into_form(workout_id):
    workout = get_workout_by_id(workout_id)
    sets_rows = get_sets_for_workout(workout_id)

    category = workout["category"] or infer_category_from_exercise(workout["exercise"])

    header = {
        "workout_date": datetime.strptime(workout["workout_date"], "%Y-%m-%d").date(),
        "category": category,
        "exercise": workout["exercise"],
        "rest_seconds": int(workout["rest_seconds"]),
        "rating": workout["rating"] if workout["rating"] in ["〇", "△", "×"] else "△",
        "workout_note": workout["workout_note"] or "",
        "body_weight_kg": float(workout["body_weight_kg"]) if workout["body_weight_kg"] is not None else 0.0,
    }

    sets_model = []
    for row in sets_rows:
        sets_model.append(
            {
                "is_warmup": bool(row["is_warmup"]),
                "weight": float(row["weight"]),
                "reps_unassisted": int(row["reps_unassisted"]),
                "reps_assisted": int(row["reps_assisted"]),
            }
        )

    if not sets_model:
        sets_model = [default_set_model()]

    load_form_state(header, sets_model, editing_id=workout_id)
    st.session_state.page = "入力"


def get_user_body_weight_kg(user):
    value = user.get("body_weight_kg")
    if value is None:
        return None
    try:
        value = float(value)
    except Exception:
        return None
    if value <= 0:
        return None
    return value


def render_previous_exercise_summary(user_id, exercise, exclude_workout_id=None):
    workout, sets_rows = get_latest_same_exercise(user_id, exercise, exclude_workout_id)
    if workout is None:
        return

    lines = [f"前回：{workout['workout_date']}"]

    main_sets = [row for row in sets_rows if not bool(row["is_warmup"])]
    for idx, row in enumerate(main_sets, start=1):
        lines.append(
            f"セット{idx}：{row['weight']}kg 補助なし{row['reps_unassisted']}回＋補助あり{row['reps_assisted']}回"
        )

    if workout["workout_note"]:
        lines.append(f"メモ：{workout['workout_note']}")

    lines.append(f"レスト：{workout['rest_seconds']}秒")
    lines.append(f"評価：{workout['rating']}")

    html = "<br>".join(lines)

    st.caption("直近の同種目")
    st.markdown(
        f"""
        <div style="
            background: rgba(70, 120, 220, 0.18);
            border-radius: 14px;
            padding: 14px 16px;
            line-height: 1.8;
            font-size: 1rem;
        ">
            {html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_set_block(i):
    row = current_sets_model()[i]

    with st.expander(f"Set {i + 1}", expanded=True):
        st.checkbox(
            "ウォームアップ",
            key=set_widget_key("is_warmup", i),
            value=bool(row["is_warmup"]),
            on_change=sync_set_field,
            args=(i, "is_warmup"),
        )

        st.number_input(
            "重さ (kg)",
            min_value=0.0,
            step=2.5,
            key=set_widget_key("weight", i),
            value=float(row["weight"]),
            on_change=sync_set_field,
            args=(i, "weight"),
        )

        st.number_input(
            "回数（補助なし）",
            min_value=0,
            step=1,
            key=set_widget_key("reps_unassisted", i),
            value=int(row["reps_unassisted"]),
            on_change=sync_set_field,
            args=(i, "reps_unassisted"),
        )

        st.number_input(
            "回数（補助あり）",
            min_value=0,
            step=1,
            key=set_widget_key("reps_assisted", i),
            value=int(row["reps_assisted"]),
            on_change=sync_set_field,
            args=(i, "reps_assisted"),
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("コピー追加", key=f"copy_{st.session_state.form_version}_{i}"):
                append_copy_set(i)
                st.rerun()
        with c2:
            if st.button("空で追加", key=f"blank_{st.session_state.form_version}_{i}"):
                append_blank_set()
                st.rerun()
        with c3:
            if st.button(
                "このセット削除",
                key=f"remove_{st.session_state.form_version}_{i}",
                disabled=(len(current_sets_model()) <= 1),
            ):
                remove_set(i)
                st.rerun()


def render_input_page(user):
    # ここで毎回プロフィール最新体重を初期値化
    current_bw_key = entry_key("body_weight_kg")
    if (
        current_bw_key not in st.session_state
        or float(st.session_state[current_bw_key]) <= 0
    ) and user.get("body_weight_kg") is not None:
        st.session_state[current_bw_key] = float(user["body_weight_kg"])

    if st.session_state.editing_workout_id is not None:
        st.warning("現在、既存記録を修正中です。")
        if st.button("修正をやめる", key="cancel_edit"):
            reset_entry_form(user=st.session_state.current_user)
            st.rerun()

    st.subheader("入力")

    st.date_input("日付", key=entry_key("workout_date"))

    category_options = [CATEGORY_PLACEHOLDER] + list(EXERCISE_MASTER.keys())
    st.selectbox("カテゴリ", category_options, key=entry_key("category"))

    selected_category = st.session_state[entry_key("category")]

    if selected_category == CATEGORY_PLACEHOLDER:
        exercise_options = [EXERCISE_PLACEHOLDER]
        st.session_state[entry_key("exercise")] = EXERCISE_PLACEHOLDER
    else:
        exercise_options = [EXERCISE_PLACEHOLDER] + EXERCISE_MASTER[selected_category]
        current_exercise = st.session_state.get(entry_key("exercise"), EXERCISE_PLACEHOLDER)
        if current_exercise not in exercise_options:
            st.session_state[entry_key("exercise")] = EXERCISE_PLACEHOLDER

    st.selectbox("種目", exercise_options, key=entry_key("exercise"))
    st.number_input("レスト (秒)", min_value=0, step=5, key=entry_key("rest_seconds"))
    st.number_input("体重 (kg)", min_value=0.0, step=0.1, key=entry_key("body_weight_kg"))

    selected_exercise = st.session_state[entry_key("exercise")].strip()
    if (
        selected_category != CATEGORY_PLACEHOLDER
        and selected_exercise != EXERCISE_PLACEHOLDER
    ):
        render_previous_exercise_summary(
            user["id"],
            selected_exercise,
            st.session_state.editing_workout_id,
        )

        if st.button("前回の全セット・メモ等を複製", key=f"copy_prev_all_{st.session_state.form_version}"):
            ok = copy_previous_full_entry(user["id"], get_current_header())
            if ok:
                st.rerun()

    st.subheader("セット入力")

    for i in range(len(current_sets_model())):
        render_set_block(i)

    current_sets = current_sets_payload()
    best_1rm, best_set = best_estimated_1rm(current_sets)

    if best_1rm is not None and best_set is not None:
        st.info(
            f'参考: 推定1RM {best_1rm:.1f} kg '
            f'（{best_set["weight"]} kg × 補助なし {best_set["reps_unassisted"]} 回 / ウォームアップ除外）'
        )
    else:
        st.caption("参考値は、補助なし1〜10回・ウォームアップ以外のセットがあると表示します。")

    st.selectbox("評価", ["〇", "△", "×"], key=entry_key("rating"))
    st.text_area("種目メモ", key=entry_key("workout_note"), placeholder="任意")

    button_label = "更新する" if st.session_state.editing_workout_id is not None else "この内容で保存"

    if st.button(button_label, type="primary", key=f"save_btn_{st.session_state.form_version}"):
        header = get_current_header()
        sets_data = current_sets_payload()

        if header["category"] == CATEGORY_PLACEHOLDER:
            st.error("カテゴリを選択してください。")
            return
        if header["exercise"] == EXERCISE_PLACEHOLDER:
            st.error("種目を選択してください。")
            return

        valid_sets = []
        for s in sets_data:
            if s["weight"] > 0 or s["reps_unassisted"] > 0 or s["reps_assisted"] > 0:
                valid_sets.append(s)

        if not valid_sets:
            st.error("最低1セットは入力してください。")
            return

        if st.session_state.editing_workout_id is None:
            save_workout(
                user["id"],
                header["workout_date"],
                header["category"],
                header["exercise"],
                header["rest_seconds"],
                header["rating"],
                header["workout_note"],
                header["body_weight_kg"],
                valid_sets,
            )
            update_user_current_weight(user["id"], header["body_weight_kg"])
            st.session_state.current_user = get_user_by_id(user["id"])
            st.session_state.flash_message = "記録を保存しました。"
            reset_entry_form(
                user=st.session_state.current_user,
                preserve_date=header["workout_date"],
                preserve_rest=header["rest_seconds"],
            )
            st.rerun()
        else:
            update_workout(
                st.session_state.editing_workout_id,
                header["workout_date"],
                header["category"],
                header["exercise"],
                header["rest_seconds"],
                header["rating"],
                header["workout_note"],
                header["body_weight_kg"],
                valid_sets,
            )
            update_user_current_weight(user["id"], header["body_weight_kg"])
            st.session_state.current_user = get_user_by_id(user["id"])
            st.session_state.flash_message = "記録を更新しました。"
            reset_entry_form(user=st.session_state.current_user)
            st.session_state.page = "記録一覧"
            st.rerun()


def render_records_page(user):
    st.subheader("記録一覧")

    with st.expander("空の日付メモを追加 / 更新", expanded=False):
        with st.form("empty_day_note_form"):
            empty_date = st.date_input("日付", value=date.today(), key="empty_day_note_date")
            empty_note = st.text_area("日付メモ", key="empty_day_note_text", placeholder="例: パーソナル5回目 / 当日キャンセル / 実施場所など")
            submitted = st.form_submit_button("この日付メモを保存")
            if submitted:
                if (empty_note or "").strip():
                    upsert_day_note(user["id"], empty_date, empty_note)
                    st.session_state.flash_message = "日付メモを保存しました。"
                else:
                    delete_day_note(user["id"], empty_date)
                    st.session_state.flash_message = "日付メモを削除しました。"
                st.rerun()

    workouts = get_workouts_for_user(user["id"])
    day_notes_map = get_all_day_notes_map(user["id"])

    workout_dates = {w["workout_date"] for w in workouts}
    note_dates = set(day_notes_map.keys())
    all_dates = sorted(workout_dates | note_dates, reverse=True)

    if not all_dates:
        st.info("まだ記録がありません。")
        return

    for workout_date in all_dates:
        day_workouts = [w for w in workouts if w["workout_date"] == workout_date]
        day_workouts = sorted(day_workouts, key=lambda x: (x["created_at"], x["id"]))  # 古いものが上
        day_note = day_notes_map.get(workout_date, "")

        entries = []
        for workout in day_workouts:
            sets_rows = get_sets_for_workout(workout["id"])
            metrics = calculate_workout_metrics(workout, sets_rows)
            entries.append(
                {
                    "workout": workout,
                    "sets_rows": sets_rows,
                    "metrics": metrics,
                }
            )

        daily = calculate_daily_summary(entries)

        st.markdown(f"## {workout_date}")

        if daily["has_kcal"]:
            kcal_text = f"{daily['est_kcal']:.0f} kcal"
        else:
            kcal_text = "体重未設定の記録あり"

        st.markdown(
            f"""
<div style="
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 16px;
">
    <div style="font-weight: 700; margin-bottom: 8px;">日別サマリー</div>
    <div>推定消費カロリー: {kcal_text}</div>
    <div>総負荷: {daily["total_load"]:.1f} kg</div>
    <div>メイン負荷: {daily["main_load"]:.1f} kg</div>
    <div>総セット数: {daily["total_sets"]}</div>
    <div>総レップ数: {daily["total_reps"]}</div>
</div>
            """,
            unsafe_allow_html=True,
        )

        with st.form(f"day_note_form_{workout_date}"):
            edited_note = st.text_area(
                "日付メモ",
                value=day_note,
                key=f"day_note_edit_{workout_date}",
                placeholder="例: パーソナル回数券の何回目か / 実施場所 / キャンセルなど",
            )
            note_saved = st.form_submit_button("日付メモを保存")
            if note_saved:
                if (edited_note or "").strip():
                    upsert_day_note(user["id"], workout_date, edited_note)
                    st.session_state.flash_message = f"{workout_date} の日付メモを保存しました。"
                else:
                    delete_day_note(user["id"], workout_date)
                    st.session_state.flash_message = f"{workout_date} の日付メモを削除しました。"
                st.rerun()

        if not day_workouts:
            st.caption("この日付には筋トレ種目の記録がありません。")
            continue

        for entry in entries:
            workout = entry["workout"]
            sets_rows = entry["sets_rows"]
            metrics = entry["metrics"]
            category_text = workout["category"] or infer_category_from_exercise(workout["exercise"])

            sets_data = []
            for row in sets_rows:
                sets_data.append(
                    {
                        "weight": row["weight"],
                        "reps_unassisted": row["reps_unassisted"],
                        "reps_assisted": row["reps_assisted"],
                        "is_warmup": bool(row["is_warmup"]),
                    }
                )

            est_1rm, est_set = best_estimated_1rm(sets_data)

            with st.expander(f"{category_text} / {workout['exercise']}", expanded=False):
                st.write(f"レスト: {workout['rest_seconds']} 秒")
                st.write(f"評価: {workout['rating']}")
                if workout["body_weight_kg"] is not None:
                    st.write(f"体重スナップショット: {float(workout['body_weight_kg']):.2f} kg")

                if metrics["est_kcal"] is not None:
                    st.write(f"推定消費カロリー（参考）: {metrics['est_kcal']:.0f} kcal")
                else:
                    st.write("推定消費カロリー（参考）: 体重未設定")

                st.write(f"種目負荷: {metrics['total_load']:.1f} kg")
                st.write(f"メイン負荷: {metrics['main_load']:.1f} kg")
                st.write(f"総セット数: {metrics['total_sets']}")
                st.write(f"総レップ数: {metrics['total_reps']}")

                for row in sets_rows:
                    label = "WU" if bool(row["is_warmup"]) else "MAIN"
                    st.markdown(
                        f"""
- Set {row["set_no"]} [{label}]  
  {row["weight"]} kg / 補助なし {row["reps_unassisted"]} 回 / 補助あり {row["reps_assisted"]} 回
"""
                    )

                if workout["workout_note"]:
                    st.caption(f'メモ: {workout["workout_note"]}')

                if est_1rm is not None and est_set is not None:
                    st.caption(
                        f'推定1RM: {est_1rm:.1f} kg '
                        f'（{est_set["weight"]} kg × 補助なし {est_set["reps_unassisted"]} 回）'
                    )

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("修正する", key=f"edit_{workout['id']}"):
                        load_workout_into_form(workout["id"])
                        st.rerun()
                with c2:
                    if st.button("削除する", key=f"delete_{workout['id']}"):
                        if st.session_state.editing_workout_id == workout["id"]:
                            reset_entry_form(user=st.session_state.current_user)
                        delete_workout(workout["id"])
                        st.session_state.flash_message = "記録を削除しました。"
                        st.rerun()


def render_stats_page(user):
    st.subheader("統計")

    category_options = list(EXERCISE_MASTER.keys())
    selected_category = st.selectbox("カテゴリ", category_options, key="stats_category")
    selected_exercise = st.selectbox("種目", EXERCISE_MASTER[selected_category], key="stats_exercise")

    workouts = get_workouts_for_user(user["id"])
    target_workouts = [w for w in workouts if w["exercise"] == selected_exercise]

    if not target_workouts:
        st.info("該当種目の記録がありません。")
        return

    by_date = {}
    for workout in target_workouts:
        sets_rows = get_sets_for_workout(workout["id"])
        main_sets = [row for row in sets_rows if not bool(row["is_warmup"])]

        if main_sets:
            max_weight = max(float(row["weight"]) for row in main_sets)
        else:
            max_weight = 0.0

        sets_data = [
            {
                "weight": row["weight"],
                "reps_unassisted": row["reps_unassisted"],
                "reps_assisted": row["reps_assisted"],
                "is_warmup": bool(row["is_warmup"]),
            }
            for row in sets_rows
        ]
        best_1rm, _ = best_estimated_1rm(sets_data)
        best_1rm = 0.0 if best_1rm is None else float(best_1rm)

        d = workout["workout_date"]
        if d not in by_date:
            by_date[d] = {"max_weight": max_weight, "estimated_1rm": best_1rm}
        else:
            by_date[d]["max_weight"] = max(by_date[d]["max_weight"], max_weight)
            by_date[d]["estimated_1rm"] = max(by_date[d]["estimated_1rm"], best_1rm)

    df = pd.DataFrame(
        [
            {
                "date": d,
                "最大セット重量": vals["max_weight"],
                "推定最大RM": vals["estimated_1rm"],
            }
            for d, vals in by_date.items()
        ]
    ).sort_values("date")

    st.line_chart(df.set_index("date")[["最大セット重量", "推定最大RM"]], use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_profile_page(user):
    st.subheader("プロフィール")

    current_name = user["display_name"] or ""
    current_height = 0.0 if user["height_cm"] is None else float(user["height_cm"])
    current_weight = 0.0 if user["body_weight_kg"] is None else float(user["body_weight_kg"])

    current_birthdate = None
    if user.get("birthdate"):
        try:
            current_birthdate = datetime.strptime(user["birthdate"], "%Y-%m-%d").date()
        except Exception:
            current_birthdate = None

    age = calculate_age(user.get("birthdate"))

    with st.form("profile_form"):
        st.text_input("名前", value=current_name, key="profile_name")
        st.number_input("身長 (cm)", min_value=0.0, step=0.5, value=float(current_height), key="profile_height")
        st.number_input("体重 (kg)", min_value=0.0, step=0.1, value=float(current_weight), key="profile_weight")
        st.date_input("生年月日", value=current_birthdate if current_birthdate else date(1990, 1, 1), key="profile_birthdate")
        submitted = st.form_submit_button("プロフィールを保存")

        if submitted:
            ok, message = update_user_profile(
                user["id"],
                st.session_state["profile_name"],
                st.session_state["profile_height"],
                st.session_state["profile_weight"],
                st.session_state["profile_birthdate"],
            )
            if ok:
                st.session_state.current_user = get_user_by_id(user["id"])
                st.session_state.flash_message = message
                st.rerun()
            else:
                st.error(message)

    if age is not None:
        st.write(f"年齢: {age}歳")
    else:
        st.write("年齢: 未設定")

    st.caption("入力ページの体重欄は、ここで保存した体重を初期値として表示します。")


st.set_page_config(
    page_title=f"筋トレメモ ver.{APP_VERSION}",
    page_icon="🏋️",
    layout="centered",
)

st.markdown(
    """
<style>
.block-container {
    max-width: 820px;
    padding-top: 1rem;
    padding-bottom: 4rem;
}
.stButton > button {
    width: 100%;
    min-height: 44px;
    border-radius: 12px;
}
div[data-testid="stExpander"] {
    border-radius: 12px;
}
.stApp,
.stApp p,
.stApp li,
.stApp label,
.stApp input,
.stApp textarea,
.stApp button,
.stApp div[data-baseweb="select"],
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stAlertContainer"] {
    font-size: 17px !important;
}
@media (max-width: 640px) {
    .block-container {
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

cookies = EncryptedCookieManager(
    prefix="workout-memo/",
    password=COOKIE_PASSWORD,
)

if not cookies.ready():
    st.stop()

init_db()
backfill_known_data()
cleanup_expired_sessions()
ensure_app_state()

existing_token = cookies.get(SESSION_COOKIE_NAME)

if st.session_state.current_user is None and existing_token:
    remembered_user = get_user_from_session(existing_token)
    if remembered_user:
        st.session_state.current_user = remembered_user
        st.session_state.org_gate_passed = True
    else:
        try:
            del cookies[SESSION_COOKIE_NAME]
            cookies.save()
        except Exception:
            pass

if st.session_state.current_user is None:
    render_app_title()

    if not st.session_state.org_gate_passed:
        st.write("団体パスワードを入力してください。")
        org_pw = st.text_input("団体パスワード", type="password", key="org_pw")
        if st.button("次へ", key="org_pw_button", type="primary"):
            if org_pw == ORG_PASSWORD:
                st.session_state.org_gate_passed = True
                st.rerun()
            else:
                st.error("団体パスワードが違います。")
        st.stop()

    login_tab, signup_tab = st.tabs(["ログイン", "新規登録"])

    with login_tab:
        login_id = st.text_input("ID", key="login_id")
        login_pw = st.text_input("PW", type="password", key="login_pw")

        if st.button("ログイン", key="login_button", type="primary"):
            user = authenticate(login_id, login_pw)
            if user:
                token = create_session(user["id"], hours=SESSION_HOURS)
                cookies[SESSION_COOKIE_NAME] = token
                cookies.save()
                st.session_state.current_user = get_user_by_id(user["id"])
                st.session_state.org_gate_passed = True
                reset_entry_form(user=st.session_state.current_user)
                st.session_state.flash_message = "ログインしました。"
                st.rerun()
            else:
                st.error("IDまたはPWが違います。")

    with signup_tab:
        signup_name = st.text_input("名前", key="signup_name")
        signup_id = st.text_input("新しいID", key="signup_id")
        signup_pw = st.text_input("新しいPW", type="password", key="signup_pw")
        signup_height = st.number_input("身長 (cm)", min_value=0.0, step=0.5, key="signup_height")
        signup_weight = st.number_input("体重 (kg)", min_value=0.0, step=0.1, key="signup_weight")
        signup_birthdate = st.date_input("生年月日", value=date(1990, 1, 1), key="signup_birthdate")

        if st.button("新規登録する", key="signup_button"):
            ok, message = create_user(
                signup_id,
                signup_pw,
                signup_name,
                signup_height,
                signup_weight,
                signup_birthdate,
            )
            if ok:
                st.success(message)
            else:
                st.error(message)

    st.stop()

user = st.session_state.current_user
ensure_form_defaults(user)

top_left, top_right = st.columns([4, 1])
with top_left:
    render_app_title()
    st.caption(
        f'ログイン中: {user["display_name"]} / ID: {user["username"]} / ログイン保持: {SESSION_HOURS}時間'
    )
with top_right:
    if st.button("ログアウト", key="logout_button"):
        existing_token = cookies.get(SESSION_COOKIE_NAME)
        if existing_token:
            delete_session(existing_token)
            try:
                del cookies[SESSION_COOKIE_NAME]
                cookies.save()
            except Exception:
                pass
        st.session_state.current_user = None
        st.session_state.org_gate_passed = False
        st.rerun()

if st.session_state.flash_message:
    st.success(st.session_state.flash_message)
    st.session_state.flash_message = None

st.sidebar.title("メニュー")
page_options = ["入力", "記録一覧", "統計", "プロフィール"]
current_index = page_options.index(st.session_state.page) if st.session_state.page in page_options else 0
st.session_state.page = st.sidebar.radio("ページ", page_options, index=current_index)

if st.session_state.page == "入力":
    render_input_page(user)
elif st.session_state.page == "記録一覧":
    render_records_page(user)
elif st.session_state.page == "統計":
    render_stats_page(user)
else:
    render_profile_page(user)
