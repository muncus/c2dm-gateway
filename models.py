from google.appengine.ext import db

class C2dmSender(db.Model):
  username = db.StringProperty()
  password = db.StringProperty()
  authtoken = db.StringProperty()

class Person(db.Model):
  """Represents a user of this service."""
  user = db.UserProperty()
  enabled = db.BooleanProperty(default=True)
  registration_id = db.StringProperty() # android c2dm registration id.


class Message(db.Model):
  """A message that we are gatewaying."""
  owner = db.UserProperty()
  body = db.TextProperty()
  subject = db.StringProperty()
  sender = db.StringProperty()
  created = db.DateTimeProperty()
  email_date = db.DateTimeProperty() # storing this so we can compute latency of notification.

