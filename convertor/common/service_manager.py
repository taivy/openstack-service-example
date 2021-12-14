import abc


class ServiceManager(object, metaclass=abc.ABCMeta):

    @abc.abstractproperty
    def service_name(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def api_version(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def publisher_id(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def conductor_topic(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def notification_topics(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def conductor_endpoints(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def notification_endpoints(self):
        raise NotImplementedError()
