import json
import asyncio
import websockets
from logger import log_info, log_error

WEBSOCKET_SERVER_LOCAL = 'ws://localhost:5000'

COMM_ROOM_TIMEOUT = 2
COMM_ERR_GENERIC = -10
COMM_ERR_TIMEOUT = -20


async def wait_room_reply(ws):
  response = await ws.recv()  # wait for room confirmation
  return response


async def event(message):
  '''
    communication to the rooms
    - create a connection to the broker
    - wait for broker confirm
    - wait for a single room confirm (timeout)
    - close the connection
  '''
  async with websockets.connect(WEBSOCKET_SERVER_LOCAL) as ws:
    message = json.dumps(message)
    print(f'send message to broker: {message}')
    await ws.send(message)
    # print('broker confirmed')
    res = await ws.recv()  # await reply from broker
    print(f'message from broker: {res}')
    try:
      res = await asyncio.wait_for(wait_room_reply(ws), timeout=COMM_ROOM_TIMEOUT)  # await reply from room
      print(f'message from room: {res}')
    except asyncio.exceptions.TimeoutError as exc:
      raise exc
    print('exit')
 

def send_event(event_name, data):
  _d = {'event': event_name, 'data': data, 'sender': 'manager', 'timestamp': ''}
  try:
    asyncio.get_event_loop().run_until_complete(event(_d))
  except asyncio.exceptions.TimeoutError as exc:
    print(str(exc))
    log_error('room timeout! Can\'t communicate with the room')
    return COMM_ERR_TIMEOUT
  except Exception as exc:
    log_error(str(exc))
    return COMM_ERR_GENERIC
