import asyncio
import websockets

async def test_connection():
    uri = "ws://localhost:8000/ws/TestPlayer"  # Ensure the port matches your server
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to the server.")

            # Send a command to the server
            await websocket.send("look")

            # Receive and print response
            response = await websocket.recv()
            print(f"📝 Server Response: {response}")

    except Exception as e:
        print(f"❌ Error: {e}")

# Run the test
asyncio.run(test_connection())
