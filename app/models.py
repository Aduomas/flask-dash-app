from flask_login import UserMixin
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from sqlalchemy.sql import func

from app.extensions import db
from app.extensions import login


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return "<User {}>".format(self.username)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, nullable=False)
    url = db.Column(db.String(256), unique=True, nullable=False)
    manufacturer_id = db.Column(
        db.Integer, db.ForeignKey("manufacturer.id"), nullable=False
    )
    eshop_id = db.Column(db.Integer, db.ForeignKey("eshop.id"), nullable=False)
    store = db.relationship("Store", backref="product")

    def __repr__(self):
        return "<Product {}>".format(self.name)


class Manufacturer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    products = db.relationship("Product", backref="manufacturer", lazy=True)

    def __repr__(self):
        return "<Manufacturer {}>".format(self.name)


class Eshop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    products = db.relationship("Product", backref="eshop", lazy=True)

    def __repr__(self):
        return "<Eshop {}>".format(self.name)


class Store(db.Model):
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    price = db.Column(
        db.Float, primary_key=True, nullable=False
    )  # primary_key just to not raise errors...
    date = db.Column(db.DateTime(timezone=True), nullable=False, default=func.now())
