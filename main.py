#!/usr/bin/env python

import logging

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from urllib import urlencode

import jinja2
import os
import webapp2

import c2dmutil

import models
class BaseHandler(webapp.RequestHandler):
  def __init__(self):
    self.jinja_env = jinja2.Environment(autoescape=True,
       loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

def redirectUnlessKlaxon(handler, path):
  """redirects user to login screen, unless user-agent contains klaxon."""
  if(handler.request.headers.has_key("user-agent")):
    logging.info(handler.request.headers["user-agent"].lower())
    if( "klaxon" in handler.request.headers["user-agent"].lower()):
      logging.info("looks like klaxon: %s" %
          handler.request.headers["user-agent"].lower())
      handler.response.set_status(401, "Unauthorized")
      handler.response.out.write("Unauthorized. try logging in.")
  handler.redirect(users.create_login_url(path))

class RegistrationHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if not user:
      redirectUnlessKlaxon(self, self.request.path)
      return 
    if self.request.path == "/unregister":
      self.unregister(user)
      return;
    elif self.request.path == "/register":
      self.register(user)
      return;

  def register(self, user):
    token = self.request.get('token')
    requested_sender = self.request.get('sender')

    existingUserQuery = models.Person.gql(
      "WHERE user = :1",
      user)
    p = existingUserQuery.get()
    if p:
      # if tokens match, no changes needed.
      if token == p.registration_id:
        logging.info("User already registered. no work needed.")
        self.response.set_status(200, "already registered.")
      else:
        logging.info("Change of token!")
        p.registration_id = token
        p.put()
        self.response.set_status(200, "Token updated.")

    else:
      logging.info("New user!")
      p = models.Person()
      p.user = user
      p.registration_id = token
      p.enabled = True
      p.put()
      self.response.set_status(200, "Registered new user.")

  def unregister(self, user):
    """Remove the registration token for the current user."""
    if not user:
      redirectUnlessKlaxon(self, "/unregister")
      return
    existingUserQuery = models.Person.gql(
      "WHERE user = :1",
      user)
    p = existingUserQuery.get()
    if p:
      # Clear the registration_id for this user.
      p.registration_id = None
      p.put()
      self.response.set_status(200, "Token removed.")
      self.response.out.write("Token removed. Unregistered.")


class MainHandler(webapp.RequestHandler):

  def get(self):
    self.jinja_env = jinja2.Environment(autoescape=True,
       loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))
    if(self.request.path == "/"):
      template = self.jinja_env.get_template('index.html')
      self.response.write(template.render())
      return
    elif(self.request.path == "/admin"):
      if not users.is_current_user_admin():
        self.response.set_status(401, "Unauthorized")
        self.response.out.write("Unauthorized. try logging in.")
        return
      auth = models.GCMSender.gql('').get() # just grab the first one. there should only be one.
      template = self.jinja_env.get_template('admin.html')
      if not auth :
        self.response.write(template.render())
        return
      self.response.write(
          template.render({'apikey': auth.apikey, 'sender': auth.sender}))
      return
    elif(self.request.path == "/gcmsetup"):
      if not users.get_current_user():
        self.redirect(users.create_login_url(self.request.url))
        return
      # make a qrcode out of our auth info, to help with user setup.
      auth = models.GCMSender.gql('').get()
      template = self.jinja_env.get_template('setup.html')
      hostname = self.request.url[:-1 * len("/gcmsetup")]
      self.response.write(
          template.render({'url': hostname,
                           'sender': auth.sender,
                           'user': users.get_current_user().email()}))
      return

    else:
      template = self.jinja_env.get_template('nope.html')
      self.response.write(template.render())
      return;

  def getQRCodeImageUrl(self, sender, url):
    return "http://chart.apis.google.com/chart?cht=qr&chs=350x350&chld=L&choe=UTF-8&chl=intent%3A%2F%2Forg.nerdcircus.android.klaxon%2Fgcmsetup%3Fsender%3D100533447903%26url%3Dhttps%3A%2F%2Fpagepusher.appspot.com"
    return "http://chart.apis.google.com/chart?cht=qr&chs=350x350&chld=L&choe=UTF-8&chl=intent%3A%2F%2Forg.nerdcircus.android.klaxon%2Fgcmsetup%3Fsender%3D%(sender)s%26url%3D%(url)s" % { 'sender': urlencode(sender), 'url': urlencode(url)}

  def post(self):
    self.jinja_env = jinja2.Environment(autoescape=True,
       loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))
    ak = self.request.get('apikey')
    sender = self.request.get('project_id')
    auth = models.GCMSender.gql('').get() # just grab the first one. there should only be one.
    if not auth:
      auth = models.GCMSender()
    auth.apikey = ak
    auth.sender = sender
    auth.put()
      

class PushTestHandler(webapp.RequestHandler):
  """test by sending a stock push message."""
  def get(self):
    self.jinja_env = jinja2.Environment(autoescape=True,
       loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))
    user = users.get_current_user()
    if not user:
      redirectUnlessKlaxon(self, "/test")
      return;
    #send a test push message.
    c = c2dmutil.C2dmUtil()
    me = models.Person.gql('WHERE user = :1', user).get()
    logging.info(me)
    if( not me ):
      template = self.jinja_env.get_template('base.html')
      self.response.set_status(400, "No Message Sent.")
      self.response.write(template.render({'content': "You are not registered. no message sent."}))
      return;
    logging.info("Sending test message to: %s" % user)
    c.sendMessage(me)
    template = self.jinja_env.get_template('base.html')
    self.response.set_status(200, "C2dm Message Sent.")
    self.response.write(template.render({
        'content': "Message sent. If you do not recieve it, check your settings, and re-register."}))


def main():
  application = webapp.WSGIApplication(
    [('/', MainHandler),
     ('/register', RegistrationHandler),
     ('/unregister', RegistrationHandler),
     ('/test', PushTestHandler),
     ('/.*', MainHandler),
    ], debug=True)

  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
