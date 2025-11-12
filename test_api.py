# 创建 test_api.py 文件
import unittest
import json
import sys
import os
from datetime import datetime
import html
import io

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask_new import app, rsa_service, Base, engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class APITestCase(unittest.TestCase):
    """API测试用例"""

    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        cls.client = app.test_client()
        cls.ctx = app.app_context()
        cls.ctx.push()

        # 创建测试数据库
        cls.test_engine = create_engine('sqlite:///test.db')
        Base.metadata.create_all(bind=cls.test_engine)
        cls.Session = sessionmaker(bind=cls.test_engine)

    def setUp(self):
        """每个测试前的设置"""
        self.session = self.Session()

    def tearDown(self):
        """每个测试后的清理"""
        self.session.rollback()
        self.session.close()

    def test_01_register_success(self):
        """测试用户注册成功"""
        data = {
            "username": "testuser_" + str(datetime.now().timestamp())[-6:],
            "password": "TestPass123!",
            "phone": "138" + str(datetime.now().timestamp())[-8:]
        }

        response = self.client.post('/api/v1/user/register',
                                    data=json.dumps(data),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result['code'], 200)
        self.assertIn('成功', result['msg'])

    def test_02_register_duplicate(self):
        """测试重复注册"""
        data = {
            "username": "duplicate_user",
            "password": "TestPass123!",
            "phone": "13800000000"
        }

        # 第一次注册
        self.client.post('/api/v1/user/register',
                         data=json.dumps(data),
                         content_type='application/json')

        # 第二次注册
        response = self.client.post('/api/v1/user/register',
                                    data=json.dumps(data),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        result = json.loads(response.data)
        self.assertEqual(result['code'], 400)

    def test_03_login_success(self):
        """测试登录成功"""
        # 先注册用户
        user_data = {
            "username": "login_test_user",
            "password": "TestPass123!",
            "phone": "13900000000"
        }
        self.client.post('/api/v1/user/register',
                         data=json.dumps(user_data),
                         content_type='application/json')

        # 测试登录
        login_data = {
            "username": "login_test_user",
            "password": "TestPass123!"
        }

        response = self.client.post('/api/v1/user/login',
                                    data=json.dumps(login_data),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result['code'], 200)
        self.assertIn('access_token', result['data'])

    def test_04_login_failure(self):
        """测试登录失败"""
        data = {
            "username": "nonexistent_user",
            "password": "WrongPass123!"
        }

        response = self.client.post('/api/v1/user/login',
                                    data=json.dumps(data),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 401)
        result = json.loads(response.data)
        self.assertEqual(result['code'], 401)

    def test_05_rate_limiting(self):
        """测试频率限制"""
        data = {
            "username": "rate_test_user",
            "password": "TestPass123!"
        }

        # 快速发送6个请求（超过5次/分钟的限制）
        responses = []
        for i in range(6):
            response = self.client.post('/api/v1/user/login',
                                        data=json.dumps(data),
                                        content_type='application/json')
            responses.append(response.status_code)

        # 最后一个请求应该被限制
        self.assertEqual(responses[-1], 429)

    def test_06_security_headers(self):
        """测试安全头"""
        response = self.client.get('/api/v1/user/login', method='OPTIONS')

        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertIn('X-Frame-Options', response.headers)
        self.assertIn('X-XSS-Protection', response.headers)

    def test_07_input_validation(self):
        """测试输入验证"""
        # 测试过大的请求体
        large_data = {"data": "x" * 1024 * 1025}  # 超过1MB

        response = self.client.post('/api/v1/user/register',
                                    data=json.dumps(large_data),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 413)


class HTMLTestRunner:
    """HTML测试报告生成器"""

    def __init__(self, stream, title="API测试报告", description=""):
        self.stream = stream
        self.title = title
        self.description = description

    def run(self, test):
        """运行测试并生成报告"""
        result = unittest.TestResult()
        test(result)

        self.generate_report(result)
        return result

    def generate_report(self, result):
        """生成HTML报告"""
        report = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{html.escape(self.title)}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .test-case {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
                .success {{ border-color: green; background: #f0fff0; }}
                .failure {{ border-color: red; background: #fff0f0; }}
                .error {{ border-color: orange; background: #fffaf0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{html.escape(self.title)}</h1>
                <p>{html.escape(self.description)}</p>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="summary">
                <h2>测试摘要</h2>
                <p>运行测试: {result.testsRun}</p>
                <p>失败: {len(result.failures)}</p>
                <p>错误: {len(result.errors)}</p>
                <p>通过: {result.testsRun - len(result.failures) - len(result.errors)}</p>
            </div>
        """

        # 添加测试用例详情
        for test, traceback in result.failures + result.errors:
            status_class = 'failure' if (test, traceback) in result.failures else 'error'
            report += f"""
            <div class="test-case {status_class}">
                <h3>{html.escape(str(test))}</h3>
                <pre>{html.escape(traceback)}</pre>
            </div>
            """

        report += "</body></html>"

        self.stream.write(report)


def run_tests_with_report():
    """运行测试并生成报告"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(APITestCase)

    # 运行测试
    with open('test_report.html', 'w', encoding='utf-8') as f:
        runner = HTMLTestRunner(f, "电子商务系统API测试报告", "安全防护机制测试")
        result = runner.run(suite)

    print(f"测试完成！查看 test_report.html 获取详细报告")
    print(f"通过: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun}")

    return result.wasSuccessful()