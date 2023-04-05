from datetime import datetime, timedelta
from logger import log_info, log_error


class Timer():

  def __init__(self, minutes):
    self.minutes = minutes
    self.running = False
    self.game_start = None
    self.game_stop = None
    self.is_game_finished = False

  def set_minutes(self, minutes):
    assert minutes
    assert minutes > 0
    self.minutes = minutes

  def get_game_end(self, format="%Y-%m-%dT%H:%M:%S"):
    assert self.running
    game_ends_at = self.game_start + timedelta(minutes=self.minutes)
    return game_ends_at.strftime(format)

  def get_time_left(self):
    assert self.game_start
    game_ends_at = self.game_start + timedelta(minutes=self.minutes)
    if self.game_stop:
      time_left = game_ends_at - self.game_stop
    else:
      now = datetime.now()
      time_left = game_ends_at - now
    log_info('time left: %s' % time_left)
    return time_left

  def first_start(self, minutes=None, false_start=False):
    assert not self.game_start
    if minutes:
      self.set_minutes(minutes)
    now = datetime.now()
    log_info('game starts at: %s' % now.strftime("%Y-%m-%dT%H:%M:%S"))
    game_ends_at = now + timedelta(minutes=self.minutes)  # calculate the end, add minutes
    str_ends = game_ends_at.strftime("%Y-%m-%dT%H:%M:%S")
    log_info('game ends at: %s' % str_ends)

    if not false_start:
      self.game_start = now
      self.running = True
     
  def stop(self):
    assert self.running
    now = datetime.now()
    log_info('game stops at: %s' % now.strftime("%Y-%m-%dT%H:%M:%S"))
    self.game_stop = now
    self.running = False

  def start(self):
    assert not self.running
    assert self.game_stop
    assert self.game_start
    now = datetime.now()
    log_info('game restarts at: %s' % now.strftime("%Y-%m-%dT%H:%M:%S"))
    time_lost = now - self.game_stop
    log_info('time lost: %s' % time_lost)
    
    self.minutes = self.minutes + time_lost.seconds / 60  # calculates new minutes to don't change the game start
    game_ends_at = self.game_start + timedelta(minutes=self.minutes) + time_lost
    str_ends = game_ends_at.strftime("%Y-%m-%dT%H:%M:%S")
    log_info('game ends at: %s' % str_ends)
    self.game_stop = None
    self.running = True

  def finish_game(self):
    now = datetime.now()
    log_info('game finished at: %s' % now.strftime("%Y-%m-%dT%H:%M:%S"))
    self.running = False
    self.game_start = None
    self.game_stop = None
    self.is_game_finished = True

  def reset(self):
    self.running = False
    self.game_start = None
    self.game_stop = None
    self.is_game_finished = False
