from flask import Blueprint, request
from app.services.ecommerce_service import ProductService, CartService, OrderService
from app.middleware.jwt_auth import jwt_required
from app.utils.response import api_response

ecommerce_bp = Blueprint("ecommerce", __name__, url_prefix="/api/ecommerce")


# ==================== 商品管理接口 ====================

@ecommerce_bp.route("/products", methods=["POST"])
@jwt_required
def create_product():
    """创建商品（需要管理员权限）"""
    data = request.get_json()
    
    name = data.get("name")
    price = data.get("price")
    
    if not name or price is None:
        return api_response(400, "商品名称和价格不能为空")
    
    if price <= 0:
        return api_response(400, "价格必须大于0")

    result = ProductService.create_product(
        name=name,
        price=price,
        description=data.get("description"),
        stock=data.get("stock", 0),
        category=data.get("category"),
        image_url=data.get("image_url"),
        created_by=request.user_info.get("user_id")
    )

    if result["success"]:
        return api_response(201, result["msg"], result["data"])
    else:
        return api_response(500, result["msg"])


@ecommerce_bp.route("/products", methods=["GET"])
def list_products():
    """获取商品列表"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    category = request.args.get("category")
    status = request.args.get("status", type=bool)
    keyword = request.args.get("keyword")

    result = ProductService.list_products(
        page=page,
        per_page=per_page,
        category=category,
        status=status,
        keyword=keyword
    )

    return api_response(200, "查询成功", result["data"])


@ecommerce_bp.route("/products/<product_id>", methods=["GET"])
def get_product(product_id):
    """获取商品详情"""
    result = ProductService.get_product(product_id)
    
    if result["success"]:
        return api_response(200, "查询成功", result["data"])
    else:
        return api_response(404, result["msg"])


@ecommerce_bp.route("/products/<product_id>", methods=["PUT"])
@jwt_required
def update_product(product_id):
    """更新商品（需要管理员权限）"""
    data = request.get_json()
    
    result = ProductService.update_product(product_id, **data)
    
    if result["success"]:
        return api_response(200, result["msg"], result["data"])
    else:
        return api_response(404, result["msg"])


@ecommerce_bp.route("/products/<product_id>", methods=["DELETE"])
@jwt_required
def delete_product(product_id):
    """删除商品（软删除）"""
    result = ProductService.delete_product(product_id)
    
    if result["success"]:
        return api_response(200, result["msg"])
    else:
        return api_response(404, result["msg"])


# ==================== 购物车接口 ====================

@ecommerce_bp.route("/cart", methods=["POST"])
@jwt_required
def add_to_cart():
    """添加商品到购物车"""
    data = request.get_json()
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not product_id:
        return api_response(400, "商品ID不能为空")

    user_id = request.user_info.get("user_id")
    result = CartService.add_to_cart(user_id, product_id, quantity)

    if result["success"]:
        return api_response(200, result["msg"], result["data"])
    else:
        return api_response(400, result["msg"])


@ecommerce_bp.route("/cart", methods=["GET"])
@jwt_required
def get_cart():
    """获取购物车列表（IDOR防护：只能查看自己的购物车）"""
    user_id = request.user_info.get("user_id")
    result = CartService.get_user_cart(user_id)
    
    return api_response(200, "查询成功", result["data"])


@ecommerce_bp.route("/cart/<cart_id>", methods=["PUT"])
@jwt_required
def update_cart_item(cart_id):
    """更新购物车项（IDOR防护：只能修改自己的购物车）"""
    data = request.get_json()
    user_id = request.user_info.get("user_id")
    
    result = CartService.update_cart_item(
        user_id,
        cart_id,
        quantity=data.get("quantity"),
        selected=data.get("selected")
    )

    if result["success"]:
        return api_response(200, result["msg"], result["data"])
    else:
        return api_response(400, result["msg"])


@ecommerce_bp.route("/cart/<cart_id>", methods=["DELETE"])
@jwt_required
def remove_from_cart(cart_id):
    """从购物车移除（IDOR防护：只能删除自己的购物车项）"""
    user_id = request.user_info.get("user_id")
    result = CartService.remove_from_cart(user_id, cart_id)

    if result["success"]:
        return api_response(200, result["msg"])
    else:
        return api_response(400, result["msg"])


@ecommerce_bp.route("/cart/clear", methods=["DELETE"])
@jwt_required
def clear_cart():
    """清空购物车（IDOR防护：只能清空自己的购物车）"""
    user_id = request.user_info.get("user_id")
    result = CartService.clear_cart(user_id)

    if result["success"]:
        return api_response(200, result["msg"])
    else:
        return api_response(500, result["msg"])


# ==================== 订单接口 ====================

@ecommerce_bp.route("/orders", methods=["POST"])
@jwt_required
def create_order():
    """从购物车创建订单（IDOR防护：只能为自己的购物车创建订单）"""
    data = request.get_json()
    
    shipping_address = data.get("shipping_address")
    contact_phone = data.get("contact_phone")
    
    if not shipping_address or not contact_phone:
        return api_response(400, "收货地址和联系电话不能为空")

    user_id = request.user_info.get("user_id")
    result = OrderService.create_order_from_cart(
        user_id=user_id,
        shipping_address=shipping_address,
        contact_phone=contact_phone,
        remark=data.get("remark"),
        cart_item_ids=data.get("cart_item_ids")
    )

    if result["success"]:
        return api_response(201, result["msg"], result["data"])
    else:
        return api_response(400, result["msg"])


@ecommerce_bp.route("/orders/<order_id>", methods=["GET"])
@jwt_required
def get_order(order_id):
    """获取订单详情（IDOR防护：只能查看自己的订单）"""
    user_id = request.user_info.get("user_id")
    result = OrderService.get_order(user_id, order_id)

    if result["success"]:
        return api_response(200, "查询成功", result["data"])
    else:
        return api_response(404, result["msg"])


@ecommerce_bp.route("/orders", methods=["GET"])
@jwt_required
def get_user_orders():
    """获取用户订单列表（IDOR防护：只能查看自己的订单）"""
    user_id = request.user_info.get("user_id")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    status = request.args.get("status")

    result = OrderService.get_user_orders(user_id, page, per_page, status)
    
    return api_response(200, "查询成功", result["data"])


@ecommerce_bp.route("/orders/<order_id>/cancel", methods=["POST"])
@jwt_required
def cancel_order(order_id):
    """取消订单（IDOR防护：只能取消自己的订单）"""
    user_id = request.user_info.get("user_id")
    result = OrderService.cancel_order(user_id, order_id)

    if result["success"]:
        return api_response(200, result["msg"])
    else:
        return api_response(400, result["msg"])


@ecommerce_bp.route("/orders/<order_id>/pay", methods=["POST"])
@jwt_required
def pay_order(order_id):
    """支付订单（IDOR防护：只能支付自己的订单）"""
    user_id = request.user_info.get("user_id")
    result = OrderService.pay_order(user_id, order_id)

    if result["success"]:
        return api_response(200, result["msg"])
    else:
        return api_response(400, result["msg"])
