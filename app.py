import sqlite3

DB_NAME = "photostudio.db"

# Статусы в соответствии с дизайном панели "Кадр"
STATUS_NEW = "Новый"
STATUS_PENDING = "Ожидание"
STATUS_CONFIRMED = "Подтвержден"


def authenticate(login: str, password: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, full_name FROM clients WHERE login = ? AND password_hash = ?",
        (login, password)
    )
    row = cur.fetchone()
    conn.close()
    return {"id": row[0], "full_name": row[1]} if row else None


def get_services():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, name, price_per_hour FROM services")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_photographers():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, specialization FROM photographers")
    rows = cur.fetchall()
    conn.close()
    return rows


def find_slot(photographer_id: int, date: str, time: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, is_busy FROM slots WHERE photographer_id = ? AND date = ? AND time = ?",
        (photographer_id, date, time)
    )
    row = cur.fetchone()
    conn.close()
    return row


def calculate_total(service_id: int, hours: int) -> float:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT price_per_hour FROM services WHERE id = ?", (service_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise ValueError("Услуга не найдена")
    return round(row[0] * hours, 2)


def validate_hours(hours) -> bool:
    try:
        h = int(hours)
    except (TypeError, ValueError):
        return False
    # ДЕФЕКТ 2: по требованиям максимум 8 часов, здесь допускается 9
    return 0 < h <= 9


def create_order(client_id, service_id, photographer_id, date, time, hours, payment_method):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    slot = find_slot(photographer_id, date, time)
    if not slot:
        conn.close()
        return {"ok": False, "message": "Слот не найден в расписании фотографа."}
    slot_id, is_busy = slot
    if is_busy:
        conn.close()
        return {"ok": False, "message": "Выбранное время уже занято. Выберите другой слот."}

    try:
        total = calculate_total(service_id, int(hours))
    except ValueError as e:
        conn.close()
        return {"ok": False, "message": str(e)}

    cur.execute(
        """INSERT INTO orders
           (client_id, service_id, photographer_id, date, time, hours, total, status, payment_method)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (client_id, service_id, photographer_id, date, time, int(hours), total, STATUS_NEW, payment_method)
    )
    order_id = cur.lastrowid
    cur.execute("UPDATE slots SET is_busy = 1 WHERE id = ?", (slot_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "order_id": order_id, "total": total, "status": STATUS_NEW}


def pay_order(order_id: int, payment_method: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, total, status FROM orders WHERE id = ?", (order_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"ok": False, "message": "Заказ не найден."}

    if payment_method == "card_declined":
        # ДЕФЕКТ 1: неточный текст сообщения при отказе оплаты
        conn.close()
        return {"ok": False, "message": "Ошибка оплаты"}

    # Смена статуса: Ожидание -> Подтвержден
    cur.execute("UPDATE orders SET status = ? WHERE id = ?", (STATUS_PENDING, order_id))
    cur.execute("UPDATE orders SET status = ? WHERE id = ?", (STATUS_CONFIRMED, order_id))
    conn.commit()
    conn.close()
    return {"ok": True, "status": STATUS_CONFIRMED, "total": row[1]}


def notify_photographer(order_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT photographer_id FROM orders WHERE id = ?", (order_id,))
    ph_id = cur.fetchone()[0]
    cur.execute("SELECT full_name FROM photographers WHERE id = ?", (ph_id,))
    ph_name = cur.fetchone()[0]
    text = f"Новая съёмка по заказу №{order_id}"
    cur.execute(
        "INSERT INTO notifications (order_id, recipient, text) VALUES (?, ?, ?)",
        (order_id, ph_name, text)
    )
    conn.commit()
    conn.close()
    return text


def format_total(total: float) -> str:
    # ДЕФЕКТ 3: сумма во второстепенном элементе (уведомлении) отображается без копеек
    return f"{int(round(total))} ₽"


def get_all_orders():
    """Функция для наполнения экрана 'Заявки' (таблица)"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, c.full_name, s.name, o.date, o.time, o.status, o.total
        FROM orders o
        JOIN clients c ON o.client_id = c.id
        JOIN services s ON o.service_id = s.id
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def client_flow(login, password, service_id, photographer_id, date, time, hours, payment_method):
    print("=" * 60)
    user = authenticate(login, password)
    if not user:
        print("Ошибка: неверный логин или пароль.")
        return

    print(f"Клиент: {user['full_name']}")

    if not validate_hours(hours):
        print("Ошибка: некорректная длительность съёмки.")
        return

    order = create_order(
        user["id"], service_id, photographer_id, date, time, hours, payment_method
    )
    if not order["ok"]:
        print("Ошибка:", order["message"])
        return

    print(f"Заявка №{order['order_id']} создана. Статус: {order['status']}")
    print(f"Сумма: {format_total(order['total'])}")

    pay = pay_order(order["order_id"], payment_method)
    if not pay["ok"]:
        print("Оплата не прошла:", pay["message"])
        return

    print(f"Оплата успешна. Статус заявки: {pay['status']}")
    text = notify_photographer(order["order_id"])
    print("Уведомление фотографу:", text)
    print(f"Сумма в квитанции: {order['total']:.2f} ₽")


if __name__ == "__main__":
    print("Доступные услуги:", get_services())
    print("Фотографы:", get_photographers())
    # Тест 1: Успешное создание
    client_flow("client", "12345", 1, 1, "2026-11-18", "10:00", 2, "card")
    print("\nВсе заявки в БД (для таблицы экрана 'Заявки'):")
    for row in get_all_orders():
        print(row)