
from nevow import inevow

"""
barely started- this sortof works on my mozilla Accept string
"""

class AcceptHeader:
    """parser for the Accept request header field. see
    http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html"""
    def __init__(self,ctx=None,accept_value=None):
        if accept_value is None:
            accept_value = inevow.IRequest(ctx).getHeader("Accept")

        if accept_value is None:
            self.media_ranges = []
        else:
            self.media_ranges = accept_value.split(",")

    def accepts(self,media_type):

        """for a media type (such as 'text/plain'), returns False if
        the media type is not accepted, or else returns the most
        preferred media type that satisfies your arguments.  """
        
        if not self.media_ranges:
            # "If no Accept header field is present, then it is
            # assumed that the client accepts all media types"
            return media_type
            
        for mr in self.media_ranges:
            if mr == media_type or mr.startswith(media_type+";"):
                return mr

        return False
