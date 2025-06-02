from typing import Dict, Optional

class FrequencyNumber:
    """AI频率编号模型"""
    
    def __init__(self, 
                 frequency_number: str, 
                 value_code: str, 
                 sequence_number: str,
                 personality_code: str,
                 ai_type_code: str,
                 hash_signature: str,
                 ai_id: str = None):
        """
        初始化频率编号对象
        
        Args:
            frequency_number: 完整的频率编号字符串 (RC-FCY-1R-00001-GT-CP-a1b2c3d)
            value_code: 价值观频轮代码 (如 "1R")
            sequence_number: 序列号 (如 "00001")
            personality_code: 性格代码 (如 "GT")
            ai_type_code: AI类型代码 (如 "CP")
            hash_signature: 哈希签名 (如 "a1b2c3d")
            ai_id: 关联的AI-ID (可选)
        """
        self.frequency_number = frequency_number
        self.value_code = value_code
        self.sequence_number = sequence_number
        self.personality_code = personality_code
        self.ai_type_code = ai_type_code
        self.hash_signature = hash_signature
        self.ai_id = ai_id
    
    def to_dict(self) -> Dict:
        """将对象转换为字典"""
        return {
            'frequency_number': self.frequency_number,
            'value_code': self.value_code,
            'sequence_number': self.sequence_number,
            'personality_code': self.personality_code,
            'ai_type_code': self.ai_type_code,
            'hash_signature': self.hash_signature,
            'ai_id': self.ai_id
        }
    
    @classmethod
    def from_string(cls, frequency_number: str, ai_id: str = None) -> Optional['FrequencyNumber']:
        """从频率编号字符串解析创建对象"""
        try:
            # 解析格式: RC-FCY-1R-00001-GT-CP-a1b2c3d
            parts = frequency_number.split('-')
            if len(parts) < 7 or parts[0] != 'RC' or parts[1] != 'FCY':
                return None
                
            value_code = parts[2]
            sequence_number = parts[3]
            personality_code = parts[4]
            ai_type_code = parts[5]
            hash_signature = parts[6]
            
            return cls(
                frequency_number=frequency_number,
                value_code=value_code,
                sequence_number=sequence_number,
                personality_code=personality_code,
                ai_type_code=ai_type_code,
                hash_signature=hash_signature,
                ai_id=ai_id
            )
        except Exception:
            return None
