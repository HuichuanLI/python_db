import os
import shutil


def is_exists(path):
    """
    判断文件是否存在
    :param path: 文件路径
    :return: bool 文件是否存在
    """
    return os.path.exists(path)


def mkdir(path):
    """
    创建文件夹
    :param path: 文件夹路径
    :return: 文件夹路径
    """
    os.makedirs(path)
    return path


def touch(path, file_name, content=''):
    """
    新建文件
    :param path: 文件夹路径
    :param file_name: 文件名
    :param content: 文件内容
    :return: 文件路径
    """
    path = join_path(path, file_name)
    try:
        with open(path, 'w+') as f:
            f.write(content)
        return path
    except Exception as e:
        print(str(e))
        return False


def join_path(*args):
    """
    拼接文件路径
    :param args: 待拼接各级路径
    :return:
    """
    return os.path.join(*args)


def remove_dir(path):
    """
    删除文件夹
    :param path: 文件夹路径
    :return:
    """
    try:
        shutil.rmtree(path)
        return True
    except Exception as e:
        print(str(e))
        return False


def delete_file(path):
    """
    删除文件
    :param path: 文件路径
    :return:
    """
    try:
        os.remove(path)
        return True
    except Exception as e:
        print(str(e))
        return False


def get_all_subobject(path, obj_type):
    """
    获取指定文件夹所有子对象
    :param path: 文件夹路径
    :param obj_type: 子对象类型 [dir | file]
    :return:
    """
    tmp = os.listdir(path)  # 获取文件夹下所有子目录
    result = []
    if obj_type == 'dir':
        for target in tmp:
            # 遍历子目录，判断是否为文件夹类型，若是则添加
            if os.path.isdir(join_path(path, target)):
                result.append(target)
        return result
    elif obj_type == 'file':
        for target in tmp:
            # 遍历子目录，判断是否为文件类型，若是则添加
            if os.path.isfile(join_path(path, target)):
                result.append(target.split('.')[0])
        return result
    else:
        return False
