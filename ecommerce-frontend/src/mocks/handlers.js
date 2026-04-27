/* eslint-disable camelcase */
import { http, HttpResponse } from 'msw';
import { products, categories } from './productMock';
import { cartItems } from './cartMock';
import { orders } from './orderMock';

export const handlers = [
  // ========== Token刷新 ==========
  http.post('/api/v1/auth/refresh', () =>
    HttpResponse.json({
      data: {
        access_token: 'mock-jwt-refreshed',
        refresh_token: 'mock-refresh-refreshed',
        expires_in: 3600
      }
    })
  ),

  // ========== 认证相关 ==========
  http.post('/api/v1/auth/login', async ({ request }) => {
    const body = await request.json();
    const { username, password } = body || {};

    if (username === 'locked@example.com') {
      return HttpResponse.json(
        { code: 'AUTH_LOCKED', message: '账户已被锁定' },
        { status: 403 }
      );
    }

    if (!password || password.length < 1) {
      return HttpResponse.json(
        { code: 'AUTH_INVALID', message: '密码不能为空' },
        { status: 401 }
      );
    }

    return HttpResponse.json({
      token: 'mock-jwt',
      refreshToken: 'mock-refresh',
      expiresIn: 3600,
      csrfToken: 'mock-csrf-token',
      user: {
        id: 'u_001',
        username: username || 'demo',
        roles: ['admin']
      }
    }, {
      status: 200,
      headers: { 'Set-Cookie': 'csrf_token=mock-csrf-token; Path=/' }
    });
  }),

  http.get('/api/v1/user/info', () =>
    HttpResponse.json({
      id: 'u_001',
      username: 'demo',
      email: 'demo@example.com',
      phone: '13800000000',
      roles: ['admin'],
      createdAt: '2024-01-01T00:00:00.000Z'
    })
  ),

  // ========== 注册 ==========
  http.post('/api/v1/users', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      data: {
        id: 'u_' + Date.now(),
        username: body.username,
        createdAt: new Date().toISOString()
      }
    }, { status: 201 });
  }),

  // ========== 登出 ==========
  http.post('/api/v1/auth/logout', () =>
    HttpResponse.json({ message: '登出成功' })
  ),

  // ========== 商品相关 ==========
  http.get('/api/ecommerce/products', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const per_page = parseInt(url.searchParams.get('per_page') || '10');
    const keyword = url.searchParams.get('keyword') || '';
    const category = url.searchParams.get('category') || '';
    const sort = url.searchParams.get('sort') || 'created_desc';

    let filtered = products.filter(p => p.status === 1);

    if (keyword) {
      filtered = filtered.filter(p =>
        p.name.toLowerCase().includes(keyword.toLowerCase()) ||
        p.description.toLowerCase().includes(keyword.toLowerCase())
      );
    }

    if (category) {
      filtered = filtered.filter(p => p.category === category);
    }

    switch (sort) {
      case 'price_asc':
        filtered.sort((a, b) => a.price - b.price);
        break;
      case 'price_desc':
        filtered.sort((a, b) => b.price - a.price);
        break;
      case 'created_desc':
      default:
        filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }

    const total = filtered.length;
    const start = (page - 1) * per_page;
    const end = start + per_page;
    const items = filtered.slice(start, end);

    return HttpResponse.json({
      data: {
        items,
        total,
        page,
        per_page,
        total_pages: Math.ceil(total / per_page)
      }
    });
  }),

  http.get('/api/ecommerce/products/:id', ({ params }) => {
    const { id } = params;
    const product = products.find(p => p.id === parseInt(id));

    if (!product) {
      return HttpResponse.json(
        { code: 'NOT_FOUND', message: '商品不存在' },
        { status: 404 }
      );
    }

    return HttpResponse.json({ data: product });
  }),

  http.post('/api/ecommerce/products', async ({ request }) => {
    const body = await request.json();
    const newProduct = {
      id: products.length + 1,
      ...body,
      status: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    products.push(newProduct);

    return HttpResponse.json({ data: newProduct, message: '商品创建成功' }, { status: 201 });
  }),

  http.put('/api/ecommerce/products/:id', async ({ params, request }) => {
    const { id } = params;
    const body = await request.json();
    const index = products.findIndex(p => p.id === parseInt(id));

    if (index === -1) {
      return HttpResponse.json(
        { code: 'NOT_FOUND', message: '商品不存在' },
        { status: 404 }
      );
    }

    products[index] = {
      ...products[index],
      ...body,
      updated_at: new Date().toISOString()
    };

    return HttpResponse.json({ data: products[index], message: '商品更新成功' });
  }),

  http.delete('/api/ecommerce/products/:id', ({ params }) => {
    const { id } = params;
    const index = products.findIndex(p => p.id === parseInt(id));

    if (index === -1) {
      return HttpResponse.json(
        { code: 'NOT_FOUND', message: '商品不存在' },
        { status: 404 }
      );
    }

    products.splice(index, 1);

    return HttpResponse.json({ message: '商品删除成功' });
  }),

  http.get('/api/ecommerce/categories', () =>
    HttpResponse.json({ data: categories })
  ),

  // ========== 购物车相关 ==========
  http.get('/api/ecommerce/cart', () => {
    const totalAmount = cartItems
      .filter(item => item.selected)
      .reduce((sum, item) => sum + item.product.price * item.quantity, 0);
    const selectedCount = cartItems.filter(item => item.selected).length;

    return HttpResponse.json({
      data: {
        items: cartItems,
        total_amount: totalAmount,
        selected_count: selectedCount
      }
    });
  }),

  http.post('/api/ecommerce/cart/add', async ({ request }) => {
    const body = await request.json();
    const { product_id, quantity } = body || {};
    const product = products.find(p => p.id === product_id);

    if (!product) {
      return HttpResponse.json(
        { code: 'NOT_FOUND', message: '商品不存在' },
        { status: 404 }
      );
    }

    const existingItem = cartItems.find(item => item.product_id === product_id);
    if (existingItem) {
      existingItem.quantity += quantity;
      existingItem.updated_at = new Date().toISOString();
      return HttpResponse.json({ data: existingItem, message: '购物车数量已更新' });
    }

    const newItem = {
      id: cartItems.length + 1,
      user_id: 'u_001',
      product_id,
      quantity,
      selected: true,
      product,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    cartItems.push(newItem);

    return HttpResponse.json({ data: newItem, message: '已加入购物车' }, { status: 201 });
  }),

  http.put('/api/ecommerce/cart/:id', async ({ params, request }) => {
    const { id } = params;
    const { quantity } = await request.json();
    const item = cartItems.find(item => item.id === parseInt(id));

    if (!item) {
      return HttpResponse.json(
        { code: 'NOT_FOUND', message: '购物车项不存在' },
        { status: 404 }
      );
    }

    item.quantity = quantity;
    item.updated_at = new Date().toISOString();

    return HttpResponse.json({ data: item, message: '数量已更新' });
  }),

  http.delete('/api/ecommerce/cart/:id', ({ params }) => {
    const { id } = params;
    const index = cartItems.findIndex(item => item.id === parseInt(id));

    if (index === -1) {
      return HttpResponse.json(
        { code: 'NOT_FOUND', message: '购物车项不存在' },
        { status: 404 }
      );
    }

    cartItems.splice(index, 1);

    return HttpResponse.json({ message: '已从购物车移除' });
  }),

  http.delete('/api/ecommerce/cart/clear', () => {
    cartItems.length = 0;
    return HttpResponse.json({ message: '购物车已清空' });
  }),

  http.post('/api/ecommerce/cart/batch-delete', async ({ request }) => {
    const { ids } = await request.json();
    const idsToDelete = ids.map(id => parseInt(id));

    for (let i = cartItems.length - 1; i >= 0; i--) {
      if (idsToDelete.includes(cartItems[i].id)) {
        cartItems.splice(i, 1);
      }
    }

    return HttpResponse.json({ message: '已批量删除' });
  }),

  // ========== 订单相关 ==========
  http.get('/api/ecommerce/orders', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const per_page = parseInt(url.searchParams.get('per_page') || '10');
    const status = url.searchParams.get('status') || '';

    let filtered = [...orders];

    if (status) {
      filtered = filtered.filter(o => o.status === status);
    }

    filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    const total = filtered.length;
    const start = (page - 1) * per_page;
    const end = start + per_page;
    const items = filtered.slice(start, end);

    return HttpResponse.json({
      data: {
        items,
        total,
        page,
        per_page,
        total_pages: Math.ceil(total / per_page)
      }
    });
  }),

  http.get('/api/ecommerce/orders/:id', ({ params }) => {
    const { id } = params;
    const order = orders.find(o => o.id === parseInt(id));

    if (!order) {
      return HttpResponse.json(
        { code: 'NOT_FOUND', message: '订单不存在' },
        { status: 404 }
      );
    }

    return HttpResponse.json({ data: order });
  }),

  http.post('/api/ecommerce/orders', async ({ request }) => {
    const { cart_item_ids } = await request.json();
    // 只选择传入的 cart_item_ids 对应的商品（同时检查 selected 状态）
    const selectedItems = cartItems.filter(
      item => cart_item_ids.includes(item.id) && item.selected
    );

    if (selectedItems.length === 0) {
      return HttpResponse.json(
        { code: 'INVALID_CART', message: '请选择要结算的商品' },
        { status: 400 }
      );
    }

    const totalAmount = selectedItems.reduce(
      (sum, item) => sum + item.product.price * item.quantity, 0
    );

    const newOrder = {
      id: orders.length + 1,
      order_no: `DD${new Date().getTime()}`,
      user_id: 'u_001',
      status: 'pending',
      status_text: '待支付',
      total_amount: totalAmount,
      total_amount_display: (totalAmount / 100).toFixed(2),
      item_count: selectedItems.length,
      created_at: new Date().toISOString(),
      paid_at: null,
      shipped_at: null,
      completed_at: null,
      items: selectedItems.map((item, index) => ({
        id: index + 1,
        product_id: item.product_id,
        product_name: item.product.name,
        price: item.product.price,
        quantity: item.quantity,
        subtotal: item.product.price * item.quantity,
        product: item.product
      }))
    };

    orders.unshift(newOrder);

    return HttpResponse.json({ data: newOrder, message: '订单创建成功' }, { status: 201 });
  }),

  http.post('/api/ecommerce/orders/:id/cancel', ({ params }) => {
    const { id } = params;
    const order = orders.find(o => o.id === parseInt(id));

    if (!order) {
      return HttpResponse.json(
        { code: 'NOT_FOUND', message: '订单不存在' },
        { status: 404 }
      );
    }

    if (order.status !== 'pending') {
      return HttpResponse.json(
        { code: 'INVALID_STATUS', message: '只能取消待支付的订单' },
        { status: 400 }
      );
    }

    order.status = 'cancelled';
    order.status_text = '已取消';
    order.cancelled_at = new Date().toISOString();

    return HttpResponse.json({ data: order, message: '订单已取消' });
  }),

  http.post('/api/ecommerce/orders/:id/pay', ({ params }) => {
    const { id } = params;
    const order = orders.find(o => o.id === parseInt(id));

    if (!order) {
      return HttpResponse.json(
        { code: 'NOT_FOUND', message: '订单不存在' },
        { status: 404 }
      );
    }

    if (order.status !== 'pending') {
      return HttpResponse.json(
        { code: 'INVALID_STATUS', message: '订单状态不允许支付' },
        { status: 400 }
      );
    }

    order.status = 'paid';
    order.status_text = '已支付';
    order.paid_at = new Date().toISOString();

    return HttpResponse.json({ data: order, message: '支付成功' });
  }),

  http.post('/api/ecommerce/orders/:id/confirm', ({ params }) => {
    const { id } = params;
    const order = orders.find(o => o.id === parseInt(id));

    if (!order) {
      return HttpResponse.json(
        { code: 'NOT_FOUND', message: '订单不存在' },
        { status: 404 }
      );
    }

    if (order.status !== 'shipped') {
      return HttpResponse.json(
        { code: 'INVALID_STATUS', message: '只能确认已发货的订单' },
        { status: 400 }
      );
    }

    order.status = 'completed';
    order.status_text = '已完成';
    order.completed_at = new Date().toISOString();

    return HttpResponse.json({ data: order, message: '确认收货成功' });
  })
];
