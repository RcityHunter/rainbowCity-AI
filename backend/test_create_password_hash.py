import logging
import bcrypt
from passlib.context import CryptContext

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash_passlib(password: str) -> str:
    """使用passlib生成密码哈希"""
    try:
        hashed = pwd_context.hash(password)
        logger.info(f"Passlib生成的哈希: {hashed}")
        return hashed
    except Exception as e:
        logger.error(f"Passlib哈希生成错误: {str(e)}")
        return None

def get_password_hash_bcrypt(password: str) -> str:
    """使用bcrypt直接生成密码哈希"""
    try:
        # 将密码转换为bytes
        if isinstance(password, str):
            password = password.encode('utf-8')
            
        # 生成盐值和哈希
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password, salt)
        
        # 转换为字符串
        hashed_str = hashed.decode('utf-8')
        logger.info(f"Bcrypt生成的哈希: {hashed_str}")
        return hashed_str
    except Exception as e:
        logger.error(f"Bcrypt哈希生成错误: {str(e)}")
        return None

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
    # 测试密码
    password = "password"
    logger.info(f"测试密码: {password}")
    
    # 使用passlib生成哈希
    logger.info("使用passlib生成密码哈希...")
    passlib_hash = get_password_hash_passlib(password)
    
    # 使用bcrypt直接生成哈希
    logger.info("使用bcrypt直接生成密码哈希...")
    bcrypt_hash = get_password_hash_bcrypt(password)
    
    # 验证新生成的哈希
    if bcrypt_hash:
        logger.info("验证新生成的bcrypt哈希...")
        verify_result = verify_password_bcrypt(password, bcrypt_hash)
        logger.info(f"验证结果: {verify_result}")

if __name__ == "__main__":
    main()
