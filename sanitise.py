from io import StringIO
from lxml import etree
from lxml.etree import _ElementUnicodeResult, _ElementStringResult
import prof

# ROADMAP
#
# Version 2:
#   "/sanitise on|off": global auto detect setting
#   "/sanitise <jid> on|off|<mode>": setting per JID: can be autodetect, off,
#                                    or a special "mode" (if there are any).

iq_count = 1

# Stores client information. JID/str~>Client/str.
clients = {}

def prof_on_presence_stanza_receive(stanza):
    """ Send a software version request when a contact comes online.
    """
    full_jid = etree.fromstring(stanza).get("from")
    if full_jid:
        send_version_request(full_jid)
    return True

def send_version_request(full_jid):
    global iq_count

    iq = etree.Element("iq", {
        "type": "get",
        "to":   full_jid,
        "id":   "sanitiser_" + str(iq_count)
    })
    etree.SubElement(iq, "query", {
        "xmlns": "jabber:iq:version"
    })

    iq_count = iq_count + 1
    prof.send_stanza(etree.tostring(iq))

def prof_on_iq_stanza_receive(stanza):
    """ Listen for software version responses and save results in the
        'clients' store.
    """
    iq = etree.fromstring(stanza)
    id = iq.get("id")
    if not id:
        return True
    if not id.startswith("sanitiser_"):
        return True
    full_jid = iq.get("from")
    if not full_jid:
        return False
 
    query = iq.find("{jabber:iq:version}query")
    if query is None:
        return False
    client = query.find("{jabber:iq:version}name")
    if client is not None:
        clients[full_jid] = client.text
    return False

def prof_pre_chat_message_display(jid, resource, message):
    """ Sanitises chat room messages if necessary.
    """
    full_jid = "%s/%s" % (jid, resource)
    if full_jid not in clients:
        return message
    return get_sanitiser(clients[full_jid])(message)

# Sanitiser functions:

def get_sanitiser(client):
    """ Returns appropriate sanitiser function for the given
        Jabber client (string).
    """
    if client.startswith('Adium'):
        return sanitise
    else:
        return lambda msg: msg

def sanitise(message):
    """ Cleans message from HTML. Raises exceptions on problems.
    """
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(unicode(message)), parser)
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
    if type(elem) in (_ElementUnicodeResult, _ElementStringResult):
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

