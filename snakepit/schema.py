from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Unicode, Boolean, UnicodeText
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, backref, deferred
from uuid import uuid4
import datetime

from sqltypes import GUID, JSONEncodedValue
from security import hash_pw

Base = declarative_base()


user_role_assoc_table = Table('users_roles', Base.metadata,
        Column('users_id', GUID, ForeignKey('users.id')),
        Column('roles_id', Integer, ForeignKey('roles.id')))

history_steps_assoc_table = Table('histories_steps', Base.metadata,
        Column('histories_id', GUID, ForeignKey('histories.id')),
        Column('steps_id', GUID, ForeignKey('steps.id')))

class User(Base):
    __tablename__ = 'users'

    id = Column(GUID, primary_key = True, default = uuid4)
    name = Column(String, unique = True)
    email = Column(String)
    passhash = Column(String)

    roles = relationship("Role", secondary = user_role_assoc_table)

    def __init__(self, name, email, password, id = None):
        self.id = (id or uuid4())
        self.name = name
        self.email = email
        if password is not None:
            self.passhash = hash_pw(password)

    def __repr__(self):
        return "<User(%r, %r)>" % (self.name, self.email)

    def new_history(self, title):
        h = History(name = title)
        self.histories.append(h)
        return h

class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key = True)
    name = Column(String(50), unique = True)

class Step(Base):
    __tablename__ = 'steps'

    id = Column(GUID, primary_key = True, default = uuid4)
    created_at = Column(DateTime(timezone = True), default = datetime.datetime.now)
    mimetype = Column(String)
    data = deferred(Column(JSONEncodedValue))
    tool = Column(String(255))

    prev_step_id = Column(GUID, ForeignKey('steps.id'), nullable = True)

    previous_step = relationship("Step", uselist = False, backref = backref("next_steps", uselist=True, remote_side = [id], order_by = created_at))

    def __init__(self, tool, mimetype, data, id = None):
        self.id = (id or uuid4())
        self.tool = tool
        self.mimetype = mimetype
        self.data = data


class History(Base):
    __tablename__ = 'histories'

    id = Column(GUID, primary_key = True, default = uuid4)
    name = Column(String)
    created_at = Column(DateTime(timezone = True), default = datetime.datetime.now)
    user_id = Column(GUID, ForeignKey('users.id'))

    user = relationship(User, backref = backref('histories', order_by=created_at))
    steps = relationship(Step, secondary = history_steps_assoc_table)

    def __init__(self, name, **kwargs):
        self.id = kwargs.get("id", uuid4())
        if "created_at" in kwargs:
            self.created_at = kwargs.get("created_at")
        self.name = name

    def __repr__(self):
        return "<History(%r, %r)>" % (self.id, self.name)

    def append_step(self, tool, mimetype, data):
        s = Step(tool = tool, mimetype = mimetype, data = data)
        if len(self.steps):
            s.previous_step = self.steps[-1]

        self.steps.append(s)
        return s

class Client(Base):
    __tablename__ = "oauth2clients"

    name = Column(Unicode(40))
    description = Column(Unicode(40))
    user_id = Column(GUID, ForeignKey('users.id'))
    user = relationship('User')
    id = Column(Unicode(40), primary_key = True)
    client_secret = Column(Unicode(55), unique = True, index = True, nullable = False)
    is_confidential = Column(Boolean)
    redirect_uris = Column(ARRAY(Unicode(255), as_tuple = True))
    default_scopes = Column(ARRAY(Unicode(255), as_tuple = True))
    allowed_grant_types = Column(ARRAY(Unicode(255), as_tuple = True))
    allowed_response_types = Column(ARRAY(Unicode(255), as_tuple = True))

    @property
    def client_type(self):
        if self.is_confidential:
            return 'confidential'
        return 'public'

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

class Grant(Base):
    __tablename__ = "oauth2grants"

    id = Column(Integer, primary_key = True)
    user_id = Column(GUID, ForeignKey('users.id'))
    user = relationship('User')
    client_id = Column(Unicode(40), ForeignKey('oauth2clients.id'), nullable = False)
    client = relationship('Client')
    code = Column(Unicode(255), index = True, nullable = False)
    redirect_uri = Column(Unicode(255))
    expires = Column(DateTime)
    scopes = Column(ARRAY(Unicode(255), as_tuple = True))

class BearerToken(Base):
    __tablename__ = "oauth2bearertokens"

    id = Column(Integer, primary_key = True)
    user_id = Column(GUID, ForeignKey('users.id'))
    user = relationship('User')
    client_id = Column(Unicode(40), ForeignKey('oauth2clients.id'), nullable = False)
    client = relationship('Client')
    token_type = Column(Unicode(40))
    access_token = Column(Unicode(255), unique=True)
    refresh_token = Column(Unicode(255), unique=True)
    expires_in = Column(Integer, default = (60 ** 2))
    created_at = Column(DateTime, default = datetime.datetime.utcnow)
    scopes = Column(ARRAY(Unicode(255)))

    @property
    def expires(self):
        return self.created_at + datetime.timedelta(seconds = self.expires_in)

