from flask import Flask
from flask_cors import CORS
import os
from datetime import timedelta


def create_app():
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key_please_change_in_production'),
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        STRIPE_SECRET_KEY=os.environ.get('STRIPE_SECRET_KEY', ''),
        STRIPE_WEBHOOK_SECRET=os.environ.get('STRIPE_WEBHOOK_SECRET', ''),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB最大上传文件大小
    )
    
    # 配置CORS，允许前端访问
    CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})
    
    # 添加CORS头部
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
    
    # 添加一个中间件来处理OPTIONS请求
    @app.after_request
    def after_request(response):
        # 不再手动添加CORS头部，避免重复
        if response.status_code == 404:
            response.status_code = 200
        return response

    from .routes.ai_routes import ai_bp
    from .routes.relationship_routes import relationship_bp
    from .routes.chat_routes import chat_bp
    from .routes.auth_routes import auth_bp
    from .routes.vip_routes import vip_bp
    from .routes.agent_routes import agent_bp
    from .routes.image_routes import image_bp
    from .routes.file_routes import file_bp
    from .routes.conversation_routes import conversation_bp
    from .routes.chat_history_routes import chat_history_bp
    # from .routes.user_routes import user_bp  # 如果有用户路由

    app.register_blueprint(ai_bp)
    app.register_blueprint(relationship_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(conversation_bp)
    app.register_blueprint(chat_history_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(vip_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(file_bp)
    # app.register_blueprint(user_bp)

    return app


app = create_app()