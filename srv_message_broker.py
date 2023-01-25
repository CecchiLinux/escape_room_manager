import asyncio
import websockets


LOCAL_SERVER_HOSTNAME = 'localhost'
LOCAL_SERVER_PORT = 5000


connected = set()


async def echo_broadcast(websocket, path):
  # register
  connected.add(websocket)
  print(websocket)
  try:
    async for message in websocket:
      reply = f'Data recieved as: {message}!'
      print(f'{reply}')
      for conn in connected:
        print(conn)
        if conn != websocket:
          print(f'Room server is repling: {reply}')
          await conn.send(message)
        else:
          await conn.send(reply)
  finally:
    # unregister
    connected.remove(websocket)


async def echo(websocket):
  async for message in websocket:
    reply = f'Data recieved as: {message}!'
    print(f'Room server is repling: {reply}')
    await websocket.send(reply)


async def main():
  async with websockets.serve(echo_broadcast, LOCAL_SERVER_HOSTNAME, LOCAL_SERVER_PORT):
    await asyncio.Future()  # run forever

if __name__ == "__main__":
  asyncio.run(main())
