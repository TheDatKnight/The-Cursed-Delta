from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio

app = FastAPI()

# Store connected players
players = {}

class Player:
    def __init__(self, websocket: WebSocket, name: str):
        self.websocket = websocket
        self.name = name
        self.room = "starting_area"

    async def send_message(self, message: str):
        await self.websocket.send_text(message)

@app.websocket("/ws/{player_name}")
async def websocket_endpoint(websocket: WebSocket, player_name: str):
    await websocket.accept()
    player = Player(websocket, player_name)
    players[player_name] = player

    await player.send_message(f"Welcome, {player_name}! You are in {player.room}.")
    try:
        while True:
            data = await websocket.receive_text()
            response = process_command(player, data)
            await player.send_message(response)
    except WebSocketDisconnect:
        del players[player_name]
        print(f"{player_name} disconnected.")

def process_command(player: Player, command: str) -> str:
    """Processes player commands."""
    command = command.lower()
    if command == "look":
        return f"You are in {player.room}. There is nothing here yet."
    elif command.startswith("say "):
        message = command[4:]
        return f"You say: {message}"
    else:
        return "Unknown command. Try 'look' or 'say <message>'."

# Run with: uvicorn backend_server:app --host 0.0.0.0 --port 8000 --reload
