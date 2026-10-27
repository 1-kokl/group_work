from app.extensions import db
from datetime import datetime
import uuid

_UNSET = object()


class Product(db.Model):
    """商品模型"""
    __tablename__ = "products"
    __table_args__ = (
        db.Index("idx_products_category_created", "category", "created_at"),
        db.Index("idx_products_status_category_created", "status", "category", "created_at"),
        db.Index("idx_products_created", "created_at"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False, comment="商品名称")
    description = db.Column(db.Text, comment="商品描述")
    price = db.Column(db.Float, nullable=False, comment="商品价格")
    stock = db.Column(db.Integer, default=0, comment="库存数量")
    category = db.Column(db.String(100), comment="商品分类")
    image_url = db.Column(db.String(500), comment="商品图片URL")
    status = db.Column(db.Boolean, default=True, comment="商品状态：上架/下架")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.BigInteger, comment="创建者ID")

    def to_dict(self, seller_username=_UNSET):
        if seller_username is _UNSET:
            seller_username = None
            if self.created_by:
                from app.services.user_service import _conn
                with _conn() as conn:
                    row = conn.execute("SELECT username FROM users WHERE id = ?", (self.created_by,)).fetchone()
                    if row:
                        seller_username = row["username"]
        
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock": self.stock,
            "category": self.category,
            "image_url": self.image_url,
            "status": self.status,
            "created_by": self.created_by,
            "seller_username": seller_username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Cart(db.Model):
    """购物车模型"""
    __tablename__ = "carts"
    __table_args__ = (
        db.Index("idx_carts_user_selected", "user_id", "selected"),
        db.Index("idx_carts_user_product", "user_id", "product_id"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.BigInteger, nullable=False, comment="用户ID")
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False, comment="商品ID")
    quantity = db.Column(db.Integer, default=1, comment="商品数量")
    selected = db.Column(db.Boolean, default=True, comment="是否选中")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    product = db.relationship("Product", backref="cart_items")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "product_price": self.product.price if self.product else None,
            "quantity": self.quantity,
            "selected": self.selected,
            "subtotal": (self.product.price * self.quantity) if self.product else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Order(db.Model):
    """订单模型"""
    __tablename__ = "orders"
    __table_args__ = (db.Index("idx_orders_user_status_created", "user_id", "status", "created_at"),)

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_no = db.Column(db.String(64), unique=True, nullable=False, comment="订单号")
    user_id = db.Column(db.BigInteger, nullable=False, comment="用户ID")
    total_amount = db.Column(db.Float, nullable=False, comment="订单总金额")
    status = db.Column(db.String(20), default="pending", comment="订单状态：pending/paid/shipped/completed/cancelled")
    shipping_address = db.Column(db.Text, comment="收货地址")
    contact_phone = db.Column(db.String(20), comment="联系电话")
    remark = db.Column(db.Text, comment="订单备注")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = db.Column(db.DateTime, comment="支付时间")
    
    # 支付相关字段
    payment_status = db.Column(db.String(20), default="unpaid", comment="支付状态：unpaid/paying/paid/failed")
    payment_method = db.Column(db.String(50), comment="支付方式：bank_transfer/alipay/wechat")
    transaction_id = db.Column(db.String(100), comment="银行交易号")
    payment_sign = db.Column(db.Text, comment="支付签名")
    payment_timestamp = db.Column(db.Integer, comment="支付时间戳")

    # 关系
    items = db.relationship("OrderItem", backref="order", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "order_no": self.order_no,
            "user_id": self.user_id,
            "total_amount": self.total_amount,
            "status": self.status,
            "payment_status": self.payment_status,
            "payment_method": self.payment_method,
            "transaction_id": self.transaction_id,
            "shipping_address": self.shipping_address,
            "contact_phone": self.contact_phone,
            "remark": self.remark,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None
        }


class OrderItem(db.Model):
    """订单项模型"""
    __tablename__ = "order_items"
    __table_args__ = (db.Index("idx_order_items_order_id", "order_id"),)

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(db.String(36), db.ForeignKey("orders.id"), nullable=False, comment="订单ID")
    product_id = db.Column(db.String(36), nullable=False, comment="商品ID")
    product_name = db.Column(db.String(200), nullable=False, comment="商品名称（快照）")
    product_price = db.Column(db.Float, nullable=False, comment="商品单价（快照）")
    quantity = db.Column(db.Integer, nullable=False, comment="购买数量")
    subtotal = db.Column(db.Float, nullable=False, comment="小计金额")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_price": self.product_price,
            "quantity": self.quantity,
            "subtotal": self.subtotal
        }
