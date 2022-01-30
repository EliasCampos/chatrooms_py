-- upgrade --
CREATE TABLE IF NOT EXISTS "chatmessage" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "text" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL  DEFAULT False,
    "author_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "chat_id" UUID NOT NULL REFERENCES "chat" ("id") ON DELETE CASCADE
);
-- downgrade --
DROP TABLE IF EXISTS "chatmessage";
