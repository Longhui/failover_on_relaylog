#-*-coding:utf8-*-
__author__='raolh'

import re, os
from optparse import OptionParser


regex_rotate=re.compile(r'Rotate\sto\s([\w\-\.]+)\s*pos:\s*(\d+)')    
regex_binlog_pos=re.compile(r'server\sid\s\d+\s*end_log_pos\s(\d+)')
regex_relaylog_pos=re.compile(r'#\sat\s(\d+)$')
MYSQLBINLOG="mysqlbinlog"


class relaylog_index():
  """
  """

  def __init__(self, index_file):
    self.handler= open(index_file, 'r')

  def find_next_one(self):
    line= self.handler.readline()
    if len(line) > 0:
      self.relaylog=line.split('/')[1].strip()
      return self.relaylog
    else:
      return None

  def __del__(self):
    self.handler.close()

class relay_log():
  """
  """

  def __init__(self, log_file):
    self.filename=log_file
    self.binlog_filename=None
    self.min_binlog_position=None
    errno= os.system('%s %s --stop-position=500 > /tmp/M8QJF9DL'%(MYSQLBINLOG, log_file))
    if 0 == errno:
      text=open('/tmp/M8QJF9DL','r')
      line=text.readline()
      while line:
        match=regex_rotate.search(line)
        if match:
          self.binlog_filename= match.group(1)
          self.min_binlog_position= match.group(2)
          break
        line=text.readline()
      text.close()
    else:
      raise Exception("convertPos fails!! mysqlbinlog %s error, errorno:%r"%(log_file, errno))

  def binlog_file(self):
    return self.binlog_filename
 
  def min_binlog_pos(self):
    return self.min_binlog_position
    
  def get_relay_pos(self, binlog_pos):
    relaylog_pos=None
    stop= 0
    errno=os.system("%s %s > /tmp/JND8HL8FS12D"%(MYSQLBINLOG, self.filename))
    if 0== errno:
      text=open('/tmp/JND8HL8FS12D','r')
      line=text.readline()
      while line:
        match= regex_relaylog_pos.search(line)
        if match:
          relaylog_pos=match.group(1)
          if stop:
            break
        match= regex_binlog_pos.search(line)
        if match:
          position=match.group(1)
          if binlog_pos == position:
            stop = 1
          if long(binlog_pos) < long(position):
            relaylog_pos=None
            break
        line=text.readline()
      text.close()
      os.system('rm /tmp/JND8HL8FS12D')
      return relaylog_pos
    else:
      raise Exception("convertPos fails!! mysqlbinlog %s error, errorno:%r"%(self.filename, errno))

def convert_pos(relaylog_index_name, binlog_filename, binlog_pos, mysqlbinlog=None):
  global MYSQLBINLOG
  if mysqlbinlog:
    MYSQLBINLOG= mysqlbinlog

  binlog_pos= binlog_pos
  if os.path.exists(relaylog_index_name):
    prev_relaylog=None; cur_relaylog=None
    relaylog_pos=None; relaylog_filename=None
    dirname= os.path.dirname(relaylog_index_name)
    index= relaylog_index(relaylog_index_name)
    relaylog_filename=index.find_next_one()
    while None != relaylog_filename:
      cur_relaylog=relay_log(dirname+'/'+relaylog_filename)
      cur_binlog_filename= cur_relaylog.binlog_file()
      cur_binlog_pos= cur_relaylog.min_binlog_pos()
      if cur_binlog_filename == binlog_filename:
        if long(cur_binlog_pos) < long(binlog_pos):
          prev_relaylog= cur_relaylog
        elif long(cur_binlog_pos) > long(binlog_pos):
          break
        else:
          relaylog_pos=cur_relaylog.get_relay_pos(binlog_pos)
          relaylog_filename=cur_relaylog.filename
          break
      elif int(cur_binlog_filename.split('.')[1]) > int(binlog_filename.split('.')[1]):
        break         
      relaylog_filename=index.find_next_one()
    if prev_relaylog:
      relaylog_filename=prev_relaylog.filename
      relaylog_pos=prev_relaylog.get_relay_pos(binlog_pos)

    return relaylog_filename, relaylog_pos
  else:
    raise Exception("%s is not exists"%(relaylog_index,))


def ParseOptions():
  parser=OptionParser()
  parser.add_option("-B","--mysqlbinlog",
                    dest="mysqlbinlog",
                    default="/usr/local/mysql/bin/mysqlbinlog",
                    help='mysqlbinlog full path')
  parser.add_option("-R","--relaylog_index",
                    dest="relaylog_index",
                    default=" ",
                    help='relaylog index file path')
  parser.add_option("-F","--master_file_name",
                    dest="master_binlog_file_name",
                    default="",
                    help='master binlog file name need to convert')

  parser.add_option("-P","--master_file_pos",
                    dest="master_binlog_file_pos",
                    default="",
                    help='master binlog file pos need to convert')
  (options, args)=parser.parse_args()
  try:
    if options.mysqlbinlog:
      MYSQLBINLOG=options.mysqlbinlog
    else:
      raise Exception()
    if options.relaylog_index:
      RELAYLOG_INDEX=options.relaylog_index
    else:
      raise Exception()
    if options.master_binlog_file_pos:
      MASTERFILEPOS=options.master_binlog_file_pos
    else:
      raise Exception()
    if options.master_binlog_file_name:
      MASTERFILENAME=options.master_binlog_file_name
    else:
      raise Exception()
  except Exception,e:
    print e
    print 'python convetPos.py --help'
    return
  (filename, pos)= convert_pos(RELAYLOG_INDEX, MASTERFILENAME, MASTERFILEPOS, mysqlbinlog=MYSQLBINLOG)
  print '\n'
  print filename
  print pos
  print '\n'

if __name__ == "__main__":
  ParseOptions()
