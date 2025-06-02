class AI_ID:
    def __init__(self, ai_id, visible_number, uuid):
        self.ai_id = ai_id
        self.visible_number = visible_number
        self.uuid = uuid

    def to_dict(self):
        return {
            'ai_id': self.ai_id,
            'visible_number': self.visible_number,
            'uuid': self.uuid
        }

    @classmethod
    def from_record(cls, record):
        """从 SurrealDB 记录创建 AI_ID 对象"""
        return cls(
            ai_id=record['ai_id'],
            visible_number=record['visible_number'],
            uuid=record['uuid']
        )