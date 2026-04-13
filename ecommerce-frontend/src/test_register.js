// 模拟前端完整注册流程测试
// 使用用户提供的数据

const axios = require('axios');

const BASE_URL = 'http://localhost:8080';  // 前端代理地址

const testData = {
  username: 'newtest999',
  email: 'test@test.com',
  password: '@Lzy123456',
  phone: '13322554455'
};

async function testRegister() {
  console.log('=== 前端注册流程测试 ===\n');
  console.log('POST /api/v1/users');
  console.log('数据:', JSON.stringify(testData, null, 2));

  try {
    const response = await axios.post(`${BASE_URL}/api/v1/users`, testData, {
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    console.log('\n状态码:', response.status);
    console.log('响应:', response.data);

    if (response.status === 200) {
      console.log('\n[OK] 注册成功!');
      return true;
    }
  } catch (error) {
    console.log('\n错误:', error.message);
    if (error.response) {
      console.log('状态码:', error.response.status);
      console.log('响应:', error.response.data);
    }
  }
  return false;
}

async function testLogin() {
  console.log('\n\n=== 登录测试 ===\n');

  try {
    const response = await axios.post(`${BASE_URL}/api/v1/auth/login`, {
      username: testData.username,
      password: testData.password
    }, {
      timeout: 10000
    });

    console.log('状态码:', response.status);
    console.log('响应:', response.data);

    if (response.status === 200) {
      console.log('\n[OK] 登录成功!');
      return true;
    }
  } catch (error) {
    console.log('\n错误:', error.message);
    if (error.response) {
      console.log('状态码:', error.response.status);
      console.log('响应:', error.response.data);
    }
  }
  return false;
}

async function runTests() {
  console.log('='.repeat(50));
  console.log('前端注册/登录完整测试');
  console.log('='.repeat(50));
  console.log('前端地址:', BASE_URL);
  console.log('');

  const registerOk = await testRegister();
  const loginOk = await testLogin();

  console.log('\n' + '='.repeat(50));
  console.log('测试结果:');
  console.log('  注册:', registerOk ? 'OK' : 'FAIL');
  console.log('  登录:', loginOk ? 'OK' : 'FAIL');
  console.log('='.repeat(50));
}

runTests().catch(console.error);