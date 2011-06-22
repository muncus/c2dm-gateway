#!/usr/bin/env python

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import models

C2DM_SENDER_ADDRESS = 'klaxon.c2dm@gmail.com'

class CredentialsHandler(webapp.RequestHandler):
  """handle the submission of our user's credentials."""
  def get(self):
    self.response.out.write("""
    <html>
      <body>
        <form action="/admin" method="post">
          <div> User: <input type="text" name="username" /></div>
          <div> password: <input type="password" name="password" /></div>
          <input type="submit"/>
        </form>
      </body>
    </html>
    """)

  def post(self):
    user = self.request.get('username')
    pw = self.request.get('password')
    auth = models.C2dmSender.gql('').get() # just grab the first one. there should only be one.
    if not auth:
      auth = models.C2dmSender()
    auth.username = user
    auth.password = pw
    auth.put()


def main():
  application = webapp.WSGIApplication(
    [('/admin', CredentialsHandler),
    ], debug=True)

  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
