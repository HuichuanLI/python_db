class Config:
    """
    配置对象
    """
    _instance = None    # 实例标志

    def __new__(cls, *args, **kw):
        # 创建新实例时调用
        if cls._instance is None:
            # 判断实例是否已经存在，如果不存在则创建
            cls._instance = object.__new__(cls, *args, **kw)
        return cls._instance
