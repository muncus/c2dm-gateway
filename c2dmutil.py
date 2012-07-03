# Helper library for sending c2dm messages.

from google.appengine.api import users
from google.appengine.ext import db

import models

import logging
import urllib
import urllib2

AUTH_URL = 'https://www.google.com/accounts/ClientLogin'
C2DM_URL = 'http://android.apis.google.com/c2dm/send'
GCM_URL = 'http://android.googleapis.com/gcm/send'
MAX_LENGTH = 1000 # maximum size of data.

class C2dmError(Exception):
  """Parent class for types of exception."""
  pass

def IsValidSender(sender_address):
  """Return true if supplied address is a valid C2dmSender."""
  valid_sender = models.C2dmSender.gql('LIMIT 1').get().username
  if sender_address.strip().lower() == valid_sender.strip().lower():
    return True
  return False

class C2dmUtil(object):
  SERVICE_TOKEN_TYPE = 'ac2dm'
  USERAGENT = 'Klaxon-Klaxonc2dmpush-1.0'

  def __init__(self):
    """load the token, user, and password."""
    self.auth_info = models.C2dmSender.gql('LIMIT 1').get()

  def getAuthToken(self):
    """if authtoken is empty, make the ClientLogin request."""
    if self.auth_info.authtoken:
      return self.auth_info.authtoken

    post_data = {
      'Email': self.auth_info.username,
      'Passwd': self.auth_info.password,
      'service': self.SERVICE_TOKEN_TYPE,
      'source': self.USERAGENT,
      }
    req = urllib2.Request(AUTH_URL, urllib.urlencode(post_data))
    response = urllib2.urlopen(req)
    
    for l in response.readlines():
      if 'Auth=' in l:
        logging.info("Found auth line!")
        token = l[5:].strip()
        self.auth_info.authtoken = token
        self.auth_info.put()

    return self.auth_info.authtoken

  def sendMessage(self, user, retry=True, **kwargs):
    """Sends a message to the specified user/Person."""
    
    post_data = {
      'registration_id': user.registration_id,
      'collapse_key': 'c2dmpage',
    }
    
    data_length = 0
    for k, v in kwargs.iteritems():
      data_length += len(v)
      post_data['data.' + k] = v
    logging.info("Data message length: %d" % data_length)

    if data_length > MAX_LENGTH: 
      #truncate data.body field to fit.
      bytes_to_remove = data_length - MAX_LENGTH
      logging.info("trying to remove %d bytes from the body." % bytes_to_remove)
      post_data['data.body'] = post_data['data.body'][0:-1*bytes_to_remove]

    req = urllib2.Request(GCM_URL, urllib.urlencode(post_data))
    req.add_header('Authorization', 'key=%s' % self.auth_info.apikey)

    resp = urllib2.urlopen(req)

    #ugh. this is resp.code in 2.4, and resp.getcode() in 2.6
    if 401 == resp.code:
      #auth token failure. oh noes!
      if retry:
        logging.warn("Sender Credentials not valid! trying to obtain new credentials.")
        self.getAuthToken()
        return self.sendMessage(user, retry=False)
      else:
        logging.error("Could not obtain functional ClientLogin token!!!!")
        return

    if 503 == resp.code:
      #TODO: handle this better.
      return

    for l in resp.readlines():
      if 'Error=' in l:
        raise C2dmError(l)
      logging.info(l)
      
