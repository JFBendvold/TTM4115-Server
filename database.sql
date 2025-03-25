-- sletter eksisterende tabeller

 drop table if exists  brukere;
 drop table if exists  oppgaver;
 drop table if exists  scootere;


-- oppretter tabeller

-- Table: brukere
CREATE TABLE brukere (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    navn VARCHAR(30),
    passord VARCHAR(100)
);

-- Table: oppgaver
CREATE TABLE oppgaver (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destinasjon VARCHAR(30)
);

-- Table: scootere
CREATE TABLE scootere (
    id INTEGER PRIMARY KEY AUTOINCREMENT
);


