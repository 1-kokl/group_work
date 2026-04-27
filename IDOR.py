import uuid
from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user

# --- 初始化应用 ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-session'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# --- 1. 数据模型 ---

class User(UserMixin, db.Model):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    
    # 关联文档
    documents = db.relationship('Document', backref='owner', lazy=True)

class Document(db.Model):
    """文档模型 - 受保护的资源"""
    id = db.Column(db.Integer, primary_key=True)
    # ✅ 关键：使用 UUID 作为公开访问标识，防止通过自增 ID 枚举
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    content = db.Column(db.String(200), nullable=False)
    
    # ✅ 关键：所有者 ID，用于权限校验
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --- 2. 用户加载回调 (Flask-Login 需要) ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- 3. 辅助函数：模拟登录用于测试 ---
# 在生产环境中，你会使用真实的登录表单和 JWT/Session

@app.route('/login/<username>')
def login(username):
    user = User.query.filter_by(username=username).first()
    if user:
        login_user(user)
        return jsonify({"message": f"Logged in as {username}", "user_id": user.id})
    return jsonify({"error": "User not found"}), 404

# --- 4. 核心业务逻辑与 API ---

@app.route('/documents', methods=['POST'])
@login_required
def create_document():
    """创建文档"""
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Content is required"}), 400
    
    new_doc = Document(
        content=data['content'],
        owner_id=current_user.id  # 自动绑定当前登录用户
    )
    db.session.add(new_doc)
    db.session.commit()
    
    return jsonify({
        "message": "Document created",
        "public_id": new_doc.public_id,
        "content": new_doc.content
    }), 201

@app.route('/documents/<string:public_id>', methods=['GET'])
@login_required
def get_document(public_id):
    """
    获取文档详情 - ✅ 防止 IDOR 的核心实现
    """
    # ❌ 错误做法：直接查找 Document.query.filter_by(public_id=public_id).first()
    # 这样任何登录用户都可以查看任何人的文档
    
    # ✅ 正确做法：同时匹配 public_id 和 当前用户 ID
    # 如果文档存在但不属于当前用户，查询结果为 None
    doc = Document.query.filter_by(
        public_id=public_id, 
        owner_id=current_user.id  # <--- 强制校验所有权
    ).first()
    
    if not doc:
        # 为了安全，通常返回 404 而不是 403，避免泄露资源是否存在
        return jsonify({"error": "Document not found or access denied"}), 404
        
    return jsonify({
        "public_id": doc.public_id,
        "content": doc.content,
        "owner_id": doc.owner_id
    })

@app.route('/documents/<string:public_id>', methods=['PUT'])
@login_required
def update_document(public_id):
    """
    更新文档 - ✅ 防止 IDOR
    """
    # 同样，先查找属于当前用户的文档
    doc = Document.query.filter_by(
        public_id=public_id, 
        owner_id=current_user.id
    ).first()
    
    if not doc:
        return jsonify({"error": "Document not found or access denied"}), 404
        
    data = request.get_json()
    if 'content' in data:
        doc.content = data['content']
        db.session.commit()
        
    return jsonify({"message": "Updated successfully", "content": doc.content})

# --- 5. 初始化数据 (仅用于演示) ---

def init_db():
    with app.app_context():
        db.create_all()
        # 如果数据库为空，创建两个测试用户和一些数据
        if not User.query.first():
            user1 = User(username='alice')
            user2 = User(username='bob')
            db.session.add_all([user1, user2])
            db.session.commit()
            
            # Alice 的文档
            doc1 = Document(content="Alice's Secret Diary", owner_id=user1.id)
            # Bob 的文档
            doc2 = Document(content="Bob's Top Secret Plans", owner_id=user2.id)
            db.session.add_all([doc1, doc2])
            db.session.commit()
            print(f"Initialized DB. Alice's Doc UUID: {doc1.public_id}")
            print(f"Initialized DB. Bob's Doc UUID: {doc2.public_id}")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)