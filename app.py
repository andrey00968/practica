from flask import Flask, render_template, request, redirect, session, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
import re
import os
import sqlite3
from docx import Document
import pandas as pd
import io

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'sborka.db')
app.config['SECRET_KEY'] = '1234'
db = SQLAlchemy(app)


# Модель пользователя для SQLAlchemy
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    sborki = db.Column(db.Text, nullable=True)
    zayavki = db.Column(db.Text, nullable=True)
    admin = db.Column(db.Integer, default=0)

# Главная страница
@app.route('/')
def index():
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            username = user.username
    return render_template('index.html', username=username)

# Страница архива
@app.route('/archive')
def archive():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('archive.html', user=user)

@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    number = data['number']
    statuses = data['statuses']
    username = data['username']
    obj_type = data['type']
    new_status = f": {', '.join(statuses)}"

    user = User.query.filter(User.username == username).first()
    
    if not user:
        print(f"No user found with username {username}")
        return '', 204
    
    updated = False

    if obj_type == 'configuration':
        # Обработка сборок
        if user.sborki and f'№{number}' in user.sborki:
            sborki = user.sborki.split('\n\n')  # Конфигурации разделены двойным абзацем
            for i, sborka in enumerate(sborki):
                if f'№{number}' in sborka:
                    parts = sborka.split(': ', 1)
                    if len(parts) > 1:
                        text = parts[1].strip().strip('"')
                        # Проверка и удаление старого статуса, если он существует
                        if '": ' in text:
                            text, _ = text.rsplit('": ', 1)
                        sborki[i] = f'№{number}: "{text}"{new_status}'
                        updated = True
            if updated:
                user.sborki = '\n\n'.join(sborki)
                db.session.commit()
                print(f"Updated configuration status for user {user.username}: {user.sborki}")
                return '', 204
    elif obj_type == 'request':
        # Обработка заявок
        if user.zayavki and f'№{number}' in user.zayavki:
            zayavki = user.zayavki.split('\n')  # Заявки разделены одиночным абзацем
            for i, z in enumerate(zayavki):
                if f'№{number}' in z:
                    parts = z.split(': ', 1)
                    if len(parts) > 1:
                        text = parts[1].strip().strip('"')
                        # Проверка и удаление старого статуса, если он существует
                        if '": ' in text:
                            text, _ = text.rsplit('": ', 1)
                        zayavki[i] = f'№{number}: "{text}"{new_status}'
                        updated = True
            if updated:
                user.zayavki = '\n'.join(zayavki)
                db.session.commit()
                print(f"Updated status for user {user.username}: {user.zayavki}")
                return '', 204

    print(f"No matching request number {number} found for user {username}")
    return '', 204

# Страница конфигуратора
@app.route('/configurator', methods=['GET', 'POST'])
def configurator():
    return render_template('configurator.html')

# Функция для парсинга конфигураций
def parse_sborki(sborki_string):
    # Регулярное выражение для парсинга конфигураций
    pattern = re.compile(r"№(\d+):\s*([^№]+?)(?=\n\n|$)", re.DOTALL)
    matches = pattern.findall(sborki_string)
    result = []
    for match in matches:
        number, content = match
        # Пытаемся найти статус
        status_match = re.search(r':\s*\d+', content)
        status = status_match.group(0).strip() if status_match else ""
        content = content.replace(status, "").strip()
        result.append((number, content.strip().replace("\n", "<br>"), status))
    return result

# Страница моих конфигураций
@app.route('/my_configurations')
def my_configurations():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            sborki = []
            if user.sborki:
                sborki = parse_sborki(user.sborki)
            return render_template('my_configurations.html', sborki=sborki, user=user)
    return redirect('/personal_account')

# Страница всех конфигураций для админа
@app.route('/all_configurations')
def all_configurations():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.admin == 1:
            all_sborki = []
            users = User.query.all()
            for u in users:
                if u.sborki:
                    sborki = parse_sborki(u.sborki)
                    for sborka in sborki:
                        all_sborki.append((sborka[0], sborka[1], u.username))
            return render_template('all_configurations.html', sborki=all_sborki, user=user, is_admin=True)
    return redirect('/personal_account')

@app.route('/save_configuration', methods=['POST'])
def save_configuration():
    if 'user_id' not in session:
        return redirect('/personal_account')

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'success': False})

    config = request.json
    config_str = '\n'.join([f'{value}' for key, value in config.items()])

    if user.sborki:
        # Подсчет количества сборок с использованием регулярного выражения для корректного учета всех номеров
        import re
        sborki = re.findall(r'№\d+:', user.sborki)
        config_number = len(sborki) + 1
        user.sborki += f'\n\n№{config_number}: "{config_str}"\n'
    else:
        config_number = 1
        user.sborki = f'№{config_number}: "{config_str}"\n'

    db.session.commit()
    return jsonify({'success': True})

# Страница моих заявок
@app.route('/my_requests')
def my_requests():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            zayavki = []
            if user.zayavki:
                for z in user.zayavki.split('\n'):
                    if z.strip():
                        parts = z.split(': ')
                        number = parts[0].split('№')[1]
                        text = parts[1].strip('"')
                        status = parts[2] if len(parts) > 2 else ''
                        zayavki.append((number, text, status))
            return render_template('my_requests.html', zayavki=zayavki, is_admin=user.admin == 1)
    return redirect('/personal_account')

# Страница личного кабинета
@app.route('/personal_account', methods=['GET', 'POST'])
def personal_account():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password')
        if 'register' in request.form:
            if User.query.filter_by(username=username).first():
                flash('Это имя пользователя уже используется.')
            elif password != confirm_password:
                flash('Пароли не совпадают.')
            elif validate_password(password):
                new_user = User(username=username, password=password, admin=0)
                db.session.add(new_user)
                db.session.commit()
                session['user_id'] = new_user.id
                return redirect('/')
            else:
                flash('Пароль должен содержать минимум 8 символов, буквы, цифры и один спецсимвол.')
        elif 'login' in request.form:
            user = User.query.filter_by(username=username).first()
            if user and user.password == password:
                session['user_id'] = user.id
                return redirect('/')
            else:
                error = 'Имя пользователя/пароль неправильные'
    return render_template('personal_account.html', error=error)

@app.route('/all_requests')
def all_requests():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.admin == 1:
            all_zayavki = []
            users = User.query.all()
            for u in users:
                if u.zayavki:
                    for z in u.zayavki.split('\n'):
                        if z.strip():
                            parts = z.split(': ')
                            number = parts[0].split('№')[1]
                            text = parts[1].strip('"')
                            all_zayavki.append((number, text, u.username))
            return render_template('all_requests.html', zayavki=all_zayavki, is_admin=True)
    return redirect('/personal_account')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

@app.route('/check_username', methods=['POST'])
def check_username():
    username = request.form['username']
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'exists': True})
    return jsonify({'exists': False})

def fetch_latest_price(detail):
    database_path = os.path.join(basedir, 'sborka.db')
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute('SELECT price_data FROM details WHERE detail=?', (detail,))
    result = cursor.fetchone()
    conn.close()

    if result:
        prices = result[0].split('\n')
        latest_price = prices[-1].split(':')[0]  # Берем только цену, без даты
        return latest_price
    return None

@app.route('/get_latest_price/<detail>')
def get_latest_price_route(detail):
    latest_price = fetch_latest_price(detail)
    if latest_price:
        return jsonify({'price': latest_price})
    return jsonify({'error': 'Price not found'}), 404

def fetch_price_history(detail):
    database_path = os.path.join(basedir, 'sborka.db')
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute('SELECT price_data FROM details WHERE detail=?', (detail,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        prices = result[0].strip().split('\n')
        price_history = [{'price': p.split(':')[0], 'date': p.split(':')[1]} for p in prices if ':' in p]
        price_history.sort(key=lambda x: x['date'])  # Сортируем по дате
        return price_history
    return []

@app.route('/get_price_history/<detail>')
def get_price_history(detail):
    price_history = fetch_price_history(detail)
    if price_history:
        return jsonify({'prices': price_history})
    return jsonify({'error': 'Price not found'}), 404

def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Za-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[@$!%*?&.]', password):
        return False
    return True

@app.route('/download_docx')
def download_docx():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.zayavki:
            doc = Document()
            for zayavka in user.zayavki.split('\n'):
                if zayavka.strip():
                    doc.add_paragraph(zayavka)
            file_stream = io.BytesIO()
            doc.save(file_stream)
            file_stream.seek(0)
            return send_file(file_stream, as_attachment=True, download_name='zayavki.docx')
    return redirect('/personal_account')

@app.route('/download_xlsx')
def download_xlsx():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.zayavki:
            data = []
            for zayavka in user.zayavki.split('\n'):
                if zayavka.strip():
                    parts = zayavka.split(': ')
                    number = parts[0].split('№')[1]
                    text = parts[1].strip('"')
                    status = parts[2] if len(parts) > 2 else ''
                    data.append([number, text, status])
            df = pd.DataFrame(data, columns=['Номер заявки', 'Текст заявки', 'Статус заявки'])
            file_stream = io.BytesIO()
            df.to_excel(file_stream, index=False, engine='xlsxwriter')
            file_stream.seek(0)
            return send_file(file_stream, as_attachment=True, download_name='zayavki.xlsx')
    return redirect('/personal_account')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

