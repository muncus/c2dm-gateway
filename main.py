#!/usr/bin/env python

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import models

C2DM_SENDER_ADDRESS = 'klaxon-c2dm@gmail.com'

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


def main():
  application = webapp.WSGIApplication(
    [('/', MainHandler),
     ('/register', RegistrationHandler),
    ], debug=True)

  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
