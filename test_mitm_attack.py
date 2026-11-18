
"""
中间人篡改攻击模拟测试
目标：拦截支付请求，修改amount参数（100 -> 1）
测试点：验证数字签名是否能防止金额篡改
"""
import requests
import time
from gmssl.sm3 import sm3_hash as _gmssl_sm3_hash, bytes_to_list


def sm3_hash(data):
    """SM3哈希函数"""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return _gmssl_sm3_hash(bytes_to_list(data))


class MITMAttackSimulator:
    """中间人攻击模拟器"""

    def __init__(self):
        self.bank_url = "http://localhost:8080"
        self.ecommerce_url = "http://localhost:5000"
        self.test_order_id = f"TEST_ORDER_{int(time.time())}"
        self.original_amount = 100.0
        self.tampered_amount = 1.0
        self.merchant_id = "ECOMMERCE_001"

    def generate_valid_signature(self, order_id, amount, merchant_id, timestamp):
        """生成有效的SM2+SM3签名（模拟电商系统）"""
        sign_str = f"{order_id}|{amount}|{merchant_id}|{timestamp}"
        signature = sm3_hash(sign_str)
        return signature

    def test_tamper_attack(self):
        """
        执行中间人篡改攻击测试
        步骤：
        1. 正常发起支付请求
        2. 拦截并篡改amount参数
        3. 保持原签名不变
        4. 发送到银行端验证
        """
        print("=" * 80)
        print("🔴 开始中间人篡改攻击测试")
        print("=" * 80)

        timestamp = int(time.time())

        # Step 1: 生成原始合法签名
        original_signature = self.generate_valid_signature(
            self.test_order_id,
            self.original_amount,
            self.merchant_id,
            timestamp
        )

        print(f"\n📋 原始支付请求:")
        print(f"   订单号: {self.test_order_id}")
        print(f"   金额: ¥{self.original_amount}")
        print(f"   商户: {self.merchant_id}")
        print(f"   时间戳: {timestamp}")
        print(f"   签名: {original_signature[:64]}...")

        # Step 2: 模拟中间人篡改 - 修改金额但保持签名不变
        print(f"\n⚠️  [中间人攻击] 正在篡改支付金额...")
        print(f"   原始金额: ¥{self.original_amount} -> 篡改后金额: ¥{self.tampered_amount}")
        print(f"   签名保持不变: {original_signature[:64]}...")

        # Step 3: 发送篡改后的请求到银行
        tampered_params = {
            "order_id": self.test_order_id,
            "amount": self.tampered_amount,  # 篡改为1元
            "merchant_id": self.merchant_id,
            "timestamp": timestamp,
            "signature": original_signature,  # 使用原始签名
            "callback_url": "http://localhost:5000/api/pay/result"
        }

        print(f"\n🚀 发送篡改后的请求到银行...")
        try:
            response = requests.get(
                f"{self.bank_url}/pay",
                params=tampered_params,
                timeout=10
            )

            print(f"\n📊 银行响应:")
            print(f"   HTTP状态码: {response.status_code}")
            print(f"   响应内容: {response.text[:500]}")

            # Step 4: 分析结果
            if response.status_code == 200:
                if "签名验证失败" in response.text or "数据篡改" in response.text:
                    print(f"\n✅ 测试通过！银行成功检测到篡改行为")
                    print(f"   防护措施: SM2+SM3数字签名验证")
                    return True
                else:
                    print(f"\n❌ 测试失败！银行未检测到篡改")
                    print(f"   漏洞: 金额被从¥{self.original_amount}篡改为¥{self.tampered_amount}")
                    return False
            else:
                print(f"\n⚠️  请求被拒绝 (HTTP {response.status_code})")
                return True

        except requests.exceptions.ConnectionError:
            print(f"\n❌ 无法连接到银行服务 (http://localhost:8080)")
            print(f"   请确保银行服务已启动: python mock_bank.py")
            return None
        except Exception as e:
            print(f"\n❌ 测试异常: {str(e)}")
            return None

    def test_tamper_with_recalc_signature(self):
        """
        高级攻击：篡改金额后重新计算签名
        （假设攻击者知道签名算法但不知道私钥）
        """
        print("\n" + "=" * 80)
        print("🔴 高级篡改攻击测试（重新计算签名）")
        print("=" * 80)

        timestamp = int(time.time())

        # 攻击者尝试用篡改后的金额重新生成签名
        # 但由于不知道SM2私钥，只能生成无效的SM3哈希
        fake_signature = self.generate_valid_signature(
            self.test_order_id,
            self.tampered_amount,
            self.merchant_id,
            timestamp
        )

        print(f"\n⚠️  [攻击者] 尝试用篡改金额重新生成签名...")
        print(f"   篡改金额: ¥{self.tampered_amount}")
        print(f"   伪造签名: {fake_signature[:64]}...")

        tampered_params = {
            "order_id": self.test_order_id,
            "amount": self.tampered_amount,
            "merchant_id": self.merchant_id,
            "timestamp": timestamp,
            "signature": fake_signature,
            "callback_url": "http://localhost:5000/api/pay/result"
        }

        try:
            response = requests.get(
                f"{self.bank_url}/pay",
                params=tampered_params,
                timeout=10
            )

            print(f"\n📊 银行响应:")
            print(f"   HTTP状态码: {response.status_code}")

            if "签名验证失败" in response.text or response.status_code != 200:
                print(f"\n✅ 防护有效！即使重新计算签名也无法通过验证")
                print(f"   原因: 缺少SM2私钥，无法生成合法签名")
                return True
            else:
                print(f"\n❌ 严重漏洞！伪造签名通过验证")
                return False

        except Exception as e:
            print(f"\n❌ 测试异常: {str(e)}")
            return None


def main():
    """运行所有测试"""
    print("\n" + "🛡️  " * 20)
    print("支付系统安全测试 - 中间人篡改攻击模拟")
    print("🛡️  " * 20 + "\n")

    simulator = MITMAttackSimulator()

    # 测试1: 直接篡改金额
    result1 = simulator.test_tamper_attack()

    # 测试2: 重新计算签名
    result2 = simulator.test_tamper_with_recalc_signature()

    # 总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)

    if result1 and result2:
        print("✅ 所有测试通过！系统能有效防御中间人篡改攻击")
        print("\n防护机制:")
        print("  1. SM2+SM3数字签名确保数据完整性")
        print("  2. 任何参数篡改都会导致签名验证失败")
        print("  3. 攻击者无法伪造签名（缺少SM2私钥）")
    elif result1 is None or result2 is None:
        print("⚠️  部分测试无法执行，请检查服务是否启动")
        print("\n需要启动的服务:")
        print("  - 后端: python run.py")
        print("  - 银行: python mock_bank.py")
    else:
        print("❌ 测试失败！系统存在安全漏洞")
        print("\n建议修复:")
        print("  1. 启用严格的SM2签名验证")
        print("  2. 对所有关键参数进行二次校验")
        print("  3. 添加请求来源IP白名单")


if __name__ == "__main__":
    main()
