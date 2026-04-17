import os
import sqlite3
import hashlib
from datetime import date, datetime, timedelta

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

APP_VERSION = "1.1.0"
DB_NAME = "workout_app.db"
SESSION_COOKIE_NAME = "workout_session_token"
SESSION_HOURS = 2

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


def get_table_columns(table_name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    rows = cur.fetchall()
    conn.close()
    return [row["name"] for row in rows]


def column_exists(table_name, column_name):
    return column_name in get_table_columns(table_name)


def utcnow():
    return datetime.utcnow()


def infer_category_from_exercise(exercise):
    exercise = (exercise or "").strip()
    for category, exercises in EXERCISE_MASTER.items():
        if exercise in exercises:
            return category
    return list(EXERCISE_MASTER.keys())[0]


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

    conn.commit()

    if not column_exists("users", "height_cm"):
        cur.execute("ALTER TABLE users ADD COLUMN height_cm REAL")
    if not column_exists("users", "body_weight_kg"):
        cur.execute("ALTER TABLE users ADD COLUMN body_weight_kg REAL")

    if not column_exists("workouts", "category"):
        cur.execute("ALTER TABLE workouts ADD COLUMN category TEXT NOT NULL DEFAULT ''")
    if not column_exists("workouts", "rest_seconds"):
        cur.execute("ALTER TABLE workouts ADD COLUMN rest_seconds INTEGER NOT NULL DEFAULT 90")
    if not column_exists("workouts", "rating"):
        cur.execute("ALTER TABLE workouts ADD COLUMN rating TEXT NOT NULL DEFAULT '△'")
    if not column_exists("workouts", "workout_note"):
        cur.execute("ALTER TABLE workouts ADD COLUMN workout_note TEXT")

    if not column_exists("workout_sets", "is_warmup"):
        cur.execute("ALTER TABLE workout_sets ADD COLUMN is_warmup INTEGER NOT NULL DEFAULT 0")
    if not column_exists("workout_sets", "rest_seconds"):
        cur.execute("ALTER TABLE workout_sets ADD COLUMN rest_seconds INTEGER NOT NULL DEFAULT 0")
    if not column_exists("workout_sets", "set_note"):
        cur.execute("ALTER TABLE workout_sets ADD COLUMN set_note TEXT DEFAULT ''")

    conn.commit()
    conn.close()


def cleanup_expired_sessions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM sessions WHERE expires_at <= ?",
        (utcnow().isoformat(),),
    )
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
        SELECT s.user_id, s.expires_at
        FROM sessions s
        WHERE s.token = ?
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


def authenticate(username, password):
    username = (username or "").strip()
    password = password or ""

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
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


def update_user_profile(user_id, display_name, height_cm, body_weight_kg):
    display_name = (display_name or "").strip()

    height_value = None if height_cm is None or float(height_cm) <= 0 else float(height_cm)
    weight_value = None if body_weight_kg is None or float(body_weight_kg) <= 0 else float(body_weight_kg)

    if not display_name:
        return False, "名前は必須です。"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET display_name = ?, height_cm = ?, body_weight_kg = ?
        WHERE id = ?
        """,
        (
            display_name,
            height_value,
            weight_value,
            user_id,
        ),
    )
    conn.commit()
    conn.close()
    return True, "プロフィールを更新しました。"


def save_workout(user_id, workout_date, category, exercise, rest_seconds, rating, workout_note, sets_data):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO workouts (
            user_id, workout_date, category, exercise, rest_seconds, rating, workout_note, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            str(workout_date),
            category.strip(),
            exercise.strip(),
            int(rest_seconds),
            rating,
            (workout_note or "").strip(),
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


def update_workout(workout_id, workout_date, category, exercise, rest_seconds, rating, workout_note, sets_data):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE workouts
        SET workout_date = ?, category = ?, exercise = ?, rest_seconds = ?, rating = ?, workout_note = ?
        WHERE id = ?
        """,
        (
            str(workout_date),
            category.strip(),
            exercise.strip(),
            int(rest_seconds),
            rating,
            (workout_note or "").strip(),
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
        if s.get("is_warmup"):
            continue

        est = estimate_1rm_brzycki(
            float(s["weight"]),
            int(s["reps_unassisted"]),
        )
        if est is not None:
            candidates.append((est, s))

    if not candidates:
        return None, None

    return max(candidates, key=lambda x: x[0])


def default_set():
    return {
        "weight": 0.0,
        "reps_unassisted": 0,
        "reps_assisted": 0,
        "is_warmup": False,
    }


def ensure_app_state():
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0
    if "set_count" not in st.session_state:
        st.session_state.set_count = 1
    if "editing_workout_id" not in st.session_state:
        st.session_state.editing_workout_id = None
    if "page" not in st.session_state:
        st.session_state.page = "入力"
    if "flash_message" not in st.session_state:
        st.session_state.flash_message = None


def entry_key(name):
    return f"{name}_{st.session_state.form_version}"


def set_key(name, index):
    return f"{name}_{st.session_state.form_version}_{index}"


def ensure_category_exercise_state():
    category_key = entry_key("category")
    exercise_key = entry_key("exercise")

    valid_categories = list(EXERCISE_MASTER.keys())

    current_category = st.session_state.get(category_key, CATEGORY_PLACEHOLDER)
    if current_category not in valid_categories:
        st.session_state[category_key] = CATEGORY_PLACEHOLDER
        st.session_state[exercise_key] = EXERCISE_PLACEHOLDER
        return

    exercise_options = EXERCISE_MASTER[current_category]
    current_exercise = st.session_state.get(exercise_key, EXERCISE_PLACEHOLDER)

    if current_exercise not in exercise_options:
        st.session_state[exercise_key] = EXERCISE_PLACEHOLDER


def ensure_form_defaults():
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

    ensure_category_exercise_state()

    for i in range(st.session_state.set_count):
        d = default_set()
        for field, value in d.items():
            key = set_key(field, i)
            if key not in st.session_state:
                st.session_state[key] = value


def read_set_from_state(index):
    return {
        "weight": float(st.session_state.get(set_key("weight", index), 0.0)),
        "reps_unassisted": int(st.session_state.get(set_key("reps_unassisted", index), 0)),
        "reps_assisted": int(st.session_state.get(set_key("reps_assisted", index), 0)),
        "is_warmup": bool(st.session_state.get(set_key("is_warmup", index), False)),
    }


def get_current_sets():
    return [read_set_from_state(i) for i in range(st.session_state.set_count)]


def collect_header_from_state():
    ensure_category_exercise_state()

    return {
        "workout_date": st.session_state.get(entry_key("workout_date"), date.today()),
        "category": st.session_state.get(entry_key("category"), CATEGORY_PLACEHOLDER),
        "exercise": st.session_state.get(entry_key("exercise"), EXERCISE_PLACEHOLDER),
        "rest_seconds": st.session_state.get(entry_key("rest_seconds"), 90),
        "rating": st.session_state.get(entry_key("rating"), "△"),
        "workout_note": st.session_state.get(entry_key("workout_note"), ""),
    }


def load_form_data(header, sets_data, editing_id=None):
    st.session_state.form_version += 1
    st.session_state.editing_workout_id = editing_id
    st.session_state.set_count = max(len(sets_data), 1)

    st.session_state[entry_key("workout_date")] = header["workout_date"]
    st.session_state[entry_key("category")] = header["category"]
    st.session_state[entry_key("rest_seconds")] = int(header["rest_seconds"])
    st.session_state[entry_key("rating")] = header["rating"]
    st.session_state[entry_key("workout_note")] = header["workout_note"]

    category = header["category"]
    if category in EXERCISE_MASTER:
        exercise_options = EXERCISE_MASTER[category]
        exercise = header["exercise"]
        if exercise not in exercise_options:
            exercise = EXERCISE_PLACEHOLDER
        st.session_state[entry_key("exercise")] = exercise
    else:
        st.session_state[entry_key("category")] = CATEGORY_PLACEHOLDER
        st.session_state[entry_key("exercise")] = EXERCISE_PLACEHOLDER

    normalized_sets = sets_data[:]
    while len(normalized_sets) < st.session_state.set_count:
        normalized_sets.append(default_set())

    for i, s in enumerate(normalized_sets):
        st.session_state[set_key("weight", i)] = float(s["weight"])
        st.session_state[set_key("reps_unassisted", i)] = int(s["reps_unassisted"])
        st.session_state[set_key("reps_assisted", i)] = int(s["reps_assisted"])
        st.session_state[set_key("is_warmup", i)] = bool(s["is_warmup"])


def add_new_set(copy_from_index=None):
    header = collect_header_from_state()
    sets_data = get_current_sets()

    if copy_from_index is None:
        sets_data.append(default_set())
    else:
        copied = dict(sets_data[copy_from_index])
        sets_data.append(copied)

    load_form_data(header, sets_data, st.session_state.editing_workout_id)


def remove_set(index):
    sets_data = get_current_sets()
    if len(sets_data) <= 1:
        return

    header = collect_header_from_state()
    new_sets = [s for i, s in enumerate(sets_data) if i != index]
    load_form_data(header, new_sets, st.session_state.editing_workout_id)


def reset_entry_form(preserve_date=None, preserve_rest=None):
    st.session_state.form_version += 1
    st.session_state.set_count = 1
    st.session_state.editing_workout_id = None

    st.session_state[entry_key("workout_date")] = preserve_date if preserve_date is not None else date.today()
    st.session_state[entry_key("rest_seconds")] = int(preserve_rest) if preserve_rest is not None else 90
    st.session_state[entry_key("category")] = CATEGORY_PLACEHOLDER
    st.session_state[entry_key("exercise")] = EXERCISE_PLACEHOLDER
    st.session_state[entry_key("rating")] = "△"
    st.session_state[entry_key("workout_note")] = ""


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
    }

    sets_data = []
    for row in sets_rows:
        sets_data.append(
            {
                "weight": float(row["weight"]),
                "reps_unassisted": int(row["reps_unassisted"]),
                "reps_assisted": int(row["reps_assisted"]),
                "is_warmup": bool(row["is_warmup"]),
            }
        )

    load_form_data(header, sets_data, editing_id=workout_id)


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


def get_exercise_met(category, exercise):
    if exercise in EXERCISE_METS:
        return EXERCISE_METS[exercise]
    if category in CATEGORY_DEFAULT_MET:
        return CATEGORY_DEFAULT_MET[category]
    return 5.0


def calculate_workout_metrics(workout, sets_rows, body_weight_kg):
    total_load = 0.0
    main_load = 0.0
    total_sets = len(sets_rows)
    main_sets = 0
    total_reps = 0
    main_reps = 0
    active_seconds = 0

    for row in sets_rows:
        reps = int(row["reps_unassisted"]) + int(row["reps_assisted"])
        load = float(row["weight"]) * reps
        is_warmup = bool(row["is_warmup"])

        total_load += load
        total_reps += reps
        active_seconds += reps * 4

        if not is_warmup:
            main_load += load
            main_reps += reps
            main_sets += 1

    rest_intervals = max(total_sets - 1, 0)
    total_seconds = active_seconds + int(workout["rest_seconds"]) * rest_intervals

    met = get_exercise_met(
        workout["category"] or infer_category_from_exercise(workout["exercise"]),
        workout["exercise"],
    )

    if body_weight_kg is not None and body_weight_kg > 0:
        est_kcal = met * body_weight_kg * (total_seconds / 3600)
    else:
        est_kcal = None

    return {
        "total_load": total_load,
        "main_load": main_load,
        "total_sets": total_sets,
        "main_sets": main_sets,
        "total_reps": total_reps,
        "main_reps": main_reps,
        "active_seconds": active_seconds,
        "total_seconds": total_seconds,
        "est_kcal": est_kcal,
        "met": met,
    }


def calculate_daily_summary(entries):
    summary = {
        "total_load": 0.0,
        "main_load": 0.0,
        "total_sets": 0,
        "main_sets": 0,
        "total_reps": 0,
        "main_reps": 0,
        "est_kcal": 0.0,
        "has_kcal": True,
    }

    for entry in entries:
        metrics = entry["metrics"]
        summary["total_load"] += metrics["total_load"]
        summary["main_load"] += metrics["main_load"]
        summary["total_sets"] += metrics["total_sets"]
        summary["main_sets"] += metrics["main_sets"]
        summary["total_reps"] += metrics["total_reps"]
        summary["main_reps"] += metrics["main_reps"]

        if metrics["est_kcal"] is None:
            summary["has_kcal"] = False
        else:
            summary["est_kcal"] += metrics["est_kcal"]

    return summary


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


def render_input_page(user):
    if st.session_state.editing_workout_id is not None:
        st.warning("現在、既存記録を修正中です。")
        if st.button("修正をやめる", key="cancel_edit"):
            reset_entry_form()
            st.rerun()

    st.subheader("入力")

    st.date_input("日付", key=entry_key("workout_date"))

    category_options = [CATEGORY_PLACEHOLDER] + list(EXERCISE_MASTER.keys())
    st.selectbox(
        "カテゴリ",
        category_options,
        key=entry_key("category"),
    )

    selected_category = st.session_state[entry_key("category")]

    if selected_category == CATEGORY_PLACEHOLDER:
        exercise_options = [EXERCISE_PLACEHOLDER]
        st.session_state[entry_key("exercise")] = EXERCISE_PLACEHOLDER
    else:
        exercise_options = [EXERCISE_PLACEHOLDER] + EXERCISE_MASTER[selected_category]
        current_exercise = st.session_state.get(entry_key("exercise"), EXERCISE_PLACEHOLDER)
        if current_exercise not in exercise_options:
            st.session_state[entry_key("exercise")] = EXERCISE_PLACEHOLDER

    st.selectbox(
        "種目",
        exercise_options,
        key=entry_key("exercise"),
    )

    st.number_input(
        "レスト (秒)",
        min_value=0,
        step=5,
        key=entry_key("rest_seconds"),
    )

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

    current_sets = get_current_sets()

    if st.session_state.editing_workout_id is not None:
        with st.form(key=f"edit_form_{st.session_state.form_version}", clear_on_submit=False):
            st.subheader("セット入力")

            for i in range(st.session_state.set_count):
                with st.expander(f"Set {i + 1}", expanded=True):
                    st.checkbox(
                        "ウォームアップ",
                        key=set_key("is_warmup", i),
                    )
                    st.number_input(
                        "重さ (kg)",
                        min_value=0.0,
                        step=2.5,
                        key=set_key("weight", i),
                    )
                    st.number_input(
                        "回数（補助なし）",
                        min_value=0,
                        step=1,
                        key=set_key("reps_unassisted", i),
                    )
                    st.number_input(
                        "回数（補助あり）",
                        min_value=0,
                        step=1,
                        key=set_key("reps_assisted", i),
                    )

            current_sets = get_current_sets()
            best_1rm, best_set = best_estimated_1rm(current_sets)

            if best_1rm is not None and best_set is not None:
                st.info(
                    f'参考: 推定1RM {best_1rm:.1f} kg '
                    f'（{best_set["weight"]} kg × 補助なし {best_set["reps_unassisted"]} 回 / ウォームアップ除外）'
                )
            else:
                st.caption("参考値は、補助なし1〜10回・ウォームアップ以外のセットがあると表示します。")

            body_weight_kg = get_user_body_weight_kg(user)
            if body_weight_kg is None:
                st.caption("参考kcalは、プロフィールで体重を設定すると記録一覧に表示されます。")
            else:
                st.caption(f"参考kcal計算にはプロフィール体重 {body_weight_kg:.1f} kg を使用します。")

            st.selectbox(
                "評価",
                ["〇", "△", "×"],
                key=entry_key("rating"),
            )

            st.text_area(
                "種目メモ",
                key=entry_key("workout_note"),
                placeholder="任意",
            )

            submitted = st.form_submit_button("更新する", type="primary")

        if submitted:
            workout_date = st.session_state[entry_key("workout_date")]
            category = st.session_state[entry_key("category")]
            exercise = st.session_state[entry_key("exercise")]
            rest_seconds = st.session_state[entry_key("rest_seconds")]
            rating = st.session_state[entry_key("rating")]
            workout_note = st.session_state[entry_key("workout_note")]
            sets_data = get_current_sets()

            valid_sets = []
            for s in sets_data:
                if s["weight"] > 0 or s["reps_unassisted"] > 0 or s["reps_assisted"] > 0:
                    valid_sets.append(s)

            if category == CATEGORY_PLACEHOLDER:
                st.error("カテゴリを選択してください。")
            elif exercise == EXERCISE_PLACEHOLDER:
                st.error("種目を選択してください。")
            elif not valid_sets:
                st.error("最低1セットは入力してください。")
            else:
                update_workout(
                    st.session_state.editing_workout_id,
                    workout_date,
                    category,
                    exercise,
                    rest_seconds,
                    rating,
                    workout_note,
                    valid_sets,
                )
                st.session_state.flash_message = "記録を更新しました。"
                reset_entry_form()
                st.session_state.page = "記録一覧"
                st.rerun()

        return

    st.subheader("セット入力")

    for i in range(st.session_state.set_count):
        with st.expander(f"Set {i + 1}", expanded=True):
            st.checkbox(
                "ウォームアップ",
                key=set_key("is_warmup", i),
            )
            st.number_input(
                "重さ (kg)",
                min_value=0.0,
                step=2.5,
                key=set_key("weight", i),
            )
            st.number_input(
                "回数（補助なし）",
                min_value=0,
                step=1,
                key=set_key("reps_unassisted", i),
            )
            st.number_input(
                "回数（補助あり）",
                min_value=0,
                step=1,
                key=set_key("reps_assisted", i),
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button(
                    "コピー追加",
                    key=f"copy_{st.session_state.form_version}_{i}",
                ):
                    add_new_set(copy_from_index=i)
                    st.rerun()
            with c2:
                if st.button(
                    "空で追加",
                    key=f"blank_{st.session_state.form_version}_{i}",
                ):
                    add_new_set(copy_from_index=None)
                    st.rerun()
            with c3:
                if st.button(
                    "このセット削除",
                    key=f"remove_{st.session_state.form_version}_{i}",
                    disabled=(st.session_state.set_count <= 1),
                ):
                    remove_set(i)
                    st.rerun()

    current_sets = get_current_sets()
    best_1rm, best_set = best_estimated_1rm(current_sets)

    if best_1rm is not None and best_set is not None:
        st.info(
            f'参考: 推定1RM {best_1rm:.1f} kg '
            f'（{best_set["weight"]} kg × 補助なし {best_set["reps_unassisted"]} 回 / ウォームアップ除外）'
        )
    else:
        st.caption("参考値は、補助なし1〜10回・ウォームアップ以外のセットがあると表示します。")

    body_weight_kg = get_user_body_weight_kg(user)
    if body_weight_kg is None:
        st.caption("参考kcalは、プロフィールで体重を設定すると記録一覧に表示されます。")
    else:
        st.caption(f"参考kcal計算にはプロフィール体重 {body_weight_kg:.1f} kg を使用します。")

    with st.form(key=f"save_form_{st.session_state.form_version}", clear_on_submit=False):
        st.selectbox(
            "評価",
            ["〇", "△", "×"],
            key=entry_key("rating"),
        )

        st.text_area(
            "種目メモ",
            key=entry_key("workout_note"),
            placeholder="任意",
        )

        submitted = st.form_submit_button("この内容で保存", type="primary")

    if submitted:
        workout_date = st.session_state[entry_key("workout_date")]
        category = st.session_state[entry_key("category")]
        exercise = st.session_state[entry_key("exercise")]
        rest_seconds = st.session_state[entry_key("rest_seconds")]
        rating = st.session_state[entry_key("rating")]
        workout_note = st.session_state[entry_key("workout_note")]
        sets_data = get_current_sets()

        valid_sets = []
        for s in sets_data:
            if s["weight"] > 0 or s["reps_unassisted"] > 0 or s["reps_assisted"] > 0:
                valid_sets.append(s)

        if category == CATEGORY_PLACEHOLDER:
            st.error("カテゴリを選択してください。")
        elif exercise == EXERCISE_PLACEHOLDER:
            st.error("種目を選択してください。")
        elif not valid_sets:
            st.error("最低1セットは入力してください。")
        else:
            save_workout(
                user["id"],
                workout_date,
                category,
                exercise,
                rest_seconds,
                rating,
                workout_note,
                valid_sets,
            )
            st.session_state.flash_message = "記録を保存しました。"
            reset_entry_form(
                preserve_date=workout_date,
                preserve_rest=rest_seconds,
            )
            st.rerun()


def render_records_page(user):
    st.subheader("記録一覧")

    workouts = get_workouts_for_user(user["id"])
    if not workouts:
        st.info("まだ記録がありません。")
        return

    body_weight_kg = get_user_body_weight_kg(user)

    grouped = {}
    for workout in workouts:
        grouped.setdefault(workout["workout_date"], []).append(workout)

    for workout_date, day_workouts in grouped.items():
        entries = []

        for workout in day_workouts:
            sets_rows = get_sets_for_workout(workout["id"])
            metrics = calculate_workout_metrics(workout, sets_rows, body_weight_kg)
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
            kcal_text = "プロフィールで体重を設定すると表示"

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

                if metrics["est_kcal"] is not None:
                    st.write(f"推定消費カロリー（参考）: {metrics['est_kcal']:.0f} kcal")
                else:
                    st.write("推定消費カロリー（参考）: プロフィールで体重を設定すると表示")

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
                        st.session_state.page = "入力"
                        st.rerun()
                with c2:
                    if st.button("削除する", key=f"delete_{workout['id']}"):
                        if st.session_state.editing_workout_id == workout["id"]:
                            reset_entry_form()
                        delete_workout(workout["id"])
                        st.session_state.flash_message = "記録を削除しました。"
                        st.rerun()


def render_profile_page(user):
    st.subheader("プロフィール")

    current_name = user["display_name"] or ""
    current_height = 0.0 if user["height_cm"] is None else float(user["height_cm"])
    current_weight = 0.0 if user["body_weight_kg"] is None else float(user["body_weight_kg"])

    with st.form("profile_form"):
        st.text_input("名前", value=current_name, key="profile_name")
        st.number_input("身長 (cm)", min_value=0.0, step=0.5, value=float(current_height), key="profile_height")
        st.number_input("体重 (kg)", min_value=0.0, step=0.1, value=float(current_weight), key="profile_weight")
        submitted = st.form_submit_button("プロフィールを保存")

        if submitted:
            ok, message = update_user_profile(
                user["id"],
                st.session_state["profile_name"],
                st.session_state["profile_height"],
                st.session_state["profile_weight"],
            )
            if ok:
                st.session_state.current_user = get_user_by_id(user["id"])
                st.session_state.flash_message = message
                st.rerun()
            else:
                st.error(message)

    st.caption("記録一覧の参考kcal計算には、ここで保存した体重を使用します。")
    st.caption("体重が未設定または0の場合、参考kcalは表示されません。")


st.set_page_config(
    page_title=f"筋トレメモ ver.{APP_VERSION}",
    page_icon="🏋️",
    layout="centered",
)

st.markdown(
    """
<style>
.block-container {
    max-width: 760px;
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
@media (max-width: 640px) {
    .block-container {
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
    h1 {
        font-size: 1.6rem;
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
cleanup_expired_sessions()
ensure_app_state()
ensure_form_defaults()

existing_token = cookies.get(SESSION_COOKIE_NAME)

if st.session_state.current_user is None and existing_token:
    remembered_user = get_user_from_session(existing_token)
    if remembered_user:
        st.session_state.current_user = remembered_user
    else:
        try:
            del cookies[SESSION_COOKIE_NAME]
            cookies.save()
        except Exception:
            pass

if st.session_state.current_user is None:
    render_app_title()
    st.write(f"IDとPWでログインして使います。ログイン状態は {SESSION_HOURS} 時間保持します。")

    login_id = st.text_input("ID", key="login_id")
    login_pw = st.text_input("PW", type="password", key="login_pw")

    if st.button("ログイン", key="login_button", type="primary"):
        user = authenticate(login_id, login_pw)
        if user:
            token = create_session(user["id"], hours=SESSION_HOURS)
            cookies[SESSION_COOKIE_NAME] = token
            cookies.save()
            st.session_state.current_user = get_user_by_id(user["id"])
            reset_entry_form()
            st.session_state.flash_message = "ログインしました。"
            st.rerun()
        else:
            st.error("IDまたはPWが違います。")

    st.stop()

user = st.session_state.current_user

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
        st.rerun()

if st.session_state.flash_message:
    st.success(st.session_state.flash_message)
    st.session_state.flash_message = None

st.sidebar.title("メニュー")
page_options = ["入力", "記録一覧", "プロフィール"]
current_index = page_options.index(st.session_state.page) if st.session_state.page in page_options else 0
st.session_state.page = st.sidebar.radio(
    "ページ",
    page_options,
    index=current_index,
)

if st.session_state.page == "入力":
    render_input_page(user)
elif st.session_state.page == "記録一覧":
    render_records_page(user)
else:
    render_profile_page(user)
