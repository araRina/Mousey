CREATE TABLE IF NOT EXISTS tags (
  id BIGINT PRIMARY KEY,

  owner_id BIGINT REFERENCES users (id) ON DELETE CASCADE,
  guild_id BIGINT REFERENCES guilds (id) ON DELETE CASCADE,

  name TEXT,
  content TEXT
);

ALTER TABLE tags ADD CONSTRAINT tags_guild_id_name_unique UNIQUE (guild_id, name);
