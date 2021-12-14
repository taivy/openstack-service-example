import abc


class BaseWorker(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def execute(self, task_uuid):
        raise NotImplementedError()
