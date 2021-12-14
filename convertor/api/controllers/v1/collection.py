import pecan
from wsme import types as wtypes

from convertor.api.controllers import base
from convertor.api.controllers import link


class Collection(base.APIBase):

    next = wtypes.text
    """A link to retrieve the next subset of the collection"""

    @property
    def collection(self):
        return getattr(self, self._type)

    def has_next(self, limit):
        """Return whether collection has more items."""
        return len(self.collection) and len(self.collection) == limit

    def get_next(self, limit, url=None, marker_field="uuid", **kwargs):
        """Return a link to the next subset of the collection."""
        if not self.has_next(limit):
            return wtypes.Unset

        resource_url = url or self._type
        q_args = ''.join(['%s=%s&' % (key, kwargs[key]) for key in kwargs])
        next_args = '?%(args)slimit=%(limit)d&marker=%(marker)s' % {
            'args': q_args, 'limit': limit,
            'marker': getattr(self.collection[-1], marker_field)}

        return link.Link.make_link('next', pecan.request.host_url,
                                   resource_url, next_args).href
