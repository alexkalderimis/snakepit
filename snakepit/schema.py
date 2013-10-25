from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from uuid import uuid4
from snakepit.security import hash_pw
import datetime
from snakepit.sqltypes import GUID, JSONEncodedValue

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
    data = Column(JSONEncodedValue)

    prev_step_id = Column(GUID, ForeignKey('steps.id'), nullable = True)

    previous_step = relationship("Step", uselist = False, backref = backref("next_steps", uselist=True, remote_side = [id], order_by = created_at))

    def __init__(self, mimetype, data, id = None):
        self.id = (id or uuid4())
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

    def append_step(self, mimetype, data):
        s = Step(mimetype = mimetype, data = data)
        if len(self.steps):
            s.previous_step = self.steps[-1]

        self.steps.append(s)
        return s

