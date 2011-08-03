# largely based on sample code from appengine docs.

import logging, email, re, urllib
from google.appengine.api import users
from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app

import c2dmutil
import models

INCOMING_MAIL_DOMAIN = 'muncus.appspotmail.com'
INCOMING_ADDRESS_RE = re.compile('(?P<recipient>[a-zA-Z0-9_+.-]+)@' + INCOMING_MAIL_DOMAIN)
INCOMING_FROM_URL_RE = re.compile('/_ah/mail/(?P<recipient>[a-zA-Z0-9_+.%-]+)@' + INCOMING_MAIL_DOMAIN)

MESSAGE_BASE_URL = 'https://muncus.appspot.com/m?msg='

class StoreMessageHandler(InboundMailHandler):
  """Save the message, but dont send c2dm message."""

  def extractIntendedRecipientEmail(self, msg):
    """Find out the email address of the intended user, based on the incoming message"""
    tolist = msg.to.split(",")
    for addr in tolist:
      match = INCOMING_ADDRESS_RE.search(addr)
      if match:
        return re.sub('\+', '@', match.group('recipient'))
    logging.warn("No intended recipient found in list: %s" % msg.to)
    # use the address posted in the path.
    match = INCOMING_FROM_URL_RE.search(urllib.unquote(self.request.path))
    if match:
      return re.sub('\+', '@', match.group('recipient'))
    return None
      
  def receive(self, mail_message):
    intended_recipient = self.extractIntendedRecipientEmail(mail_message)
    logging.info("Received a message for: " + intended_recipient)

    intended_user = users.User(intended_recipient)
    p = models.Person.gql("WHERE user = :1", intended_user).get()
    if not p:
      logging.fatal("User unknown: " + intended_recipient)
      return
    else:
      m = models.Message()
      m.owner = p.user
      m.sender = mail_message.sender
      m.subject = mail_message.subject
      #TODO: make this handle messages better.
      bodies = mail_message.bodies('text/plain')
      m.body = bodies.next()[1].decode()
      #m.body = mail_message.original.as_string()
      #m.body = mail_message.bodies('text/plain')
      #m.email_date = mail_message.date
      m.put()
      logging.info("stored message!")

      c = c2dmutil.C2dmUtil()
      c.sendMessage(p, subject=m.subject, body=m.body, frm=mail_message.sender, url=MESSAGE_BASE_URL+str(m.key().id()))

    

application = webapp.WSGIApplication([StoreMessageHandler.mapping()], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
