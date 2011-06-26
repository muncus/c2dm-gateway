#!/usr/bin/env python

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import c2dmutil

import models


class MessageHandler(webapp.RequestHandler):
  """ Handler to display, and reply to Messages."""
  def get(self):
    msg_key = self.request.get('msg')
    msg = models.Message.get_by_key_name(msg_key)
    if not msg:
      self.response.set_status(404, 'no such message')
      return
    self.response.out.write(msg.body)

  def put(self):
    """Takes two args, 'msg' and 'reply'."""
    msg_key = self.request.get('msg')
    reply = self.request.get('reply')
    msg = models.Message.get_by_key_name(msg_key)

    mail.send_mail(
      sender=users.get_current_user().email(),
      subject=msg.subject,
      to=msg.sender,
      body=reply)
    self.response.set_status(200, "Sent reply")
      

class RegistrationHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if not user:
      #self.response.set_status(403, "User not logged in")
      self.redirect(users.create_login_url('/register'))
      return 
    token = self.request.get('token')

    existingUserQuery = models.Person.gql(
      "WHERE user = :1",
      user)
    p = existingUserQuery.get()
    if p:
      # if tokens match, no changes needed.
      if token == p.registration_id:
        self.response.set_status(200, "already registered.")
      else:
        p.registration_id = token
        p.put()
        self.response.set_status(200, "Token updated.")

    else:
      p = models.Person()
      p.user = user
      p.registration_id = token
      p.enabled = True
      p.put()
      self.response.set_status(200, "Registered new user.")


class MainHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write('Hello world!')

class PushTestHandler(webapp.RequestHandler):
  """test by sending a stock push message."""
  def get(self):
    #send a test push message.
    c = c2dmutil.C2dmUtil()
    me = models.Person.gql('WHERE user = :1', users.get_current_user()).get()
    c.getAuthToken()
    c.sendMessage(me)


def main():
  application = webapp.WSGIApplication(
    [('/', MainHandler),
     ('/register', RegistrationHandler),
     ('/m', MessageHandler),
     ('/test', PushTestHandler),
    ], debug=True)

  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
