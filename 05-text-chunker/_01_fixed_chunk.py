from newspaper.images import chunk_size

# 固定长度切割
def split_string_by_n(s, n=5):
    """
    将字符串每 n 个字符切割一次
    """
    return [s[i:i+n] for i in range(0, len(s), n)]

# 示例
if __name__ == '__main__':
    text = "HelloWorldPythonCode"
    result = split_string_by_n(text, 5)
    print(result)
# 输出: ['Hello', 'World', 'Pytho', 'nCode']