import sqlite3
import os
from datetime import datetime
from app.models.ecommerce_models import Product, Cart, Order, OrderItem
from app import db


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

        return {
            "success": True,
            "data": {
                "items": [p.to_dict() for p in pagination.items],
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
        # 检查商品是否存在
        product = Product.query.get(product_id)
        if not product:
            return {"success": False, "msg": "商品不存在"}
        if not product.status:
            return {"success": False, "msg": "商品已下架"}

        # 检查是否已在购物车中
        cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
        
        try:
            if cart_item:
                cart_item.quantity += quantity
                cart_item.updated_at = datetime.utcnow()
            else:
                cart_item = Cart(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity
                )
                db.session.add(cart_item)
            
            db.session.commit()
            return {"success": True, "data": cart_item.to_dict(), "msg": "添加成功"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"添加失败: {str(e)}"}

    @staticmethod
    def get_user_cart(user_id):
        """获取用户购物车（IDOR防护：只能查看自己的购物车）"""
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        return {
            "success": True,
            "data": [item.to_dict() for item in cart_items],
            "total": sum(item.quantity for item in cart_items)
        }

    @staticmethod
    def update_cart_item(user_id, cart_id, quantity=None, selected=None):
        """更新购物车项（IDOR防护：只能修改自己的购物车）"""
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

    @staticmethod
    def batch_delete(user_id, cart_ids):
        """批量删除购物车项（IDOR防护：只能删除自己的购物车项）"""
        try:
            cart_items = Cart.query.filter(
                Cart.id.in_(cart_ids),
                Cart.user_id == user_id
            ).all()

            if not cart_items:
                return {"success": False, "msg": "没有找到要删除的商品"}

            for item in cart_items:
                db.session.delete(item)

            db.session.commit()
            return {"success": True, "msg": f"已删除 {len(cart_items)} 件商品"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"删除失败: {str(e)}"}


class OrderService:
    """订单服务"""

    @staticmethod
    def generate_order_no():
        """生成订单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        import random
        random_str = str(random.randint(1000, 9999))
        return f"ORD{timestamp}{random_str}"

    @staticmethod
    def create_order_from_cart(user_id, shipping_address, contact_phone, remark=None, cart_item_ids=None):
        """从购物车创建订单（IDOR防护：只能为自己的购物车创建订单）"""
        # 获取选中的购物车项
        query = Cart.query.filter_by(user_id=user_id, selected=True)
        
        if cart_item_ids:
            query = query.filter(Cart.id.in_(cart_item_ids))
        
        cart_items = query.all()

        if not cart_items:
            return {"success": False, "msg": "购物车为空，请先添加商品"}

        try:
            # 计算总金额并检查库存
            total_amount = 0
            order_items_data = []

            for cart_item in cart_items:
                # IDOR防护：再次验证
                if cart_item.user_id != user_id:
                    return {"success": False, "msg": "无权操作此购物车项"}

                product = Product.query.get(cart_item.product_id)
                if not product:
                    return {"success": False, "msg": f"商品 {cart_item.product_id} 不存在"}
                
                if not product.status:
                    return {"success": False, "msg": f"商品 {product.name} 已下架"}

                # 检查库存
                has_stock, stock_msg = ProductService.check_stock(cart_item.product_id, cart_item.quantity)
                if not has_stock:
                    return {"success": False, "msg": f"商品 {product.name}: {stock_msg}"}

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
            db.session.flush()  # 获取订单ID

            # 创建订单项
            for item_data in order_items_data:
                order_item = OrderItem(
                    order_id=order.id,
                    **item_data
                )
                db.session.add(order_item)

            # 减少库存
            for item_data in order_items_data:
                success, msg = ProductService.reduce_stock(item_data["product_id"], item_data["quantity"])
                if not success:
                    db.session.rollback()
                    return {"success": False, "msg": f"库存扣减失败: {msg}"}

            # 清空已下单的购物车项
            for cart_item in cart_items:
                db.session.delete(cart_item)

            db.session.commit()
            return {"success": True, "data": order.to_dict(), "msg": "订单创建成功"}

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
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "msg": "订单不存在"}

        # IDOR防护：验证用户ID
        if order.user_id != user_id:
            return {"success": False, "msg": "无权操作此订单"}

        if order.status != "pending":
            return {"success": False, "msg": "只能取消待支付的订单"}

        try:
            order.status = "cancelled"
            order.cancelled_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()

            # 恢复库存
            for item in order.items:
                ProductService.reduce_stock(item.product_id, -item.quantity)

            db.session.commit()
            return {"success": True, "data": order.to_dict(), "msg": "订单已取消"}
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
            return {"success": True, "data": order.to_dict(), "msg": "支付成功"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"支付失败: {str(e)}"}

    @staticmethod
    def confirm_receipt(user_id, order_id):
        """确认收货（IDOR防护：只能确认自己的订单）"""
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "msg": "订单不存在"}

        # IDOR防护：验证用户ID
        if order.user_id != user_id:
            return {"success": False, "msg": "无权操作此订单"}

        if order.status != "shipped":
            return {"success": False, "msg": "订单状态不正确，只有已发货的订单才能确认收货"}

        try:
            order.status = "completed"
            order.completed_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()
            db.session.commit()
            return {"success": True, "data": order.to_dict(), "msg": "确认收货成功"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"确认收货失败: {str(e)}"}

    @staticmethod
    def ship_order(user_id, order_id):
        """发货（仅管理员或商家）"""
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "msg": "订单不存在"}

        if order.status != "paid":
            return {"success": False, "msg": "只能发货已支付的订单"}

        try:
            order.status = "shipped"
            order.shipped_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()
            db.session.commit()
            return {"success": True, "data": order.to_dict(), "msg": "发货成功"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "msg": f"发货失败: {str(e)}"}

