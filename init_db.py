"""Create database and tables using credentials from .env"""
import pymysql
from config import Config


def init_db():
    conn = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        autocommit=True,
    )
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}`")
        cur.execute(f"USE `{Config.DB_NAME}`")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                mobile_no VARCHAR(15) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                amount DECIMAL(12, 2) NOT NULL,
                category VARCHAR(50) NOT NULL,
                description VARCHAR(255) DEFAULT '',
                expense_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_date (user_id, expense_date)
            )
            """
        )
    conn.close()
    print(f"Database '{Config.DB_NAME}' is ready.")


if __name__ == "__main__":
    init_db()
