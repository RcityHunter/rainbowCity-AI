# SQLAlchemy模拟对象
class MockModel:
    def __init__(self):
        pass

class MockColumn:
    def __init__(self, type_obj, primary_key=False, nullable=True, unique=False, default=None):
        self.type = type_obj
        self.primary_key = primary_key
        self.nullable = nullable
        self.unique = unique
        self.default = default

class MockInteger:
    pass

class MockString:
    def __init__(self, length):
        self.length = length

class MockText:
    pass

class MockDateTime:
    pass

class MockBoolean:
    pass

class MockJSON:
    pass

class MockEnum:
    def __init__(self, enum_class):
        self.enum_class = enum_class

class MockArray:
    def __init__(self, item_type):
        self.item_type = item_type

class MockForeignKey:
    def __init__(self, reference):
        self.reference = reference

class MockDB:
    def __init__(self):
        self.Model = MockModel
    
    def Column(self, type_obj, primary_key=False, nullable=True, unique=False, default=None, *args, **kwargs):
        return MockColumn(type_obj, primary_key, nullable, unique, default)
    
    def ForeignKey(self, reference):
        return MockForeignKey(reference)
    
    @property
    def Integer(self):
        return MockInteger()
    
    def String(self, length):
        return MockString(length)
    
    @property
    def Text(self):
        return MockText()
    
    @property
    def DateTime(self):
        return MockDateTime()
    
    @property
    def Boolean(self):
        return MockBoolean()
    
    @property
    def JSON(self):
        return MockJSON()
    
    def Enum(self, enum_class):
        return MockEnum(enum_class)
    
    def ARRAY(self, item_type):
        return MockArray(item_type)

# 创建全局db对象
db = MockDB()