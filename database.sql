-- sletter eksisterende tabeller

 drop table if exists  brukere;
 drop table if exists  oppgaver;
 drop table if exists  scootere;


-- oppretter tabeller

-- Table: brukere
CREATE TABLE brukere (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    navn VARCHAR(30),
    passord VARCHAR(100),
    reward INTEGER

);

-- Table: oppgaver
CREATE TABLE oppgaver (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scooterid INTEGER,
    brukerid INTEGER, 
    latitude FLOAT,
    longitude FLOAT,
    radius FLOAT,
    reward INTEGER,
    FOREIGN KEY (scooterid) REFERENCES scootere(id) ON DELETE CASCADE,
    FOREIGN KEY (brukerid) REFERENCES brukere(id)
);

-- Table: scootere
CREATE TABLE scootere (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    latitude FLOAT,
    longitude FLOAT,
    available BOOLEAN, 
    battery INTEGER
);


