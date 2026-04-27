import { products } from './productMock';

const orders = [
  {
    id: 1,
    order_no: 'DD202403200001',
    user_id: 'u_001',
    status: 'completed',
    status_text: '已完成',
    total_amount: 799800,
    total_amount_display: '7998.00',
    item_count: 2,
    created_at: '2024-03-20T10:30:00Z',
    paid_at: '2024-03-20T10:35:00Z',
    shipped_at: '2024-03-21T09:00:00Z',
    completed_at: '2024-03-23T14:00:00Z',
    items: [
      {
        id: 1,
        product_id: 1,
        product_name: products[0].name,
        price: products[0].price,
        quantity: 1,
        subtotal: products[0].price,
        product: products[0]
      },
      {
        id: 2,
        product_id: 3,
        product_name: products[2].name,
        price: products[2].price,
        quantity: 1,
        subtotal: products[2].price,
        product: products[2]
      }
    ]
  },
  {
    id: 2,
    order_no: 'DD202403190002',
    user_id: 'u_001',
    status: 'shipped',
    status_text: '已发货',
    total_amount: 299700,
    total_amount_display: '2997.00',
    item_count: 1,
    created_at: '2024-03-19T15:20:00Z',
    paid_at: '2024-03-19T15:25:00Z',
    shipped_at: '2024-03-20T10:00:00Z',
    completed_at: null,
    items: [
      {
        id: 3,
        product_id: 8,
        product_name: products[7].name,
        price: products[7].price,
        quantity: 1,
        subtotal: products[7].price,
        product: products[7]
      }
    ]
  },
  {
    id: 3,
    order_no: 'DD202403180003',
    user_id: 'u_001',
    status: 'paid',
    status_text: '已支付',
    total_amount: 296640,
    total_amount_display: '2966.40',
    item_count: 3,
    created_at: '2024-03-18T09:45:00Z',
    paid_at: '2024-03-18T09:50:00Z',
    shipped_at: null,
    completed_at: null,
    items: [
      {
        id: 4,
        product_id: 5,
        product_name: products[4].name,
        price: products[4].price,
        quantity: 3,
        subtotal: products[4].price * 3,
        product: products[4]
      }
    ]
  },
  {
    id: 4,
    order_no: 'DD202403170004',
    user_id: 'u_001',
    status: 'pending',
    status_text: '待支付',
    total_amount: 1234899,
    total_amount_display: '12348.99',
    item_count: 2,
    created_at: '2024-03-17T14:10:00Z',
    paid_at: null,
    shipped_at: null,
    completed_at: null,
    items: [
      {
        id: 5,
        product_id: 2,
        product_name: products[1].name,
        price: products[1].price,
        quantity: 1,
        subtotal: products[1].price,
        product: products[1]
      }
    ]
  },
  {
    id: 5,
    order_no: 'DD202403150005',
    user_id: 'u_001',
    status: 'cancelled',
    status_text: '已取消',
    total_amount: 89900,
    total_amount_display: '899.00',
    item_count: 1,
    created_at: '2024-03-15T11:25:00Z',
    paid_at: null,
    shipped_at: null,
    completed_at: null,
    cancelled_at: '2024-03-15T12:00:00Z',
    items: [
      {
        id: 6,
        product_id: 4,
        product_name: products[3].name,
        price: products[3].price,
        quantity: 1,
        subtotal: products[3].price,
        product: products[3]
      }
    ]
  },
  {
    id: 6,
    order_no: 'DD202403140006',
    user_id: 'u_001',
    status: 'completed',
    status_text: '已完成',
    total_amount: 269900,
    total_amount_display: '2699.00',
    item_count: 1,
    created_at: '2024-03-14T08:30:00Z',
    paid_at: '2024-03-14T08:35:00Z',
    shipped_at: '2024-03-15T10:00:00Z',
    completed_at: '2024-03-17T16:00:00Z',
    items: [
      {
        id: 7,
        product_id: 9,
        product_name: products[8].name,
        price: products[8].price,
        quantity: 1,
        subtotal: products[8].price,
        product: products[8]
      }
    ]
  },
  {
    id: 7,
    order_no: 'DD202403120007',
    user_id: 'u_001',
    status: 'shipped',
    status_text: '已发货',
    total_amount: 459900,
    total_amount_display: '4599.00',
    item_count: 1,
    created_at: '2024-03-12T16:20:00Z',
    paid_at: '2024-03-12T16:25:00Z',
    shipped_at: '2024-03-13T09:00:00Z',
    completed_at: null,
    items: [
      {
        id: 8,
        product_id: 7,
        product_name: products[6].name,
        price: products[6].price,
        quantity: 1,
        subtotal: products[6].price,
        product: products[6]
      }
    ]
  },
  {
    id: 8,
    order_no: 'DD202403100008',
    user_id: 'u_001',
    status: 'completed',
    status_text: '已完成',
    total_amount: 1249900,
    total_amount_display: '12499.00',
    item_count: 1,
    created_at: '2024-03-10T09:15:00Z',
    paid_at: '2024-03-10T09:20:00Z',
    shipped_at: '2024-03-11T10:00:00Z',
    completed_at: '2024-03-14T11:30:00Z',
    items: [
      {
        id: 9,
        product_id: 2,
        product_name: products[1].name,
        price: products[1].price,
        quantity: 1,
        subtotal: products[1].price,
        product: products[1]
      }
    ]
  },
  {
    id: 9,
    order_no: 'DD202403080009',
    user_id: 'u_001',
    status: 'completed',
    status_text: '已完成',
    total_amount: 599900,
    total_amount_display: '5999.00',
    item_count: 1,
    created_at: '2024-03-08T13:40:00Z',
    paid_at: '2024-03-08T13:45:00Z',
    shipped_at: '2024-03-09T09:30:00Z',
    completed_at: '2024-03-12T15:00:00Z',
    items: [
      {
        id: 10,
        product_id: 11,
        product_name: products[10].name,
        price: products[10].price,
        quantity: 1,
        subtotal: products[10].price,
        product: products[10]
      }
    ]
  },
  {
    id: 10,
    order_no: 'DD202403050010',
    user_id: 'u_001',
    status: 'completed',
    status_text: '已完成',
    total_amount: 199800,
    total_amount_display: '1998.00',
    item_count: 2,
    created_at: '2024-03-05T10:00:00Z',
    paid_at: '2024-03-05T10:05:00Z',
    shipped_at: '2024-03-06T08:00:00Z',
    completed_at: '2024-03-09T14:30:00Z',
    items: [
      {
        id: 11,
        product_id: 3,
        product_name: products[2].name,
        price: products[2].price,
        quantity: 2,
        subtotal: products[2].price * 2,
        product: products[2]
      }
    ]
  },
  {
    id: 11,
    order_no: 'DD202403030011',
    user_id: 'u_001',
    status: 'completed',
    status_text: '已完成',
    total_amount: 269900,
    total_amount_display: '2699.00',
    item_count: 1,
    created_at: '2024-03-03T14:25:00Z',
    paid_at: '2024-03-03T14:30:00Z',
    shipped_at: '2024-03-04T10:00:00Z',
    completed_at: '2024-03-07T09:00:00Z',
    items: [
      {
        id: 12,
        product_id: 8,
        product_name: products[7].name,
        price: products[7].price,
        quantity: 1,
        subtotal: products[7].price,
        product: products[7]
      }
    ]
  },
  {
    id: 12,
    order_no: 'DD202403010012',
    user_id: 'u_001',
    status: 'completed',
    status_text: '已完成',
    total_amount: 9897,
    total_amount_display: '98.97',
    item_count: 3,
    created_at: '2024-03-01T08:50:00Z',
    paid_at: '2024-03-01T08:55:00Z',
    shipped_at: '2024-03-02T09:00:00Z',
    completed_at: '2024-03-05T11:00:00Z',
    items: [
      {
        id: 13,
        product_id: 5,
        product_name: products[4].name,
        price: products[4].price,
        quantity: 1,
        subtotal: products[4].price,
        product: products[4]
      }
    ]
  }
];

export { orders };
