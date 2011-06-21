# largely based on sample code from appengine docs.

import logging, email, re
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
    logging.info("Received a message for: " + self.extractIntendedRecipientEmail(mail_message))
    

application = webapp.WSGIApplication([StoreMessageHandler.mapping()], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
