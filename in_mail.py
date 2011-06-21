# largely based on sample code from appengine docs.

import logging, email, re
from google.appengine.api import users
from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app

import models

INCOMING_MAIL_DOMAIN = 'pager-gateway.appspotmail.com'
INCOMING_ADDRESS_RE = re.compile('(?P<recipient>[a-zA-Z0-9_+.-]+)@' + INCOMING_MAIL_DOMAIN)

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
      m.subject = mail_message.subject
      #TODO: make this handle messages better.
      m.body = mail_message.original.as_string()
      #m.email_date = mail_message.date
      m.put()
      logging.info("stored message!")

    

application = webapp.WSGIApplication([StoreMessageHandler.mapping()], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
