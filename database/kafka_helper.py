# coding:utf8

from kafka import KafkaProducer, KafkaConsumer
from yamls import conf
from common.utils import logger_track


class KafkaHelper(object):
    """kafka消息队列，存放异步爬虫任务"""

    @logger_track
    def __init__(self) -> object:
        self.consumer = KafkaConsumer(bootstrap_servers=[conf.kafka_configs["bootstrap_servers"]],
                                      group_id=conf.kafka_configs["group_id"])
        self.producer = KafkaProducer(bootstrap_servers=[conf.kafka_configs["bootstrap_servers"]])

    def get_task_by_block(self):
        """
        获取任务，阻塞式
        :return:
        """
        self.consumer.subscribe(topics=conf.kafka_configs["topic"])
        while True:
            msg = self.consumer.poll(timeout_ms=5)  # 从kafka获取消息
            if msg != {}:
                return msg
            import time
            time.sleep(0.5)

    def get_task_by_anysc(self):
        """
        获取任务，非阻塞
        :return:
        """
        self.consumer.subscribe(topics=conf.kafka_configs["topic"])
        msg = self.consumer.poll(timeout_ms=3)  # 从kafka获取消息
        return msg

    def put_task(self, task):
        """
        投放任务
        :param task: 任务
        :return:
        """
        self.producer.send(conf.kafka_configs["topic"], task.encode("utf-8"))


if __name__ == '__main__':
    kh = KafkaHelper()
    import time

    while True:
        time.sleep(1)
        kh.put_task("product")
