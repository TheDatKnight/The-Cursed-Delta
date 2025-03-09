from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import asyncio
import random
import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load database URL from Railway environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Ensure we use the correct connection string format for SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create database tables
Base.metadata.create_all(bind=engine)


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./game.db")  # Use PostgreSQL on Railway, SQLite for local testing
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# Character Database Model
class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    race = Column(String)
    char_class = Column(String)
    hp = Column(Integer)
    strength = Column(Integer)
    agility = Column(Integer)

Base.metadata.create_all(bind=engine)

# Character options
RACES = {
    "human": {"hp": 20, "strength": 5, "agility": 5},
    "elf": {"hp": 18, "strength": 4, "agility": 7},
    "orc": {"hp": 25, "strength": 7, "agility": 3}
}

CLASSES = {
    "warrior": {"bonus_hp": 5, "bonus_str": 3, "bonus_agi": 0},
    "rogue": {"bonus_hp": 2, "bonus_str": 1, "bonus_agi": 4},
    "mage": {"bonus_hp": 1, "bonus_str": 0, "bonus_agi": 2}
}

players = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Player:
    def __init__(self, websocket: WebSocket, name: str):
        self.websocket = websocket
        self.name = name
        self.room = "starting_area"

    async def send_message(self, message: str):
        await self.websocket.send_text(message)

@app.websocket("/ws/{player_name}")
async def websocket_endpoint(websocket: WebSocket, player_name: str, db=Depends(get_db)):
    await websocket.accept()
    
    player = Player(websocket, player_name)
    players[player_name] = player

    # Check if character exists in database
    char = db.query(Character).filter(Character.name == player_name).first()
    
    if not char:
        await player.send_message("Welcome! Let's create your character.\nChoose a race: human, elf, orc.")
        while True:
            race = await websocket.receive_text()
            if race in RACES:
                break
            await player.send_message("Invalid race. Choose: human, elf, orc.")

        await player.send_message("Choose a class: warrior, rogue, mage.")
        while True:
            char_class = await websocket.receive_text()
            if char_class in CLASSES:
                break
            await player.send_message("Invalid class. Choose: warrior, rogue, mage.")

        # Generate character stats and save to database
        base_stats = RACES[race]
        class_bonus = CLASSES[char_class]
        new_character = Character(
            name=player_name,
            race=race,
            char_class=char_class,
            hp=base_stats["hp"] + class_bonus["bonus_hp"],
            strength=base_stats["strength"] + class_bonus["bonus_str"],
            agility=base_stats["agility"] + class_bonus["bonus_agi"]
        )
        db.add(new_character)
        db.commit()
        db.refresh(new_character)

        await player.send_message(f"Character Created! Race: {race.capitalize()}, Class: {char_class.capitalize()}\nStats: HP {new_character.hp}, Strength {new_character.strength}, Agility {new_character.agility}")
    
    else:
        await player.send_message(f"Welcome back, {char.name}! You are in a misty swamp.\nExits: north")

    try:
        while True:
            command = await websocket.receive_text()
            response = process_command(player, command)
            await player.send_message(response)
    except WebSocketDisconnect:
        del players[player_name]
        print(f"{player_name} disconnected.")

def process_command(player: Player, command: str) -> str:
    command = command.lower()

    if command == "look":
        return "You are in a misty swamp. Exits: north"
    
    elif command.startswith("move "):
        direction = command.split(" ")[1]
        if direction == "north":
            return "You move north into the voodoo village."
        return "You can't go that way."

    return "Unknown command. Try 'look' or 'move north'."
