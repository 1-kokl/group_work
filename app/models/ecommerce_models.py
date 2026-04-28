from app import db
from datetime import datetime
import uuid


class Product(db.Model):
    """商品模型"""
    __tablename__ = "products"

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

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock": self.stock,
            "category": self.category,
            "image_url": self.image_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Cart(db.Model):
    """购物车模型"""
    __tablename__ = "carts"

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
            "product": {
                "id": self.product.id,
                "name": self.product.name,
                "price": self.product.price,
                "stock": self.product.stock,
                "category": self.product.category,
                "image_url": self.product.image_url
            } if self.product else None,
            "quantity": self.quantity,
            "selected": self.selected,
            "subtotal": (self.product.price * self.quantity) if self.product else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Order(db.Model):
    """订单模型"""
    __tablename__ = "orders"

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
    shipped_at = db.Column(db.DateTime, comment="发货时间")          # ← 新增
    completed_at = db.Column(db.DateTime, comment="完成时间")         # ← 新增
    cancelled_at = db.Column(db.DateTime, comment="取消时间")         # ← 新增

    # 关系
    items = db.relationship("OrderItem", backref="order", lazy=True)

    def to_dict(self):
        status_map = {
            "pending": "待支付",
            "paid": "已支付",
            "shipped": "已发货",
            "completed": "已完成",
            "cancelled": "已取消"
        }

        item_count = sum(item.quantity for item in self.items) if self.items else 0

        return {
            "id": self.id,
            "order_no": self.order_no,
            "user_id": self.user_id,
            "total_amount": self.total_amount,
            "status": self.status,
            "status_text": status_map.get(self.status, "未知状态"),
            "item_count": item_count,
            "shipping_address": self.shipping_address,
            "contact_phone": self.contact_phone,
            "remark": self.remark,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None
        }


class OrderItem(db.Model):
    """订单项模型"""
    __tablename__ = "order_items"

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
