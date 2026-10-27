import sqlite3
import os
from datetime import datetime
from app.models.ecommerce_models import Product, Cart, Order, OrderItem
from app.extensions import db
from sqlalchemy import update
from sqlalchemy.orm import joinedload
import uuid


def _begin_write():
    """Serialize SQLite read/modify/write operations before taking a read snapshot."""
    connection = db.session.connection()
    if connection.dialect.name == "sqlite" and not connection.connection.driver_connection.in_transaction:
        connection.exec_driver_sql("BEGIN IMMEDIATE")


def _seller_names(products):
    ids = sorted({p.created_by for p in products if p.created_by is not None})
    if not ids:
        return {}
    from app.services.user_service import _conn
    with _conn() as conn:
        # Only '?' placeholders are generated; every seller id is separately bound.
        rows = conn.execute("SELECT id,username FROM users WHERE id IN ("+",".join("?" for _ in ids)+")", ids).fetchall()  # nosec B608
    return {row["id"]: row["username"] for row in rows}


class ProductService:
    """商品服务"""

    @staticmethod
    def create_product(name, price, description=None, stock=0, category=None, image_url=None, created_by=None):
        """创建商品"""
        try:
            product = Product(
                name=name,
                price=price,
                description=description,
                stock=stock,
                category=category,
                image_url=image_url,
                created_by=created_by
            )
            db.session.add(product)
            db.session.commit()
            return {"success": True, "data": product.to_dict(), "msg": "商品创建成功"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"商品创建失败: {str(e)}"}

    @staticmethod
    def get_product(product_id):
        """获取单个商品"""
        product = Product.query.get(product_id)
        if not product:
            return {"success": False, "msg": "商品不存在"}
        return {"success": True, "data": product.to_dict()}

    @staticmethod
    def list_products(page=1, per_page=10, category=None, status=None, keyword=None):
        """获取商品列表（支持分页和筛选）"""
        query = Product.query

        if category:
            query = query.filter(Product.category == category)
        
        if status is not None:
            query = query.filter(Product.status == status)
        
        if keyword:
            query = query.filter(Product.name.like(f"%{keyword}%"))

        pagination = query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        sellers = _seller_names(pagination.items)

        return {
            "success": True,
            "data": {
                "items": [p.to_dict(seller_username=sellers.get(p.created_by)) for p in pagination.items],
                "total": pagination.total,
                "page": page,
                "per_page": per_page,
                "pages": pagination.pages
            }
        }

    @staticmethod
    def update_product(product_id, **kwargs):
        """更新商品信息"""
        product = Product.query.get(product_id)
        if not product:
            return {"success": False, "msg": "商品不存在"}

        try:
            for key, value in kwargs.items():
                if hasattr(product, key) and key not in ['id', 'created_at', 'updated_at']:
                    setattr(product, key, value)
            
            db.session.commit()
            return {"success": True, "data": product.to_dict(), "msg": "商品更新成功"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"商品更新失败: {str(e)}"}

    @staticmethod
    def delete_product(product_id):
        """删除商品（软删除，改为下架状态）"""
        product = Product.query.get(product_id)
        if not product:
            return {"success": False, "msg": "商品不存在"}

        try:
            product.status = False
            db.session.commit()
            return {"success": True, "msg": "商品已下架"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"操作失败: {str(e)}"}

    @staticmethod
    def check_stock(product_id, quantity):
        """检查库存"""
        product = Product.query.get(product_id)
        if not product:
            return False, "商品不存在"
        if not product.status:
            return False, "商品已下架"
        if product.stock < quantity:
            return False, f"库存不足，当前库存: {product.stock}"
        return True, "库存充足"

    @staticmethod
    def reduce_stock(product_id, quantity):
        """减少库存"""
        product = Product.query.get(product_id)
        if not product:
            return False, "商品不存在"
        if product.stock < quantity:
            return False, "库存不足"
        
        try:
            product.stock -= quantity
            db.session.commit()
            return True, "库存更新成功"
        except Exception as e:
            db.session.rollback()
            return False, str(e)


class CartService:
    """购物车服务"""

    @staticmethod
    def add_to_cart(user_id, product_id, quantity=1):
        """添加商品到购物车"""
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            return {"success": False, "msg": "数量必须为正整数"}
        try:
            _begin_write()
            product = db.session.get(Product, product_id)
            if not product or not product.status:
                db.session.rollback()
                return {"success": False, "msg": "商品不存在或已下架"}
            cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
            if cart_item:
                cart_item.quantity += quantity
                cart_item.updated_at = datetime.utcnow()
            else:
                cart_item = Cart(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity
                )
                cart_item.product = product
                db.session.add(cart_item)
            db.session.flush()
            payload = cart_item.to_dict()
            db.session.commit()
            return {"success": True, "data": payload, "msg": "添加成功"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"添加失败: {str(e)}"}

    @staticmethod
    def get_user_cart(user_id):
        """获取用户购物车（IDOR防护：只能查看自己的购物车）"""
        cart_items = Cart.query.options(joinedload(Cart.product)).filter_by(user_id=user_id).all()
        return {
            "success": True,
            "data": [item.to_dict() for item in cart_items],
            "total": sum(item.quantity for item in cart_items)
        }

    @staticmethod
    def update_cart_item(user_id, cart_id, quantity=None, selected=None):
        """更新购物车项（IDOR防护：只能修改自己的购物车）"""
        if quantity is not None and (isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0):
            return {"success": False, "msg": "数量必须为正整数"}
        cart_item = Cart.query.get(cart_id)
        if not cart_item:
            return {"success": False, "msg": "购物车项不存在"}
        
        # IDOR防护：验证用户ID
        if cart_item.user_id != user_id:
            return {"success": False, "msg": "无权操作此购物车项"}

        try:
            if quantity is not None:
                if quantity <= 0:
                    return {"success": False, "msg": "数量必须大于0"}
                cart_item.quantity = quantity
            
            if selected is not None:
                cart_item.selected = selected
            
            cart_item.updated_at = datetime.utcnow()
            db.session.commit()
            return {"success": True, "data": cart_item.to_dict(), "msg": "更新成功"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"更新失败: {str(e)}"}

    @staticmethod
    def remove_from_cart(user_id, cart_id):
        """从购物车移除（IDOR防护：只能删除自己的购物车项）"""
        cart_item = Cart.query.get(cart_id)
        if not cart_item:
            return {"success": False, "msg": "购物车项不存在"}
        
        # IDOR防护：验证用户ID
        if cart_item.user_id != user_id:
            return {"success": False, "msg": "无权操作此购物车项"}

        try:
            db.session.delete(cart_item)
            db.session.commit()
            return {"success": True, "msg": "移除成功"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"移除失败: {str(e)}"}

    @staticmethod
    def clear_cart(user_id):
        """清空购物车（IDOR防护：只能清空自己的购物车）"""
        try:
            Cart.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            return {"success": True, "msg": "购物车已清空"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"清空失败: {str(e)}"}


class OrderService:
    """订单服务"""

    @staticmethod
    def generate_order_no():
        """生成订单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = uuid.uuid4().hex
        return f"ORD{timestamp}{random_str}"

    @staticmethod
    def create_order_from_cart(user_id, shipping_address, contact_phone, remark=None, cart_item_ids=None):
        """从购物车创建订单（IDOR防护：只能为自己的购物车创建订单）"""
        try:
            _begin_write()
            query = Cart.query.options(joinedload(Cart.product)).filter_by(user_id=user_id, selected=True)
            if cart_item_ids:
                query = query.filter(Cart.id.in_(cart_item_ids))
            cart_items = query.all()
            if not cart_items:
                db.session.rollback()
                return {"success": False, "msg": "购物车为空，请先添加商品"}
            # 计算总金额并检查库存
            total_amount = 0
            order_items_data = []

            for cart_item in cart_items:
                # IDOR防护：再次验证
                if cart_item.user_id != user_id:
                    raise ValueError("无权操作此购物车项")

                product = cart_item.product
                if not product:
                    raise ValueError(f"商品 {cart_item.product_id} 不存在")
                
                if not product.status:
                    raise ValueError(f"商品 {product.name} 已下架")

                # 检查库存
                if isinstance(cart_item.quantity, bool) or not isinstance(cart_item.quantity, int) or cart_item.quantity <= 0 or product.stock < cart_item.quantity:
                    raise ValueError(f"商品 {product.name}: 库存不足或数量无效")

                subtotal = product.price * cart_item.quantity
                total_amount += subtotal

                order_items_data.append({
                    "product_id": cart_item.product_id,
                    "product_name": product.name,
                    "product_price": product.price,
                    "quantity": cart_item.quantity,
                    "subtotal": subtotal
                })

            # 创建订单
            order_no = OrderService.generate_order_no()
            order = Order(
                order_no=order_no,
                user_id=user_id,
                total_amount=total_amount,
                shipping_address=shipping_address,
                contact_phone=contact_phone,
                remark=remark,
                status="pending"
            )
            db.session.add(order)
            db.session.flush()  # 获取订单ID；全部操作只在末尾提交一次

            # 创建订单项
            for item_data in order_items_data:
                order_item = OrderItem(
                    **item_data
                )
                order.items.append(order_item)

            # 减少库存
            for item_data in order_items_data:
                changed = db.session.execute(update(Product).where(
                    Product.id == item_data["product_id"], Product.status.is_(True),
                    Product.stock >= item_data["quantity"],
                ).values(stock=Product.stock-item_data["quantity"])).rowcount
                if changed != 1:
                    raise ValueError("库存不足，请刷新后重试")

            # 清空已下单的购物车项
            for cart_item in cart_items:
                db.session.delete(cart_item)

            db.session.flush()
            payload = order.to_dict()
            db.session.commit()
            return {"success": True, "data": payload, "msg": "订单创建成功"}

        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"订单创建失败: {str(e)}"}

    @staticmethod
    def get_order(user_id, order_id):
        """获取订单详情（IDOR防护：只能查看自己的订单）"""
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "msg": "订单不存在"}
        
        # IDOR防护：验证用户ID
        if order.user_id != user_id:
            return {"success": False, "msg": "无权查看此订单"}

        return {"success": True, "data": order.to_dict()}

    @staticmethod
    def get_user_orders(user_id, page=1, per_page=10, status=None):
        """获取用户订单列表（IDOR防护：只能查看自己的订单）"""
        query = Order.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter(Order.status == status)

        pagination = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            "success": True,
            "data": {
                "items": [order.to_dict() for order in pagination.items],
                "total": pagination.total,
                "page": page,
                "per_page": per_page,
                "pages": pagination.pages
            }
        }

    @staticmethod
    def cancel_order(user_id, order_id):
        """取消订单（IDOR防护：只能取消自己的订单）"""
        try:
            _begin_write()
            order = db.session.get(Order, order_id)
            if not order or order.user_id != user_id or order.status != "pending":
                db.session.rollback()
                return {"success": False, "msg": "订单不存在、无权操作或状态不允许取消"}
            order.status = "cancelled"
            order.updated_at = datetime.utcnow()

            # 恢复库存
            for item in order.items:
                db.session.execute(update(Product).where(Product.id == item.product_id).values(
                    stock=Product.stock+item.quantity))

            db.session.commit()
            return {"success": True, "msg": "订单已取消"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"取消失败: {str(e)}"}

    @staticmethod
    def pay_order(user_id, order_id):
        """支付订单（IDOR防护：只能支付自己的订单）"""
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "msg": "订单不存在"}
        
        # IDOR防护：验证用户ID
        if order.user_id != user_id:
            return {"success": False, "msg": "无权操作此订单"}

        if order.status != "pending":
            return {"success": False, "msg": "订单状态不正确"}

        try:
            order.status = "paid"
            order.paid_at = datetime.utcnow()
            db.session.commit()
            return {"success": True, "msg": "支付成功"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"支付失败: {str(e)}"}
