describe('Auth API (mocked)', () => {
  const baseURL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000';

  it('returns token when credentials are correct', async () => {
    const res = await fetch(`${baseURL}/api/v1/user/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        identifier: 'demo@example.com',
        password: 'correct-password'
      })
    });

    const body = await res.json();
    expect(res.status).toBe(200);
    expect(body.token).toBeDefined();
    expect(body.user.username).toBe('demo');
  });

  it('rejects locked accounts', async () => {
    const res = await fetch(`${baseURL}/api/v1/user/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        identifier: 'locked@example.com',
        password: 'correct-password'
      })
    });

    const body = await res.json();
    expect(res.status).toBe(403);
    expect(body.code).toBe('AUTH_LOCKED');
  });
});

