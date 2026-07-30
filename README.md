# Expense Tracker

Simple daily expense tracker built with **Flask**, **MySQL**, **HTML/CSS/JS**, and **Bootstrap**. Mobile-first, black & white UI.

## Features

- Register / login with mobile number + password
- Quickly add expenses (amount, category, note, date)
- View today's spending total and list
- Browse previous days' expenses
- Delete expenses
- Responsive layout optimized for mobile

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and set your MySQL root password:

```bash
copy .env.example .env
```

Edit `.env`:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=expense_tracker
SECRET_KEY=any-random-string
```

### 3. Create database tables

```bash
python init_db.py
```

(Or run `schema.sql` in MySQL Workbench / CLI.)

### 4. Run the app

```bash
python app.py
```

Open in browser: [http://127.0.0.1:5000](http://127.0.0.1:5000)

On your phone (same Wi‑Fi), use your PC's IP, e.g. `http://192.168.x.x:5000`.

## Project structure

```
Project1/
├── app.py
├── config.py
├── schema.sql
├── requirements.txt
├── .env.example
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── history.html
└── static/
    ├── css/style.css
    └── js/app.js
```
