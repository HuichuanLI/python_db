from syldb.conf import Config


class LeafNode:
    """
    缓存结点
    """

    def __init__(self, node_obj=None, node_heat=0, is_dirty=False):
        """
        初始化结点
        :param node_obj: 结点保存的对象
        :param node_heat: 结点热度
        :param is_dirty: 是否脏结点
        """
        self.node_obj = node_obj
        self.node_heat = node_heat
        self.is_dirty = is_dirty


class BranchNode:
    """
    缓存分支结点
    """

    def __init__(self, node_name, obj=None, size=16):
        """
        实例化分支结点
        :param node_name: 结点名称
        :param obj: 结点保存的对象
        :param size: 结点大小
        """
        self.node_name = node_name
        self.size = size
        self.obj = obj

    def get_all_node(self):
        """
        获取所有子结点
        :return:
        """
        res = {}
        for key, value in self.__dict__.items():
            # 获取所有属性，并去除非缓存结点属性
            if key in ['node_name', 'size', 'obj']:
                continue
            res[key] = value
        return res

    def get_minimum_node(self):
        """
        获取最低热度与结点
        :return:
        """
        nodes = self.get_all_node()
        min_heat = self.get_average_heat()
        target_node = None
        for key, value in nodes.items():
            # 遍历所有结点，找出最低热度结点
            if value.node_heat <= min_heat:
                min_heat = value.node_heat
                target_node = key
        return min_heat, target_node

    def get_total_heat(self):
        """
        获取总热度
        :return:
        """
        nodes = self.get_all_node()
        total_heat = 0
        for key, value in nodes.items():
            # 遍历所有结点，计算总热度
            total_heat += value.node_heat
        return total_heat

    def get_average_heat(self):
        """
        获取平均热度
        :return:
        """
        nodes = self.get_all_node()
        total_heat = self.get_total_heat()
        return total_heat // len(nodes) if len(nodes) else 0  # 容错操作，防止无结点

    def add_node(self, node_name, node_obj):
        """
        添加结点
        :param node_name: 结点名称
        :param node_obj: 结点内保存的对象
        :return:
        """
        node_name = str(node_name)
        if getattr(self, node_name, None) is not None:
            # 若已存在该结点，则直接返回它
            return getattr(self, node_name)
        nodes = self.get_all_node()
        if len(nodes) >= self.size and getattr(Config(), 'auto_commit_signal', False):
            # 若已缓存结点数大于最大值，且自动提交标识为真，则调整缓存池大小
            self.restore_size()

        return self.__add(node_name, node_obj)

    def __add(self, node_name, node_obj):
        """
        添加结点功能方法
        :param node_name: 结点名称
        :param node_obj: 结点内保存的对象
        :return:
        """
        average_heat = self.get_average_heat()
        node = LeafNode(node_obj, average_heat + 1, False)  # 实例化缓存结点，并添加相应信息
        setattr(self, node_name, node)  # 添加缓存结点到当前分支结点

        return getattr(self, node_name)

    def restore_size(self):
        """
        调整分支结点中包含的缓存结点
        :return:
        """
        while len(self.get_all_node()) >= self.size:
            # 持续调整到缓存结点数量符合预定义
            _, target_node = self.get_minimum_node()  # 获取最低热度结点
            self.dump_node(target_node)  # 保存该结点到磁盘
            delattr(self, target_node)

    def get_node(self, node_name):
        """
        获取缓存结点
        :param node_name: 结点名称
        :return:
        """
        node_name = str(node_name)
        if getattr(self, node_name, None) is not None:
            # 若结点存在
            node = getattr(self, node_name)  # 取出结点
            node.node_heat += 1  # 结点存在，热度加一
            node.is_dirty = True
            return getattr(self, node_name)
        return None

    def get_dirty_node(self):
        """
        获取脏结点
        :return:
        """
        res = []
        for key, value in self.get_all_node().items():
            # 遍历所有结点，找出脏结点
            if value.is_dirty:
                res.append(key)
        return res

    def commit(self):
        """
        提交当前结点到磁盘
        :return:
        """
        for node_name in self.get_dirty_node():
            # 将所有脏结点提交
            self.dump_node(node_name)
        self.obj.commit()  # 提交数据库或数据表对象

    def rollback(self):
        """
        回滚当前缓存结点
        :return:
        """
        for node_name in self.get_dirty_node():
            # 从磁盘中加载结点到缓存，替换脏结点
            self.load_node(node_name)
        self.obj.rollback()

    def dump_node(self, node_name):
        """
        保存结点
        :param node_name: 结点名称
        :return:
        """
        node_name = str(node_name)
        node = getattr(self, node_name).node_obj  # 取出对象
        node.commit()  # 提交修改

    def load_node(self, node_name):
        """
        加载结点
        :param node_name: 结点名称
        :return:
        """
        node_name = str(node_name)
        node = getattr(self, node_name).node_obj  # 取出对象
        node.rollback()  # 回滚


class CachePool:
    """
    缓存池
    """
    _instance = None

    def __init__(self):
        """
        实例化缓存池
        """
        self.__current_node = None  # 记录当前被调用的数据库缓存

    def __new__(cls, *args, **kwargs):
        """
        单例模式控制方法
        :param args:
        :param kwargs:
        """
        if cls._instance is None:
            # 对象未被实例化，则实例化当前对象，并保存
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def get_cache(self, db_name):
        """
        获取数据库级缓存结点
        :param db_name: 数据库名
        :return:
        """
        if self.__current_node is not None and getattr(Config(), 'auto_commit_signal', False):
            # 若已有数据库缓存被选中，且允许自动提交，则切换时先提交当前数据库改动
            self.__current_node.commit()

        if getattr(self, db_name, None) is None:
            return None

        self.__current_node = getattr(self, db_name)
        return getattr(self, db_name)

    def add_cache(self, db_name, db_obj):
        """
        添加数据库缓存
        :param db_name: 数据库名称
        :param db_obj: 数据库对象
        :return:
        """
        if getattr(self, db_name, None) is not None:
            # 若选中数据库缓存结点已存在，则直接返回它
            return getattr(self, db_name)

        node = BranchNode(db_name, db_obj)  # 实例化分支结点，并传入数据库对象
        setattr(self, db_name, node)  # 记录缓存结点
        return getattr(self, db_name)  # 返回新添加的结点

    def flush_cache_to_disk(self):
        """
        将缓存内容刷到磁盘
        :return:
        """
        db_name_list = self.__dict__.keys()
        for db_name in db_name_list:
            # 获取所有缓存结点，并排除干扰属性
            if db_name == '__current_node':
                continue
            node = getattr(self, db_name, None)
            if node is not None:
                # 依次提交结点到磁盘
                node.commit()
