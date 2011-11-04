#!/usr/bin/env python

import logging

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.runtime.apiproxy_errors import ApplicationError

import models

class MessageHandler(webapp.RequestHandler):
  """ Handler to display, and reply to Messages."""
  def get(self):
    logging.error("are we even getting here!?")
    if self.request.get('reply'):
      logging.error("are we even getting here?")
      return self.post() # convenience, for testing.
    msg_key = self.request.get('msg')
    msg = models.Message.get_by_id(int(msg_key))
    if not msg:
      self.response.set_status(404, 'no such message')
      logging.info("Message not found: %s" % msg_key)
      return
    self.response.out.write(msg.body)

  def post(self):
    """Takes two args, 'msg' and 'reply'."""
    msg_key = self.request.get('msg')
    reply = self.request.get('reply')
    msg = models.Message.get_by_id(int(msg_key))
    if not msg:
      self.response.set_status(400, "no such message")
      self.response.out.write("no such message.")

    logging.info("Replying to msg %s, from %s, with %s " % (msg_key, msg.sender, reply))
    logging.info("from: %s" % users.get_current_user().email())
    reply_msg = mail.EmailMessage(
      sender=users.get_current_user().email(),
      subject=msg.subject,
      to=msg.sender,
      body=reply)
    reply_msg.check_initialized()

    #logging.error("sender: " + reply_msg.sender)
    #logging.error("to: " + reply_msg.to)
    #logging.error("subject: " + reply_msg.subject)
    #logging.error("body: " + reply_msg.body)

    try:
      reply_msg.send()
      self.response.set_status(200, "Sent reply")
      self.response.out.write("Message sent!")
    except ApplicationError, e:
      logging.exception("Mail sending failed: %s", e)
      self.response.set_status(500, "Reply not sent.")
      self.response.out.write(e)
      

def main():
  application = webapp.WSGIApplication(
    [ ('/m.*', MessageHandler),
    ], debug=True)

  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
