"""
导出银行公钥到电商系统
运行此脚本后，将生成的 bank_public_key.txt 复制到电商项目根目录
"""
import os

# 银行密钥文件路径
bank_key_file = "bank_sm2_key.txt"

if os.path.exists(bank_key_file):
    with open(bank_key_file, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.read().strip().split("\n") if ln.strip()]
    
    if len(lines) >= 2:
        public_key = lines[1]
        
        # 写入电商项目
        with open("bank_public_key.txt", "w", encoding="utf-8") as f:
            f.write(public_key)
        
        print("✅ 银行公钥已导出到 bank_public_key.txt")
        print(f"公钥: {public_key[:50]}...")
    else:
        print("❌ 银行密钥文件格式错误")
else:
    print("❌ 银行密钥文件不存在，请先运行 mock_bank.py 生成密钥")
