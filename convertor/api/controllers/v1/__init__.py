import datetime

import pecan
from pecan import rest
import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from convertor.api.controllers import link
from convertor.api.controllers.v1 import task
from convertor.api.controllers.v1 import versions


class APIBase(wtypes.Base):

    created_at = wsme.wsattr(datetime.datetime, readonly=True)
    """The time in UTC at which the object is created"""

    updated_at = wsme.wsattr(datetime.datetime, readonly=True)
    """The time in UTC at which the object is updated"""

    deleted_at = wsme.wsattr(datetime.datetime, readonly=True)
    """The time in UTC at which the object is deleted"""

    def as_dict(self):
        """Render this object as a dict of its fields."""
        return dict((k, getattr(self, k))
                    for k in self.fields
                    if hasattr(self, k) and
                    getattr(self, k) != wsme.Unset)

    def unset_fields_except(self, except_list=None):
        """Unset fields so they don't appear in the message body.
        :param except_list: A list of fields that won't be touched.
        """
        if except_list is None:
            except_list = []

        for k in self.as_dict():
            if k not in except_list:
                setattr(self, k, wsme.Unset)


class MediaType(APIBase):
    """A media type representation."""

    base = wtypes.text
    type = wtypes.text

    def __init__(self, base, type):
        self.base = base
        self.type = type


class V1(APIBase):
    """The representation of the version 1 of the API."""

    id = wtypes.text
    """The ID of the version, also acts as the release number"""

    media_types = [MediaType]
    """An array of supcontainersed media types for this version"""

    tasks = [link.Link]
    """Links to the tasks resource"""

    links = [link.Link]
    """Links that point to a specific URL for this version and documentation"""

    @staticmethod
    def convert():
        v1 = V1()
        v1.id = "v1"
        base_url = pecan.request.application_url
        v1.links = [link.Link.make_link('self', base_url,
                                        'v1', '', bookmark=True)
                    ]
        v1.media_types = [MediaType('application/json',
                          'application/vnd.openstack.convertor.v1+json')]
        v1.tasks = [link.Link.make_link('self', base_url,
                                          'tasks', ''),
                    link.Link.make_link('bookmark',
                                        base_url,
                                        'tasks', '',
                                        bookmark=True)
                    ]
        return v1


class Controller(rest.RestController):
    """Version 1 API controller root."""

    tasks = task.TasksController()

    @wsme_pecan.wsexpose(V1)
    def get(self):
        # NOTE: The reason why convert() it's being called for every
        #       request is because we need to get the host url from
        #       the request object to make the links.
        return V1.convert()


__all__ = ("Controller", )