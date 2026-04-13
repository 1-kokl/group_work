// 测试密码校验
// 后端要求: 长度>=2, 仅字母数字下划线
// 前端要求: 长度>=8, 需要大写字母和数字

const testPassword = "@Lzy123456";

console.log("=== 密码测试 ===");
console.log("测试密码:", testPassword);

// 前端 checkPassword 规则
function checkPassword(password) {
  if (!password) return [false, '密码不能为空'];
  if (password.length < 8) return [false, '密码长度至少8位'];
  if (!/[A-Z]/.test(password)) return [false, '密码需包含大写字母'];
  if (!/[0-9]/.test(password)) return [false, '密码需包含数字'];
  return [true, ''];
}

const [ok, msg] = checkPassword(testPassword);
console.log("前端校验结果:", ok ? "通过" : "失败", ok ? "" : "- " + msg);

// 后端规则: 无限制(只要有username/password)
console.log("\n后端校验: 密码只要存在即可，通过");

// 检查密码中的特殊字符@
console.log("\n特殊字符 @ 测试:");
console.log("@ 在正则 ^[a-zA-Z0-9_]+$ 中不匹配");
console.log("后端注册会返回: 用户名仅支持字母、数字、下划线");
