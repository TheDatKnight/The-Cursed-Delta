from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio

app = FastAPI()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "The Cursed Delta MUD is running!"}


# Define the game world (rooms and connections)
rooms = {
    "starting_area": {"desc": "You are in a misty swamp. The trees whisper around you.", "exits": {"north": "voodoo_village"}},
    "voodoo_village": {"desc": "A mysterious village filled with flickering lanterns and chanting.", "exits": {"south": "starting_area", "east": "pirate_cove"}},
    "pirate_cove": {"desc": "A hidden cove where ghostly pirates linger.", "exits": {"west": "voodoo_village"}}
}

# Store connected players
players = {}

class Player:
    def __init__(self, websocket: WebSocket, name: str):
        self.websocket = websocket
        self.name = name
        self.room = "starting_area"  # Default starting room

    async def send_message(self, message: str):
        await self.websocket.send_text(message)

@app.websocket("/ws/{player_name}")
async def websocket_endpoint(websocket: WebSocket, player_name: str):
    await websocket.accept()
    player = Player(websocket, player_name)
    players[player_name] = player

    await player.send_message(f"Welcome, {player_name}! {rooms[player.room]['desc']}\nExits: {', '.join(rooms[player.room]['exits'].keys())}")
    try:
        while True:
            data = await websocket.receive_text()
            response = process_command(player, data)
            await player.send_message(response)
    except WebSocketDisconnect:
        del players[player_name]
        print(f"{player_name} disconnected.")

def process_command(player: Player, command: str) -> str:
    """Processes player commands, including movement."""
    command = command.lower()
    if command == "look":
        return f"{rooms[player.room]['desc']}\nExits: {', '.join(rooms[player.room]['exits'].keys())}"
    elif command.startswith("move "):
        direction = command.split(" ")[1]
        if direction in rooms[player.room]["exits"]:
            player.room = rooms[player.room]["exits"][direction]
            return f"You move {direction}. {rooms[player.room]['desc']}\nExits: {', '.join(rooms[player.room]['exits'].keys())}"
        else:
            return "You can't go that way."
    elif command.startswith("say "):
        message = command[4:]
        return f"You say: {message}"
    else:
        return "Unknown command. Try 'look', 'move <direction>', or 'say <message>'."
