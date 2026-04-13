// 模拟前端axios请求，测试完整注册流程
const http = require('http');

const testUsername = '前端测试账号' + Date.now();

const postData = JSON.stringify({
  username: testUsername,
  password: '@Lzy123456',
  phone: '13322554455'
});

console.log('=== 模拟前端请求测试 ===');
console.log('请求数据:', postData);
console.log('');

const options = {
  hostname: 'localhost',
  port: 8080,
  path: '/api/v1/users',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(postData)
  }
};

const req = http.request(options, (res) => {
  console.log('状态码:', res.statusCode);
  console.log('响应头:', JSON.stringify(res.headers, null, 2));

  let data = '';
  res.on('data', (chunk) => { data += chunk; });
  res.on('end', () => {
    console.log('响应内容:', data);
    try {
      const json = JSON.parse(data);
      if (res.statusCode === 200) {
        console.log('\n[OK] 注册成功!');
      } else {
        console.log('\n[FAIL] 注册失败:', json.msg);
      }
    } catch (e) {
      console.log('解析响应失败');
    }
  });
});

req.on('error', (e) => {
  console.error('请求错误:', e.message);
});

req.write(postData);
req.end();