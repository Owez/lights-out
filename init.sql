-- A bot in a guild, important for whitelisting. ID is discord bot id
CREATE TABLE IF NOT EXISTS bot(id INTEGER PRIMARY KEY NOT NULL);

-- The main center of the database, stores guild infomation. ID is discord guild id
CREATE TABLE IF NOT EXISTS guild(id INTEGER PRIMARY KEY NOT NULL);

-- Linking tables for bot and guild, allowing whitelisting many-many relationship
CREATE TABLE IF NOT EXISTS guild_bot(
    bot_id INTEGER,
    guild_id INTEGER,
    FOREIGN KEY(bot_id) REFERENCES bot(id) ON DELETE CASCADE,
    FOREIGN KEY(guild_id) REFERENCES guild(id) ON DELETE CASCADE
);

-- A table of reports given from users (named `author`)
CREATE TABLE IF NOT EXISTS report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    author INTEGER NOT NULL
);