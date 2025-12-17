import sqlite3


def init_db(db_path: str = 'users.db') -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            height REAL,
            weight REAL,
            activity_level TEXT,
            gender TEXT,
            years_experience INTEGER,
            brm REAL,
            goal TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            week_number INTEGER,
            training_days TEXT,
            current_day INTEGER,
            completed_days INTEGER,
            session_active BOOLEAN DEFAULT 1,
            check01_passed BOOLEAN DEFAULT 0,
            check02_passed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id INTEGER,
            training_date DATE,
            training_type TEXT,
            completed BOOLEAN,
            pain_feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (session_id) REFERENCES training_sessions(id)
        )
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_training_user_id ON training_sessions(user_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_training_log_user_id ON training_log(user_id)
    ''')
    conn.commit()
    conn.close()


def save_user_to_db(user_data: dict, db_path: str = 'users.db') -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Всегда создаем новую запись
    cursor.execute('''
        INSERT INTO users 
        (user_id, username, height, weight, activity_level, gender, years_experience, brm, goal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_data['user_id'],
        user_data['username'],
        user_data['height'],
        user_data['weight'],
        user_data['activity_level'],
        user_data['gender'],
        user_data['years_experience'],
        user_data.get('brm'),
        user_data.get('goal')
    ))

    conn.commit()
    conn.close()
def get_all_users(db_path: str = 'users.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u1.* FROM users u1
        INNER JOIN (
            SELECT user_id, MAX(created_at) as max_date 
            FROM users 
            GROUP BY user_id
        ) u2 ON u1.user_id = u2.user_id AND u1.created_at = u2.max_date
        ORDER BY u1.created_at DESC
    ''')
    users = cursor.fetchall()
    conn.close()
    return users


def get_user_by_id(user_id: int, db_path: str = 'users.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
    ''', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_all_user_forms(user_id: int, db_path: str = 'users.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT * FROM users 
        WHERE user_id = ? 
        ORDER BY created_at ASC
    ''', (user_id,))
    forms = cursor.fetchall()
    conn.close()
    return forms


def delete_last_user_form(user_id: int, db_path: str = 'users.db') -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM users WHERE id = (
            SELECT id FROM users WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
        )
    ''', (user_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def delete_all_user_forms(user_id: int, db_path: str = 'users.db') -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def has_user_forms(user_id: int, db_path: str = 'users.db') -> bool:
    """Проверяет, есть ли у пользователя хотя бы одна анкета"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE user_id = ?', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def get_user_first_form(user_id: int, db_path: str = 'users.db'):
    """Получает первую анкету пользователя"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users 
        WHERE user_id = ? 
        ORDER BY created_at ASC 
        LIMIT 1
    ''', (user_id,))
    form = cursor.fetchone()
    conn.close()
    return form


def get_user_previous_form(user_id: int, current_form_id: int, db_path: str = 'users.db'):
    """Получает предыдущую анкету пользователя относительно текущей"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users 
        WHERE user_id = ? AND id < ?
        ORDER BY created_at DESC 
        LIMIT 1
    ''', (user_id, current_form_id))
    form = cursor.fetchone()
    conn.close()
    return form


# Функции для тренировочного процесса
def create_training_session(user_id: int, week_number: int, training_days: str, db_path: str = 'users.db') -> int:
    """Создает новую тренировочную сессию"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO training_sessions (user_id, week_number, training_days, current_day, completed_days)
        VALUES (?, ?, ?, 0, 0)
    ''', (user_id, week_number, training_days))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def get_active_training_session(user_id: int, db_path: str = 'users.db'):
    """Получает активную тренировочную сессию пользователя"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM training_sessions 
        WHERE user_id = ? AND session_active = 1
        ORDER BY created_at DESC 
        LIMIT 1
    ''', (user_id,))
    session = cursor.fetchone()
    conn.close()
    return session


def update_training_session(session_id: int, current_day: int = None, completed_days: int = None, 
                          session_active: bool = None, check01_passed: bool = None, 
                          check02_passed: bool = None, week_number: int = None, db_path: str = 'users.db'):
    """Обновляет тренировочную сессию"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if current_day is not None:
        updates.append("current_day = ?")
        params.append(current_day)
    if completed_days is not None:
        updates.append("completed_days = ?")
        params.append(completed_days)
    if session_active is not None:
        updates.append("session_active = ?")
        params.append(session_active)
    if check01_passed is not None:
        updates.append("check01_passed = ?")
        params.append(check01_passed)
    if check02_passed is not None:
        updates.append("check02_passed = ?")
        params.append(check02_passed)
    if week_number is not None:
        updates.append("week_number = ?")
        params.append(week_number)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(session_id)
        
        query = f"UPDATE training_sessions SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
    
    conn.commit()
    conn.close()


def add_training_log(user_id: int, session_id: int, training_date: str, training_type: str, 
                    completed: bool, pain_feedback: str = None, db_path: str = 'users.db'):
    """Добавляет запись в лог тренировок"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO training_log (user_id, session_id, training_date, training_type, completed, pain_feedback)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, session_id, training_date, training_type, completed, pain_feedback))
    conn.commit()
    conn.close()


def get_training_log(user_id: int, session_id: int = None, db_path: str = 'users.db'):
    """Получает лог тренировок пользователя"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if session_id:
        cursor.execute('''
            SELECT * FROM training_log 
            WHERE user_id = ? AND session_id = ?
            ORDER BY training_date DESC
        ''', (user_id, session_id))
    else:
        cursor.execute('''
            SELECT * FROM training_log 
            WHERE user_id = ?
            ORDER BY training_date DESC
        ''', (user_id,))
    
    logs = cursor.fetchall()
    conn.close()
    return logs


def advance_to_next_week(user_id: int, db_path: str = 'users.db'):
    """Переводит пользователя на следующую неделю тренировок"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем активную сессию
    cursor.execute('''
        SELECT * FROM training_sessions 
        WHERE user_id = ? AND session_active = 1
        ORDER BY created_at DESC 
        LIMIT 1
    ''', (user_id,))
    session = cursor.fetchone()
    
    if session:
        session_id = session[0]
        current_week = session[2]
        new_week = current_week + 1
        
        # Обновляем номер недели и сбрасываем счетчики
        cursor.execute('''
            UPDATE training_sessions 
            SET week_number = ?, completed_days = 0, current_day = 0, 
                check02_passed = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_week, session_id))
        
        conn.commit()
        conn.close()
        return new_week
    else:
        conn.close()
        return None


def get_all_active_training_sessions(db_path: str = 'users.db'):
    """Получает все активные тренировочные сессии"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM training_sessions 
        WHERE session_active = 1
        ORDER BY created_at DESC
    ''')
    sessions = cursor.fetchall()
    conn.close()
    return sessions


def get_pending_training_check(user_id: int, training_date: str, db_path: str = 'users.db'):
    """Получает запись о проверке тренировки"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM training_log 
        WHERE user_id = ? AND training_date = ? AND completed IS NULL
        ORDER BY created_at DESC 
        LIMIT 1
    ''', (user_id, training_date))
    log = cursor.fetchone()
    conn.close()
    return log