import logging
import bcrypt
from passlib.context import CryptContext

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password_passlib(plain_password: str, hashed_password: str) -> bool:
    """使用passlib验证密码"""
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        logger.info(f"Passlib验证结果: {result}")
        return result
    except Exception as e:
        logger.error(f"Passlib验证错误: {str(e)}")
        return False

def verify_password_bcrypt(plain_password: str, hashed_password: str) -> bool:
    """使用bcrypt直接验证密码"""
    try:
        # 将明文密码转换为bytes
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
            
        # 将哈希密码转换为bytes
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
            
        result = bcrypt.checkpw(plain_password, hashed_password)
        logger.info(f"Bcrypt验证结果: {result}")
        return result
    except Exception as e:
        logger.error(f"Bcrypt验证错误: {str(e)}")
        return False

def main():
    # 测试密码和哈希值
    plain_password = "password"
    hashed_password = "$2b$12$gxanQDLXhBS/t9PKMj4lROlu03GP.cItlllu28UqsCe202sFfj/ii"
    
    logger.info(f"测试密码: {plain_password}")
    logger.info(f"哈希密码: {hashed_password}")
    
    # 使用passlib验证
    logger.info("使用passlib验证密码...")
    passlib_result = verify_password_passlib(plain_password, hashed_password)
    logger.info(f"Passlib验证结果: {passlib_result}")
    
    # 使用bcrypt直接验证
    logger.info("使用bcrypt直接验证密码...")
    bcrypt_result = verify_password_bcrypt(plain_password, hashed_password)
    logger.info(f"Bcrypt验证结果: {bcrypt_result}")

if __name__ == "__main__":
    main()
