import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

DB_NAME = "photostudio.db"

def load_orders():
    for i in tree.get_children():
        tree.delete(i)
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, c.full_name, s.name, o.date, o.status, o.total
        FROM orders o
        JOIN clients c ON o.client_id = c.id
        JOIN services s ON o.service_id = s.id
    """)
    rows = cur.fetchall()
    conn.close()
    
    for row in rows:
        tree.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], f"{row[5]:.2f} ₽"))

def open_add_window():
    win = tk.Toplevel(root)
    win.title("Новая заявка")
    win.geometry("400x350")
    win.grab_set()

    tk.Label(win, text="Оформление новой заявки", font=("Arial", 14, "bold")).pack(pady=10)

    tk.Label(win, text="Услуга:").pack(anchor="w", padx=20)
    service_var = tk.StringVar()
    services = ["Портретная съёмка", "Семейная съёмка", "Коммерческая съёмка"]
    service_combo = ttk.Combobox(win, textvariable=service_var, values=services, state="readonly")
    service_combo.current(0)
    service_combo.pack(fill="x", padx=20, pady=5)

    tk.Label(win, text="Дата (ГГГГ-ММ-ДД):").pack(anchor="w", padx=20)
    date_entry = tk.Entry(win)
    date_entry.insert(0, "2026-12-01")
    date_entry.pack(fill="x", padx=20, pady=5)

    tk.Label(win, text="Количество часов (целое число):").pack(anchor="w", padx=20)
    hours_entry = tk.Entry(win)
    hours_entry.insert(0, "2")
    hours_entry.pack(fill="x", padx=20, pady=5)

    tk.Label(win, text="Статус:").pack(anchor="w", padx=20)
    status_var = tk.StringVar()
    status_combo = ttk.Combobox(win, textvariable=status_var, values=["Новый", "Ожидание", "Подтвержден"], state="readonly")
    status_combo.current(0)
    status_combo.pack(fill="x", padx=20, pady=5)

    def save_order():
        service_name = service_var.get()
        date_val = date_entry.get()
        status_val = status_var.get()
        
        try:
            hours_val = int(hours_entry.get())
            if hours_val <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество часов (больше 0)!")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id, price_per_hour FROM services WHERE name = ?", (service_name,))
        service_data = cur.fetchone()
        
        if not service_data:
            messagebox.showerror("Ошибка", "Услуга не найдена в БД!")
            conn.close()
            return

        service_id = service_data[0]
        total = service_data[1] * hours_val

        cur.execute("""
            INSERT INTO orders (client_id, service_id, photographer_id, date, time, hours, total, status, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, service_id, 1, date_val, '12:00', hours_val, total, status_val, 'card'))
        
        conn.commit()
        conn.close()

        load_orders()
        messagebox.showinfo("Успех", f"Заявка на сумму {total} ₽ успешно создана!")
        win.destroy()

    tk.Button(win, text="Сохранить заявку", bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), command=save_order).pack(pady=20, fill="x", padx=20)

root = tk.Tk()
root.title("ИС «Фотостудия» - Панель управления")
root.geometry("1000x600")
root.configure(bg="#f4f5f7")

sidebar = tk.Frame(root, bg="#2c3e50", width=200)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

tk.Label(sidebar, text="Кадр", bg="#2c3e50", fg="white", font=("Arial", 20, "bold")).pack(pady=20)
tk.Button(sidebar, text="Дашборд", bg="#2c3e50", fg="white", bd=0, font=("Arial", 12)).pack(fill="x", pady=5)
tk.Button(sidebar, text="Заявки", bg="#34495e", fg="white", bd=0, font=("Arial", 12, "bold")).pack(fill="x", pady=5)
tk.Button(sidebar, text="Расписание", bg="#2c3e50", fg="white", bd=0, font=("Arial", 12)).pack(fill="x", pady=5)
tk.Button(sidebar, text="Клиенты", bg="#2c3e50", fg="white", bd=0, font=("Arial", 12)).pack(fill="x", pady=5)

main_frame = tk.Frame(root, bg="#f4f5f7")
main_frame.pack(side="right", fill="both", expand=True)

header_frame = tk.Frame(main_frame, bg="#f4f5f7")
header_frame.pack(fill="x", padx=20, pady=20)

tk.Label(header_frame, text="Все заявки", bg="#f4f5f7", font=("Arial", 18, "bold")).pack(side="left")
tk.Button(header_frame, text="+ Добавить заявку", bg="#3498db", fg="white", font=("Arial", 10), command=open_add_window).pack(side="right")

style = ttk.Style()
style.configure("Treeview", font=("Arial", 10), rowheight=25)
style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

tree = ttk.Treeview(main_frame, columns=("id", "client", "service", "date", "status", "total"), show="headings")
tree.heading("id", text="ID")
tree.heading("client", text="Клиент")
tree.heading("service", text="Услуга")
tree.heading("date", text="Дата")
tree.heading("status", text="Статус")
tree.heading("total", text="Сумма")

tree.column("id", width=50)
tree.column("client", width=200)
tree.column("service", width=200)
tree.column("date", width=100)
tree.column("status", width=150)
tree.column("total", width=100)

tree.pack(fill="both", expand=True, padx=20, pady=10)

load_orders()

root.mainloop()