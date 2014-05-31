#DROP TABLE IF EXISTS location;

CREATE TABLE IF NOT EXISTS location(
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    longitude FLOAT NOT NULL,
    latitude FLOAT NOT NULL,
    query VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    PRIMARY KEY (query),
    KEY index_id (id)) ENGINE=MyISAM;


CREATE TABLE IF NOT EXISTS users(
    uid CHAR(128) NOT NULL,
    stime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    last_status BOOLEAN NOT NULL DEFAULT TRUE,
    last_query VARCHAR(255) NOT NULL,
    PRIMARY KEY (uid),
    KEY index_stime (stime)) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS feedback(
    ticket INT UNSIGNED NOT NULL AUTO_INCREMENT,
    uid CHAR(128) NOT NULL,
    stime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    type TINYINT NOT NULL,
    query VARCHAR(255) NOT NULL,
    PRIMARY KEY(ticket),
    KEY index_uid (uid),
    KEY index_stime (stime),
    KEY index_type (type)) ENGINE=MyISAM;