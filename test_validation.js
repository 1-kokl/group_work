// 模拟前端安全验证
// 使用用户提供的数据

const data = {
  username: "iopiop",
  email: "1331997366@qq.com",
  password: "@Lzy123456",
  phone: "13322554455"
};

console.log("=== 模拟前端数据验证 ===\n");

// 用户名校验
function checkUsername(username) {
  if (!username) return [false, '用户名不能为空'];
  if (username.length < 4 || username.length > 20) {
    return [false, '用户名长度需4-20位'];
  }
  if (!/^[a-zA-Z0-9]+$/.test(username)) {
    return [false, '用户名仅支持字母和数字'];
  }
  return [true, ''];
}

// 密码强度校验
function validatePasswordStrength(password) {
  const feedback = [];
  let score = 0;
  if (!password) {
    return { valid: false, feedback: ['密码不能为空'], score: 0 };
  }
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^a-zA-Z0-9]/.test(password)) score += 1;

  const [ok, msg] = checkPassword(password);
  if (!ok) {
    feedback.push(msg);
  }
  return { valid: ok, feedback, score };
}

function checkPassword(password) {
  if (!password) return [false, '密码不能为空'];
  if (password.length < 8) {
    return [false, '密码长度至少8位'];
  }
  if (!/[A-Z]/.test(password)) {
    return [false, '密码需包含大写字母'];
  }
  if (!/[0-9]/.test(password)) {
    return [false, '密码需包含数字'];
  }
  return [true, ''];
}

// 手机号校验
function checkPhone(phone) {
  if (!phone) return [false, '手机号不能为空'];
  if (!/^1[3-9]\d{9}$/.test(phone)) {
    return [false, '手机号格式错误'];
  }
  return [true, ''];
}

// 测试
console.log("用户名:", data.username);
console.log(checkUsername(data.username));

console.log("\n密码:", data.password);
const pwResult = validatePasswordStrength(data.password);
console.log("密码校验:", pwResult);

console.log("\n手机号:", data.phone);
console.log(checkPhone(data.phone));

console.log("\n邮箱:", data.email);
console.log(/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email) ? "格式正确" : "格式错误");

console.log("\n=== 结论 ===");
if (checkUsername(data.username)[0] && checkPhone(data.phone)[0] && validatePasswordStrength(data.password).valid) {
  console.log("所有字段通过前端验证!");
} else {
  console.log("有字段未通过验证!");
}
