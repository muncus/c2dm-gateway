# Helper library for sending c2dm messages.

from google.appengine.api import users
from google.appengine.ext import db

import models

import urllib
import urllib2

class C2dmUtil(object):
  SERVICE_TOKEN_TYPE = 'ac2dm'
  USERAGENT = 'Klaxon-Klaxonc2dmpush-1.0'

  AUTH_URL = 'https://www.google.com/accounts/ClientLogin'
  C2DM_URL = 'http://android.apis.google.com/c2dm/send'

  def __init__(self):
    """load the token, user, and password."""
    self.auth_info = C2dmSender.gql('LIMIT 1').get()

  def getAuthToken(self):
    """if authtoken is empty, make the ClientLogin request."""
    if self.auth_info.authtoken:
      return self.auth_info.authtoken

    post_data = {
      'Email': self.auth_info.username,
      'Passwd': self.auth_info.password,
      'service': SERVICE_TOKEN_TYPE,
      'source': USERAGENT,
      }
    req = urllib2.Request(AUTH_URL, urllib.urlencode(post_data))
    response = urllib2.urlopen(req)
    
    for l in response.readlines():
      if 'Auth=' in l:
        logging.info("Found auth line!")
        self.auth_info.authtoken = l[5:]
        self.auth_info.put()

    return self.auth_info.authtoken

  def sendMessage(self, user):
    """Sends a message to the specified user/Person."""
    #TODO: extend this to take kwargs, or subj/url args.
    
    post_data = {
      'registration_id': user.registration_id,
      'collapse_key': 'c2dmpage',
      'data.foo': 'bar',
    }
    req = urllib2.Request(C2DM_URL, urllib.urlencode(post_data))
    req.add_header('Authorization', 'GoogleLogin auth=%s' % self.auth_info.authtoken)

    resp = urllib2.urlopen(req)

    for l in resp.readlines():
      logging.info(l)
      
