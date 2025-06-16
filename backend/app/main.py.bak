from flask import Flask
from flask_cors import CORS
from app.db import init_db  # 导入 init_db

def create_app():
    app = Flask(__name__)
    CORS(app)

    # 初始化数据库连接管理
    init_db(app)

    from .routes.ai_routes import ai_bp
    # from .routes.auth_routes import auth_bp  # 如果有认证路由
    # from .routes.user_routes import user_bp  # 如果有用户路由

    app.register_blueprint(ai_bp)
    # app.register_blueprint(auth_bp)
    # app.register_blueprint(user_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')