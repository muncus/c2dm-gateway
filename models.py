from google.appengine.ext import db

class Person(db.Model):
  """Represents a user of this service."""
  user = db.UserProperty(required=True)
  enabled = db.BooleanProperty(default=True)
  registration_id = db.StringProperty() # android c2dm registration id.


class Message(db.Model):
  """A message that we are gatewaying."""
  owner = db.UserProperty()
  body = db.TextProperty()
  subject = db.StringProperty()
  created = db.DateTimeProperty()
  email_date = db.DateTimeProperty() # storing this so we can compute latency of notification.

