from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db
from flask_login import current_user, login_required, login_user, logout_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("routes.index"))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')
        if remember == 'on':
            remember = True
        else:
            remember = False
        
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Invalid username or password', category='error')
            return redirect(url_for('auth.login'))
        if check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            return redirect(url_for("routes.index"))
        else:
            flash('Invalid username or password', category='error')
            return redirect(url_for('auth.login'))
            
    return render_template('login.html', text='Testing')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("routes.index"))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long', category='error')
        elif password1 != password2:
            flash('Passwords do not match', category='error')
        elif len(password1) < 3:
            flash('Password must be at least 3 characters long', category='error')
        else:
            new_user = User(username=username, password_hash=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('Registration successful', category='success')
            return redirect(url_for('routes.index'))
        
    return render_template('register.html')

