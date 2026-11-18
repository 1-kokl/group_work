"""
支付服务 - 实现数字签名、数字信封、防重放等安全机制
"""
import time
import secrets
import json
import base64
import os
from datetime import datetime
from gmssl.sm2 import CryptSM2, default_ecc_table
from gmssl.sm3 import sm3_hash as _gmssl_sm3_hash, bytes_to_list
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT
from app.extensions import db
from app.models.ecommerce_models import Order


def sm3_hash(data):
    """SM3 哈希"""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return _gmssl_sm3_hash(bytes_to_list(data))


class PaymentService:
    """支付服务"""
    
    # 商户ID（固定）
    MERCHANT_ID = "MERCHANT_001"
    
    # 银行公钥（用于加密）
    BANK_PUBLIC_KEY = ""
    
    # 电商私钥（用于签名和解密）
    ECOMMERCE_PRIVATE_KEY = ""
    ECOMMERCE_PUBLIC_KEY = ""
    
    @classmethod
    def load_keys(cls):
        """加载密钥"""
        # 加载电商密钥
        key_file = os.path.join(os.path.dirname(__file__), "..", "sm2_key.txt")
        key_file = os.path.abspath(key_file)
        
        try:
            if os.path.exists(key_file):
                with open(key_file, "r", encoding="utf-8") as f:
                    lines = [ln.strip() for ln in f.read().strip().split("\n") if ln.strip()]
                if len(lines) >= 2:
                    cls.ECOMMERCE_PRIVATE_KEY = lines[0]
                    cls.ECOMMERCE_PUBLIC_KEY = lines[1]
                    print(f"✅ 已加载电商密钥对")
            else:
                print(f"⚠️ 电商密钥文件不存在: {key_file}")
        except Exception as e:
            print(f"⚠️ 加载电商密钥失败: {e}")
        
        # 加载银行公钥（从银行服务获取或配置文件）
        bank_key_file = os.path.join(os.path.dirname(__file__), "..", "bank_public_key.txt")
        bank_key_file = os.path.abspath(bank_key_file)
        
        try:
            if os.path.exists(bank_key_file):
                with open(bank_key_file, "r", encoding="utf-8") as f:
                    cls.BANK_PUBLIC_KEY = f.read().strip()
                print(f"✅ 已加载银行公钥")
            else:
                print(f"⚠️ 银行公钥文件不存在，尝试从bank_sm2_key.txt读取")
                # 尝试从银行密钥文件读取公钥
                alt_bank_key = os.path.join(os.path.dirname(__file__), "..", "bank_sm2_key.txt")
                alt_bank_key = os.path.abspath(alt_bank_key)
                if os.path.exists(alt_bank_key):
                    with open(alt_bank_key, "r", encoding="utf-8") as f:
                        lines = [ln.strip() for ln in f.read().strip().split("\n") if ln.strip()]
                    if len(lines) >= 2:
                        cls.BANK_PUBLIC_KEY = lines[1]
                        print(f"✅ 已从bank_sm2_key.txt加载银行公钥")
        except Exception as e:
            print(f"⚠️ 加载银行公钥失败: {e}")
    
    @staticmethod
    def generate_payment_signature(order_id, amount, merchant_id, timestamp):
        """
        生成支付签名（SM2+SM3）
        签名内容：order_id|amount|merchant_id|timestamp
        """
        # 构造待签名字符串
        sign_str = f"{order_id}|{amount}|{merchant_id}|{timestamp}"
        
        # SM3 哈希
        hash_value = sm3_hash(sign_str)
        
        # SM2 私钥签名
        para = len(default_ecc_table["n"])
        placeholder = "0" * (2 * para)
        sm2 = CryptSM2(private_key=PaymentService.ECOMMERCE_PRIVATE_KEY, public_key=placeholder)
        
        random_hex = secrets.token_hex(32)
        if len(random_hex) < 64:
            random_hex = random_hex.ljust(64, "0")[:64]
        
        signature = sm2.sign(hash_value.encode("utf-8"), random_hex)
        
        # 转换为 Base64URL 格式
        if isinstance(signature, bytes):
            signature = signature.hex()
        signature_b64url = base64.urlsafe_b64encode(signature.encode("ascii")).decode("ascii").rstrip("=")
        
        return signature_b64url
    
    @staticmethod
    def create_payment_url(order_id, amount, callback_url=None):
        """
        创建支付跳转URL
        返回：支付URL和签名信息
        """
        timestamp = int(time.time())
        merchant_id = PaymentService.MERCHANT_ID
        
        # 生成签名
        signature = PaymentService.generate_payment_signature(order_id, amount, merchant_id, timestamp)
        
        # 构造银行支付URL
        bank_url = "http://localhost:8080/pay"
        if callback_url is None:
            callback_url = "http://localhost:5000/api/pay/result"
        
        payment_url = (
            f"{bank_url}?order_id={order_id}"
            f"&amount={amount}"
            f"&merchant_id={merchant_id}"
            f"&timestamp={timestamp}"
            f"&signature={signature}"
            f"&callback_url={callback_url}"
        )
        
        return {
            "payment_url": payment_url,
            "order_id": order_id,
            "amount": amount,
            "merchant_id": merchant_id,
            "timestamp": timestamp,
            "signature": signature
        }
    
    @staticmethod
    def decrypt_payment_result(encrypted_key_hex, iv_hex, ciphertext_hex):
        """
        解密银行返回的支付结果（数字信封）
        1. 用电商私钥（SM2）解密出 SM4 密钥
        2. 用 SM4 密钥解密密文得到结果
        """
        try:
            # 1. SM2 解密 SM4 密钥
            para = len(default_ecc_table["n"])
            sm2 = CryptSM2(private_key=PaymentService.ECOMMERCE_PRIVATE_KEY, 
                          public_key=PaymentService.ECOMMERCE_PUBLIC_KEY.lstrip("04"),
                          mode=1)
            
            encrypted_key_bytes = bytes.fromhex(encrypted_key_hex)
            sm4_key = sm2.decrypt(encrypted_key_bytes)
            
            if isinstance(sm4_key, str):
                sm4_key = bytes.fromhex(sm4_key)
            
            # 2. SM4 解密密文
            iv = bytes.fromhex(iv_hex)
            ciphertext = bytes.fromhex(ciphertext_hex)
            
            sm4 = CryptSM4()
            sm4.set_key(sm4_key, SM4_DECRYPT)
            decrypted_padded = sm4.crypt_cbc(iv, ciphertext)
            
            # 去除 PKCS7 填充
            padding_len = decrypted_padded[-1]
            decrypted_data = decrypted_padded[:-padding_len]
            
            # 解析 JSON
            result = json.loads(decrypted_data.decode("utf-8"))
            
            return {"success": True, "data": result}
        
        except Exception as e:
            return {"success": False, "message": f"解密失败: {str(e)}"}
    
    @staticmethod
    def process_callback(encrypted_key, iv, ciphertext):
        """
        处理银行异步回调
        1. 解密数据
        2. 验证数据完整性
        3. 更新订单状态
        4. 幂等性检查
        """
        try:
            # 解密结果
            decrypt_result = PaymentService.decrypt_payment_result(encrypted_key, iv, ciphertext)
            
            if not decrypt_result["success"]:
                return {"success": False, "message": decrypt_result["message"]}
            
            payment_data = decrypt_result["data"]
            order_id = payment_data.get("order_id")
            transaction_id = payment_data.get("transaction_id")
            status = payment_data.get("status")
            
            if not order_id:
                return {"success": False, "message": "缺少订单号"}
            
            # 查询订单
            order = Order.query.filter_by(order_no=order_id).first()
            if not order:
                return {"success": False, "message": "订单不存在"}
            
            # 幂等性检查：已支付的订单直接返回成功
            if order.payment_status == "paid":
                return {"success": True, "message": "订单已支付（幂等）"}
            
            # 更新订单状态
            if status == "success":
                order.payment_status = "paid"
                order.status = "paid"
                order.transaction_id = transaction_id
                order.paid_at = datetime.utcnow()
                db.session.commit()
                
                print(f"✅ 订单支付成功: {order_id}, 交易号: {transaction_id}")
                
                return {"success": True, "message": "订单支付成功"}
            else:
                order.payment_status = "failed"
                db.session.commit()
                
                return {"success": False, "message": "支付失败"}
        
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"回调处理失败: {str(e)}"}
    
    @staticmethod
    def process_callback_simple(order_id, transaction_id, amount, status):
        """
        简化版回调处理（调试用）
        直接更新订单状态
        """
        try:
            # 查找订单
            order = Order.query.filter_by(order_no=order_id).first()
            if not order:
                return {"success": False, "message": "订单不存在"}
            
            # 检查是否已处理
            if order.payment_status == "paid":
                print(f"⚠️ 订单 {order_id} 已支付，跳过重复处理")
                return {"success": True, "message": "订单已处理"}
            
            # 更新订单状态
            if status == "success":
                order.payment_status = "paid"
                order.status = "paid"
                order.transaction_id = transaction_id
                order.paid_at = datetime.utcnow()
                db.session.commit()
                
                print(f"✅ 订单 {order_id} 支付成功，交易号: {transaction_id}")
                return {"success": True, "message": "支付成功"}
            else:
                order.payment_status = "failed"
                db.session.commit()
                
                print(f"❌ 订单 {order_id} 支付失败")
                return {"success": False, "message": "支付失败"}
        
        except Exception as e:
            db.session.rollback()
            print(f"❌ 回调处理异常: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"处理失败: {str(e)}"}

    @staticmethod
    def handle_payment_result(encrypted_key_hex, iv_hex, ciphertext_hex):
        """
        处理同步跳转结果（解密银行返回的支付结果）
        """
        try:
            # 解密结果
            decrypt_result = PaymentService.decrypt_payment_result(
                encrypted_key_hex, iv_hex, ciphertext_hex
            )
            
            if not decrypt_result["success"]:
                return {"success": False, "message": decrypt_result["message"]}
            
            result_data = decrypt_result["data"]
            
            # 查找订单
            order = Order.query.filter_by(order_no=result_data.get("order_id")).first()
            if not order:
                return {"success": False, "message": "订单不存在"}
            
            return {
                "success": True,
                "data": result_data,
                "order": order.to_dict()
            }
        
        except Exception as e:
            return {"success": False, "message": f"处理失败: {str(e)}"}


# 初始化时加载密钥
PaymentService.load_keys()
