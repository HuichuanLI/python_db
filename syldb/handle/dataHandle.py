import base64


def decode_data(content):
    """
    解码数据
    :param content: 待解码内容
    :return: 解码后数据
    """
    content = base64.decodebytes(content)
    return content.decode()[::-1]


def encode_data(content):
    """
    编码数据
    :param content: 待编码内容
    :return: 编码后数据
    """
    content = content[::-1].encode()
    return base64.encodebytes(content)
