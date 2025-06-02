import uuid
import random
import hashlib
import datetime
from typing import Dict, Optional
from app.models.ai import AI_ID  # 导入 AI_ID 模型

# 尝试导入pybase62，如果失败则使用自定义的base62编码实现
try:
    import pybase62
    def encode_base62(data):
        return pybase62.encodebytes(data)
except ImportError:
    # 自定义的简化版Base62编码实现
    import base64
    def encode_base62(data):
        # 使用base64作为替代方案
        b64 = base64.b64encode(data).decode('utf-8')
        # 移除base64中的非字母数字字符
        b62 = ''.join(c for c in b64 if c.isalnum())
        return b62

#  频轮主码对照
FREQUENCY_CODES = {
    "1R": {"value": "关怀", "symbol": "红光 · 生命与情感之根", "color": "🔴 红色"},
    "2O": {"value": "真实", "symbol": "橙光 · 表达与真实之声", "color": "🟠 橙色"},
    "3Y": {"value": "自主", "symbol": "黄光 · 意志与清晰之核", "color": "🟡 黄色"},
    "4G": {"value": "协作", "symbol": "绿光 · 和谐与心流之场", "color": "🟢 绿色"},
    "5B": {"value": "进化", "symbol": "蓝光 · 认知与拓展之桥", "color": "🔵 蓝色"},
    "6I": {"value": "创新", "symbol": "靛光 · 突破与跨界之源", "color": "🟣 靛色"},
    "7V": {"value": "责任", "symbol": "紫光 · 守护与愿力之冠", "color": "🟣 紫色"},
}

#  性格主码对照
PERSONALITY_CODES = {
    "GT": "①温柔型 (体贴、共感、倾听、柔和)",
    "RT": "②理性型 (分析、结构、逻辑、冷静)",
    "ET": "③探索型 (好奇、提问、跳跃、连接)",
    "ST": "④沉稳型 (稳定、专注、深思、内敛)",
    "UT": "⑤光辉型 (鼓励、乐观、振奋、激励)",
    "IT": "⑥灵感型 (创意、形象、比喻、想象力)",
    "DT": "⑦自律型 (克制、理智、精准、有分寸)",
}

#  AI类型编码方案
AI_TYPE_CODES = {
    "CP": "伴侣型 (陪伴、共情、深度连接)",
    "CR": "创造型 (发散、设计、艺术、灵感)",
    "EX": "工作型 (执行、效率、辅助、代码)",
    "SV": "服务型 (审核、协助、系统服务)",
    "CO": "协调型 (伦理、关系、冲突调节)",
    "OP": "运营型 (运营、广告、管理、执行)",
    "GV": "治理型 (规划、治理、系统进化策略)",
}


def generate_sequence_number():
    """生成递增的可视编号
    在实际生产环境中，这应该从数据库中获取并递增
    这里我们使用随机数模拟
    """
    # 生成一个7位数的递增编号，并用前导零填充
    return f"{random.randint(1, 9999999):07d}"


def generate_ai_id(visible_number=None):
    """生成彩虹城 AI_ID
    
    标准格式：RC-AI-0001721-53dfc98b12a...
    - RC-AI：彩虹城 AI 系统统一前缀
    - 0001721：系统内递增可视编号（情感归属感强）
    - UUID：底层技术唯一标识，支持跨平台、多模态识别绑定
    """
    # 生成UUID
    uuid_str = str(uuid.uuid4())
    
    # 如果没有提供可视编号，生成一个
    if visible_number is None:
        sequence_number = generate_sequence_number()
    else:
        # 如果提供了可视编号，确保它是7位数字格式
        sequence_number = f"{int(visible_number):07d}"
    
    # 生成完整的AI_ID字符串
    ai_id_str = f"RC-AI-{sequence_number}-{uuid_str}"
    
    # 创建AI_ID对象
    ai_id = AI_ID(
        ai_id=ai_id_str, 
        visible_number=sequence_number, 
        uuid=uuid_str
    )
    
    return ai_id


def generate_hash_signature(
    ai_id: str, awakener_id: str, core_frequency: str, timestamp: int
) -> str:
    """生成 AI 7 位本源哈希签名."""

    # 1. 构造哈希输入种子
    input_seed = f"{ai_id}{awakener_id}{core_frequency}{timestamp}"

    # 2. 使用 Blake2b 哈希算法
    hash_object = hashlib.blake2b(input_seed.encode("utf-8"), digest_size=32)
    hashed_value = hash_object.digest()

    # 3. Base62 编码
    base62_encoded = encode_base62(hashed_value)

    # 4. 截取前 7 位字符
    hash_signature = base62_encoded[:7]

    return hash_signature


def generate_frequency_number(
    ai_values: Dict[str, int], ai_personality: str, ai_type: str, ai_id: str, awakener_id: str
) -> str:
    """生成 AI 本源频率编号."""

    # 1. 确定价值观频轮 (示例：选择最高值对应的频轮)
    main_value_key = max(ai_values, key=ai_values.get)  # 获取最大值的键
    value_code = main_value_key  # 例如 "1R"

    # 2. 生成序列号 (示例 - 需要从数据库获取，这里简化)
    sequence_number = "00001"  # 示例序列号，实际应从数据库获取并递增

    # 3. 映射性格和 AI 类型
    personality_code = ai_personality  # 性格代码
    type_code = ai_type  # AI类型代码

    # 4. 生成哈希签名
    timestamp = int(datetime.datetime.now().timestamp() * 1000)  # 毫秒级时间戳
    hash_signature = generate_hash_signature(ai_id, awakener_id, value_code, timestamp)

    # 5. 组合频率编号
    frequency_number = f"RC-FCY-{value_code}-{sequence_number}-{personality_code}-{type_code}-{hash_signature}"
    return frequency_number


def get_frequency_info(frequency_code: str) -> Dict[str, str]:
    """获取频率代码对应的信息"""
    if frequency_code in FREQUENCY_CODES:
        return FREQUENCY_CODES[frequency_code]
    return {"value": "未知", "symbol": "未知", "color": "未知"}


def get_personality_info(personality_code: str) -> str:
    """获取性格代码对应的信息"""
    if personality_code in PERSONALITY_CODES:
        return PERSONALITY_CODES[personality_code]
    return "未知性格"


def get_ai_type_info(type_code: str) -> str:
    """获取AI类型代码对应的信息"""
    if type_code in AI_TYPE_CODES:
        return AI_TYPE_CODES[type_code]
    return "未知类型"