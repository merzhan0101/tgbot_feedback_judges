import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name="feedback.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_table()
    
    def create_table(self):
        cursor = self.conn.cursor()
        
        # Удаляем старую таблицу если она существует
        cursor.execute('DROP TABLE IF EXISTS feedback')
        
        # Создаем новую таблицу со всеми колонками
        cursor.execute('''
            CREATE TABLE feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judge_name TEXT NOT NULL,
                round_name TEXT NOT NULL,
                faction_name TEXT NOT NULL,
                speaker_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                feedback_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                username TEXT
            )
        ''')
        self.conn.commit()
    
    def add_feedback(self, judge_name, round_name, faction_name, speaker_name, score, feedback_text, user_id=None, username=None):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO feedback (judge_name, round_name, faction_name, speaker_name, score, feedback_text, user_id, username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (judge_name, round_name, faction_name, speaker_name, score, feedback_text, user_id, username))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_all_feedback(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM feedback ORDER BY created_at DESC')
        return cursor.fetchall()
    
    def get_feedback_by_id(self, feedback_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM feedback WHERE id = ?', (feedback_id,))
        return cursor.fetchone()
    
    def delete_feedback(self, feedback_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM feedback WHERE id = ?', (feedback_id,))
        self.conn.commit()
        return cursor.rowcount
    
    def get_statistics(self):
        cursor = self.conn.cursor()
        
        # Общая статистика
        cursor.execute('SELECT COUNT(*) FROM feedback')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT judge_name) FROM feedback')
        judges_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(score) FROM feedback')
        avg_score = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT round_name, COUNT(*) as count 
            FROM feedback 
            GROUP BY round_name 
            ORDER BY count DESC
        ''')
        rounds_stats = cursor.fetchall()
        
        return {
            'total': total,
            'judges_count': judges_count,
            'avg_score': round(avg_score, 2) if avg_score else 0,
            'rounds_stats': rounds_stats
        }
    
    def search_feedback(self, keyword):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM feedback 
            WHERE judge_name LIKE ? OR faction_name LIKE ? OR speaker_name LIKE ? OR feedback_text LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
        return cursor.fetchall()
    
    def close(self):
        self.conn.close()