# Import necessary libraries and modules
from sqlalchemy import create_engine, String, Float, ForeignKey, Table, Integer, Column, DateTime, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship
from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os


# Initialize Flask app
app = Flask(__name__)

# Configure database connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URI', 'mysql+mysqlconnector://root:<XXXXXXXX>@localhost/ecommerceapi'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)


# Base class for all ORM models
class Base(db.Model):
    __abstract__ = True


# Association table for many-to-many relationship between orders and products
order_product_association = Table(
    "order_product_association",
    Base.metadata,
    Column("order_id", ForeignKey("orderTable.id"), primary_key=True),
    Column("product_id", ForeignKey("productTable.id"), primary_key=True)
)


# User model
class UserTable(Base):
    __tablename__ = "userTable"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship to orders
    orders: Mapped[list["OrderTable"]] = relationship("OrderTable", back_populates="user")


# Order model
class OrderTable(Base):
    __tablename__ = "orderTable"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    user_id: Mapped[int] = mapped_column(ForeignKey("userTable.id"), nullable=False)

    # Relationships
    user: Mapped["UserTable"] = relationship("UserTable", back_populates="orders")
    products: Mapped[list["ProductTable"]] = relationship("ProductTable", secondary=order_product_association, back_populates="orders")


# Product model
class ProductTable(Base):
    __tablename__ = "productTable"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationship to orders
    orders: Mapped[list["OrderTable"]] = relationship("OrderTable", secondary=order_product_association, back_populates="products")


# Marshmallow schemas for serialization/deserialization
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserTable
        include_relationships = True


class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        include_fk = True
        model = OrderTable


class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ProductTable


# Instantiate schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


# User endpoints
@app.route('/users', methods=['POST'])
def create_user():
    # Create a new user
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
        
    new_user = UserTable(
        name=user_data['name'],
        email=user_data['email'],
        address=user_data['address']  
    )
    db.session.add(new_user)
    db.session.commit()
    
    return user_schema.jsonify(new_user), 201


@app.route('/users', methods=['GET'])
def get_users():
    # Get all users
    query = select(UserTable)
    users = db.session.execute(query).scalars().all()
    
    return users_schema.jsonify(users), 200


@app.route('/users/<int:id>', methods=["GET"])
def get_user(id):
    # Get a single user by ID
    user = db.session.get(UserTable, id)
    if not user:
        return jsonify({"Message": "User not found"}), 404
    
    return user_schema.jsonify(user), 200


@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    # Update user details
    user = db.session.get(UserTable, id)
    if not user:
        return jsonify({"Message": "Invalid User ID"}), 400
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    user.name = user_data['name']
    user.email = user_data['email']
    user.address = user_data['address']     
    
    db.session.commit()
    return user_schema.jsonify(user), 200   


@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    # Delete a user by ID
    user = db.session.get(UserTable, id)
    if not user:
        return jsonify({"Message": "Invalid User ID"}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({"Message": "User removed"}), 200


# Product endpoints
@app.route('/products', methods=['POST'])
def create_product():
    # Create a new product
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_product = ProductTable(
        product_name=product_data['product_name'],
        price=product_data['price']
    )
    db.session.add(new_product)
    db.session.commit()

    return product_schema.jsonify(new_product), 201


@app.route('/products', methods=['GET'])
def get_products():
    # Get all products
    query = select(ProductTable)
    products = db.session.execute(query).scalars().all()

    return products_schema.jsonify(products), 200


@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    # Get a single product by ID
    product = db.session.get(ProductTable, id)
    if not product:
        return jsonify({"Message": "Product not found"}), 404

    return product_schema.jsonify(product), 200


@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    # Update product details
    product = db.session.get(ProductTable, id)
    if not product:
        return jsonify({"Message": "Product not found"}), 404

    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    product.product_name = product_data['product_name']
    product.price = product_data['price']

    db.session.commit()
    return product_schema.jsonify(product), 200


@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    # Delete a product by ID
    product = db.session.get(ProductTable, id)
    if not product:
        return jsonify({"Message": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"Message": "Product deleted"}), 200


@app.route('/orders', methods=['POST'])
def create_order():
    # Validate the input data
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    # Check if the user exists
    user = db.session.get(UserTable, order_data['user_id'])
    if not user:
        return jsonify({"Message": "User not found"}), 404

    # Create the order
    new_order = OrderTable(
        user_id=order_data['user_id'],
        order_date=order_data.get('order_date', datetime.now())
    )
    db.session.add(new_order)
    db.session.commit()

    return order_schema.jsonify(new_order), 201


@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product_to_order(order_id, product_id):
    # Add a product to an order
    order = db.session.get(OrderTable, order_id)
    product = db.session.get(ProductTable, product_id)

    if not order or not product:
        return jsonify({"Message": "Order or Product not found"}), 404

    if product in order.products:
        return jsonify({"Message": "Product already in order"}), 400

    order.products.append(product)
    db.session.commit()
    return jsonify({"Message": "Product added to order"}), 200


@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product_from_order(order_id, product_id):
    # Remove a product from an order
    order = db.session.get(OrderTable, order_id)
    product = db.session.get(ProductTable, product_id)

    if not order or not product:
        return jsonify({"Message": "Order or Product not found"}), 404

    if product not in order.products:
        return jsonify({"Message": "Product not in order"}), 400

    order.products.remove(product)
    db.session.commit()
    return jsonify({"Message": "Product removed from order"}), 200


@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_orders_for_user(user_id):
    # Get all orders for a specific user
    user = db.session.get(UserTable, user_id)
    if not user:
        return jsonify({"Message": "User not found"}), 404

    orders = user.orders
    return orders_schema.jsonify(orders), 200


@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_products_for_order(order_id):
    # Get all products in a specific order
    order = db.session.get(OrderTable, order_id)
    if not order:
        return jsonify({"Message": "Order not found"}), 404

    products = order.products
    return products_schema.jsonify(products), 200

@app.route('/reset-database', methods=['POST'])
def reset_database():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    return jsonify({"Message": "Database reset successfully"}), 200

if __name__ == "__main__":
    # Create all tables in the database
    with app.app_context():
        db.create_all()
        
    # Run the Flask app
    app.run(debug=True)
