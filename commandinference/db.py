
class Log(object):
    """
    programs can call these methods to query the log, but they can
    also listen to dispatcher events. The sender will be the string
    'commandinference.db':

    signal 'commandAdded' - every command, args are uri, time, user

    ..more signals for more specific events, so listeners can filter
    better. Things like the tuple ('commandAdded', 'someType')
    
    """
    def addCommand(self, uri, time, user):
        """record a newly issued command

        uri is the command, which may be reused. Since we don't try to
        snapshot all the details of the command or anything, it might
        be hard to reconstruct old commands later. Commands should
        probably not be modified once they've been issued, so this uri
        stays meaningful in the future.

        time is an xs:dateTime Literal with the time the command was
        issued. Normally commands are submitted in order, but we might
        have to insert historical ones sometimes.

        user is the URI of the person who issued the command
        """

    def lastCommandOfClass(self, class_):
        """
        the most recent (command, time, user) entry where the command
        has the given rdf:type
        """
        
