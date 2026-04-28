import { products } from './productMock';

const cartItems = [
  {
    id: 1,
    user_id: 'u_001',
    product_id: 1,
    quantity: 1,
    selected: true,
    product: products[0],
    created_at: '2024-03-20T10:30:00Z',
    updated_at: '2024-03-20T10:30:00Z'
  },
  {
    id: 2,
    user_id: 'u_001',
    product_id: 3,
    quantity: 2,
    selected: true,
    product: products[2],
    created_at: '2024-03-19T15:20:00Z',
    updated_at: '2024-03-19T15:20:00Z'
  },
  {
    id: 3,
    user_id: 'u_001',
    product_id: 8,
    quantity: 1,
    selected: false,
    product: products[7],
    created_at: '2024-03-18T09:45:00Z',
    updated_at: '2024-03-18T09:45:00Z'
  },
  {
    id: 4,
    user_id: 'u_001',
    product_id: 5,
    quantity: 3,
    selected: true,
    product: products[4],
    created_at: '2024-03-17T14:10:00Z',
    updated_at: '2024-03-17T14:10:00Z'
  },
  {
    id: 5,
    user_id: 'u_001',
    product_id: 4,
    quantity: 1,
    selected: false,
    product: products[3],
    created_at: '2024-03-16T11:25:00Z',
    updated_at: '2024-03-16T11:25:00Z'
  }
];

export { cartItems };
