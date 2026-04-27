"""
电商模块API路由
包含：商品管理、购物车、订单管理
"""
from flask import Blueprint, request
from app.utils.response import api_response
from app.middleware.jwt_auth import jwt_required
from app.services.ecommerce_service import ProductService, CartService, OrderService
from app.models.ecommerce_models import Product, Cart, Order

ecommerce_bp = Blueprint("ecommerce", __name__, url_prefix="/api/ecommerce")


# ==================== 商品管理接口 ====================

@ecommerce_bp.route("/categories", methods=["GET"])
def get_categories():
    """
    获取商品分类列表
    """
    try:
        categories = [
            {"id": "electronics", "name": "电子产品"},
            {"id": "clothing", "name": "服装"},
            {"id": "food", "name": "食品"},
            {"id": "books", "name": "图书"},
            {"id": "home", "name": "家居"},
            {"id": "beauty", "name": "美妆"},
            {"id": "sports", "name": "运动"},
            {"id": "toys", "name": "玩具"}
        ]
        return api_response(200, "获取分类成功", categories)
    except Exception as e:
        return api_response(500, f"获取分类失败: {str(e)}")


@ecommerce_bp.route("/products", methods=["GET"])
def list_products():
    """
    获取商品列表
    ---
    查询参数:
        page: 页码(默认1)
        per_page: 每页数量(默认10)
        category: 商品分类(可选)
        keyword: 搜索关键词(可选)
        sort_by: 排序方式(可选: price_asc, price_desc)
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        category = request.args.get("category")
        keyword = request.args.get("keyword")
        sort_by = request.args.get("sort_by")

        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10

        result = ProductService.list_products(
            page=page,
            per_page=per_page,
            category=category,
            status=True,
            keyword=keyword
        )

        if not result.get("success"):
            return api_response(500, result.get("msg", "获取商品列表失败"))

        data = result["data"]

        items = data["items"]
        if sort_by == "price_asc":
            items = sorted(items, key=lambda x: x.get("price", 0))
        elif sort_by == "price_desc":
            items = sorted(items, key=lambda x: x.get("price", 0), reverse=True)

        data["items"] = items

        return api_response(200, "获取商品列表成功", data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_response(500, f"获取商品列表失败: {str(e)}")


@ecommerce_bp.route("/products/<product_id>", methods=["GET"])
def get_product(product_id):
    """
    获取商品详情
    ---
    参数:
        product_id: 商品ID
    """
    result = ProductService.get_product(product_id)

    if not result.get("success"):
        return api_response(404, result.get("msg", "商品不存在"))

    product = result["data"]
    if not product.get("status"):
        return api_response(404, "商品不存在或已下架")

    return api_response(200, "获取商品详情成功", product)


@ecommerce_bp.route("/products", methods=["POST"])
@jwt_required
def create_product():
    """
    发布商品
    ---
    需要JWT认证
    请求体:
        name: 商品名称(必填)
        price: 价格(必填, 单位: 分)
        stock: 库存(必填)
        description: 商品描述
        category: 商品分类
        image_url: 商品图片URL
    """
    data = request.get_json()

    name = data.get("name")
    price = data.get("price")
    stock = data.get("stock")
    description = data.get("description")
    category = data.get("category")
    image_url = data.get("image_url")

    if not name:
        return api_response(400, "商品名称不能为空")

    if price is None:
        return api_response(400, "商品价格不能为空")

    if stock is None:
        return api_response(400, "库存数量不能为空")

    try:
        price = int(price)
        stock = int(stock)
    except (ValueError, TypeError):
        return api_response(400, "价格和库存必须是数字")

    if price <= 0:
        return api_response(400, "商品价格必须大于0")

    if stock < 0:
        return api_response(400, "库存数量不能为负数")

    current_user_id = request.user_info.get("user_id")

    result = ProductService.create_product(
        name=name,
        price=price,
        description=description,
        stock=stock,
        category=category,
        image_url=image_url,
        created_by=current_user_id
    )

    if not result.get("success"):
        return api_response(500, result.get("msg", "商品创建失败"))

    return api_response(201, "商品发布成功", result["data"])


@ecommerce_bp.route("/products/<product_id>", methods=["PUT"])
@jwt_required
def update_product(product_id):
    """
    编辑商品
    ---
    需要JWT认证
    IDOR防护: 验证当前用户是否为商品所有者
    请求体:
        price: 价格(可选)
        stock: 库存(可选)
        description: 商品描述(可选)
        category: 商品分类(可选)
        image_url: 商品图片URL(可选)
    """
    product = Product.query.get(product_id)
    if not product:
        return api_response(404, "商品不存在")

    current_user_id = request.user_info.get("user_id")
    if product.created_by != current_user_id:
        return api_response(403, "无权编辑此商品")

    data = request.get_json()
    updates = {}

    if "price" in data:
        try:
            price = int(data["price"])
            if price < 0:
                return api_response(400, "价格不能为负数")
            updates["price"] = price
        except (ValueError, TypeError):
            return api_response(400, "价格必须是数字")

    if "stock" in data:
        try:
            stock = int(data["stock"])
            if stock < 0:
                return api_response(400, "库存不能为负数")
            updates["stock"] = stock
        except (ValueError, TypeError):
            return api_response(400, "库存必须是数字")

    if "description" in data:
        updates["description"] = data["description"]

    if "category" in data:
        updates["category"] = data["category"]

    if "image_url" in data:
        updates["image_url"] = data["image_url"]

    if not updates:
        return api_response(400, "没有需要更新的字段")

    result = ProductService.update_product(product_id, **updates)

    if not result.get("success"):
        return api_response(500, result.get("msg", "商品更新失败"))

    return api_response(200, "商品更新成功", result["data"])


@ecommerce_bp.route("/products/<product_id>", methods=["DELETE"])
@jwt_required
def delete_product(product_id):
    """
    下架商品(软删除)
    ---
    需要JWT认证
    IDOR防护: 验证当前用户是否为商品所有者
    """
    product = Product.query.get(product_id)
    if not product:
        return api_response(404, "商品不存在")

    current_user_id = request.user_info.get("user_id")
    if product.created_by != current_user_id:
        return api_response(403, "无权下架此商品")

    result = ProductService.delete_product(product_id)

    if not result.get("success"):
        return api_response(500, result.get("msg", "商品下架失败"))

    return api_response(200, "商品已下架")


# ==================== 购物车接口 ====================

@ecommerce_bp.route("/cart/add", methods=["POST"])
@jwt_required
def add_to_cart():
    """
    添加商品到购物车
    ---
    需要JWT认证
    请求体:
        product_id: 商品ID(必填)
        quantity: 数量(必填, 默认1)
    """
    data = request.get_json()

    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not product_id:
        return api_response(400, "商品ID不能为空")

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return api_response(400, "数量必须是数字")

    if quantity <= 0:
        return api_response(400, "数量必须大于0")

    current_user_id = request.user_info.get("user_id")

    result = CartService.add_to_cart(current_user_id, product_id, quantity)

    if not result.get("success"):
        return api_response(400, result.get("msg", "添加购物车失败"))

    return api_response(200, "添加成功", result["data"])


@ecommerce_bp.route("/cart", methods=["POST"])


@ecommerce_bp.route("/cart", methods=["GET"])
@jwt_required
def get_cart():
    """
    查看购物车
    ---
    需要JWT认证
    IDOR防护: 只返回当前用户的购物车数据
    """
    current_user_id = request.user_info.get("user_id")
    result = CartService.get_user_cart(current_user_id)

    if not result.get("success"):
        return api_response(500, result.get("msg", "获取购物车失败"))

    return api_response(200, "获取购物车成功", {
        "items": result.get("data", []),
        "total_items": result.get("total", 0)
    })


@ecommerce_bp.route("/cart/<cart_item_id>", methods=["PUT"])
@jwt_required
def update_cart_item(cart_item_id):
    """
    修改购物车商品数量
    ---
    需要JWT认证
    IDOR防护: 验证当前用户是否为购物车项所有者
    请求体:
        quantity: 新数量
    """
    cart_item = Cart.query.get(cart_item_id)
    if not cart_item:
        return api_response(404, "购物车项不存在")

    current_user_id = request.user_info.get("user_id")
    if cart_item.user_id != current_user_id:
        return api_response(403, "无权操作此购物车项")

    data = request.get_json()
    quantity = data.get("quantity")

    if quantity is None:
        return api_response(400, "数量不能为空")

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return api_response(400, "数量必须是数字")

    if quantity <= 0:
        return api_response(400, "数量必须大于0")

    result = CartService.update_cart_item(current_user_id, cart_item_id, quantity=quantity)

    if not result.get("success"):
        return api_response(400, result.get("msg", "更新失败"))

    return api_response(200, "更新成功", result["data"])


@ecommerce_bp.route("/cart/<cart_item_id>", methods=["DELETE"])
@jwt_required
def remove_from_cart(cart_item_id):
    """
    删除购物车商品
    ---
    需要JWT认证
    IDOR防护: 验证当前用户是否为购物车项所有者
    """
    cart_item = Cart.query.get(cart_item_id)
    if not cart_item:
        return api_response(404, "购物车项不存在")

    current_user_id = request.user_info.get("user_id")
    if cart_item.user_id != current_user_id:
        return api_response(403, "无权操作此购物车项")

    result = CartService.remove_from_cart(current_user_id, cart_item_id)

    if not result.get("success"):
        return api_response(400, result.get("msg", "移除失败"))

    return api_response(200, "移除成功")


@ecommerce_bp.route("/cart/batch-delete", methods=["POST"])
@jwt_required
def batch_delete_cart():
    """
    批量删除购物车商品
    ---
    需要JWT认证
    请求体: { ids: [...] }
    """
    data = request.get_json()
    ids = data.get("ids", [])

    if not ids:
        return api_response(400, "请选择要删除的商品")

    current_user_id = request.user_info.get("user_id")
    result = CartService.batch_delete(current_user_id, ids)

    if not result.get("success"):
        return api_response(400, result.get("msg", "删除失败"))

    return api_response(200, "批量删除成功")


@ecommerce_bp.route("/cart", methods=["DELETE"])
@jwt_required
def clear_cart():
    """
    清空购物车
    ---
    需要JWT认证
    IDOR防护: 只清空当前用户的购物车
    """
    current_user_id = request.user_info.get("user_id")
    result = CartService.clear_cart(current_user_id)

    if not result.get("success"):
        return api_response(500, result.get("msg", "清空失败"))

    return api_response(200, "购物车已清空")


# ==================== 订单管理接口 ====================

@ecommerce_bp.route("/orders", methods=["POST"])
@jwt_required
def create_order():
    """
    从购物车生成订单
    ---
    需要JWT认证
    请求体:
        shipping_address: 收货地址(必填)
        contact_phone: 联系电话(必填)
        remark: 订单备注(可选)
        cart_item_ids: 购物车项ID列表(可选，不传则使用所有选中的商品)
    """
    data = request.get_json()

    shipping_address = data.get("shipping_address")
    contact_phone = data.get("contact_phone")
    remark = data.get("remark")
    cart_item_ids = data.get("cart_item_ids")

    if not shipping_address:
        return api_response(400, "收货地址不能为空")

    if not contact_phone:
        return api_response(400, "联系电话不能为空")

    current_user_id = request.user_info.get("user_id")

    result = OrderService.create_order_from_cart(
        user_id=current_user_id,
        shipping_address=shipping_address,
        contact_phone=contact_phone,
        remark=remark,
        cart_item_ids=cart_item_ids
    )

    if not result.get("success"):
        return api_response(400, result.get("msg", "订单创建失败"))

    return api_response(201, "订单创建成功", result["data"])


@ecommerce_bp.route("/orders", methods=["GET"])
@jwt_required
def list_orders():
    """
    查看订单列表
    ---
    需要JWT认证
    IDOR防护: 只返回当前用户的订单
    查询参数:
        page: 页码(默认1)
        per_page: 每页数量(默认10)
        status: 订单状态(可选: pending, paid, shipped, completed, cancelled)
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    status = request.args.get("status")

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 10

    current_user_id = request.user_info.get("user_id")

    result = OrderService.get_user_orders(
        user_id=current_user_id,
        page=page,
        per_page=per_page,
        status=status
    )

    if not result.get("success"):
        return api_response(500, result.get("msg", "获取订单列表失败"))

    return api_response(200, "获取订单列表成功", result["data"])


@ecommerce_bp.route("/orders/<order_id>", methods=["GET"])
@jwt_required
def get_order(order_id):
    """
    查看订单详情
    ---
    需要JWT认证
    IDOR防护: 验证当前用户是否为订单所有者
    """
    current_user_id = request.user_info.get("user_id")
    result = OrderService.get_order(current_user_id, order_id)

    if not result.get("success"):
        msg = result.get("msg", "订单不存在")
        if "不存在" in msg or "无权" in msg:
            return api_response(403, msg)
        return api_response(404, msg)

    return api_response(200, "获取订单详情成功", result["data"])


@ecommerce_bp.route("/orders/<order_id>/cancel", methods=["PUT"])
@jwt_required
def cancel_order(order_id):
    """
    取消订单
    ---
    需要JWT认证
    IDOR防护: 验证当前用户是否为订单所有者
    """
    current_user_id = request.user_info.get("user_id")
    result = OrderService.cancel_order(current_user_id, order_id)

    if not result.get("success"):
        msg = result.get("msg", "取消失败")
        if "不存在" in msg:
            return api_response(404, msg)
        if "无权" in msg:
            return api_response(403, msg)
        return api_response(400, msg)

    return api_response(200, "订单已取消")


@ecommerce_bp.route("/orders/<order_id>/pay", methods=["POST"])
@jwt_required
def pay_order(order_id):
    """
    支付订单
    ---
    需要JWT认证
    IDOR防护: 验证当前用户是否为订单所有者
    """
    current_user_id = request.user_info.get("user_id")
    result = OrderService.pay_order(current_user_id, order_id)

    if not result.get("success"):
        msg = result.get("msg", "支付失败")
        if "不存在" in msg:
            return api_response(404, msg)
        if "无权" in msg:
            return api_response(403, msg)
        return api_response(400, msg)

    return api_response(200, "支付成功")


@ecommerce_bp.route("/orders/<order_id>/confirm", methods=["POST"])
@jwt_required
def confirm_order(order_id):
    """
    确认收货
    ---
    需要JWT认证
    IDOR防护: 验证当前用户是否为订单所有者
    """
    current_user_id = request.user_info.get("user_id")
    result = OrderService.confirm_receipt(current_user_id, order_id)

    if not result.get("success"):
        msg = result.get("msg", "确认收货失败")
        if "不存在" in msg:
            return api_response(404, msg)
        if "无权" in msg:
            return api_response(403, msg)
        return api_response(400, msg)

    return api_response(200, "确认收货成功")
