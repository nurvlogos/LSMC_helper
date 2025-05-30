import sqlite3
import customtkinter as ctk
from tkinter import colorchooser, messagebox
import os
import json
import keyboard

POINTS_FILE = "custom_points.json"
LABELS_FILE = "custom_labels.json"
COLORS_FILE = "custom_colors.json"
HOTKEYS_FILE = "hotkeys.json"
STATUTE_FILE = "ustav.txt"

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

def ensure_statute_file():
    statute_text = """Глава I. Общие положения​
(сюда вставьте полный текст устава, как раньше)
"""
    if not os.path.exists(STATUTE_FILE):
        with open(STATUTE_FILE, "w", encoding="utf-8") as f:
            f.write(statute_text)

def load_statute():
    ensure_statute_file()
    with open(STATUTE_FILE, "r", encoding="utf-8") as f:
        return f.read()

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
        self.root.geometry("750x750")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.user_id = "default_user"
        c.execute("SELECT * FROM stats WHERE user_id = ?", (self.user_id,))
        if not c.fetchone():
            c.execute("INSERT INTO stats(user_id) VALUES (?)", (self.user_id,))
            conn.commit()
        self.dark_mode = True
        self.hotkeys = load_hotkeys()
        self.load_custom()
        self.setup_main_panel()
        self.setup_global_hotkeys()

    def clear_window(self):
        # Remove all widgets from the root window
        for widget in self.root.winfo_children():
            widget.destroy()

    def load_custom(self):
        self.POINTS = load_json(POINTS_FILE, DEFAULT_POINTS)
        self.LABELS = load_json(LABELS_FILE, DEFAULT_LABELS)
        self.COLORS = load_json(COLORS_FILE, DEFAULT_COLORS)
        for k in DEFAULT_POINTS:
            if k not in self.POINTS: self.POINTS[k] = DEFAULT_POINTS[k]
            if k not in self.LABELS: self.LABELS[k] = DEFAULT_LABELS[k]
            if k not in self.COLORS: self.COLORS[k] = DEFAULT_COLORS[k]

    def save_custom(self):
        save_json(POINTS_FILE, self.POINTS)
        save_json(LABELS_FILE, self.LABELS)
        save_json(COLORS_FILE, self.COLORS)

    def animate_btn(self, btn, color):
        original = btn.cget("fg_color")
        btn.configure(fg_color="#f3f708")
        btn.after(120, lambda: btn.configure(fg_color=color))

    def show_side_menu(self):
        if getattr(self, 'side_menu', None) and self.side_menu.winfo_exists():
            return
        self.side_menu = ctk.CTkFrame(self.root, width=180, fg_color="#23272f", corner_radius=0)
        self.side_menu.place(x=0, y=0, relheight=1.0)
        ctk.CTkLabel(self.side_menu, text="Меню", font=("Segoe UI", 18, "bold")).pack(pady=(22,12))
        ctk.CTkButton(
            self.side_menu, text="Устав", width=150, height=38,
            fg_color="#2563EB", font=("Segoe UI", 14, "bold"),
            command=self.show_statute_panel
        ).pack(pady=8)
        ctk.CTkButton(
            self.side_menu, text="Отыгровки", width=150, height=38,
            fg_color="#F59E42", font=("Segoe UI", 14, "bold"),
            command=lambda: self.show_coming_soon_panel("Отыгровки")
        ).pack(pady=8)
        ctk.CTkButton(
            self.side_menu, text="Помощь", width=150, height=38,
            fg_color="#22C55E", font=("Segoe UI", 14, "bold"),
            command=self.open_help_window
        ).pack(pady=8)
        ctk.CTkButton(
            self.side_menu, text="Asosiy menu", width=150, height=38, fg_color="#334155",
            font=("Segoe UI", 13, "bold"), command=self.setup_main_panel
        ).pack(pady=8)
        ctk.CTkButton(
            self.side_menu, text="✖", width=48, height=32, fg_color="#dc2626", text_color="#fff",
            font=("Segoe UI", 18, "bold"), command=self.hide_side_menu, corner_radius=18
        ).pack(pady=(25,8))

    def hide_side_menu(self):
        if getattr(self, 'side_menu', None):
            self.side_menu.destroy()
            self.side_menu = None

    def show_statute_panel(self):
        self.clear_window()
        menu_icon = ctk.CTkButton(
            self.root, text="≡", width=40, height=40, font=("Segoe UI", 30, "bold"),
            fg_color="#23272f", hover_color="#23272f", text_color="#2563EB",
            command=self.show_side_menu, corner_radius=16
        )
        menu_icon.place(x=9, y=9)
        panel = ctk.CTkFrame(self.root, width=520, height=640, fg_color="#23272f", corner_radius=16)
        panel.place(x=115, y=40)
        ctk.CTkLabel(panel, text="Устав LSMC", font=("Segoe UI", 20, "bold")).pack(pady=(10,2))
        text_box = ctk.CTkTextbox(panel, width=495, height=510, font=("Segoe UI", 12), fg_color="#23272f", wrap="word")
        text_box.pack(pady=(2,8), padx=2)
        text_box.insert("0.0", load_statute())
        text_box.configure(state="disabled")
        ctk.CTkButton(
            panel, text="Asosiy menu", width=180, height=32, fg_color="#2563EB", text_color="#fff",
            font=("Segoe UI", 14, "bold"), command=self.setup_main_panel
        ).pack(pady=(5,12))

    def show_coming_soon_panel(self, title):
        self.clear_window()
        menu_icon = ctk.CTkButton(
            self.root, text="≡", width=40, height=40, font=("Segoe UI", 30, "bold"),
            fg_color="#23272f", hover_color="#23272f", text_color="#2563EB",
            command=self.show_side_menu, corner_radius=16
        )
        menu_icon.place(x=9, y=9)
        panel = ctk.CTkFrame(self.root, width=350, height=200, fg_color="#23272f", corner_radius=16)
        panel.place(x=200, y=150)
        ctk.CTkLabel(panel, text=title, font=("Segoe UI", 18, "bold")).pack(pady=(18,8))
        ctk.CTkLabel(panel, text="Comming soon...", font=("Segoe UI", 15, "italic")).pack(pady=(0,10))
        ctk.CTkButton(
            panel, text="Asosiy menu", width=120, height=30, fg_color="#2563EB", text_color="#fff",
            font=("Segoe UI", 13, "bold"), command=self.setup_main_panel
        ).pack(pady=(6,4))

    def open_help_window(self):
        win = ctk.CTkToplevel(self.root)
        win.title("Помощь / Help")
        win.geometry("500x470")
        win.resizable(False, False)
        ctk.CTkLabel(win, text="Помощь / Help", font=("Segoe UI", 20, "bold")).pack(pady=(16, 6))
        help_text = (
            "Программа статистики LSMC.\n\n"
"- Вы добавляете баллы с каждым нажатием кнопки или с помощью горячей клавиши.\n"
"- Вы можете увидеть общий результат через окно статистики.\n"
"- Измените кнопку или выберите цвет через панель администратора.\n"
"- Горячие клавиши можно использовать из окна «Настройки».\n"
"По дополнительным вопросам:\n"
"Discord: arvibek\n"
"Telegram: t.me/nurvlogos"
        )
        box = ctk.CTkTextbox(win, width=440, height=300, font=("Segoe UI", 13), fg_color="#23272f")
        box.insert("0.0", help_text)
        box.configure(state="disabled")
        box.pack(pady=(0,10), padx=10)
        ctk.CTkButton(win, text="Yopish", fg_color="#2563EB", width=120, command=win.destroy).pack(pady=10)

    def open_admin_panel(self):
        admin_win = ctk.CTkToplevel(self.root)
        admin_win.title("Admin панель: Кнопки")
        admin_win.geometry("900x700")
        admin_win.resizable(True, True)

        frame = ctk.CTkFrame(admin_win, fg_color="#23272f")
        frame.pack(fill="both", expand=True, padx=10, pady=12)

        scrolled = ctk.CTkScrollableFrame(frame, width=860, height=410, fg_color="#2e323a")
        scrolled.pack(pady=(4, 16), padx=4, fill="x")

        button_keys = list(self.LABELS.keys())
        entries = {}

        for i, key in enumerate(button_keys):
            ctk.CTkLabel(scrolled, text=f"{key}", width=110, anchor="e").grid(row=i, column=0, padx=6, pady=6)
            name_e = ctk.CTkEntry(scrolled, width=195, height=36)
            name_e.insert(0, self.LABELS[key])
            name_e.grid(row=i, column=1, padx=6)
            point_e = ctk.CTkEntry(scrolled, width=80, height=36)
            point_e.insert(0, str(self.POINTS[key]))
            point_e.grid(row=i, column=2, padx=6)
            color_e = ctk.CTkEntry(scrolled, width=100, height=36)
            color_e.insert(0, self.COLORS[key])
            color_e.grid(row=i, column=3, padx=6)

            def choose_color(e=color_e, k=key):
                color = colorchooser.askcolor(title="Выберите цвет", color=self.COLORS.get(k, "#2563EB"))[1]
                if color:
                    e.delete(0, 'end')
                    e.insert(0, color)
            ctk.CTkButton(scrolled, text="🎨", width=44, height=36, fg_color="#2563EB",
                          command=choose_color).grid(row=i, column=4, padx=4)
            if key not in DEFAULT_BUTTONS:
                ctk.CTkButton(scrolled, text="Удалить", fg_color="#dc2626", width=70, height=36,
                              command=lambda k=key: delete_button(k)).grid(row=i, column=5, padx=6)
            entries[key] = (name_e, point_e, color_e)

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

        ctk.CTkLabel(frame, text="Добавить новую кнопку (Max 4):", font=("Segoe UI", 18, "bold")).pack(pady=(8, 2))
        add_frm = ctk.CTkFrame(frame, fg_color="#23272f")
        add_frm.pack(pady=(0, 16))
        new_name = ctk.CTkEntry(add_frm, width=180, height=36)
        new_name.grid(row=0, column=0, padx=6)
        new_point = ctk.CTkEntry(add_frm, width=60, height=36)
        new_point.grid(row=0, column=1, padx=6)
        new_color = ctk.CTkEntry(add_frm, width=100, height=36)
        new_color.insert(0, "#22C55E")
        new_color.grid(row=0, column=2, padx=6)
        def pick_new_color():
            color = colorchooser.askcolor(title="Выберите цвет", color=new_color.get())[1]
            if color:
                new_color.delete(0, 'end')
                new_color.insert(0, color)
        ctk.CTkButton(add_frm, text="🎨", width=44, height=36, fg_color="#2563EB", command=pick_new_color).grid(row=0, column=3, padx=4)

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
                messagebox.showerror("Ошибка", "Балл должен быть целым числом!")
                return
            color = new_color.get().strip()
            if not label or not color:
                messagebox.showerror("Ошибка", "Заполните все поля!")
                return
            key = "btn_" + str(abs(hash(label+color)))[-8:]
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

        ctk.CTkButton(add_frm, text="Добавить", fg_color="#2563EB", width=110, height=36, command=add_new_button).grid(row=0, column=4, padx=7)

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

        ctk.CTkButton(frame, text="Сохранить", fg_color="#22C55E", font=("Segoe UI", 18, "bold"),
                      width=180, height=44, command=save_admin).pack(pady=14)

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
        self.clear_window()
        menu_icon = ctk.CTkButton(
            self.root, text="≡", width=40, height=40, font=("Segoe UI", 30, "bold"),
            fg_color="#23272f", hover_color="#23272f", text_color="#2563EB",
            command=self.show_side_menu, corner_radius=16
        )
        menu_icon.place(x=9, y=9)
        title_label = ctk.CTkLabel(self.root, text="LSMC Статистика Программа", font=("Segoe UI", 20, "bold"))
        title_label.pack(pady=(10, 4))
        self.total_label = ctk.CTkLabel(self.root, text="Общий балл: 0", font=("Segoe UI", 14, "bold"))
        self.total_label.pack(pady=2)
        self.progress = ctk.CTkProgressBar(self.root, width=520, height=12, progress_color="#2563EB")
        self.progress.set(0)
        self.progress.pack(pady=8)
        self.text = ctk.CTkTextbox(self.root, width=520, height=80, font=("Consolas", 11), fg_color="#23272f")
        self.text.pack(pady=(2, 10))
        self.text.configure(state="disabled")
        button_frame = ctk.CTkScrollableFrame(self.root, width=700, height=280, fg_color="#23272f")
        button_frame.pack(padx=4, pady=(0, 12))
        buttons_per_row = 4
        for i, key in enumerate(self.LABELS):
            color = self.COLORS.get(key, "#2563EB")
            hotkey_txt = self.hotkeys.get(key, "")
            btn_text = f"{self.LABELS[key]}"
            if hotkey_txt:
                btn_text += f"\n[{hotkey_txt}]"
            btn = ctk.CTkButton(
                button_frame,
                text=btn_text,
                fg_color=color,
                width=155,
                height=40,
                font=("Segoe UI", 11, "bold"),
                command=lambda k=key, c=color: [self.increment_stat(k), self.animate_btn(self.button_refs[k], c)]
            )
            btn.grid(row=i // buttons_per_row, column=i % buttons_per_row, padx=6, pady=6, sticky="ew")
            btn.bind("<Enter>", lambda e, b=btn: b.configure(cursor="hand2", hover_color="#1e293b"))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(fg_color=c))
            if not hasattr(self, 'button_refs'):
                self.button_refs = {}
            self.button_refs[key] = btn
        btn_row_frame = ctk.CTkFrame(self.root, fg_color="#23272f")
        btn_row_frame.pack(pady=(4, 8))
        reset_btn = ctk.CTkButton(btn_row_frame, text="Сброс", fg_color="#EF4444", hover_color="#c72f27",
                                  font=("Segoe UI", 12, "bold"), width=100, height=30,
                                  command=self.reset_stats)
        reset_btn.pack(side="left", padx=7)
        settings_btn = ctk.CTkButton(btn_row_frame, text="Настройки", fg_color="#2563EB", hover_color="#174bd6",
                                     font=("Segoe UI", 12, "bold"), width=100, height=30,
                                     command=self.open_settings_window)
        settings_btn.pack(side="left", padx=7)
        help_btn = ctk.CTkButton(btn_row_frame, text="Помощь", fg_color="#22C55E", width=100, height=30,
                                 command=self.open_help_window)
        help_btn.pack(side="left", padx=7)
        admin_btn = ctk.CTkButton(btn_row_frame, text="Админ панель", fg_color="#4f46e5", width=100, height=30,
                                  command=self.open_admin_panel)
        admin_btn.pack(side="left", padx=7)
        self.credit_label = ctk.CTkLabel(self.root, text="By A.Magnate", font=("Segoe UI", 10, "italic"))
        self.credit_label.pack(anchor="se", padx=10, pady=2)
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
        self.text.configure(state="normal")
        self.text.delete("0.0", "end")
        self.text.insert("end", text)
        self.text.configure(state="disabled")
        self.total_label.configure(text=f"Общий балл: {total}")
        self.progress.set((total % 100) / 100 if total > 0 else 0)

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

    def open_settings_window(self):
        settings_win = ctk.CTkToplevel(self.root)
        settings_win.title("Настройки")
        settings_win.geometry("510x670")
        settings_win.resizable(False, False)
        ctk.CTkLabel(settings_win, text="Темная тема:", font=("Segoe UI", 16)).pack(pady=(18, 5))

        def theme_toggle():
            self.dark_mode = not self.dark_mode
            ctk.set_appearance_mode("dark" if self.dark_mode else "light")
            self.setup_main_panel()
            settings_win.destroy()

        ctk.CTkButton(settings_win, text="Сменить тему", fg_color="#4C566A", width=180, command=theme_toggle).pack(pady=6)
        ctk.CTkButton(settings_win, text="Сбросить статистику", fg_color="#BF616A", width=180,
                      command=lambda: [self.reset_stats(), settings_win.destroy()]).pack(pady=(12, 8))
        ctk.CTkLabel(settings_win, text="Настройка горячих клавиш:\nПример: ctrl+1, alt+e, shift+alt+2", font=("Segoe UI", 13, "bold")).pack(pady=(20, 8))

        hotkey_scrolled = ctk.CTkScrollableFrame(settings_win, width=470, height=230)
        hotkey_scrolled.pack(pady=8)
        entries = {}
        for i, (key, label) in enumerate(self.LABELS.items()):
            ctk.CTkLabel(hotkey_scrolled, text=label, width=155, anchor="e").grid(row=i, column=0, padx=4, pady=4)
            e = ctk.CTkEntry(hotkey_scrolled, width=200)
            e.insert(0, self.hotkeys.get(key, ""))
            e.grid(row=i, column=1, padx=4)
            entries[key] = e

        def save_hotkey_settings():
            new_hotkeys = {}
            for k, v in entries.items():
                hotk = v.get().strip()
                if hotk:
                    if not all(c.isalnum() or c in "+-" for c in hotk.replace(' ', '')):
                        messagebox.showerror("Xatolik", f"Hotkey noto'g'ri formatda: {hotk}\nTo'g'ri misol: ctrl+1, alt+e")
                        return
                    new_hotkeys[k] = hotk
            self.remove_global_hotkeys()
            self.hotkeys = new_hotkeys
            save_hotkeys(self.hotkeys)
            self.setup_global_hotkeys()
            messagebox.showinfo("Горячие клавиши", "Горячие клавиши сохранены!")
            settings_win.destroy()

        ctk.CTkButton(settings_win, text="Сохранить", fg_color="#2563EB", width=140, command=save_hotkey_settings).pack(pady=(14, 5))
        ctk.CTkButton(settings_win, text="Закрыть", fg_color="#D8DEE9", text_color="#2E3440", width=140, command=settings_win.destroy).pack(pady=7)

    def show_help(self):
        self.open_help_window()

if __name__ == "__main__":
    ensure_statute_file()
    root = ctk.CTk()
    app = LSMCApp(root)
    root.mainloop()