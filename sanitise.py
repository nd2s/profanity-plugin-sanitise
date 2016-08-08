from io import StringIO
from lxml import etree
from lxml.etree import _ElementUnicodeResult 
import prof

# ROADMAP
#
# Version 1:
#   Automatically detect contacts' client and sanitise if necessary. 
# 
# Version 2:
#   "/sanitise on|off": global auto detect setting
#   "/sanitise <jid> on|off|<mode>": setting per JID: can be autodetect, off,
#                                    or a special "mode" (if there are any).

# Stores client information. JID/str~>Client/str.
clients = {}

def prof_init(version, status, account_name, jid):
    # TODO
    pass

def prof_on_presence_stanza_receive(stanza):
    """ Send a software version request when a contact comes online.
    """
    # TODO
    return True

def prof_on_iq_stanza_receive(stanza):
    """ Listen for software version responses and save results in the
        'clients' store.
    """
    # TODO
    return True

def prof_pre_chat_message_display(jid, message):
    """ Sanitises chat room messages if necessary.
    """
    if jid not in clients:
        return message
    return get_sanitiser(clients[jid])(message)

# Sanitiser functions:

def get_sanitiser(client):
    """ Returns appropriate sanitiser function for the given
        Jabber client (string).
    """
    if client.startswith('Adium'):
        return try_sanitise
    else:
        return lambda msg: msg

def sanitise(message):
    """ Cleans message from HTML. Raises exceptions on problems.
    """
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(message), parser)
    elems = tree.xpath('(//br|//a|//*[not(self::a)]/text())')
    return "".join(map(substitude, elems))

def try_sanitise(message):
    """ Same as 'sanitise' but returns unmodified message if it encounters
        a problem, instead of throwing an exception.
    """
    try:
        return sanitise(message)
    except:
        return message

def substitude(elem):
    """ Substitudes an lxml element with a string representation.
    """
    if type(elem) is _ElementUnicodeResult:
        return str(elem)
    else:
        if elem.tag == 'br':
            return "\n"
        elif elem.tag == 'a':
            text = elem.text or ''
            href = elem.get('href', '')
            if not text and not href:
                return ''
            elif text == href:
                return href
            else:
                return "%s (%s)" % (text, href)
        else:
            raise Exception("unhandled tag <%s>" % elem.tag)

