import pickle


def dump_obj(path, obj):
    """
    保存对象到磁盘
    :param path: 保存路径
    :param obj: 要保存的对象
    :return:
    """
    with open(path, 'wb') as f:
        # 依据文件句柄，保存对象
        pickle.dump(obj, f)


def load_obj(path):
    """
    从磁盘中加载对象
    :param path: 对象所在路径
    :return:
    """
    with open(path, 'rb') as f:
        # 依据文件句柄，获取对象
        obj = pickle.load(f)
    return obj
