from flask import Flask, render_template, request, redirect, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import re
import os
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
    
    user = User.query.filter(User.username == username, User.zayavki.like(f'%№{number}%')).first()
    if user:
        zayavki = user.zayavki.split('\n')
        for i, z in enumerate(zayavki):
            if f'№{number}' in z:
                parts = z.split(': ')
                text = parts[1].strip('"')
                zayavki[i] = f'№{number}: "{text}": {", ".join(statuses)}'
        user.zayavki = '\n'.join(zayavki)
        db.session.commit()
        print(f"Updated status for user {user.username}: {user.zayavki}")
    else:
        print(f"No user found with username {username} and request number {number}")
    return '', 204

# Страница конфигуратора
@app.route('/configurator', methods=['GET', 'POST'])
def configurator():
    return render_template('configurator.html')

# Страница моих конфигураций
@app.route('/my_configurations')
def my_configurations():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            sborki = user.sborki.split(';') if user.sborki else []
            return render_template('my_configurations.html', sborki=sborki)
    return redirect('/personal_account')

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

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
