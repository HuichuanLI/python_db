from threading import Thread


class TransactionWorker(Thread):
    """
    事务操作对象
    """
    def __init__(self, func, in_queue, out_queue, **kwargs):
        super().__init__(**kwargs)
        self.func = func
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        for item in self.in_queue:
            # 遍历事务操作子内容
            result = self.func(item)
            if result:
                self.out_queue.put(result)
