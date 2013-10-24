from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from uuid import uuid4
import bcrypt
import datetime
from snakepit.sqltypes import GUID, JSONEncodedValue

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(GUID, primary_key = True, default = uuid4)
    name = Column(String)
    email = Column(String)
    passhash = Column(String)

    def __init__(self, name, email, password, id = None):
        self.id = id
        self.name = name
        self.email = email
        if password is not None:
            self.passhash = bcrypt.hashpw(password, bcrypt.gensalt())

    def __repr__(self):
        return "<User(%r, %r)>" % (self.name, self.email)

    def new_history(self, title):
        h = History(name = title)
        self.histories.append(h)
        return h

history_steps_assoc_table = Table('histories_steps', Base.metadata,
        Column('histories.id', GUID, ForeignKey('histories.id')),
        Column('steps.id', GUID, ForeignKey('steps.id')))

class Step(Base):
    __tablename__ = 'steps'

    id = Column(GUID, primary_key = True, default = uuid4)
    created_at = Column(DateTime(timezone = True), default = datetime.datetime.now)
    mimetype = Column(String)
    data = Column(JSONEncodedValue)

    prev_step_id = Column(GUID, ForeignKey('steps.id'), nullable = True)

    previous_step = relationship("Step", backref = backref("next_steps", remote_side = [id], order_by = created_at))


class History(Base):
    __tablename__ = 'histories'

    id = Column(GUID, primary_key = True, default = uuid4)
    name = Column(String)
    created_at = Column(DateTime(timezone = True), default = datetime.datetime.now)
    user_id = Column(GUID, ForeignKey('users.id'))

    user = relationship(User, backref = backref('histories', order_by=created_at))
    steps = relationship(Step, secondary = history_steps_assoc_table)

    def __init__(self, name, **kwargs):
        self.id = kwargs.get("id")
        self.created_at = kwargs.get("created_at")
        self.name = name

    def __repr__(self):
        return "<History(%r, %r)>" % (self.id, self.name)

