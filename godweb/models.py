from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from godweb.extensions import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # user, admin
    godcoin_balance = db.Column(db.Integer, default=0)
    avatar = db.Column(db.String(255), default='default.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    topups = db.relationship('Topup', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship('Post', backref='category', lazy=True)

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    thumbnail = db.Column(db.String(255))
    is_premium = db.Column(db.Boolean, default=False)
    premium_price = db.Column(db.Integer, default=0)  # GodCoin price
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    views = db.Column(db.Integer, default=0)
    # Pin priority: 0 = not pinned, 1 = user pinned, 2 = admin pinned
    pin_priority = db.Column(db.Integer, default=0)
    pinned_by = db.Column(db.String(20), default=None)  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    comments = db.relationship('Comment', backref='post', lazy=True)
    purchases = db.relationship('PostPurchase', backref='post', lazy=True)

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PostPurchase(db.Model):
    __tablename__ = 'post_purchases'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='post_purchases')

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)  # GodCoin price
    image = db.Column(db.String(255))
    stock = db.Column(db.Integer, default=0)  # Number of accounts remaining in file
    sold_count = db.Column(db.Integer, default=0)  # Number of accounts sold
    inventory_file = db.Column(db.String(255))  # Path to txt file containing accounts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='product', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    account_info = db.Column(db.Text, nullable=False)  # The account info given to user
    price = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # topup, purchase, admin_add, admin_subtract
    amount = db.Column(db.Integer, nullable=False)  # positive or negative
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Topup(db.Model):
    __tablename__ = 'topups'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Amount in VND
    godcoin_amount = db.Column(db.Integer, nullable=False)  # GodCoin to receive
    method = db.Column(db.String(50), nullable=False)  # momo, bank
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
