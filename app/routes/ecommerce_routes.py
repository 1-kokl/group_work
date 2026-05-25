# app/routes/ecommerce_routes.py
from flask import Blueprint, jsonify, request
from datetime import datetime
import uuid

# 创建蓝图
ecommerce_bp = Blueprint('ecommerce', __name__, url_prefix='/api/ecommerce')

# --- 模拟数据库 ---
products_db = []
carts_db = {}
orders_db = {}

@ecommerce_bp.route('/test', methods=['GET'])
def test():
    return jsonify({
        "code": 200,
        "msg": "Ecommerce routes loaded successfully"
    })

@ecommerce_bp.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"code": 400, "msg": "缺少商品名称"}), 400
    
    product = {
        "id": str(uuid.uuid4()),
        "name": data.get('name'),
        "price": float(data.get('price', 0)),
        "stock": int(data.get('stock', 0)),
        "description": data.get('description', ''),
        "created_at": datetime.utcnow().isoformat()
    }
    products_db.append(product)
    return jsonify({"code": 201, "msg": "创建成功", "data": product}), 201

@ecommerce_bp.route('/products', methods=['GET'])
def list_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    start = (page - 1) * per_page
    end = start + per_page
    items = products_db[start:end]
    
    return jsonify({
        "code": 200,
        "data": {
            "items": items,
            "total": len(products_db),
            "page": page,
            "per_page": per_page
        }
    }), 200

@ecommerce_bp.route('/cart', methods=['POST'])
def add_to_cart():
    user_id = "test_user_1" 
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return jsonify({"code": 400, "msg": "缺少商品ID"}), 400
    
    if user_id not in carts_db:
        carts_db[user_id] = []
        
    for item in carts_db[user_id]:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            return jsonify({"code": 200, "msg": "购物车更新成功", "data": carts_db[user_id]}), 200
            
    carts_db[user_id].append({"product_id": product_id, "quantity": quantity})
    return jsonify({"code": 200, "msg": "添加成功", "data": carts_db[user_id]}), 200

@ecommerce_bp.route('/orders', methods=['POST'])
def create_order():
    user_id = "test_user_1"
    data = request.get_json()
    
    if user_id not in carts_db or not carts_db[user_id]:
        return jsonify({"code": 400, "msg": "购物车为空"}), 400
    
    total_amount = 0
    order_items = []
    for cart_item in carts_db[user_id]:
        product = next((p for p in products_db if p['id'] == cart_item['product_id']), None)
        if product:
            subtotal = product['price'] * cart_item['quantity']
            total_amount += subtotal
            order_items.append({
                "product_id": product['id'],
                "product_name": product['name'],
                "price": product['price'],
                "quantity": cart_item['quantity'],
                "subtotal": subtotal
            })
    
    if not order_items:
        return jsonify({"code": 400, "msg": "商品不存在"}), 400

    order_id = str(uuid.uuid4())
    order_no = f"ORD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
    
    order = {
        "id": order_id,
        "order_no": order_no,
        "user_id": user_id,
        "items": order_items,
        "total_amount": total_amount,
        "shipping_address": data.get('shipping_address', ''),
        "contact_phone": data.get('contact_phone', ''),
        "remark": data.get('remark', ''),
        "status": "pending",
        "payment_status": "unpaid",
        "transaction_id": None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    orders_db[order_id] = order
    carts_db[user_id] = []
    
    return jsonify({"code": 201, "msg": "订单创建成功", "data": order}), 201

@ecommerce_bp.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    order = orders_db.get(order_id)
    if not order:
        return jsonify({"code": 404, "msg": "订单不存在"}), 404
    
    return jsonify({"code": 200, "data": order}), 200