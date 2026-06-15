

import os
import sqlite3
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'applications.db')

app = Flask(__name__)
app.secret_key = 'super_secret_key_satti_crm'


def get_db_connection():
    return sqlite3.connect(DB_PATH)



def init_db():
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS applications 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, parent_name TEXT, child_name TEXT, phone TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'new')''')

    c.execute('''CREATE TABLE IF NOT EXISTS groups 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age_range TEXT, teacher_name TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS children 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, parent_name TEXT, phone TEXT, group_id INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS staff 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, position TEXT, phone TEXT, salary INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS finance 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, category TEXT, amount INTEGER, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, description TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, child_id INTEGER, date DATE, status TEXT,
                  FOREIGN KEY(child_id) REFERENCES children(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    c.execute("SELECT * FROM users")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password) VALUES ('admin', '1234')")
        print("[СИСТЕМА] Создан стандартный профиль администратора.")

    conn.commit()
    conn.close()

init_db()

def log_action(action_text):

    user = "Система"
    if session.get('logged_in'):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE id=1")
        u = c.fetchone()
        if u: user = u[0]
        conn.close()

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO logs (user, action) VALUES (?, ?)", (user, action_text))
    conn.commit()
    conn.close()


# логин

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Обработка входа в панель администратора."""
    error = None
    if request.method == 'POST':
        login_input = request.form.get('username')
        password_input = request.form.get('password')
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (login_input, password_input))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['logged_in'] = True
            log_action("Успешный вход в систему")
            return redirect(url_for('dashboard'))
        else:
            error = "Неверный логин или пароль. Повторите попытку."
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """Завершение сеанса пользователя."""
    session.clear()
    return redirect(url_for('login'))


# главный сайт

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_application', methods=['POST'])
def submit_application():
    parent = request.form.get('parent_name')
    child = request.form.get('child_name')
    phone = request.form.get('phone')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO applications (parent_name, child_name, phone) VALUES (?, ?, ?)", (parent, child, phone))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/page/<page_name>')
def show_page(page_name):
   
    pages_data = {
        'about': {
            'title': 'О нас', 
            'content': '<h2>Добро пожаловать в SATTI!</h2><p>Мы - современный детский сад, где каждый ребенок чувствует себя как дома. У нас работают лучшие педагоги, а программа направлена на всестороннее развитие малышей.</p>'
        },
        'staff': {
            'title': 'Наши воспитатели', 
            'content': '<h2>Наши специалисты</h2><p>Команда детского сада SATTI - это профессионалы с многолетним стажем. Каждый воспитатель регулярно проходит курсы повышения квалификации и имеет сертификаты оказания первой помощи.</p>'
        },
        'food': {
            'title': 'Питание', 
            'content': '<h2>Вкусное и полезное меню</h2><p>Мы предлагаем сбалансированное 5-разовое питание. Меню разработано детским диетологом с учетом всех норм и стандартов. Мы используем только свежие фермерские продукты.</p>'
        },
        'groups': {
            'title': 'Наши группы', 
            'content': '<h2>Возрастные группы</h2><p>У нас работают группы для разных возрастов: от ясельной (1.5-3 года) до подготовительной (5-6 лет). Максимальное количество детей в группе - 15 человек.</p>'
        },
        'gallery': {
            'title': 'Галерея', 
            'content': '<h2>Фотографии нашего сада</h2><p>Раздел находится в стадии наполнения. Скоро здесь появятся фотографии наших веселых праздников, занятий и прогулок!</p>'
        },
        'contacts': {
            'title': 'Контакты', 
            'content': '<h2>Свяжитесь с нами</h2><p><strong>Адрес:</strong> г. Алматы, ул. Примерная, д. 123<br><strong>Телефон:</strong> +7 (777) 123-45-67<br><strong>Email:</strong> info@satti.kz<br><strong>Режим работы:</strong> Пн-Пт с 8:00 до 19:00</p>'
        }
    }
    

    page = pages_data.get(page_name)
    if not page:
        return "<h1 style='text-align:center; margin-top:50px; font-family:sans-serif;'>Страница не найдена 😢</h1>", 404
        

    return render_template('page.html', title=page['title'], content=page['content'])



@app.route('/dashboard')
def dashboard():
    """Главная панель сводной статистики (Дашборд)."""
    if not session.get('logged_in'): return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM applications ORDER BY id DESC")
    apps = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'new'")
    count_new = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM children")
    count_kids = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM staff")
    count_staff = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('dashboard.html', applications=apps, new_count=count_new, total_children=count_kids, total_staff=count_staff)


@app.route('/update_status/<int:id>/<new_status>')
def update_status(id, new_status):
    if not session.get('logged_in'): return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (new_status, id))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/delete_application/<int:id>')
def delete_application(id):
    if not session.get('logged_in'): return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM applications WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/recruit_child/<int:app_id>/<int:group_id>')
def recruit_child(app_id, group_id):
    """Логика перевода ребенка из статуса кандидата (заявка) в действующую группу."""
    if not session.get('logged_in'): return redirect('/login')
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
    app_data = c.fetchone()
    
    if app_data:
        parent = app_data[1]
        child = app_data[2]
        phone = app_data[3]
        c.execute("INSERT INTO children (name, parent_name, phone, group_id) VALUES (?, ?, ?, ?)", 
                  (child, parent, phone, group_id))
        c.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        conn.commit()
        log_action(f"Зачисление ребенка: {child} в группу ID {group_id}")
    
    conn.close()
    return redirect(f'/group/{group_id}')




@app.route('/groups')
def groups_page():
    if not session.get('logged_in'): return redirect('/login')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM groups")
    groups_list = c.fetchall()
    c.execute("SELECT * FROM staff")
    staff_list = c.fetchall()
    conn.close()
    return render_template('groups.html', groups=groups_list, staff=staff_list)

@app.route('/add_group', methods=['POST'])
def add_group():
    if not session.get('logged_in'): return redirect('/login')
    name = request.form['group_name']
    age = request.form['age_range']
    teacher = request.form['teacher_name']
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO groups (name, age_range, teacher_name) VALUES (?, ?, ?)", (name, age, teacher))
    conn.commit()
    conn.close()
    log_action(f"Создана новая группа: {name}")
    return redirect('/groups')

@app.route('/group/<int:group_id>')
def group_detail(group_id):
    """Детальная карточка группы со списком детей и кандидатов."""
    if not session.get('logged_in'): return redirect('/login')
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
    group_info = c.fetchone()
    
    if not group_info:
        conn.close()
        return "<h1 style='text-align:center; font-family:sans-serif; margin-top:50px;'>Группа не найдена или была удалена 🗑️</h1><div style='text-align:center;'><a href='/groups' style='font-family:sans-serif; color:blue;'>Вернуться к списку групп</a></div>", 404
        
    c.execute("SELECT * FROM children WHERE group_id = ?", (group_id,))
    kids = c.fetchall()
    c.execute("SELECT * FROM applications WHERE status = 'accepted'")
    candidates = c.fetchall()
    c.execute("SELECT * FROM staff")
    staff_list = c.fetchall()
    conn.close()
    
    return render_template('group_detail.html', group=group_info, children=kids, candidates=candidates, staff=staff_list)

@app.route('/update_group_teacher', methods=['POST'])
def update_group_teacher():
    if not session.get('logged_in'): return redirect('/login')
    group_id = request.form['group_id']
    new_teacher = request.form['teacher_name']
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE groups SET teacher_name = ? WHERE id = ?", (new_teacher, group_id))
    conn.commit()
    conn.close()
    return redirect(f'/group/{group_id}')

@app.route('/add_child_to_group', methods=['POST'])
def add_child_to_group():
    """Добавление ребенка в группу вручную минуя заявки."""
    if not session.get('logged_in'): return redirect('/login')
    name = request.form['child_name']
    parent = request.form['parent_name']
    phone = request.form['phone']
    group_id = request.form['group_id']
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO children (name, parent_name, phone, group_id) VALUES (?, ?, ?, ?)", 
              (name, parent, phone, group_id))
    conn.commit()
    conn.close()
    log_action(f"Ручное добавление ребенка: {name} в группу {group_id}")
    return redirect(f'/group/{group_id}')

@app.route('/delete_child/<int:child_id>/<int:group_id>')
def delete_child(child_id, group_id):
    if not session.get('logged_in'): return redirect('/login')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM children WHERE id = ?", (child_id,))
    child_name = c.fetchone()[0]
    c.execute("DELETE FROM children WHERE id = ?", (child_id,))
    conn.commit()
    conn.close()
    log_action(f"Удален ребенок: {child_name} (ID: {child_id})")
    return redirect(f'/group/{group_id}')




@app.route('/staff')
def staff_page():
    if not session.get('logged_in'): return redirect('/login')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM staff")
    staff_list = c.fetchall()
    conn.close()
    return render_template('staff.html', staff=staff_list)

@app.route('/add_staff', methods=['POST'])
def add_staff():
    if not session.get('logged_in'): return redirect('/login')
    name = request.form['name']
    position = request.form['position']
    phone = request.form['phone']
    salary = request.form['salary']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO staff (name, position, phone, salary) VALUES (?, ?, ?, ?)", (name, position, phone, salary))
    conn.commit()
    conn.close()
    log_action(f"Принят сотрудник: {name} ({position})")
    return redirect('/staff')

@app.route('/delete_staff/<int:id>')
def delete_staff(id):
    """Увольнение сотрудника с отвязкой от курируемых групп."""
    if not session.get('logged_in'): return redirect('/login')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM staff WHERE id = ?", (id,))
    staff_record = c.fetchone()

    if not staff_record:
        conn.close()
        return redirect('/staff')

    staff_name = staff_record[0]
    c.execute("UPDATE groups SET teacher_name = 'Не назначен' WHERE teacher_name = ?", (staff_name,))
    c.execute("DELETE FROM staff WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    log_action(f"Уволен сотрудник: {staff_name}. Группы освобождены.")
    return redirect('/staff')




@app.route('/finance')
def finance_page():
    """Сводка по доходам и расходам предприятия."""
    if not session.get('logged_in'): return redirect('/login')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM finance ORDER BY id DESC")
    transactions = c.fetchall()
    c.execute("SELECT SUM(amount) FROM finance WHERE type = 'income'")
    total_income = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM finance WHERE type = 'expense'")
    total_expense = c.fetchone()[0] or 0
    conn.close()
    balance = total_income - total_expense
    return render_template('finance.html', transactions=transactions, income=total_income, expense=total_expense, balance=balance)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if not session.get('logged_in'): return redirect('/login')
    type_trans = request.form['type']
    category = request.form['category']
    amount = int(request.form['amount'])
    description = request.form['description']
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO finance (type, category, amount, description) VALUES (?, ?, ?, ?)", 
              (type_trans, category, amount, description))
    conn.commit()
    conn.close()
    log_action(f"Финансы: {type_trans} {amount}тг ({category})")
    return redirect('/finance')

@app.route('/delete_transaction/<int:id>')
def delete_transaction(id):
    if not session.get('logged_in'): return redirect('/login')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM finance WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/finance')




@app.route('/journal')
def journal_page():
    """Учет посещаемости детей по группам."""
    if not session.get('logged_in'): return redirect('/login')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM groups")
    groups = c.fetchall()
    
    selected_group_id = request.args.get('group_id')
    children_list = []
    today = date.today()
    
    if selected_group_id:
        c.execute('''
            SELECT c.id, c.name, a.status 
            FROM children c
            LEFT JOIN attendance a ON c.id = a.child_id AND a.date = ?
            WHERE c.group_id = ?
        ''', (today, selected_group_id))
        children_list = c.fetchall()
    
    conn.close()
    return render_template('journal.html', groups=groups, children=children_list, selected_group_id=selected_group_id, today=today)

@app.route('/save_attendance', methods=['POST'])
def save_attendance():
    """Сохранение отметок о присутствии за текущий день."""
    if not session.get('logged_in'): return redirect('/login')
    group_id = request.form.get('group_id')
    today = date.today()
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''DELETE FROM attendance WHERE date = ? AND child_id IN 
                 (SELECT id FROM children WHERE group_id = ?)''', (today, group_id))
    
    for key, value in request.form.items():
        if key.startswith('status_'):
            child_id = key.split('_')[1]
            c.execute("INSERT INTO attendance (child_id, date, status) VALUES (?, ?, ?)", (child_id, today, value))
            
    conn.commit()
    conn.close()
    log_action(f"Заполнен табель группы ID: {group_id}")
    return redirect(f'/journal?group_id={group_id}')




@app.route('/settings')
def settings_page():
    if not session.get('logged_in'): return redirect('/login')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = 1")
    admin = c.fetchone()
    c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 50")
    logs = c.fetchall()
    conn.close()
    return render_template('settings.html', admin=admin, logs=logs)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect('/login')
    new_username = request.form['username']
    new_password = request.form['password']
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET username = ?, password = ? WHERE id = 1", (new_username, new_password))
    conn.commit()
    conn.close()
    log_action(f"Изменены настройки входа. Новый логин: {new_username}")
    return redirect('/settings')

if __name__ == '__main__':
    app.run(debug=True, port=5001)