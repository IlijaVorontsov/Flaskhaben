from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' # Postgres: postgresql://user:password@localhost:5432/database
app.config['SECRET_KEY'] = 'X!7RV*wr3GFFnA8dn88Mmc'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    products = db.relationship('Product', backref='user', lazy=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    owner = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@login_manager.user_loader
def load_user(id):
    return db.session.query(User).filter_by(id=id).first()


@app.route('/products')
def products():
    products = db.session.query(Product).all()
    return render_template('products.html', products=products)

@app.route('/products/<int:product_id>')
def product(product_id):
    product = db.session.query(Product).filter_by(id=product_id).first()
    return render_template('product.html', product=product)

@login_required
@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == "POST":
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        if not name or not price or not description:
            return render_template('add_product.html', error="Please fill out all fields")

        new_product = Product(name=name, price=price, description=description, owner=current_user.id)
        db.session.add(new_product)
        db.session.commit()
        return render_template('add_product.html', success="Product added")
    elif request.method == "GET":
        return render_template('add_product.html')

@login_required
@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = db.session.query(Product).filter_by(id=product_id).first()
    if request.method == "POST":
        
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        if not name or not price or not description:
            return render_template('edit_product.html', product=product, error="Please fill out all fields")
        db.session.query(Product).filter_by(id=product_id).update(dict(name=name, price=price, description=description))
        db.session.commit()
        return render_template('edit_product.html', product=product, success="Product edited")
    elif request.method == "GET":
        return render_template('edit_product.html', product=product)

@app.route('/products/delete/<int:product_id>')
def delete_product(product_id):
    db.session.query(Product).filter_by(id=product_id).delete()
    db.session.commit()
    return redirect(url_for('products'))

@app.route('/')
def home():
    if current_user.is_authenticated:
        products = db.session.query(Product).filter_by(owner=current_user.id).all()
        return render_template('home.html', products=products)
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') # Check if works

        user = db.session.query(User).filter_by(username=username).first()

        if user:
            if bcrypt.check_password_hash(user.password, password):
                login_user(user, remember=remember_me)
                return render_template('home.html')
            else:
                return render_template('login.html', error="Incorrect password")
        else:
            return render_template('login.html', error="User does not exist")
    elif request.method == "GET":
        return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user = db.session.query(User).filter_by(username=username).first()

        if user:
            return render_template('register.html', error="User already exists")
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return render_template('register.html', success="User created")
    elif request.method == "GET":
        return render_template('register.html')
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    if not os.path.exists('var/app-instance/database.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True, port=5001)