"""
电商模块交互式演示
通过菜单选择操作，实时查看后端响应
"""
from app import create_app, db
from app.models.ecommerce_models import Product, Cart, Order, OrderItem
from app.services.ecommerce_service import ProductService, CartService, OrderService


def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(result, title="结果"):
    """打印操作结果"""
    print(f"\n{title}:")
    if result.get('success'):
        print(f"  ✅ {result.get('msg', '成功')}")
        if 'data' in result:
            data = result['data']
            if isinstance(data, dict):
                for key, value in data.items():
                    if key not in ['items']:
                        print(f"     {key}: {value}")
            elif isinstance(data, list):
                print(f"     共 {len(data)} 条记录")
    else:
        print(f"  ❌ {result.get('msg', '失败')}")


def demo_product_management(app_ctx):
    """商品管理演示"""
    while True:
        print_section("📦 商品管理")
        print("1. 创建商品")
        print("2. 查看所有商品")
        print("3. 查看商品详情")
        print("4. 更新商品")
        print("5. 删除商品（下架）")
        print("6. 搜索商品")
        print("0. 返回主菜单")
        
        choice = input("\n请选择操作 (0-6): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            # 创建商品
            print("\n--- 创建新商品 ---")
            name = input("商品名称: ").strip()
            if not name:
                print("❌ 名称不能为空")
                continue
            
            try:
                price = float(input("商品价格: ").strip())
            except:
                print("❌ 价格格式错误")
                continue
            
            try:
                stock = int(input("库存数量: ").strip())
            except:
                print("❌ 库存格式错误")
                continue
            
            category = input("商品分类 (手机/电脑/耳机/平板/手表): ").strip() or "其他"
            description = input("商品描述: ").strip()
            
            result = ProductService.create_product(
                name=name,
                price=price,
                description=description,
                stock=stock,
                category=category
            )
            print_result(result, "创建结果")
            
        elif choice == '2':
            # 查看所有商品
            page = input("页码 (默认1): ").strip() or 1
            per_page = input("每页数量 (默认10): ").strip() or 10
            
            result = ProductService.list_products(page=int(page), per_page=int(per_page))
            print_result(result, f"商品列表 (第{page}页)")
            
            if result.get('success') and result['data']['items']:
                print("\n详细列表:")
                for i, product in enumerate(result['data']['items'], 1):
                    status = "✅上架" if product['status'] else "❌下架"
                    print(f"  {i}. [{product['id'][:8]}...] {product['name']}")
                    print(f"     价格: ¥{product['price']} | 库存: {product['stock']} | 分类: {product['category']} | {status}")
                    
        elif choice == '3':
            # 查看商品详情
            product_id = input("商品ID: ").strip()
            if not product_id:
                print("❌ ID不能为空")
                continue
            
            result = ProductService.get_product(product_id)
            print_result(result, "商品详情")
            
        elif choice == '4':
            # 更新商品
            product_id = input("商品ID: ").strip()
            if not product_id:
                print("❌ ID不能为空")
                continue
            
            print("\n输入要更新的字段（直接回车跳过）:")
            updates = {}
            
            name = input("新名称: ").strip()
            if name:
                updates['name'] = name
            
            price = input("新价格: ").strip()
            if price:
                try:
                    updates['price'] = float(price)
                except:
                    print("❌ 价格格式错误")
                    continue
            
            stock = input("新库存: ").strip()
            if stock:
                try:
                    updates['stock'] = int(stock)
                except:
                    print("❌ 库存格式错误")
                    continue
            
            if not updates:
                print("❌ 没有提供任何更新内容")
                continue
            
            result = ProductService.update_product(product_id, **updates)
            print_result(result, "更新结果")
            
        elif choice == '5':
            # 删除商品
            product_id = input("商品ID: ").strip()
            confirm = input(f"确定要下架商品 {product_id} 吗？(y/n): ").strip().lower()
            
            if confirm == 'y':
                result = ProductService.delete_product(product_id)
                print_result(result, "删除结果")
            else:
                print("已取消")
                
        elif choice == '6':
            # 搜索商品
            keyword = input("搜索关键词: ").strip()
            category = input("分类 (可选): ").strip()
            
            result = ProductService.list_products(keyword=keyword, category=category if category else None)
            print_result(result, f"搜索结果 (关键词: {keyword})")
            
            if result.get('success') and result['data']['items']:
                for i, product in enumerate(result['data']['items'], 1):
                    print(f"  {i}. {product['name']} - ¥{product['price']}")
        else:
            print("❌ 无效选择")


def demo_cart_management(app_ctx, user_id=1):
    """购物车管理演示"""
    while True:
        print_section("🛒 购物车管理")
        print(f"当前用户ID: {user_id}")
        print("1. 查看购物车")
        print("2. 添加商品到购物车")
        print("3. 修改商品数量")
        print("4. 移除商品")
        print("5. 清空购物车")
        print("0. 返回主菜单")
        
        choice = input("\n请选择操作 (0-5): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            # 查看购物车
            result = CartService.get_user_cart(user_id)
            print_result(result, "购物车内容")
            
            if result.get('success') and result['data']:
                total = 0
                print("\n购物车明细:")
                for item in result['data']:
                    subtotal = item['subtotal']
                    total += subtotal
                    print(f"  - {item['product_name']}")
                    print(f"    数量: {item['quantity']} x ¥{item['product_price']} = ¥{subtotal}")
                print(f"\n💰 总计: ¥{total:.2f}")
                
        elif choice == '2':
            # 添加商品
            product_id = input("商品ID: ").strip()
            if not product_id:
                print("❌ ID不能为空")
                continue
            
            try:
                quantity = int(input("数量 (默认1): ").strip() or 1)
            except:
                print("❌ 数量格式错误")
                continue
            
            result = CartService.add_to_cart(user_id, product_id, quantity)
            print_result(result, "添加结果")
            
        elif choice == '3':
            # 先查看购物车获取cart_id
            cart_result = CartService.get_user_cart(user_id)
            if not cart_result.get('success') or not cart_result['data']:
                print("❌ 购物车为空")
                continue
            
            print("\n当前购物车:")
            for item in cart_result['data']:
                print(f"  ID: {item['id'][:8]}... | {item['product_name']} x {item['quantity']}")
            
            cart_id = input("\n购物车项ID: ").strip()
            try:
                quantity = int(input("新数量: ").strip())
            except:
                print("❌ 数量格式错误")
                continue
            
            result = CartService.update_cart_item(user_id, cart_id, quantity=quantity)
            print_result(result, "更新结果")
            
        elif choice == '4':
            # 移除商品
            cart_result = CartService.get_user_cart(user_id)
            if not cart_result.get('success') or not cart_result['data']:
                print("❌ 购物车为空")
                continue
            
            print("\n当前购物车:")
            for item in cart_result['data']:
                print(f"  ID: {item['id'][:8]}... | {item['product_name']}")
            
            cart_id = input("\n要移除的购物车项ID: ").strip()
            confirm = input("确定移除？(y/n): ").strip().lower()
            
            if confirm == 'y':
                result = CartService.remove_from_cart(user_id, cart_id)
                print_result(result, "移除结果")
            else:
                print("已取消")
                
        elif choice == '5':
            # 清空购物车
            confirm = input("确定要清空购物车吗？(y/n): ").strip().lower()
            if confirm == 'y':
                result = CartService.clear_cart(user_id)
                print_result(result, "清空结果")
            else:
                print("已取消")
        else:
            print("❌ 无效选择")


def demo_order_management(app_ctx, user_id=1):
    """订单管理演示"""
    while True:
        print_section("📋 订单管理")
        print(f"当前用户ID: {user_id}")
        print("1. 创建订单（从购物车）")
        print("2. 查看我的订单")
        print("3. 查看订单详情")
        print("4. 支付订单")
        print("5. 取消订单")
        print("0. 返回主菜单")
        
        choice = input("\n请选择操作 (0-5): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            # 创建订单
            print("\n--- 创建订单 ---")
            
            # 先查看购物车
            cart_result = CartService.get_user_cart(user_id)
            if not cart_result.get('success') or not cart_result['data']:
                print("❌ 购物车为空，请先添加商品")
                continue
            
            print("\n购物车内容:")
            total = 0
            for item in cart_result['data']:
                subtotal = item['subtotal']
                total += subtotal
                print(f"  - {item['product_name']} x {item['quantity']} = ¥{subtotal}")
            print(f"\n总计: ¥{total:.2f}")
            
            shipping_address = input("\n收货地址: ").strip()
            if not shipping_address:
                print("❌ 地址不能为空")
                continue
            
            contact_phone = input("联系电话: ").strip()
            if not contact_phone:
                print("❌ 电话不能为空")
                continue
            
            remark = input("备注 (可选): ").strip()
            
            result = OrderService.create_order_from_cart(
                user_id=user_id,
                shipping_address=shipping_address,
                contact_phone=contact_phone,
                remark=remark
            )
            print_result(result, "订单创建结果")
            
            if result.get('success'):
                print(f"\n🎉 订单号: {result['data']['order_no']}")
                print(f"💰 订单金额: ¥{result['data']['total_amount']}")
                
        elif choice == '2':
            # 查看订单列表
            result = OrderService.get_user_orders(user_id)
            print_result(result, "我的订单")
            
            if result.get('success') and result['data']['items']:
                print("\n订单列表:")
                for order in result['data']['items']:
                    status_map = {
                        'pending': '⏳待支付',
                        'paid': '✅已支付',
                        'cancelled': '❌已取消'
                    }
                    status = status_map.get(order['status'], order['status'])
                    print(f"  📦 {order['order_no']}")
                    print(f"     金额: ¥{order['total_amount']} | 状态: {status}")
                    print(f"     下单时间: {order['created_at']}")
                    print()
                    
        elif choice == '3':
            # 查看订单详情
            order_id = input("订单ID: ").strip()
            result = OrderService.get_order(user_id, order_id)
            print_result(result, "订单详情")
            
            if result.get('success'):
                order = result['data']
                print(f"\n订单号: {order['order_no']}")
                print(f"总金额: ¥{order['total_amount']}")
                print(f"状态: {order['status']}")
                print(f"收货地址: {order['shipping_address']}")
                print(f"联系电话: {order['contact_phone']}")
                print(f"\n商品明细:")
                for item in order['items']:
                    print(f"  - {item['product_name']} x {item['quantity']} = ¥{item['subtotal']}")
                    
        elif choice == '4':
            # 支付订单
            order_id = input("订单ID: ").strip()
            confirm = input(f"确定支付订单 {order_id} 吗？(y/n): ").strip().lower()
            
            if confirm == 'y':
                result = OrderService.pay_order(user_id, order_id)
                print_result(result, "支付结果")
            else:
                print("已取消")
                
        elif choice == '5':
            # 取消订单
            order_id = input("订单ID: ").strip()
            confirm = input(f"确定取消订单 {order_id} 吗？(y/n): ").strip().lower()
            
            if confirm == 'y':
                result = OrderService.cancel_order(user_id, order_id)
                print_result(result, "取消结果")
            else:
                print("已取消")
        else:
            print("❌ 无效选择")


def main_menu():
    """主菜单"""
    app = create_app()
    
    with app.app_context():
        # 初始化数据库
        print_section("🚀 电商系统演示")
        print("正在初始化数据库...")
        db.create_all()
        print("✅ 数据库就绪\n")
        
        while True:
            print_section("🏪 电商系统 - 主菜单")
            print("1. 📦 商品管理（增删改查）")
            print("2. 🛒 购物车管理")
            print("3. 📋 订单管理")
            print("0. 退出系统")
            
            choice = input("\n请选择功能模块 (0-3): ").strip()
            
            if choice == '0':
                print("\n👋 感谢使用，再见！\n")
                break
            elif choice == '1':
                demo_product_management(app)
            elif choice == '2':
                demo_cart_management(app)
            elif choice == '3':
                demo_order_management(app)
            else:
                print("❌ 无效选择，请重新输入")


if __name__ == "__main__":
    main_menu()
