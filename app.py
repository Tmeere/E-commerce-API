from sqlalchemy import create_engine, String, Float, ForeignKey, Table, Integer, Column, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# Configure the SQLAlchemy database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:4Siblings@localhost/ecommerceapi'
# Create the SQLAlchemy engine
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

# Define the base class for ORM models
class Base(DeclarativeBase):
    pass

# Association table for many-to-many relationship between OrderTable and ProductTable
order_product_association = Table(
    "order_product_association",
    Base.metadata,
    Column("order_id", ForeignKey("orderTable.id"), primary_key=True),
    Column("product_id", ForeignKey("productTable.id"), primary_key=True)
)

# Define the User model
class User(Base):
    __tablename__ = "userTable"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship to orders
    orders: Mapped[list["OrderTable"]] = relationship("OrderTable", back_populates="user")

# Define the OrderTable model
class OrderTable(Base):
    __tablename__ = "orderTable"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(ForeignKey("userTable.id"), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    products: Mapped[list["ProductTable"]] = relationship("ProductTable", secondary=order_product_association, back_populates="orders")

# Define the ProductTable model
class ProductTable(Base):
    __tablename__ = "productTable"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationship to orders
    orders: Mapped[list["OrderTable"]] = relationship("OrderTable", secondary=order_product_association, back_populates="products")

# Create all tables in the database
Base.metadata.create_all(engine)


if __name__ == "__main__":
    with app.app_context():
        cb.create_all()
        
    app.run(debug=True)