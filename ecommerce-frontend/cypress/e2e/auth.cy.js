describe('Authentication Flow', () => {
  beforeEach(() => {
    cy.intercept('POST', '/api/v1/user/login', (req) => {
      if (req.body.identifier === 'demo@example.com') {
        req.reply({
          statusCode: 200,
          body: {
            token: 'mock-jwt',
            refreshToken: 'mock-refresh',
            expiresIn: 3600,
            user: {
              id: 'u_001',
              username: 'demo',
              roles: ['admin']
            }
          }
        });
      } else {
        req.reply({
          statusCode: 401,
          body: {
            code: 'AUTH_INVALID',
            message: '用户名或密码错误'
          }
        });
      }
    }).as('loginRequest');

    cy.intercept('GET', '/api/v1/user/info', {
      statusCode: 200,
      body: {
        id: 'u_001',
        username: 'demo',
        email: 'demo@example.com',
        phone: '13800000000'
      }
    }).as('profileRequest');
  });

  it('logs in with valid credentials', () => {
    cy.visit('/login');
    cy.findByPlaceholderText('请输入用户名或邮箱').type('demo@example.com');
    cy.findByPlaceholderText('请输入密码').type('correct-password');
    cy.findByPlaceholderText('请输入验证码').type('123456');
    cy.findByRole('button', { name: '登录' }).click();

    cy.wait('@loginRequest');
    cy.url().should('include', '/dashboard');
  });
});

