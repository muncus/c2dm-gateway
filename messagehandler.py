#!/usr/bin/env python

import logging

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import webapp

import models

class MessageHandler(webapp.RequestHandler):
  """ Handler to display, and reply to Messages."""
  def get(self):
    if self.request.get('reply'):
      return self.put() # convenience, for testing.
    msg_key = self.request.get('msg')
    msg = models.Message.get_by_id(int(msg_key))
    if not msg:
      self.response.set_status(404, 'no such message')
      logging.info("Message not found: %s" % msg_key)
      return
    self.response.out.write(msg.body)

  def put(self):
    """Takes two args, 'msg' and 'reply'."""
    msg_key = self.request.get('msg')
    reply = self.request.get('reply')
    msg = models.Message.get_by_id(int(msg_key))

    logging.info("Replying to msg %s, from %s" % msg_key, msg.sender)
    mail.send_mail(
      sender=users.get_current_user().email(),
      subject=msg.subject,
      to=msg.sender,
      body=reply)
    self.response.set_status(200, "Sent reply")
      

def main():
  application = webapp.WSGIApplication(
    [ ('/m.*', MessageHandler),
    ], debug=True)

  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
