-- upgrade --
CREATE TABLE IF NOT EXISTS "chat" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "title" VARCHAR(160) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "creator_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);;
CREATE TABLE "chat_user" ("user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,"chat_id" UUID NOT NULL REFERENCES "chat" ("id") ON DELETE CASCADE);
-- downgrade --
DROP TABLE IF EXISTS "chat_user";
DROP TABLE IF EXISTS "chat";
