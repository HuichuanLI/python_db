import os
import random
import string
from configparser import ConfigParser

from syldb.tools.fileTools import join_path, is_exists, touch
from syldb.conf import Config


class ConfigHandle:
    """
    配置文件操作对象
    """

    def __init__(self, path, file_name, content=None):
        """
        初始化对象
        :param path: 配置文件路径
        :param file_name: 配置文件名称
        :param content: 配置文件内容
        """
        self.__path = path
        self.__file_name = file_name

        # 实例化一个 ConfigParser 对象
        self.__config = ConfigParser(allow_no_value=True)

        if not content:
            # 若配置文件内容为空，则获取默认配置内容
            self.__content = self.__default_config()
        else:
            self.__content = content

        if not is_exists(join_path(self.__path, self.__file_name)):
            # 配置文件不存在，则创建配置文件
            self.create_config_file(content=self.__default_config())

        self.__get_config()  # 获取配置文件

    @staticmethod
    def __default_config():
        """
        获取默认配置
        :return:
        """
        return {
            'user': {
                'user_name': 'root',
                'password': '',
            },
            'system': {
                'data_path': join_path(os.getcwd(), 'syldb', 'data'),
                'work_path': join_path(os.getcwd(), 'syldb')
            },
            'store': {
                'page_size': 10000,
            }
        }

    @staticmethod
    def __random_password():
        """
        随机生成一个长度为 10 的密码
        :return: 随机密码
        """
        return "".join([random.choice(string.ascii_letters) for i in range(10)])

    @staticmethod
    def __check_password(password):
        """
        检查密码是否满足条件
        :param password: 待检查密码
        :return:
        """
        return '%' in password or '#' in password

    def create_config_file(self, content):
        """
        创建配置文件
        :param content: 配置文件内容
        :return:
        """
        # 创建配置文件
        path = touch(self.__path, self.__file_name)

        # 提示用户输入 root 账号的密码
        password = str(input('Enter the root password:'))
        if password == '':
            # 若用户未输入，则生成随机密码
            password = self.__random_password()
            # 告知用户默认密码
            print(f'root default password: {password}')
        elif self.__check_password(password):
            while self.__check_password(password):
                password = str(input('Password can not contain "%" or "#". Please enter again: '))

        content['user']['password'] = password

        for section, tmp in content.items():
            # 循环遍历嵌套字典，添加结点与数据
            if not self.__config.has_section(section):
                # 容错操作，防止冲突
                self.__config.add_section(section)

                for key, value in tmp.items():
                    if not self.__config.has_option(section, key):
                        # 容错操作，防止冲突
                        # 配置文件的值必须为 string 格式，因此需要做一次强制转义
                        self.__config.set(section, key, str(value))

        # 往文件中写入数据
        self.__config.write(open(path, 'w'))

    def __get_config(self):
        """
        加载配置文件
        :return:
        """
        # 读取配置文件
        self.__config.read(join_path(self.__path, self.__file_name), encoding='utf-8')

        # 实例化配置对象
        db_config = Config()

        # 获取所有的节点
        all_sections = self.__config.sections()
        for section in all_sections:
            # 遍历节点，获取配置信息
            items = self.__config.items(section)

            for key, value in items:
                # 拆包配置信息为键与值
                if not hasattr(db_config, key):
                    # 容错操作，防止配置冲突，配置项唯一
                    # 将配置信息以键为属性，创建到配置对象中
                    setattr(db_config, key, value)
