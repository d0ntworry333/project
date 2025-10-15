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
		CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)
	''')
	conn.commit()
	conn.close()


def save_user_to_db(user_data: dict, db_path: str = 'users.db') -> None:
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()

	cursor.execute('SELECT id FROM users WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
				   (user_data['user_id'],))
	existing_user = cursor.fetchone()

	if existing_user:
		cursor.execute('''
			UPDATE users SET
			username = ?, height = ?, weight = ?, activity_level = ?, 
			gender = ?, years_experience = ?, brm = ?, goal = ?, updated_at = CURRENT_TIMESTAMP
			WHERE id = ?
		''', (
			user_data['username'],
			user_data['height'],
			user_data['weight'],
			user_data['activity_level'],
			user_data['gender'],
			user_data['years_experience'],
			user_data.get('brm'),
			user_data.get('goal'),
			existing_user[0]
		))
	else:
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
		SELECT * FROM users 
		WHERE user_id = ? 
		ORDER BY created_at DESC
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
