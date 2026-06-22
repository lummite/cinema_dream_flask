import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc

# ===============================
# Настройка подключения к MS SQL
# ===============================
CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=DESKTOP-4GLOKAQ\\SQLEXPRESS;'
    'DATABASE=cinema_dream;'
    'Trusted_Connection=yes;'
)


def get_conn():
    return pyodbc.connect(CONN_STR)


# ===============================
# Получение жанров
# ===============================
def get_genres():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM Genres ORDER BY name")
    genres = cur.fetchall()
    cur.close()
    conn.close()
    return genres


# ===============================
# Добавление фильма
# ===============================
def add_movie():
    title = movie_entries['title'].get().strip()
    if not title:
        messagebox.showerror("Ошибка", "Название фильма обязательно!")
        return

    try:
        year = int(movie_entries['year'].get()) if movie_entries['year'].get() else None
        rating = float(movie_entries['rating'].get()) if movie_entries['rating'].get() else None
        duration = int(movie_entries['duration'].get()) if movie_entries['duration'].get() else None
        budget = int(movie_entries['budget'].get()) if movie_entries['budget'].get() else None
        box_office = int(movie_entries['box_office'].get()) if movie_entries['box_office'].get() else None
    except ValueError:
        messagebox.showerror("Ошибка", "Поля с числами должны быть числовыми")
        return

    country = movie_entries['country'].get() or None
    director = movie_entries['director'].get() or None
    actors = movie_entries['actors'].get() or None
    age_limit = movie_entries['age_limit'].get() or None
    cover_image = movie_entries['cover_image'].get() or None
    movie_file = movie_entries['movie_file'].get() or None
    description = movie_entries['description'].get("1.0", tk.END).strip() or None

    genre_ids = [gid for gid, var in movie_genres_vars.items() if var.get() == 1]
    if not genre_ids:
        messagebox.showwarning("Внимание", "Не выбран ни один жанр. Фильм будет добавлен без жанров.")

    try:
        conn = get_conn()
        cur = conn.cursor()

        # Вставка фильма с OUTPUT INSERTED.id
        cur.execute("""
            INSERT INTO Movies
            (title, year, country, rating, duration, director, actors, budget, box_office, age_limit, cover_image, movie_file, description)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, title, year, country, rating, duration, director, actors, budget, box_office, age_limit, cover_image,
                  movie_file, description)

        movie_id = cur.fetchone()[0]

        # Вставка жанров
        for gid in genre_ids:
            cur.execute("INSERT INTO MovieGenres (movie_id, genre_id) VALUES (?, ?)", movie_id, gid)

        conn.commit()
        cur.close()
        conn.close()

        messagebox.showinfo("Успех", f"Фильм '{title}' успешно добавлен!")

        # Очистка полей
        for ent in movie_entries.values():
            if isinstance(ent, tk.Entry):
                ent.delete(0, tk.END)
            elif isinstance(ent, tk.Text):
                ent.delete("1.0", tk.END)
        for var in movie_genres_vars.values():
            var.set(0)

    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при добавлении: {e}")


# ===============================
# Добавление сериала/аниме
# ===============================
def add_series():
    title = series_entries['title'].get().strip()
    if not title:
        messagebox.showerror("Ошибка", "Название сериала/аниме обязательно")
        return

    try:
        year = int(series_entries['year'].get()) if series_entries['year'].get() else None
        rating = float(series_entries['rating'].get()) if series_entries['rating'].get() else None
    except ValueError:
        messagebox.showerror("Ошибка", "Год и рейтинг должны быть числами")
        return

    country = series_entries['country'].get() or None
    director = series_entries['director'].get() or None
    actors = series_entries['actors'].get() or None
    age_limit = series_entries['age_limit'].get() or None
    cover_image = series_entries['cover_image'].get() or None
    description = series_entries['description'].get("1.0", tk.END).strip() or None
    series_type = series_entries['type'].get()

    genre_ids = [gid for gid, var in series_genres_vars.items() if var.get() == 1]
    if not genre_ids:
        messagebox.showwarning("Внимание", "Не выбран ни один жанр. Сериал/Аниме будет добавлен без жанров.")

    try:
        conn = get_conn()
        cur = conn.cursor()

        # Вставка сериала с OUTPUT INSERTED.id
        cur.execute("""
            INSERT INTO Series
            (title, year, country, rating, director, actors, age_limit, cover_image, description, type)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, title, year, country, rating, director, actors, age_limit, cover_image, description, series_type)

        series_id = cur.fetchone()[0]

        # Вставка жанров
        for gid in genre_ids:
            cur.execute("INSERT INTO SeriesGenres (series_id, genre_id) VALUES (?, ?)", series_id, gid)

        # Вставка сезонов и серий
        for season_frame in season_frames:
            s_num = season_frame['season_number'].get()
            s_year = season_frame['season_year'].get()
            if not s_num:
                continue

            cur.execute("""
                INSERT INTO Seasons (series_id, season_number, year)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?)
            """, series_id, int(s_num), int(s_year) if s_year else None)

            season_id = cur.fetchone()[0]

            for ep in season_frame['episodes']:
                ep_num = ep['number'].get()
                ep_title = ep['title'].get()
                ep_duration = ep['duration'].get()
                ep_file = ep['file'].get()
                if not ep_num or not ep_file:
                    continue
                cur.execute("""
                    INSERT INTO Episodes (season_id, episode_number, title, duration, movie_file)
                    VALUES (?, ?, ?, ?, ?)
                """, season_id, int(ep_num), ep_title or None,
                          int(ep_duration) if ep_duration else None, ep_file)

        conn.commit()
        cur.close()
        conn.close()

        messagebox.showinfo("Успех", f"Сериал/Аниме '{title}' успешно добавлен!")

        # Очистка полей
        for ent in series_entries.values():
            if isinstance(ent, tk.Entry):
                ent.delete(0, tk.END)
            elif isinstance(ent, tk.Text):
                ent.delete("1.0", tk.END)
        for var in series_genres_vars.values():
            var.set(0)
        for frame in season_frames:
            frame['frame'].destroy()
        season_frames.clear()

    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при добавлении: {e}")



# ===============================
# GUI
# ===============================
root = tk.Tk()
root.title("Добавление контента")

tabControl = ttk.Notebook(root)
tab_movie = ttk.Frame(tabControl)
tab_series = ttk.Frame(tabControl)
tabControl.add(tab_movie, text='Фильм')
tabControl.add(tab_series, text='Сериал/Аниме')
tabControl.pack(expand=1, fill="both")

# ---------------- Фильм ----------------
movie_entries = {}
fields = [
    ('title', "Название", "Пример: Джентльмены"),
    ('year', "Год", "Пример: 2019"),
    ('country', "Страна", "Пример: США"),
    ('rating', "Рейтинг", "Пример: 8.7"),
    ('duration', "Длительность", "Пример: 113"),
    ('director', "Режиссёр", "Пример: Гай Ричи"),
    ('actors', "Актёры", "Пример: Мэттью Макконахи, Чарли Ханнэм"),
    ('budget', "Бюджет", "Пример: 22000000"),
    ('box_office', "Сборы", "Пример: 115171795"),
    ('age_limit', "Возрастное ограничение", "Пример: 18+"),
    ('cover_image', "Путь к обложке", "Пример: movies/The Gentlemen/cover.webp"),
    ('movie_file', "Путь к видео", "Пример: movies/The Gentlemen/The Gentlemen.mp4")
]

for idx, (key, label_text, example) in enumerate(fields):
    tk.Label(tab_movie, text=label_text).grid(row=idx, column=0, sticky='w')
    ent = tk.Entry(tab_movie, width=50)
    ent.grid(row=idx, column=1, pady=2)
    movie_entries[key] = ent
    tk.Label(tab_movie, text=example, fg="gray").grid(row=idx, column=2, sticky='w')

tk.Label(tab_movie, text="Описание").grid(row=len(fields), column=0, sticky='nw')
txt_desc = tk.Text(tab_movie, width=50, height=4)
txt_desc.grid(row=len(fields), column=1, pady=2)
movie_entries['description'] = txt_desc

# Жанры
genres = get_genres()
tk.Label(tab_movie, text="Жанры").grid(row=len(fields) + 1, column=0, sticky='nw')
movie_genres_vars = {}
frm_genres = tk.Frame(tab_movie)
frm_genres.grid(row=len(fields) + 1, column=1, sticky='w')
for idx, (gid, name) in enumerate(genres):
    var = tk.IntVar()
    chk = tk.Checkbutton(frm_genres, text=name, variable=var)
    chk.grid(row=idx // 4, column=idx % 4, sticky='w', padx=2)
    movie_genres_vars[gid] = var

tk.Button(tab_movie, text="Добавить фильм", bg="#2d89ef", fg="white", command=add_movie).grid(
    row=len(fields) + 2, column=0, columnspan=2, pady=10)

# ---------------- Сериал/Аниме ----------------
series_entries = {}
series_fields = [
    ('title', "Название", "Пример: Игра престолов"),
    ('year', "Год", "Пример: 2011"),
    ('country', "Страна", "Пример: США"),
    ('rating', "Рейтинг", "Пример: 9.0"),
    ('director', "Режиссёр", "Пример: Дэвид Бениофф"),
    ('actors', "Актёры", "Пример: Питер Динклэйдж, Эмилия Кларк"),
    ('age_limit', "Возрастное ограничение", "Пример: 16+"),
    ('cover_image', "Путь к обложке", "Пример: series/GameOfThrones/cover.webp")
]

for idx, (key, label_text, example) in enumerate(series_fields):
    tk.Label(tab_series, text=label_text).grid(row=idx, column=0, sticky='w')
    ent = tk.Entry(tab_series, width=50)
    ent.grid(row=idx, column=1, pady=2)
    series_entries[key] = ent
    tk.Label(tab_series, text=example, fg="gray").grid(row=idx, column=2, sticky='w')

tk.Label(tab_series, text="Описание").grid(row=len(series_fields), column=0, sticky='nw')
txt_desc_series = tk.Text(tab_series, width=50, height=4)
txt_desc_series.grid(row=len(series_fields), column=1, pady=2)
series_entries['description'] = txt_desc_series

# Тип
tk.Label(tab_series, text="Тип").grid(row=len(series_fields) + 1, column=0, sticky='w')
type_var = tk.StringVar(value="Сериал")
tk.OptionMenu(tab_series, type_var, "Сериал", "Аниме").grid(row=len(series_fields) + 1, column=1, sticky='w')
series_entries['type'] = type_var

# Жанры
tk.Label(tab_series, text="Жанры").grid(row=len(series_fields) + 2, column=0, sticky='nw')
series_genres_vars = {}
frm_genres_series = tk.Frame(tab_series)
frm_genres_series.grid(row=len(series_fields) + 2, column=1, sticky='w')
for idx, (gid, name) in enumerate(genres):
    var = tk.IntVar()
    chk = tk.Checkbutton(frm_genres_series, text=name, variable=var)
    chk.grid(row=idx // 4, column=idx % 4, sticky='w', padx=2)
    series_genres_vars[gid] = var

# ---------------- Сезоны с прокруткой ----------------
tk.Label(tab_series, text="Сезоны").grid(row=len(series_fields) + 3, column=0, sticky='nw')

# Фрейм для кнопки + Canvas
season_outer_frame = tk.Frame(tab_series)
season_outer_frame.grid(row=len(series_fields) + 3, column=1, sticky='nsew')

# Кнопка добавления сезона сверху Canvas
btn_add_season = tk.Button(season_outer_frame, text="Добавить сезон", command=lambda: add_season(), bg="#2d89ef", fg="white")
btn_add_season.pack(side="top", pady=5, anchor="w")

# Canvas для прокрутки
canvas = tk.Canvas(season_outer_frame, width=800, height=250)
scrollbar = tk.Scrollbar(season_outer_frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

season_container = scrollable_frame
season_frames = []

# ---------------- Функции добавления сезона и серии ----------------
def add_season():
    frame = tk.Frame(season_container, bd=1, relief='sunken', pady=5, padx=5)
    frame.pack(fill='x', pady=5)

    season_number = tk.Entry(frame, width=5)
    season_year = tk.Entry(frame, width=7)

    tk.Label(frame, text="Сезон №").grid(row=0, column=0)
    season_number.grid(row=0, column=1, padx=2)
    tk.Label(frame, text="Год").grid(row=0, column=2)
    season_year.grid(row=0, column=3, padx=2)

    episodes = []

    def add_episode():
        ep_frame = tk.Frame(frame)
        ep_frame.grid(sticky='w', pady=2)

        ep_number = tk.Entry(ep_frame, width=5)
        ep_title = tk.Entry(ep_frame, width=20)
        ep_duration = tk.Entry(ep_frame, width=5)
        ep_file = tk.Entry(ep_frame, width=30)

        tk.Label(ep_frame, text="№").grid(row=0, column=0)
        ep_number.grid(row=0, column=1)
        tk.Label(ep_frame, text="Название").grid(row=0, column=2)
        ep_title.grid(row=0, column=3)
        tk.Label(ep_frame, text="Длительность").grid(row=0, column=4)
        ep_duration.grid(row=0, column=5)
        tk.Label(ep_frame, text="Файл").grid(row=0, column=6)
        ep_file.grid(row=0, column=7)

        episodes.append({
            'number': ep_number,
            'title': ep_title,
            'duration': ep_duration,
            'file': ep_file
        })
        canvas.yview_moveto(1.0)  # прокрутка вниз после добавления

    # Кнопка добавления серии внутри блока сезона
    tk.Button(frame, text="Добавить серию", command=add_episode, bg="#2d89ef", fg="white").grid(row=1, column=0, columnspan=4, pady=5)

    season_frames.append({
        'frame': frame,
        'season_number': season_number,
        'season_year': season_year,
        'episodes': episodes
    })
    canvas.yview_moveto(1.0)



# Кнопка добавления сезона СВНЕХУ Canvas
tk.Button(tab_series, text="Добавить сезон", command=add_season).grid(row=len(series_fields) + 4, column=1, sticky='w', pady=5)

# Кнопка добавления сериала/аниме СНИЗУ Canvas
btn_add_series = tk.Button(tab_series, text="Добавить сериал/аниме", command=add_series, bg="#28a745", fg="white")
btn_add_series.grid(row=len(series_fields) + 5, column=1, sticky='w', pady=10)


root.mainloop()
