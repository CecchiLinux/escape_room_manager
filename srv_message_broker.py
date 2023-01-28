import asyncio
import websockets


LOCAL_SERVER_HOSTNAME = 'localhost'
LOCAL_SERVER_PORT = 5000


connected = set()


async def echo_broadcast(websocket, path):
  # when room connects, this function add it to the connected (no messages to read)
  connected.add(websocket)  # register websocket (no duplicates, it's a set)
  print(connected)  # debug
  try:
    async for message in websocket:
      reply = f'broker recieved data as: {message}!'
      print(f'{reply}')
      for conn in connected:
        if conn != websocket:  # don't get back to the sender
          print(f'broker is forwarding to the recipient: [{conn} - {message}]')
          await conn.send(message)
          print('recipient confirmed')
        else:
          print('broker replying to the sender')
          await conn.send('ok')
          print('sender confirmed')
  finally:
    # unregister
    connected.remove(websocket)


# async def echo(websocket):
#   async for message in websocket:
#     reply = f'Data recieved as: {message}!'
#     print(f'Room server is repling: {reply}')
#     await websocket.send(reply)


async def main():
  async with websockets.serve(echo_broadcast, LOCAL_SERVER_HOSTNAME, LOCAL_SERVER_PORT):
    await asyncio.Future()  # run forever

if __name__ == "__main__":
  asyncio.run(main())
