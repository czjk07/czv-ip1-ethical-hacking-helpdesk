PRIORITIES = ("Low", "Medium", "High")
STATUSES = ("Open", "In Progress", "Closed")


def create_user(db, username, email, password_hash, role="client"):
    cur = db.execute(
        "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (username, email, password_hash, role),
    )
    db.commit()
    return get_user(db, cur.lastrowid)


def get_user(db, user_id):
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_username(db, username):
    return db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()


def update_user_credentials(db, user_id, password_hash, role):
    db.execute(
        "UPDATE users SET password_hash = ?, role = ? WHERE id = ?",
        (password_hash, role, user_id),
    )
    db.commit()


def create_ticket(db, user_id, title, description, priority, attachment=None):
    cur = db.execute(
        "INSERT INTO tickets (user_id, title, description, priority, attachment)"
        " VALUES (?, ?, ?, ?, ?)",
        (user_id, title, description, priority, attachment),
    )
    db.commit()
    return cur.lastrowid


def set_ticket_attachment(db, ticket_id, attachment):
    db.execute(
        "UPDATE tickets SET attachment = ? WHERE id = ?", (attachment, ticket_id)
    )
    db.commit()


def get_ticket(db, ticket_id):
    return db.execute(
        "SELECT t.*, u.username AS owner_username FROM tickets t"
        " JOIN users u ON u.id = t.user_id WHERE t.id = ?",
        (ticket_id,),
    ).fetchone()


def list_tickets_by_user(db, user_id):
    return db.execute(
        "SELECT * FROM tickets WHERE user_id = ? ORDER BY created_at DESC, id DESC",
        (user_id,),
    ).fetchall()


def list_all_tickets(db):
    return db.execute(
        "SELECT t.*, u.username AS owner_username FROM tickets t"
        " JOIN users u ON u.id = t.user_id ORDER BY t.created_at DESC, t.id DESC"
    ).fetchall()


def search_tickets(db, query, user_id=None):
    pattern = (
        "%"
        + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        + "%"
    )
    sql = (
        "SELECT t.*, u.username AS owner_username FROM tickets t"
        " JOIN users u ON u.id = t.user_id"
        " WHERE (t.title LIKE ? ESCAPE '\\' OR t.description LIKE ? ESCAPE '\\')"
    )
    params = [pattern, pattern]
    if user_id is not None:
        sql += " AND t.user_id = ?"
        params.append(user_id)
    sql += " ORDER BY t.created_at DESC, t.id DESC"
    return db.execute(sql, params).fetchall()


def update_ticket_status(db, ticket_id, status):
    db.execute(
        "UPDATE tickets SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (status, ticket_id),
    )
    db.commit()


def add_comment(db, ticket_id, user_id, body):
    cur = db.execute(
        "INSERT INTO comments (ticket_id, user_id, body) VALUES (?, ?, ?)",
        (ticket_id, user_id, body),
    )
    db.commit()
    return cur.lastrowid


def list_comments(db, ticket_id):
    return db.execute(
        "SELECT c.*, u.username, u.role FROM comments c"
        " JOIN users u ON u.id = c.user_id WHERE c.ticket_id = ?"
        " ORDER BY c.created_at ASC, c.id ASC",
        (ticket_id,),
    ).fetchall()


def find_ticket_by_attachment(db, filename):
    return db.execute(
        "SELECT * FROM tickets WHERE attachment = ?", (filename,)
    ).fetchone()
