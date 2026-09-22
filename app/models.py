from sqlalchemy import Column,Integer,String,JSON,DateTime,func
from app.database import Base


class Item(Base):
  __tablename__ = "items"

  id = Column(Integer,primary_key=True,index=True)
  name = Column(String,nullable=False)
  description = Column(String,nullable=True)

class DiscoveredHost(Base):
  __tablename__ = "discovered_hosts"

  id = Column(Integer,primary_key=True,index=True)
  ip= Column(String,nullable=False,unique=True)
  mac = Column(String,nullable=True)
  vendor = Column(String,nullable=True)
  hostname = Column(String,nullable=True)
  os_guess = Column(String,nullable=True)
  status = Column(String,nullable=False,default="up")
  open_ports = Column(JSON,nullable=True)
  first_seen = Column(DateTime(timezone = True),server_default = func.now(),nullable = False)
  last_seen = Column(DateTime(timezone = True),server_default = func.now(),nullable = False)
  





  