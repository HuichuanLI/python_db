# ©Copyright: KentWangYQ
# URL: https://github.com/KentWangYQ/py-algorithms
# LICENSE: MIT LICENSE

import sys

from syldb.tools.storageTools import load_obj, dump_obj
from syldb.tools.fileTools import join_path


class BPNode:
    """
    B+树结点
    """

    def __init__(self, domain=5, is_leaf=False):
        """
        初始化结点
        :param domain: 结点的域
        :param is_leaf: 是否为叶子结点
        """
        self.values = None  # 卫星数据
        self.key_num = 0  # 关键字数量
        self.is_leaf = is_leaf
        self.next = None  # 下一结点指针，仅限叶子结点
        self.keys = [None for _ in range(2 * domain)]  # 关键字列表
        self.childs = [None for _ in range(2 * domain)]  # 子结点列表

        if self.is_leaf:
            # 若为叶子结点，则初始化卫星数据列表
            self.values = [None for _ in range(2 * domain)]

    def insert_key(self, index, key):
        """
        插入关键字
        :param index: 待插入关键字索引
        :param key: 关键字
        :return:
        """
        final_index = self.key_num - 1  # 获取当前最后一个关键字的索引
        while final_index >= index:
            # 将目标索引的右侧数据依次右移
            self.keys[final_index + 1] = self.keys[final_index]
            final_index -= 1

        self.keys[index] = key
        self.key_num += 1

    def insert_value(self, index, value):
        """
        插入卫星数据
        :param index: 待插入卫星数据索引
        :param value: 待插入数据
        :return:
        """
        # 获取最后一位数据的索引
        final_index = len([tmp_value for tmp_value in self.values if tmp_value is not None]) - 1

        while final_index >= index:
            # 将目标索引的右侧数据依次右移
            self.values[final_index + 1] = self.values[final_index]

            final_index -= 1

        self.values[index] = value

    def insert_child(self, index, child_node):
        """
        插入子结点
        :param index: 待插入子结点索引
        :param child_node: 子结点
        :return:
        """
        # 获取最后一位数据的索引
        final_index = len([child for child in self.childs if child is not None]) - 1

        while final_index >= index:
            # 将目标索引的右侧数据依次右移
            self.childs[final_index + 1] = self.childs[final_index]
            final_index -= 1

        self.childs[index] = child_node

    def append_key(self, key):
        """
        追加关键字
        :param key: 待追加关键字
        :return:
        """
        self.keys[self.key_num] = key  # 添加关键字
        self.key_num += 1  # 数量加一

    def append_value(self, value):
        """
        追加卫星数据
        :param value: 待追加卫星数据
        :return:
        """
        # 获取当前有效值的个数，并以此为索引
        index = len([value for value in self.values if value is not None])
        self.values[index] = value

    def append_child(self, child_node):
        """
        追加子结点
        :param child_node: 待追加子结点
        :return:
        """
        # 获取当前有效子结点的数量，并以此为索引
        index = len([child for child in self.childs if child])
        self.childs[index] = child_node

    def delete_key(self, index):
        """
        删除关键字
        :param index: 待删除关键字索引
        :return:
        """
        # 获取该关键字
        key = self.keys[index]

        while index < self.key_num - 1:
            # 将 index 位置右边的元素左移
            self.keys[index] = self.keys[index + 1]
            index += 1

        self.pop_key()
        return key

    def delete_value(self, index):
        """
        删除卫星数据
        :param index: 待删除卫星数据索引
        :return:
        """
        # 获取指定值
        value = self.values[index]
        # 获取当前最后一个有效值的位置索引
        final_index = len(
            [tmp_value for tmp_value in self.values if tmp_value is not None]) - 1

        while index < final_index:
            # 将 index 位置右边的元素左移
            self.values[index] = self.values[index + 1]
            index += 1

        self.pop_value()
        return value

    def delete_child(self, index):
        """
        删除子结点
        :param index: 待删除子结点索引
        :return:
        """
        child = self.childs[index]

        # 获取当前最后一个有效子结点的位置索引
        final_index = len(
            [tmp_child for tmp_child in self.childs if tmp_child is not None]) - 1

        while index < final_index:
            # 将 index 右侧的子结点左移
            self.childs[index] = self.childs[index + 1]
            index += 1

        self.pop_child()
        return child

    def pop_key(self):
        """
        弹出关键字列表最后一个元素，并将关键字列表恢复标准
        """
        key = self.keys[self.key_num - 1]
        self.keys[self.key_num - 1] = None
        self.key_num -= 1
        return key

    def pop_value(self):
        """
        弹出卫星数据列表最后一个元素，并将卫星数据列表恢复标准
        """
        index = len([value for value in self.values if value is not None]) - 1
        value = self.values[index]
        self.values[index] = None
        return value

    def pop_child(self):
        """
        弹出子结点列表最后一个元素，并将子结点列表恢复标准
        """
        index = len([child for child in self.childs if child is not None]) - 1
        child = self.childs[index]
        self.childs[index] = None
        return child


class BPTree:
    """
    B+树对象
    """

    def __init__(self, domain=5, path='', index_name='', is_new=False):
        """
        实例化 B+树
        :param domain: B+树的域
        :param path: B+树 保存路径
        :param index_name: 索引名称
        :param is_new: 是否新建 B+树
        """
        self.root = None
        self.head = None
        self.domain = domain
        self._init_tree()
        self.path = path
        self.name = index_name

        if is_new:
            self.__dump_tree()

        self.__load_tree()

    def _init_tree(self):
        """
        创建 B+树
        :return:
        """
        node = BPNode(domain=self.domain, is_leaf=True)
        self.root = node
        self.head = node

    def make_tree(self, keys, values):
        """
        依据传入数据直接构建 B+树
        :param keys: 关键字列表
        :param values: 卫星数据列表
        :return:
        """
        if len(keys) != len(values):
            # 键与值数量不等
            return None

        for i in range(len(keys)):
            # 循环插入结点
            self.insert_item(key=keys[i], value=values[i])
        else:
            # 所有数据正常插入，返回当前树
            self.__dump_tree()
            return self

        return None

    def traversal_tree(self):
        """
        遍历 B+树
        :return:
        """
        keys = []
        values = []
        node = self.head
        while node:
            keys += [key for key in node.keys if key is not None]
            values += [value for value in node.values if value is not None]
            node = node.next
        return {
            'keys': keys,
            'values': values
        }

    def _split_node(self, node, index):
        """
        拆分结点
        当结点的关键字满时，将结点拆分为两个新结点并重新链接至 B+树
        左结点持有原结点前 domain - 1 个数据，右结点持有 domain 个数据
        :param node: 待拆分结点
        :param index: 子结点索引
        :return:
        """
        old_node = node.childs[index]  # 获取待拆分原结点

        # 根据原结点信息创建新结点
        new_node = BPNode(domain=self.domain, is_leaf=old_node.is_leaf)

        for _ in range(self.domain):
            # 将后 t 个数据转移到新结点中
            new_node.insert_key(0, old_node.pop_key())
            new_node.insert_child(0, old_node.pop_child())
            if new_node.is_leaf:
                new_node.insert_value(0, old_node.pop_value())

        # 在父结点中，注册新结点
        node.insert_key(index + 1, new_node.keys[0])
        node.insert_child(index + 1, new_node)

        if old_node.is_leaf:
            # 若原结点为叶子结点，就要维护数据链表
            new_node.next, old_node.next = old_node.next, new_node

    def _merge_node(self, node, index):
        """
        合并结点
        当结点只有 domain - 1 个关键字，且左结点或右结点也仅有 domain - 1 个关键字时，合并两个结点
        :param node: 父结点
        :param index: 子结点索引
        :return:
        """
        old_node = node.childs[index]  # 待合并原结点

        # 获取左兄弟，若不存在则为None
        left_bro = node.childs[index - 1] if index > 0 else None
        # 获取右兄弟，若不存在则为None
        right_bro = node.childs[index + 1] if index < node.key_num - 1 else None

        if left_bro and left_bro.key_num <= self.domain - 1:
            # 情况一，存在左兄弟结点，且左兄弟结点仅有 domain - 1 个关键字，则与左兄弟结点合并
            while old_node.key_num > 0:
                # 将原结点数据合并到左兄弟结点中
                left_bro.append_key(old_node.delete_key(0))
                left_bro.append_child(old_node.delete_child(0))
                if old_node.is_leaf:
                    # 若为叶子结点，则需添加数据
                    left_bro.append_value(old_node.delete_value(0))

            if old_node.is_leaf:
                # 若为叶子结点，维护数据链表
                left_bro.next = old_node.next

            # 在父结点中删除原结点
            node.delete_key(index)
            node.delete_child(index)

            return True

        elif right_bro and right_bro.key_num <= self.domain - 1:
            # 情况二，存在右兄弟结点，且右兄弟结点仅有 t-1 个关键字，则与右兄弟合并
            while right_bro.key_num > 0:
                # 将右兄弟结点数据合并到原结点中
                old_node.append_key(right_bro.delete_key(0))
                old_node.append_child(right_bro.delete_child(0))
                if old_node.is_leaf:
                    # 若为叶子结点，则需添加数据
                    old_node.append_value(right_bro.delete_value(0))

            if old_node.is_leaf:
                # 若为叶子结点，维护数据链表
                old_node.next = right_bro.next

            # 在父结点中删除右兄弟结点
            node.delete_key(index + 1)
            node.delete_child(index + 1)

            return True

        # 情况三：左右结点均不满足条件，则无法合并
        return False

    def _rotation(self, node, index):
        """
        关键字旋转
        当结点的关键字满时，检查相邻兄弟结点是否有空余位置；
        如果有则将一部分关键字转移到相邻兄弟结点，优先左兄弟结点。
        该操作有助于减少高消耗的结点拆分操作。
        :param node: 父结点
        :param index: 子结点索引
        :return:
        """
        target_node = node.childs[index]  # 目标结点

        # 获取左兄弟，若不存在则为None
        left_bro = node.childs[index - 1] if index > 0 else None
        # 获取右兄弟，若不存在则为None
        right_bro = node.childs[index + 1] if index < node.key_num - 1 else None

        '''
        无限旋转的坑：
        
        问题描述：当目标结点为满结点，响铃兄弟结点只有一个空余位置，且旋转处于两节点之 间的边界关键字时，会出现两个相邻兄弟结点相互旋转的死循环
        
        示例：domain=2, [1,2] [3,5,6]，后者为目标结点，做插入关键字 4 的操作定位结点索引为 1 ，关键字 3 做左旋，结果为[1,2,3] [5,6]，
            此时重新定位结点索引为 0 ，需要关键字 3 做右旋，又回到最初状态，陷入死循环
            
        解决方案：需要保证兄弟结点至少有两个空余位置，才可以做旋转
        '''
        if left_bro and left_bro.key_num < 2 * self.domain - 2:
            # 情况一，左兄弟存在，且有至少两个空余位置

            # 目标结点第一个数据左旋
            left_bro.append_key(target_node.delete_key(0))
            left_bro.append_child(target_node.delete_child(0))
            if target_node.is_leaf:
                left_bro.append_value(target_node.delete_value(0))

            # 更新父结点中的子结点分割边界
            node.keys[index] = node.childs[index].keys[0]
            return True

        elif right_bro and right_bro.key_num < 2 * self.domain - 2:
            # 情况二，右兄弟存在，且至少两个空余位置

            # 目标结点的最后一个数据右旋
            right_bro.insert_key(0, target_node.pop_key())
            right_bro.insert_child(0, target_node.pop_child())
            if target_node.is_leaf:
                right_bro.insert_value(0, target_node.pop_value())

            # 更新父结点中的子结点分割边界
            node.keys[index + 1] = node.childs[index + 1].keys[0]

            return True

        # 情况三，上述两种情况都不满足，返回 False
        return False

    def _de_rotation(self, node, index):
        """
        关键字逆旋转
        当结点仅有 domain - 1 个关键字时，检查相邻兄弟结点是否有多于 domain - 1 个关键字；
        如果有，则从相邻兄弟结点转移一部分关键字到该结点，优先左兄弟结点。
        该操作有助于减小高消耗的结点合并操作.
        :param node: 父结点
        :param index: 子结点索引
        :return:
        """
        target_node = node.childs[index]  # 目标结点

        # 获取左兄弟，若不存在则为None
        left_bro = node.childs[index - 1] if index > 0 else None
        # 获取右兄弟，若不存在则为None
        right_bro = node.childs[index + 1] if index < node.key_num - 1 else None

        if left_bro and left_bro.key_num > self.domain - 1:
            # 情况一，左兄弟存在，且关键字数量大于 domain - 1

            # 目标结点最后一个数据右旋
            target_node.insert_key(0, left_bro.pop_key())
            target_node.insert_child(0, left_bro.pop_key())
            if target_node.is_leaf:
                target_node.insert_value(0, left_bro.pop_value())

            # 更新父结点中的子结点分割边界
            node.keys[index] = node.childs[index].keys[0]

            return True

        elif right_bro and right_bro.key_num > self.domain - 1:
            # 情况二，右兄弟存在，且关键字数量大于 domain - 1

            # 目标结点第一个数据左旋
            target_node.append_key(right_bro.delete_key(0))
            target_node.append_child(right_bro.delete_child(0))
            if target_node.is_leaf:
                target_node.append_value(right_bro.delete_value(0))

            # 更新父结点中的子结点分割边界
            node.keys[index + 1] = node.childs[index + 1].keys[0]

            return True

        # 情况三，上述两种情况都不满足，返回 False
        return False

    def _insert_not_full(self, node, key, value):
        """
        非满结点插入操作
        :param node: 父结点
        :param key: 关键字
        :param value: 卫星数据
        :return:
        """
        if node.is_leaf:
            # 情况一，结点为叶子结点，直接进行插入
            index = node.key_num - 1  # 获取当前关键字长度

            while index >= 0 and key < node.keys[index]:
                # 寻找关键字插入位置的索引
                index -= 1

            index += 1  # 上述寻找过程为找到比待插入关键字小的，故加一

            node.insert_key(index, key)
            node.insert_value(index, value)

        else:
            # 情况二，结点为内部结点
            if key < node.keys[0]:
                # 若 key 小于现有的最小关键字，则 key 则成为最小关键字
                node.keys[0] = key

            index = node.key_num - 1
            while index >= 0 and key < node.keys[index]:
                # 寻找关键字插入位置的索引
                index -= 1

            if node.childs[index].key_num >= 2 * self.domain - 1:
                # 情况二A，结点 node 已满，则对 node 先做旋转，若失败则做拆分
                if not self._rotation(node, index):
                    self._split_node(node, index)

                # 递归插入，知道叶子结点为止
                self._insert_not_full(node.childs[index], key, value)
            else:
                # 情况二B，结点 node 未满，直接插入
                self._insert_not_full(node.childs[index], key, value)

    def insert_item(self, key, value):
        """
        插入数据
        :param key: 关键字
        :param value: 卫星数据
        :return:
        """
        root = self.root
        ''' if self.__check_exist:
            raise Exception(f'{key}已存在，请检查后重试') '''

        if root.key_num >= 2 * self.domain - 1:
            # 若根结点已满，先做拆分和升高操作
            node = BPNode(domain=self.domain, is_leaf=False)
            self.root = node
            node.childs[0] = root
            node.insert_key(0, root.keys[0])
            self._split_node(node, 0)

        self._insert_not_full(self.root, key, value)

    def delete_item(self, node, key):
        """
        删除数据
        :param node: 待操作结点
        :param key: 关键字
        :return:
        """
        index = node.key_num - 1
        while index >= 0 and key < node.keys[index]:
            index -= 1

        if node.is_leaf:
            # 情况一，结点为叶子结点，直接删除
            tmp_index = node.keys.index(key)
            if tmp_index > -1:
                # 若关键字存在，删除关键字与卫星数据
                node.delete_key(tmp_index)
                node.delete_value(tmp_index)
        else:
            # 情况二，结点为内部结点
            if index < 0:
                # key 小于树的最小值，证明不在树中
                return
            if node.childs[index].key_num <= self.domain - 1:
                # 情况二A，结点仅有 domain - 1 个关键字，则对结点先做逆旋转，若失败则做合并
                if not self._de_rotation(node, index):
                    self._merge_node(node, index)
                    if index > node.n - 1 or key < node.keys[index]:
                        index -= 1

            if key == node.keys[index]:
                # 情况二B，关键字 key 正好是分割关键字，使用它的后继代替它
                tmp_node, tmp_index = self.successor(node, index)
                node.keys[index] = tmp_node.keys[tmp_index]

            # 递归删除关键字
            self.delete_item(node.childs[index], key)

    def search_item(self, node, key, is_match=False):
        """
        # todo 允许关键字查找与值查找
        查找关键字
        :param node: 待查找结点
        :param key: 关键字
        :param is_match: 是否模糊检索
        :return:
        """
        index = node.key_num - 1

        while index >= 0 and key < node.keys[index]:
            # 寻找指定关键字的位置索引
            index -= 1

        if index < 0:
            # 若key 小于树的最小值，即为不存在
            if is_match:
                return node, -1
            return None, -1

        if node.is_leaf:
            # 若为叶子结点，直接定位关键字
            if key == node.keys[index]:
                return node, index
            elif is_match:
                return node, -1
            else:
                return None, -1

        # 递归搜索
        return self.search_item(node.childs[index], key)

    def update_item(self, key, value):
        """
        修改关键字与卫星数据
        :param key: 关键字
        :param value: 卫星数据
        :return:
        """
        node, index = self.search_item(self.root, key)
        if node is not None:
            node.values[index] = value

    def update_key(self, old_key, new_key):
        """
        替换关键字
        :param old_key: 旧关键字
        :param new_key: 新关键字
        :return:
        """
        node, index = self.search_item(self.root, old_key)
        if node is not None:
            node.keys[index] = new_key

    def get_key(self, value):
        node = self.head
        while node:
            keys = [tmp_key for tmp_key in node.keys if tmp_key is not None]
            values = [tmp_value for tmp_value in node.values if tmp_value is not None]

            for i in range(len(values)):
                if values[i] == value:
                    return keys[i]

            node = node.next
        return None

    def get_height(self):
        """
        获取 B+树高度
        :return:
        """
        node = self.root
        height = 1
        while node:
            node = node.childs[0]
            height += 1
        return height

    @staticmethod
    def minimum(node):
        """
        获取最小关键字结点与位置索引
        :param node:
        :return:
        """
        while node.childs[0]:
            node = node.childs[0]
        return node, 0

    @staticmethod
    def maximum(node):
        """
        获取最大关键字结点与索引
        :param node: 父结点
        :return:
        """
        while node.childs[node.key_num - 1]:
            node = node.childs[node.key_num - 1]
        return node, node.key_num - 1

    def max_key(self):
        """
        获取最大关键字
        :return:
        """
        node = self.root
        while node.childs[node.key_num - 1]:
            node = node.childs[node.key_num - 1]
        return node.keys[node.key_num - 1]

    def min_key(self):
        """
        获取最小关键字
        :return:
        """
        node = self.root
        while node.childs[0]:
            node = node.childs[0]
        return node.keys[0]

    def get_data(self, key):
        """
        获取指定关键字的卫星数据
        :param key:
        :return:
        """
        node, index = self.search_item(self.root, key)
        if not node:
            return None
        value = node.values[index]
        return value

    def get_range_data(self, left_key=None, right_key=None, left_equal=True, right_equal=True):
        """
        获取范围内数据
        :param right_equal: 右区间等号
        :param left_equal: 左区间等号
        :param left_key: 范围最小值
        :param right_key: 范围最大值
        :return:
        """
        if left_key is not None and left_key > self.max_key():
            # 左区间大于最大值
            return None

        if right_key is not None and right_key < self.min_key():
            # 右区间小于最小值
            return None

        if right_key is None and left_key is None:
            return None

        elif left_key is None:
            # 左区间为空，即条件为 < 或 <=

            if (right_equal and right_key >= self.max_key()) or (not right_equal and right_key > self.max_key()):
                # 右区间大于或等于最大值，返回全部
                values = self.traversal_tree()['values']
                return values

            values = []
            node = self.head
            while node:
                # 从头开始遍历树
                for i in range(node.key_num):
                    if node.keys[i] is None:
                        # 跳过空值
                        continue

                    if right_equal is True and node.keys[i] <= right_key:
                        # 条件为 <=
                        values.append(node.values[i])

                    elif right_equal is False and node.keys[i] < right_key:
                        # 条件为 <
                        values.append(node.values[i])

                    else:
                        # 不满足条件，则遍历完成
                        return values

                node = node.next

        elif right_key is None:
            # 右区间为空，即条件为 > 或 >=

            if (left_equal and left_key <= self.min_key()) or (not left_equal and left_key < self.min_key()):
                # 左区间小于或等于最小值，返回全部
                values = self.traversal_tree()['values']
                return values

            node, _ = self.search_item(self.root, left_key, is_match=True)

            values = []

            if node is None:
                # 若不存在左条件结点，则找最近的满足条件结点
                node = self.head
                while left_key > node.keys[node.key_num-1]:
                    node = node.next

            while node:
                for key in node.keys:
                    if key is None:
                        continue
                    if (left_equal is False and key == left_key) or key < left_key:
                        continue
                    value = self.get_data(key)
                    values.append(value)
                node = node.next

            return values

        else:
            node, _ = self.search_item(self.root, left_key, is_match=True)
            values = []
            while node:
                for key in node.keys:
                    if key is None:
                        continue
                    if (left_equal is False and key == left_key) or key < left_key:
                        continue
                    if (right_equal is True and key > right_key) or key >= right_key:
                        break
                    value = self.get_data(key)
                    values.append(value)
                node = node.next
            return values

    def predecessor(self, node, index):
        """
        获取指定关键字前驱
        :param node: 父结点
        :param index: 索引
        :return:
        """
        if node.is_leaf:
            if index <= 0:
                return None, -1
            return node, index - 1
        return self.maximum(node.childs[index])

    def successor(self, node, index):
        """
        获取指定关键字后继
        :param node: 父结点
        :param index: 索引
        :return:
        """
        if node.is_leaf:
            if index >= node.key_num - 1:
                return None, -1
            return node, index + 1
        return self.minimum(node.childs[index])

    def leaf_count(self):
        count = 0
        node = self.root
        while node:
            count += 1
            node = node.next
        return count

    def commit(self):
        """
        提交修改
        :return:
        """
        self.__dump_tree()

    def rollback(self):
        """
        回滚修改
        :return:
        """
        self.__load_tree()

    def __dump_tree(self):
        """
        保存 B+树对象
        :return:
        """
        limit = self.leaf_count() if self.leaf_count() > 1000 else 1000
        sys.setrecursionlimit(limit + 10)
        path = join_path(self.path, self.name) + '.idx'  # 构造表对象存储路径
        dump_obj(path, self)
        sys.setrecursionlimit(1000)

    def __load_tree(self):
        """
        加载 B+树对象
        :return:
        """
        limit = self.leaf_count() if self.leaf_count() > 1000 else 1000
        sys.setrecursionlimit(limit + 10)
        path = join_path(self.path, self.name) + '.idx'  # 构造表对象存储路径
        obj = load_obj(path)  # 获取表对象
        self.__dict__ = obj.__dict__  # 映射对象值
        sys.setrecursionlimit(1000)
