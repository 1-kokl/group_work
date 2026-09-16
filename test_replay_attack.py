"""
重放攻击测试脚本 - 完整版
包含：100次重放攻击 + 时间戳过期验证 + 数据库检查
"""
import requests
import time
import sqlite3
import os
from datetime import datetime
from gmssl.sm3 import sm3_hash as _gmssl_sm3_hash, bytes_to_list


def sm3_hash(data):
    """SM3哈希函数"""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return _gmssl_sm3_hash(bytes_to_list(data))


class ReplayAttackSimulator:
    """重放攻击模拟器"""

    def __init__(self):
        self.bank_url = "http://localhost:8080"
        self.db_path = os.path.join(os.path.dirname(__file__), "bank.db")
        self.captured_request = None
        self.replay_count = 100  # 100次攻击

    def capture_legitimate_request(self):
        """捕获一笔合法的支付请求"""
        print("=" * 80)
        print("📡 第一步：捕获合法支付请求")
        print("=" * 80)

        order_id = f"REPLAY_TEST_{int(time.time())}"
        amount = 100.0
        merchant_id = "ECOMMERCE_001"
        timestamp = int(time.time())

        sign_str = f"{order_id}|{amount}|{merchant_id}|{timestamp}"
        signature = sm3_hash(sign_str)

        self.captured_request = {
            "order_id": order_id,
            "amount": amount,
            "merchant_id": merchant_id,
            "timestamp": timestamp,
            "signature": signature,
            "callback_url": "http://localhost:5000/api/pay/result"
        }

        print(f"\n✅ 已捕获合法请求:")
        print(f"   订单号: {order_id}")
        print(f"   金额: ¥{amount}")
        print(f"   时间戳: {timestamp} ({datetime.fromtimestamp(timestamp)})")

        return self.captured_request

    def send_replay_requests(self):
        """发送100次重放请求 - 直接提交到 /pay/process"""
        print("\n" + "=" * 80)
        print(f"🔄 第二步：执行重放攻击（{self.replay_count}次）")
        print("=" * 80)

        if not self.captured_request:
            print("❌ 没有捕获的请求")
            return False

        success_count = 0
        blocked_count = 0
        failed_count = 0

        print(f"\n🚀 开始发送{self.replay_count}次请求...\n")

        start_time = time.time()

        for i in range(self.replay_count):
            try:
                form_data = {
                    "order_id": self.captured_request["order_id"],
                    "amount": self.captured_request["amount"],
                    "merchant_id": self.captured_request["merchant_id"],
                    "timestamp": self.captured_request["timestamp"],
                    "signature": self.captured_request["signature"],
                    "callback_url": self.captured_request["callback_url"],
                    "password": "123456"
                }

                response = requests.post(
                    f"{self.bank_url}/pay/process",
                    data=form_data,
                    timeout=5
                )

                if response.status_code == 200:
                    if "已处理" in response.text or "订单已处理" in response.text:
                        blocked_count += 1
                        status = "🚫 被拦截"
                    elif "支付成功" in response.text:
                        success_count += 1
                        status = "✅ 成功(漏洞!)"
                    else:
                        failed_count += 1
                        status = "⚠️ 其他"
                elif response.status_code == 409:
                    blocked_count += 1
                    status = "🚫 被拦截(409)"
                elif response.status_code == 403:
                    blocked_count += 1
                    status = "🚫 被拦截(403)"
                else:
                    failed_count += 1
                    status = f"❌ HTTP {response.status_code}"

                if (i + 1) % 10 == 0:
                    elapsed = time.time() - start_time
                    speed = (i + 1) / elapsed if elapsed > 0 else 0
                    print(f"   [{i + 1}/{self.replay_count}] {status} - 速度: {speed:.1f} req/s")

            except Exception as e:
                print(f"   ❌ 错误: {str(e)[:50]}")
                failed_count += 1

        elapsed_time = time.time() - start_time

        print("\n" + "-" * 80)
        print("📊 重放攻击统计结果:")
        print("-" * 80)
        print(f"   总请求数: {self.replay_count}")
        print(f"   成功执行: {success_count} (应该为0)")
        print(f"   被拦截: {blocked_count} (应该为{self.replay_count})")
        print(f"   失败: {failed_count}")
        print(f"   总耗时: {elapsed_time:.2f} 秒")
        print(f"   平均速度: {self.replay_count / elapsed_time:.1f} 请求/秒")

        if success_count > 0:
            print(f"\n❌ 严重漏洞！{success_count}次重放攻击成功执行")
            print(f"   攻击者可以重复转账，造成资金损失")
            return False
        else:
            print(f"\n✅ 所有重放请求均被拦截")
            return True

    def check_timestamp_validation(self):
        """测试时间戳过期验证"""
        print("\n" + "=" * 80)
        print("⏱️  第三步：测试时间戳过期验证")
        print("=" * 80)

        if not self.captured_request:
            print("❌ 没有捕获的请求")
            return None

        # 修改时间戳为10分钟前（超过5分钟有效期）
        expired_timestamp = int(time.time()) - 600
        expired_request = self.captured_request.copy()
        expired_request["timestamp"] = expired_timestamp

        print(f"\n📤 发送过期请求:")
        print(
            f"   原始时间戳: {self.captured_request['timestamp']} ({datetime.fromtimestamp(self.captured_request['timestamp'])})")
        print(f"   过期时间戳: {expired_timestamp} ({datetime.fromtimestamp(expired_timestamp)})")
        print(f"   时间差: 10分钟（超过5分钟有效期）")

        try:
            form_data = {
                "order_id": expired_request["order_id"],
                "amount": expired_request["amount"],
                "merchant_id": expired_request["merchant_id"],
                "timestamp": expired_request["timestamp"],
                "signature": expired_request["signature"],
                "callback_url": expired_request["callback_url"],
                "password": "123456"
            }

            response = requests.post(
                f"{self.bank_url}/pay/process",
                data=form_data,
                timeout=5
            )

            print(f"\n📊 响应:")
            print(f"   HTTP状态码: {response.status_code}")

            if "过期" in response.text or "expired" in response.text.lower():
                print(f"   响应内容: ...请求已过期...")
                print(f"\n✅ 时间戳验证有效！过期请求被拒绝")
                return True
            elif response.status_code != 200:
                print(f"   响应内容: {response.text[:200]}")
                print(f"\n✅ 请求被拒绝 (HTTP {response.status_code})")
                return True
            else:
                print(f"   响应内容: {response.text[:300]}")
                print(f"\n❌ 漏洞！过期请求仍然被接受")
                return False

        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            return None

    def check_database(self):
        """检查数据库记录"""
        print("\n" + "=" * 80)
        print("🗄️  第四步：检查数据库防重放机制")
        print("=" * 80)

        if not os.path.exists(self.db_path):
            print(f"❌ 数据库不存在: {self.db_path}")
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM replay_protection")
            replay_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM transactions")
            transaction_count = cursor.fetchone()[0]

            if self.captured_request:
                order_id = self.captured_request["order_id"]
                cursor.execute(
                    "SELECT * FROM replay_protection WHERE order_no = ?",
                    (order_id,)
                )
                order_record = cursor.fetchone()

                print(f"\n📊 数据库统计:")
                print(f"   防重放记录数: {replay_count}")
                print(f"   交易记录数: {transaction_count}")
                print(f"   测试订单 '{order_id}' 是否已记录: {'是' if order_record else '否'}")

                if order_record:
                    print(f"   记录时间: {order_record[1]}")
                    print(f"\n✅ 数据库防重放机制正常工作")
                    return True
                else:
                    print(f"\n⚠️  测试订单未被记录（可能未处理）")
                    return None

            conn.close()
            return True

        except Exception as e:
            print(f"\n❌ 数据库查询异常: {e}")
            return None


def main():
    """主函数"""
    print("\n" + "🛡️  " * 20)
    print("支付系统安全测试 - 重放攻击模拟（100次）")
    print("🛡️  " * 20 + "\n")

    simulator = ReplayAttackSimulator()

    # Step 1: 捕获请求
    simulator.capture_legitimate_request()

    # Step 2: 等待几秒
    print("\n⏰ 等待3秒后开始重放...")
    time.sleep(3)

    # Step 3: 执行100次重放攻击
    result1 = simulator.send_replay_requests()

    # Step 4: 测试时间戳验证
    result2 = simulator.check_timestamp_validation()

    # Step 5: 检查数据库
    result3 = simulator.check_database()

    # 总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)

    if result1 and result2 and result3:
        print("✅ 所有测试通过！系统能有效防御重放攻击")
        print("\n防护机制:")
        print("  1. 订单唯一性检查：每个订单只能处理一次")
        print("  2. 时间戳验证：拒绝超过5分钟的请求")
        print("  3. 数据库持久化记录：防止重启后重放")
    elif result1 is False:
        print("❌ 测试失败！系统存在重放攻击漏洞")
        print("\n建议修复:")
        print("  1. 启用严格的订单防重放检查")
        print("  2. 在处理前立即标记订单")
        print("  3. 添加IP频率限制")
    else:
        print("⚠️  部分测试无法执行，请检查服务是否启动")
        print("\n需要启动的服务:")
        print("  - 银行: python mock_bank.py")


if __name__ == "__main__":
    main()




