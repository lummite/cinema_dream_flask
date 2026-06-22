import pyodbc

# ---------------- Подключение к базе (глобальное) ----------------
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=DESKTOP-4GLOKAQ\\SQLEXPRESS;'
    'DATABASE=cinema_dream;'
    'Trusted_Connection=yes;'
)

# ---------------- Вспомогательная функция ----------------
def row_to_dict(cursor, row):
    return {column[0]: row[i] for i, column in enumerate(cursor.description)}

# ---------------- Получение случайных фильмов ----------------
def get_random_movies(limit=8):
    cursor = conn.cursor()
    cursor.execute(f"SELECT TOP ({limit}) id, title, cover_image FROM Movies ORDER BY NEWID()")
    return [row_to_dict(cursor, row) for row in cursor.fetchall()]

# ---------------- Получение случайных сериалов/аниме ----------------
def get_random_series(limit=8, media_type="Сериал"):
    cursor = conn.cursor()
    cursor.execute(f"SELECT TOP ({limit}) id, title, cover_image FROM Series WHERE type=? ORDER BY NEWID()", media_type)
    return [row_to_dict(cursor, row) for row in cursor.fetchall()]

# ---------------- Получить все фильмы ----------------
def get_all_movies():
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, cover_image, year, rating FROM Movies ORDER BY title")
    return [row_to_dict(cursor, row) for row in cursor.fetchall()]

# ---------------- Получить все сериалы ----------------
def get_all_series():
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, cover_image, year, rating FROM Series WHERE type='Сериал' ORDER BY title")
    return [row_to_dict(cursor, row) for row in cursor.fetchall()]

# ---------------- Получить все аниме ----------------
def get_all_anime():
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, cover_image, year, rating FROM Series WHERE type='Аниме' ORDER BY title")
    return [row_to_dict(cursor, row) for row in cursor.fetchall()]

# ---------------- Получить жанры фильма ----------------
def get_movie_genres(movie_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.name
        FROM MovieGenres mg
        JOIN Genres g ON mg.genre_id = g.id
        WHERE mg.movie_id = ?
    """, movie_id)
    return [row[0] for row in cursor.fetchall()]

# ---------------- Получить жанры сериала/аниме ----------------
def get_series_genres(series_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.name
        FROM SeriesGenres sg
        JOIN Genres g ON sg.genre_id = g.id
        WHERE sg.series_id = ?
    """, series_id)
    return [row[0] for row in cursor.fetchall()]

# ---------------- Получить фильм по ID ----------------
def get_movie_by_id(movie_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Movies WHERE id = ?", movie_id)
    row = cursor.fetchone()
    if not row:
        return None
    return row_to_dict(cursor, row)

# ---------------- Получить сериал/аниме по ID ----------------
def get_series_by_id(series_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Series WHERE id = ?", series_id)
    row = cursor.fetchone()
    if not row:
        return None
    return row_to_dict(cursor, row)

# ---------------- Получить все эпизоды сериала ----------------
def get_episodes_by_series_id(series_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM Episodes
        WHERE season_id IN (
            SELECT id FROM Seasons WHERE series_id = ?
        )
        ORDER BY season_id ASC, episode_number ASC
    """, series_id)
    rows = cursor.fetchall()
    return [row_to_dict(cursor, row) for row in rows]

# ---------------- Общая функция фильтрации ----------------
def get_movies_filtered(year=None, rating=None, sort=None, genres=None):
    cursor = conn.cursor()
    query = """
        SELECT DISTINCT m.id, m.title, m.cover_image, m.year, m.rating
        FROM Movies m
        LEFT JOIN MovieGenres mg ON m.id = mg.movie_id
        LEFT JOIN Genres g ON mg.genre_id = g.id
        WHERE 1=1
    """
    params = []

    if year:
        query += " AND m.year = ?"
        params.append(year)

    if rating:
        query += " AND m.rating >= ?"
        params.append(rating)

    if genres:
        placeholders = ','.join('?' for _ in genres)
        query += f" AND g.name IN ({placeholders})"
        params.extend(genres)

    if sort:
        if sort == "year-new":
            query += " ORDER BY m.year DESC"
        elif sort == "year-old":
            query += " ORDER BY m.year ASC"
        elif sort == "alpha-asc":
            query += " ORDER BY m.title ASC"
        elif sort == "alpha-desc":
            query += " ORDER BY m.title DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [row_to_dict(cursor, row) for row in rows]

def get_series_filtered(year=None, rating=None, sort=None, genres=None):
    return get_series_anime_filtered("Сериал", year, rating, sort, genres)

def get_anime_filtered(year=None, rating=None, sort=None, genres=None):
    return get_series_anime_filtered("Аниме", year, rating, sort, genres)

def get_series_anime_filtered(media_type, year=None, rating=None, sort=None, genres=None):
    cursor = conn.cursor()
    query = """
        SELECT DISTINCT s.id, s.title, s.cover_image, s.year, s.rating
        FROM Series s
        LEFT JOIN SeriesGenres sg ON s.id = sg.series_id
        LEFT JOIN Genres g ON sg.genre_id = g.id
        WHERE s.type = ?
    """
    params = [media_type]

    if year:
        query += " AND s.year = ?"
        params.append(year)

    if rating:
        query += " AND s.rating >= ?"
        params.append(rating)

    if genres:
        placeholders = ','.join('?' for _ in genres)
        query += f" AND g.name IN ({placeholders})"
        params.extend(genres)

    if sort:
        if sort == "year-new":
            query += " ORDER BY s.year DESC"
        elif sort == "year-old":
            query += " ORDER BY s.year ASC"
        elif sort == "alpha-asc":
            query += " ORDER BY s.title ASC"
        elif sort == "alpha-desc":
            query += " ORDER BY s.title DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [row_to_dict(cursor, row) for row in rows]
