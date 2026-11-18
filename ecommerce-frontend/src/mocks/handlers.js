import { rest } from 'msw';

const API_BASE = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000';

export const handlers = [
  rest.post(`${API_BASE}/api/v1/user/login`, async (req, res, ctx) => {
    const { identifier, password } = await req.json();

    if (identifier === 'locked@example.com') {
      return res(
        ctx.status(403),
        ctx.json({
          code: 'AUTH_LOCKED',
          message: '账户已被锁定'
        })
      );
    }

    if (password !== 'correct-password') {
      return res(
        ctx.status(401),
        ctx.json({
          code: 'AUTH_INVALID',
          message: '用户名或密码错误'
        })
      );
    }

    return res(
      ctx.status(200),
      ctx.cookie('csrf_token', 'mock-csrf-token', { path: '/' }),
      ctx.json({
        token: 'mock-jwt',
        refreshToken: 'mock-refresh',
        expiresIn: 3600,
        csrfToken: 'mock-csrf-token',
        user: {
          id: 'u_001',
          username: 'demo',
          roles: ['admin']
        }
      })
    );
  }),

  rest.get(`${API_BASE}/api/v1/user/info`, (_req, res, ctx) =>
    res(
      ctx.status(200),
      ctx.json({
        id: 'u_001',
        username: 'demo',
        email: 'demo@example.com',
        phone: '13800000000',
        roles: ['admin'],
        createdAt: '2024-01-01T00:00:00.000Z'
      })
    )
  )
];

