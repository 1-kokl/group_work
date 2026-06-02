import { render, fireEvent, waitFor, screen } from '@testing-library/vue';
import { createStore } from 'vuex';
import Login from '@/pages/auth/Login.vue';

const loginMock = jest.fn().mockResolvedValue({
  id: 'u_001',
  username: 'demo'
});

const mockAuthModule = {
  namespaced: true,
  actions: {
    login: loginMock
  },
  getters: {
    isAuthenticated: () => false
  }
};

const mockUserModule = {
  namespaced: true,
  actions: {
    setProfile: jest.fn()
  }
};

function renderLogin() {
  const store = createStore({
    modules: {
      auth: mockAuthModule,
      user: mockUserModule
    }
  });

  return render(Login, {
    global: {
      plugins: [store],
      stubs: ['router-link', 'router-view']
    }
  });
}

describe('Login.vue', () => {
  beforeEach(() => {
    loginMock.mockClear();
  });

  it('submits credentials after validation', async () => {
    renderLogin();

    await fireEvent.update(screen.getByPlaceholderText('请输入用户名或邮箱'), 'demo@example.com');
    await fireEvent.update(screen.getByPlaceholderText('请输入密码'), 'correct-password');
    await fireEvent.update(screen.getByPlaceholderText('请输入验证码'), '123456');

    await fireEvent.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() =>
      expect(loginMock).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          identifier: 'demo@example.com',
          password: 'correct-password'
        }),
        undefined
      )
    );
  });
});

