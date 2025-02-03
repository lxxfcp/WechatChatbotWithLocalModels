from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)

    chats = relationship("Conversation", back_populates="owner")

class Bot(Base):
    __table__ = "bots"

    appid = Column(String, primary_key=True)

    chats = relationship("Conversation", back_populates="bot")

class Conversation(Base):
    __tablename__ = "conversation"

    owner_id = Column(String, ForeignKey("users.id"), primary_key=True)
    bot_id = Column(String, ForeignKey("bots.id"),primary_key=True)
    title = Column(String, index=True)
    description = Column(String, index=True)

    owner = relationship("User", back_populates="chats")
    bot = relationship("Bot", back_populates="chats")