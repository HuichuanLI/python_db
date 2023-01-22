from queue import Queue


class OneWayQueue(Queue):
    """单向队列"""
    STOP_FLAG = 'OVER'

    def close(self):
        self.put(self.STOP_FLAG)

    def __iter__(self):
        while True:
            item = self.get()
            try:
                if item == self.STOP_FLAG:
                    return
                yield item
            finally:
                self.task_done()