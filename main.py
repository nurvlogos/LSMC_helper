import sqlite3
import tkinter as tk
from tkinter import messagebox, font, ttk, colorchooser
from PIL import Image, ImageTk
import os
import json
import threading
import keyboard

POINTS_FILE = "custom_points.json"
LABELS_FILE = "custom_labels.json"
COLORS_FILE = "custom_colors.json"
HOTKEYS_FILE = "hotkeys.json"

DEFAULT_BUTTONS = [
    'patrol', 'room', 'neodmirin', 'ksilotab', 'reanimation', 'call_accept', 'event', 'surgery',
    'inspection', 'supply', 'gmp', 'exams', 'self_interview', 'assist_interview', 'accepted_person', 'exam_interview'
]
DEFAULT_POINTS = {
    'patrol': 10, 'room': 10, 'neodmirin': 3, 'ksilotab': 7,
    'reanimation': 4, 'call_accept': 4, 'event': 10, 'surgery': 15,
    'inspection': 15, 'supply': 10, 'gmp': 15, 'exams': 7,
    'self_interview': 10, 'assist_interview': 5, 'accepted_person': 5, 'exam_interview': 5
}
DEFAULT_LABELS = {
    'patrol': "Патрулирование", 'room': "Палата", 'neodmirin': "Неодмирин", 'ksilotab': "Ксилотаба",
    'reanimation': "Реанимация", 'call_accept': "Принятый вызов", 'event': "Мероприятие", 'surgery': "Проведение операции",
    'inspection': "Санитарная инспекция", 'supply': "Поставка", 'gmp': "ГМП", 'exams': "Экзамены",
    'self_interview': "Сам провел собеседование", 'assist_interview': "Помог провести собеседование",
    'accepted_person': "Принятый человек", 'exam_interview': "Экзамен (собеседование)"
}
DEFAULT_COLORS = {
    'patrol': "#2563EB", 'room': "#22C55E", 'neodmirin': "#F59E42", 'ksilotab': "#EF4444",
    'reanimation': "#2563EB", 'call_accept': "#22C55E", 'event': "#F59E42", 'surgery': "#EF4444",
    'inspection': "#2563EB", 'supply': "#22C55E", 'gmp': "#F59E42", 'exams': "#EF4444",
    'self_interview': "#2563EB", 'assist_interview': "#22C55E", 'accepted_person': "#F59E42", 'exam_interview': "#EF4444"
}

MAX_BUTTONS = 20

def load_json(fname, default):
    if os.path.exists(fname):
        with open(fname, "r", encoding="utf-8") as f:
            return json.load(f)
    return dict(default)

def save_json(fname, data):
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_hotkeys():
    return load_json(HOTKEYS_FILE, {})

def save_hotkeys(hotkeys):
    save_json(HOTKEYS_FILE, hotkeys)

def get_all_buttons(labels):
    return list(labels.keys())

conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS stats (
    user_id TEXT PRIMARY KEY
)
''')
for b in DEFAULT_BUTTONS:
    try:
        c.execute(f"ALTER TABLE stats ADD COLUMN {b} INTEGER DEFAULT 0")
    except:
        pass
conn.commit()

class LSMCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LSMC Статистика By Arvi")
        self.root.geometry("760x850")
        self.root.configure(bg="#2E3440")

        self.user_id = "default_user"
        c.execute("SELECT * FROM stats WHERE user_id = ?", (self.user_id,))
        if not c.fetchone():
            c.execute("INSERT INTO stats(user_id) VALUES (?)", (self.user_id,))
            conn.commit()

        self.dark_mode = True
        self.hotkeys = load_hotkeys()
        self.load_custom()
        self.build_menu()
        self.setup_main_panel()
        self.setup_global_hotkeys()

    def load_custom(self):
        self.POINTS = load_json(POINTS_FILE, DEFAULT_POINTS)
        self.LABELS = load_json(LABELS_FILE, DEFAULT_LABELS)
        self.COLORS = load_json(COLORS_FILE, DEFAULT_COLORS)
        # Add missing defaults
        for k in DEFAULT_POINTS:
            if k not in self.POINTS: self.POINTS[k] = DEFAULT_POINTS[k]
            if k not in self.LABELS: self.LABELS[k] = DEFAULT_LABELS[k]
            if k not in self.COLORS: self.COLORS[k] = DEFAULT_COLORS[k]

    def save_custom(self):
        save_json(POINTS_FILE, self.POINTS)
        save_json(LABELS_FILE, self.LABELS)
        save_json(COLORS_FILE, self.COLORS)

    def build_menu(self):
        menubar = tk.Menu(self.root)
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Сброс", command=self.reset_stats)
        view_menu.add_command(label="Сменить тему", command=self.toggle_theme)
        view_menu.add_separator()
        view_menu.add_command(label="Открыть настройки", command=self.open_settings_window)
        menubar.add_cascade(label="Настройки", menu=view_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Помощь", command=self.show_help)
        menubar.add_cascade(label="Помощь", menu=help_menu)
        self.root.config(menu=menubar)

    def open_settings_window(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Настройки")
        settings_win.geometry("540x640")
        settings_win.configure(bg="#ECEFF4" if not self.dark_mode else "#2E3440")
        settings_win.resizable(False, False)

        theme_label = tk.Label(settings_win, text="Темная тема:",
                               bg=settings_win["bg"],
                               fg="#2E3440" if not self.dark_mode else "#ECEFF4",
                               font=("Segoe UI", 12))
        theme_label.pack(pady=(18, 5))

        theme_button = tk.Button(settings_win, text="Сменить тему",
                                 command=lambda: [self.toggle_theme(), settings_win.destroy()],
                                 bg="#4C566A", fg="#ECEFF4", relief="flat",
                                 font=("Segoe UI", 10, "bold"))
        theme_button.pack(pady=5)

        reset_button = tk.Button(settings_win, text="Сбросить статистику",
                                 command=lambda: [self.reset_stats(), settings_win.destroy()],
                                 bg="#BF616A", fg="#FFFFFF", relief="flat",
                                 font=("Segoe UI", 10, "bold"))
        reset_button.pack(pady=(20, 5))

        hotkey_label = tk.Label(settings_win, text="Настройка горячих клавиш:\nПример: ctrl+1, alt+e, shift+alt+2",
                                bg=settings_win["bg"],
                                fg="#2E3440" if not self.dark_mode else "#ECEFF4",
                                font=("Segoe UI", 12, "bold"))
        hotkey_label.pack(pady=(18, 3))

        # SCROLLABLE frame for hotkeys
        hotkey_canvas = tk.Canvas(settings_win, borderwidth=0, highlightthickness=0,
                                  height=200, bg=settings_win["bg"])
        scrollbar = tk.Scrollbar(settings_win, orient="vertical", command=hotkey_canvas.yview)
        hotkey_frame = tk.Frame(hotkey_canvas, bg=settings_win["bg"])
        hotkey_canvas.create_window((0, 0), window=hotkey_frame, anchor='nw')
        hotkey_canvas.configure(yscrollcommand=scrollbar.set)
        hotkey_canvas.pack(side="left", fill="both", expand=True, padx=(8,0), pady=2)
        scrollbar.pack(side="right", fill="y", pady=2)

        entries = {}
        row = 0
        for key, label in self.LABELS.items():
            l = tk.Label(hotkey_frame, text=label, width=22,
                         bg=hotkey_frame["bg"],
                         fg="#2E3440" if not self.dark_mode else "#ECEFF4",
                         anchor="e", font=("Segoe UI", 10))
            l.grid(row=row, column=0, sticky="e", padx=2, pady=2)
            e = tk.Entry(hotkey_frame, width=28, font=("Segoe UI", 10))
            e.insert(0, self.hotkeys.get(key, ""))
            e.grid(row=row, column=1, sticky="w", padx=2, pady=2)
            entries[key] = e
            row += 1

        hotkey_frame.update_idletasks()
        hotkey_canvas.config(scrollregion=hotkey_canvas.bbox("all"))

        def on_mousewheel(event):
            hotkey_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        hotkey_canvas.bind_all("<MouseWheel>", on_mousewheel)

        def save_hotkey_settings():
            new_hotkeys = {}
            for k, v in entries.items():
                hotk = v.get().strip()
                if hotk:
                    if not all(c.isalnum() or c in "+-" for c in hotk.replace(' ', '')):
                        messagebox.showerror("Xatolik",
                                             f"Hotkey noto'g'ri formatda: {hotk}\nTo'g'ri misol: ctrl+1, alt+e")
                        return
                    new_hotkeys[k] = hotk
            self.remove_global_hotkeys()
            self.hotkeys = new_hotkeys
            save_hotkeys(self.hotkeys)
            self.setup_global_hotkeys()
            messagebox.showinfo("Горячие клавиши", "Горячие клавиши сохранены!")
            settings_win.destroy()

        save_btn = tk.Button(settings_win, text="Сохранить ", command=save_hotkey_settings,
                             bg="#2563EB", fg="#ECEFF4", relief="flat", font=("Segoe UI", 10, "bold"))
        save_btn.pack(pady=(16, 8))

        admin_btn = tk.Button(settings_win, text="Админ панель", command=self.open_admin_panel,
                              bg="#4f46e5", fg="#eceff4", relief="flat", font=("Segoe UI", 10, "bold"))
        admin_btn.pack(pady=(10,12))

        close_button = tk.Button(settings_win, text="Закрыть", command=settings_win.destroy,
                                 bg="#D8DEE9", fg="#2E3440", relief="flat", font=("Segoe UI", 10))
        close_button.pack(pady=6)



    def open_admin_panel(self):
        admin_win = tk.Toplevel(self.root)
        admin_win.title("Admin панель: Кнопки")
        admin_win.geometry("840x640")
        admin_win.configure(bg="#2E3440" if self.dark_mode else "#eceff4")
        admin_win.resizable(True, True)

        style = ttk.Style(admin_win)
        if self.dark_mode:
            style.theme_use('clam')
            style.configure("TLabel", background="#2E3440", foreground="#eceff4")
            style.configure("TEntry", fieldbackground="#434c5e", foreground="#eceff4")
            style.configure("TButton", background="#2563EB", foreground="#eceff4")
        else:
            style.theme_use('clam')
            style.configure("TLabel", background="#eceff4", foreground="#222")
            style.configure("TEntry", fieldbackground="#fff", foreground="#222")
            style.configure("TButton", background="#2563EB", foreground="#fff")

        # Canvas + scrollbar
        admin_frame = ttk.Frame(admin_win, padding=12)
        admin_frame.pack(fill="both", expand=True)
        admin_canvas = tk.Canvas(admin_frame, borderwidth=0, highlightthickness=0, bg=admin_win["bg"], height=400)
        admin_canvas.pack(side="left", fill="both", expand=True)
        admin_scrollbar = ttk.Scrollbar(admin_frame, orient="vertical", command=admin_canvas.yview)
        admin_scrollbar.pack(side="right", fill="y")
        admin_canvas.configure(yscrollcommand=admin_scrollbar.set)

        frm = ttk.Frame(admin_canvas)
        admin_canvas.create_window((0, 0), window=frm, anchor='nw')

        button_keys = list(self.LABELS.keys())
        entries = {}

        def choose_color(e, key):
            color = colorchooser.askcolor(title="Выберите цвет", color=self.COLORS.get(key, "#2563EB"))[1]
            if color:
                e.delete(0, tk.END)
                e.insert(0, color)

        def delete_button(key):
            if key in DEFAULT_BUTTONS:
                messagebox.showerror("Ошибка", "Стандартные кнопки удалить нельзя!")
                return
            if messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить этот кнопку?"):
                self.LABELS.pop(key, None)
                self.POINTS.pop(key, None)
                self.COLORS.pop(key, None)
                self.hotkeys.pop(key, None)
                try:
                    c.execute(f"ALTER TABLE stats DROP COLUMN {key}")
                except Exception:
                    pass
                conn.commit()
                self.save_custom()
                save_hotkeys(self.hotkeys)
                self.setup_main_panel()
                messagebox.showinfo("OK", "Кнопка полностью удалена!")
                admin_win.destroy()

        # Table header
        header_font = ("Segoe UI", 10, "bold")
        headers = ["Ключ", "Имя", "Баллы", "Цвет", "", ""]
        for j, h in enumerate(headers):
            ttk.Label(frm, text=h, font=header_font).grid(row=0, column=j, padx=4, pady=3, sticky="nsew")
        for i, key in enumerate(button_keys):
            row = i + 1
            ttk.Label(frm, text=f"{key}", width=17, anchor="e").grid(row=row, column=0, padx=4, pady=4, sticky="w")
            name_e = ttk.Entry(frm, width=20)
            name_e.insert(0, self.LABELS[key])
            name_e.grid(row=row, column=1, padx=4, sticky="ew")
            point_e = ttk.Entry(frm, width=8)
            point_e.insert(0, str(self.POINTS[key]))
            point_e.grid(row=row, column=2, padx=4)
            color_e = ttk.Entry(frm, width=11)
            color_e.insert(0, self.COLORS[key])
            color_e.grid(row=row, column=3, padx=4)
            color_btn = ttk.Button(frm, text="🎨", command=lambda e=color_e, k=key: choose_color(e, k))
            color_btn.grid(row=row, column=4, padx=2)
            if key not in DEFAULT_BUTTONS:
                del_btn = ttk.Button(frm, text="Удалить", command=lambda k=key: delete_button(k),
                                     style="Danger.TButton")
                del_btn.grid(row=row, column=5, padx=2)
            entries[key] = (name_e, point_e, color_e)

        frm.update_idletasks()
        admin_canvas.config(scrollregion=admin_canvas.bbox("all"))

        def on_mousewheel(event):
            admin_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        admin_canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Add new button
        sep = ttk.Separator(admin_win, orient="horizontal")
        sep.pack(fill="x", pady=8)
        add_lbl = ttk.Label(admin_win, text="Добавить новую кнопку (Max 4):", font=("Segoe UI", 12, "bold"))
        add_lbl.pack(pady=(8, 2))
        add_frm = ttk.Frame(admin_win, padding=8)
        add_frm.pack()
        new_name = ttk.Entry(add_frm, width=20)
        new_name.grid(row=0, column=0, padx=4)
        new_point = ttk.Entry(add_frm, width=8)
        new_point.grid(row=0, column=1, padx=4)
        new_color = ttk.Entry(add_frm, width=11)
        new_color.insert(0, "#22C55E")
        new_color.grid(row=0, column=2, padx=4)

        def pick_new_color():
            color = colorchooser.askcolor(title="Выберите цвет", color=new_color.get())[1]
            if color:
                new_color.delete(0, tk.END)
                new_color.insert(0, color)

        ttk.Button(add_frm, text="🎨", command=pick_new_color).grid(row=0, column=3, padx=2)

        def add_new_button():
            custom_count = len([k for k in self.LABELS if k not in DEFAULT_BUTTONS])
            if len(self.LABELS) >= MAX_BUTTONS:
                messagebox.showerror("Ошибка", f"Максимум {MAX_BUTTONS} кнопок разрешено!")
                return
            if custom_count >= 4:
                messagebox.showerror("Ошибка", "Максимум 4 пользовательских кнопки!")
                return
            label = new_name.get().strip()
            try:
                point = int(new_point.get().strip())
            except:
                messagebox.showerror("Ошибка", "Балл должен быть целым числом!"); return
            color = new_color.get().strip()
            if not label or not color:
                messagebox.showerror("Ошибка", "Заполните все поля!")
                return
            key = "btn_" + str(abs(hash(label + color)))[-8:]
            if key in self.LABELS:
                messagebox.showerror("Ошибка", "Кнопка с таким названием уже существует!")
                return
            self.LABELS[key] = label
            self.POINTS[key] = point
            self.COLORS[key] = color
            try:
                c.execute(f"ALTER TABLE stats ADD COLUMN {key} INTEGER DEFAULT 0")
                conn.commit()
            except:
                pass
            self.save_custom()
            self.setup_main_panel()
            messagebox.showinfo("OK", "Добавлена новая кнопка!")
            admin_win.destroy()

        ttk.Button(add_frm, text="Добавить", command=add_new_button).grid(row=0, column=4, padx=6)

        # Save button
        def save_admin():
            for key in entries:
                name, point, color = entries[key]
                self.LABELS[key] = name.get().strip() or "Без названия"
                try:
                    self.POINTS[key] = int(point.get().strip())
                except:
                    self.POINTS[key] = 1
                self.COLORS[key] = color.get().strip() or "#2563EB"
            self.save_custom()
            self.setup_main_panel()
            messagebox.showinfo("OK", "Изменения сохранены.")
            admin_win.destroy()

        save_btn = ttk.Button(admin_win, text="Сохранить", command=save_admin)
        save_btn.pack(pady=14)

    # ... Qolgan metodlar o'zgarmaydi (setup_main_panel, update_stats, increment_stat, reset_stats, toggle_theme, show_help)
# ... (main va boshqa o'zgarmas qismi)

    def setup_global_hotkeys(self):
        self.remove_global_hotkeys()
        self.global_hotkey_handlers = []
        for key, hot in self.hotkeys.items():
            if hot.strip():
                def make_callback(k):
                    return lambda: self.increment_stat_threadsafe(k)
                handler = keyboard.add_hotkey(hot, make_callback(key))
                self.global_hotkey_handlers.append(handler)

    def remove_global_hotkeys(self):
        if hasattr(self, 'global_hotkey_handlers'):
            for h in self.global_hotkey_handlers:
                try:
                    keyboard.remove_hotkey(h)
                except Exception:
                    pass
            self.global_hotkey_handlers = []

    def increment_stat_threadsafe(self, field):
        def _update():
            self.increment_stat(field)
        self.root.after(0, _update)

    def setup_main_panel(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        if not self.dark_mode:
            bg_color = "#F7FAFC"
            fg_color = "#2D3748"
            accent_color = "#3182CE"
            text_bg = "#FFFFFF"
            text_fg = fg_color
        else:
            bg_color = "#1E293B"
            fg_color = "#E2E8F0"
            accent_color = "#2563EB"
            text_bg = "#334155"
            text_fg = fg_color

        title_font = font.Font(family="Segoe UI", size=20, weight="bold")
        label_font = ("Segoe UI", 14, "bold")
        text_font = ("Consolas", 12)

        title_label = tk.Label(self.root, text="LSMC Статистика Программа", bg=bg_color, fg=fg_color, font=title_font)
        title_label.pack(pady=(16, 4))

        self.total_label = tk.Label(self.root, text="Общий балл: 0", bg=bg_color, fg=fg_color, font=label_font)
        self.total_label.pack(pady=2)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=550, mode="determinate",
                                        style="blue.Horizontal.TProgressbar")
        self.progress.pack(pady=8)

        self.text = tk.Text(self.root, height=8, width=72,
                            bg=text_bg, fg=text_fg,
                            font=text_font, bd=2, relief="groove")
        self.text.pack(pady=(0, 8), padx=10)
        self.text.configure(state=tk.DISABLED)

        button_canvas = tk.Canvas(self.root, bg=bg_color, highlightthickness=0, height=310)
        button_canvas.pack(fill="x", padx=12)
        btn_scrollbar = tk.Scrollbar(self.root, orient="vertical", command=button_canvas.yview)
        btn_scrollbar.place(relx=1.0, rely=0.41, anchor="ne", height=310)
        button_canvas.configure(yscrollcommand=btn_scrollbar.set)
        btn_frame = tk.Frame(button_canvas, bg=bg_color)
        button_canvas.create_window((0, 0), window=btn_frame, anchor='nw')

        buttons_per_row = 4
        for i, key in enumerate(self.LABELS):
            color = self.COLORS.get(key, "#2563EB")
            btn = tk.Button(btn_frame, text=f"{self.LABELS[key]}", width=22,
                            bg=color, fg="#FFFFFF",
                            font=("Segoe UI", 10, "bold"),
                            relief="flat", command=lambda k=key: self.increment_stat(k))
            btn.grid(row=i // buttons_per_row, column=i % buttons_per_row, padx=8, pady=7, sticky="ew")

        btn_frame.update_idletasks()
        button_canvas.config(scrollregion=button_canvas.bbox("all"))

        def on_mousewheel(event):
            button_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        button_canvas.bind_all("<MouseWheel>", on_mousewheel)

        btn_row_frame = tk.Frame(self.root, bg=bg_color)
        btn_row_frame.pack(pady=(10, 10))

        reset_btn = tk.Button(btn_row_frame, text="Сброс", bg="#EF4444", fg="#FFFFFF",
                              font=("Segoe UI", 12, "bold"), relief="flat",
                              command=self.reset_stats)
        reset_btn.pack(side="left", padx=8)

        settings_btn = tk.Button(btn_row_frame, text="Настройки", bg=accent_color, fg="#FFFFFF",
                                 font=("Segoe UI", 12, "bold"), relief="flat",
                                 command=self.open_settings_window)
        settings_btn.pack(side="left", padx=8)

        self.credit_label = tk.Label(self.root, text="By A.Magnate", bg=bg_color, fg=fg_color,
                                     font=("Segoe UI", 10, "italic"))
        self.credit_label.place(relx=1.0, rely=1.0, anchor="se", x=-15, y=-12)

        menu_button = tk.Button(self.root, text="≡", font=("Segoe UI", 22, "bold"),
                                bg=bg_color, fg=fg_color, bd=0, activebackground=bg_color,
                                activeforeground=fg_color, cursor="hand2")
        menu_button.place(x=10, y=10)

        popup_menu = tk.Menu(self.root, tearoff=0)
        popup_menu.add_command(label="Сброс", command=self.reset_stats)
        popup_menu.add_command(label="Сменить тему", command=self.toggle_theme)
        popup_menu.add_separator()
        popup_menu.add_command(label="Помощь", command=self.show_help)

        def show_popup(event):
            popup_menu.tk_popup(event.x_root, event.y_root)
        menu_button.bind("<Button-1>", show_popup)
        self.update_stats()

    def update_stats(self):
        c.execute("SELECT * FROM stats WHERE user_id = ?", (self.user_id,))
        data = c.fetchone()
        if not data:
            return
        text = ""
        total = 0
        columns = [desc[0] for desc in c.description]
        for key in self.LABELS:
            try:
                idx = columns.index(key)
                count = data[idx]
            except Exception:
                count = 0
            point = self.POINTS.get(key, 1)
            label = self.LABELS[key]
            text += f"{label}: {count}    ({count * point} балл)\n"
            total += count * point

        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, text)
        self.text.configure(state=tk.DISABLED)
        self.total_label.configure(text=f"Общий балл: {total}")
        self.progress["value"] = total % 100

    def increment_stat(self, field):
        try:
            c.execute(f"UPDATE stats SET {field} = {field} + 1 WHERE user_id = ?", (self.user_id,))
        except Exception:
            c.execute(f"ALTER TABLE stats ADD COLUMN {field} INTEGER DEFAULT 0")
            c.execute(f"UPDATE stats SET {field} = {field} + 1 WHERE user_id = ?", (self.user_id,))
        conn.commit()
        self.update_stats()

    def reset_stats(self):
        if messagebox.askyesno("Подтверждение", "Вы действительно хотите сбросить статистику?"):
            c.execute("DELETE FROM stats WHERE user_id = ?", (self.user_id,))
            c.execute("INSERT INTO stats(user_id) VALUES (?)", (self.user_id,))
            conn.commit()
            self.update_stats()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.setup_main_panel()
        self.setup_global_hotkeys()

    def show_help(self):
        messagebox.showinfo("Помощь", "Программа для отслеживания статистики LSMC.\n\n"
                                     "Нажмите на кнопки или используйте горячие клавиши для добавления баллов.\n"
                                     "Горячие клавиши работают даже когда программа в фоне!\n"
                                     "Используйте меню для смены темы и сброса данных.\n"
                                     "В настройках можно задать свои горячие клавиши для быстрого ввода.\n\n"
                                     "Мой Дискорд : arvibek \n"
                                     "Telegram : t.me/nurvlogos")

if __name__ == "__main__":
    root = tk.Tk()
    app = LSMCApp(root)
    root.mainloop()