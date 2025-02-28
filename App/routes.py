from flask import render_template, redirect, url_for, flash, request
from app import app, db
from app.forms import RegistrationForm, LoginForm, TransactionForm
from app.models import User, Transaction
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Generate account number (simple example)
        last_user = User.query.order_by(User.id.desc()).first()
        new_acc_no = f"ACC{100001 if not last_user else 100001 + last_user.id}"
        
        user = User(
            account_number=new_acc_no,
            name=form.name.data,
            email=form.email.data,
            balance=0.0
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check email/password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
                    .order_by(Transaction.timestamp.desc()).limit(5).all()
    return render_template('index.html', 
                         balance=current_user.balance,
                         transactions=transactions)

@app.route('/transaction', methods=['GET', 'POST'])
@login_required
def transaction():
    form = TransactionForm()
    if form.validate_on_submit():
        amount = form.amount.data
        t_type = form.transaction_type.data
        
        if t_type == 'withdraw' and amount > current_user.balance:
            flash('Insufficient funds', 'danger')
            return redirect(url_for('transaction'))
        
        # Update balance
        if t_type == 'deposit':
            current_user.balance += amount
        else:
            current_user.balance -= amount
        
        # Record transaction
        transaction = Transaction(
            amount=amount,
            transaction_type=t_type,
            user_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'{t_type.capitalize()} successful!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('transaction.html', form=form)

@app.route('/statement')
@login_required
def statement():
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
                    .order_by(Transaction.timestamp.desc()).all()
    return render_template('statement.html', transactions=transactions)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
