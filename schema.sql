DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS examples;
DROP TABLE IF EXISTS explanations;
DROP TABLE IF EXISTS explanations_evaluation;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL
);

CREATE TABLE examples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  path TEXT NOT NULL,
  label TEXT NOT NULL,
  prediction TEXT NOT NULL
);

CREATE TABLE explanations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  example_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  path TEXT NOT NULL,
  FOREIGN KEY(example_id) REFERENCES examples(id)
);

CREATE TABLE explanations_evaluation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  explanation_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  score INTEGER NOT NULL,
  FOREIGN KEY(explanation_id) REFERENCES explanations(id),
  FOREIGN KEY(user_id) REFERENCES users(id)
);