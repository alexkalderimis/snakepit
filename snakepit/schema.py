from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from uuid import uuid4 as random_uuid
import bcrypt
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid = True), primary_key = True)
    name = Column(String)
    email = Column(String)
    passhash = Column(String)

    def __init__(self, name, email, password, id = None):
        if id is None:
            self.id = random_uuid()
        else:
            self.id = id
        self.name = name
        self.email = email
        if password is not None:
            self.passhash = bcrypt.hashpw(password, bcrypt.gensalt())

    def __repr__(self):
        return "<User(%r, %r)>" % (self.name, self.email)

class History(Base):
    __tablename__ = 'histories'

    id = Column(UUID(as_uuid = True), primary_key = True)
    name = Column(String)
    created_at = Column(DateTime(timezone = True))
    user_id = Column(UUID(as_uuid = True), ForeignKey('users.id'))

    user = relationship(User, backref = backref('histories', order_by=created_at))

    def __init__(self, name):
        if id is None:
            self.id = random_uuid()
        else:
            self.id = id
        self.name = name
        self.created_at = datetime.datetime.now()

    def __repr__(self):
        return "<History(%r, %r)>" % (self.id, self.name)

