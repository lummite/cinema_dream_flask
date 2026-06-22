from flask import Flask, render_template, send_from_directory, request, jsonify
import db
import os

app = Flask(__name__)

MEDIA_FOLDER = os.path.join(os.getcwd(), "media")

# ===== Главная страница =====
@app.route('/')
def index():
    movies = db.get_random_movies(8)
    series = db.get_random_series(8, media_type="Сериал")
    anime = db.get_random_series(8, media_type="Аниме")
    return render_template('index.html', movies=movies, series=series, anime=anime)

# ===== Обложки =====
@app.route('/covers/<path:filename>')
def cover(filename):
    return send_from_directory(MEDIA_FOLDER, filename)

# ===== Универсальный маршрут для видео =====
@app.route('/media/<path:filepath>')
def media_files(filepath):
    return send_from_directory(MEDIA_FOLDER, filepath)

# ===== Страница категорий =====
@app.route('/content')
def content():
    category = request.args.get('category', 'movie')
    if category == 'movie':
        title = "Фильмы"
        items = db.get_all_movies()
    elif category == 'series':
        title = "Сериалы"
        items = db.get_all_series()
    elif category == 'anime':
        title = "Аниме"
        items = db.get_all_anime()
    else:
        title = "Категория"
        items = []

    return render_template('content.html', title=title, items=items, category=category)

# ===== Плеер =====
@app.route('/player/<content_type>/<int:item_id>')
def player(content_type, item_id):
    if content_type == 'movie':
        item = db.get_movie_by_id(item_id)
        genres = db.get_movie_genres(item_id)
        if not item:
            return "Элемент не найден", 404
        video_file = item.get('movie_file')
    elif content_type in ['series', 'anime']:
        item = db.get_series_by_id(item_id)
        genres = db.get_series_genres(item_id)
        if not item:
            return "Элемент не найден", 404
        episodes = db.get_episodes_by_series_id(item_id)
        if not episodes:
            return "Эпизоды не найдены", 404
        video_file = episodes[0]['movie_file']  # только первая серия)
    else:
        return "Элемент не найден", 404

    title = item.get('title', 'Плеер')
    return render_template(
        'player.html',
        item=item,
        type=content_type,
        title=title,
        genres=genres,
        video_file=video_file
    )

# ===== API поиск =====
@app.route('/api/search')
def search_api():
    query = request.args.get('query', '').strip().lower()
    if not query:
        return jsonify([])

    results = []

    for m in db.get_all_movies():
        if query in m['title'].lower():
            results.append({'id': m['id'], 'title': m['title'], 'type': 'movie'})
    for s in db.get_all_series():
        if query in s['title'].lower():
            results.append({'id': s['id'], 'title': s['title'], 'type': 'series'})
    for a in db.get_all_anime():
        if query in a['title'].lower():
            results.append({'id': a['id'], 'title': a['title'], 'type': 'anime'})

    return jsonify(results)

# ===== API фильтры и сортировка =====
@app.route('/api/filter')
def filter_api():
    category = request.args.get('category', 'movie')
    year = request.args.get('year')
    rating = request.args.get('rating')
    sort = request.args.get('sort')
    genres = request.args.getlist('genres[]')  # несколько жанров

    # Преобразуем числовые значения
    year = int(year) if year else None
    rating = float(rating) if rating else None

    if category == 'movie':
        items = db.get_movies_filtered(year=year, genres=genres, rating=rating, sort=sort)
    elif category == 'series':
        items = db.get_series_filtered(year=year, genres=genres, rating=rating, sort=sort)
    elif category == 'anime':
        items = db.get_anime_filtered(year=year, genres=genres, rating=rating, sort=sort)
    else:
        items = []

    return jsonify(items)

# ===== Получить все жанры для фильтров =====
@app.route('/api/genres')
def genres_api():
    category = request.args.get('category', 'movie')
    if category == 'movie':
        table = "MovieGenres"
        join_table = "Movies"
        id_col = "movie_id"
    else:
        table = "SeriesGenres"
        join_table = "Series"
        id_col = "series_id"

    cursor = db.conn.cursor()
    cursor.execute(f"""
        SELECT DISTINCT g.name
        FROM Genres g
        JOIN {table} mg ON g.id = mg.genre_id
        JOIN {join_table} m ON m.id = mg.{id_col}
    """)
    rows = cursor.fetchall()
    genres = [r[0] for r in rows]
    return jsonify(genres)


if __name__ == '__main__':
    app.run(debug=True)
