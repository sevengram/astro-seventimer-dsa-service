DROP TABLE IF EXISTS devices;
DROP TABLE IF EXISTS start_app;
DROP TABLE IF EXISTS location_service;
DROP TABLE IF EXISTS weather_service;
DROP TABLE IF EXISTS satellite_service;

CREATE TABLE IF NOT EXISTS devices(
	uuid CHAR(128) NOT NULL,
	version CHAR(16) NOT NULL,
	info VARCHAR(255),
	PRIMARY KEY (uuid)) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS start_app(
	ip CHAR(40) NOT NULL, 
	stime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	uuid CHAR(128) NOT NULL,
	version CHAR(16) NOT NULL,
    channel CHAR(20) NOT NULL DEFAULT 'unknown',
	KEY index_uuid (uuid),
	KEY index_stime (stime)) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS location_service(
	ip CHAR(40) NOT NULL, 
	stime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	delay INT NOT NULL,
	network TINYINT NOT NULL,
	provider TINYINT NOT NULL,
	uuid CHAR(128) NOT NULL,
	version CHAR(16) NOT NULL,
	longitude FLOAT,
	latitude FLOAT,
	location_info VARCHAR(255),
	KEY index_uuid (uuid),
	KEY index_cost (delay),
	KEY index_stime (stime)) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS weather_service(
	ip CHAR(40) NOT NULL, 
	stime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	total_delay INT NOT NULL,
	server_delay INT NOT NULL,
	network TINYINT NOT NULL,
	uuid CHAR(128) NOT NULL,
	version CHAR(16) NOT NULL,
	KEY index_uuid (uuid),
	KEY index_total_delay (total_delay),
	KEY index_server_delay (server_delay),
	KEY index_stime (stime)) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS satellite_service(
	ip CHAR(40) NOT NULL, 
	stime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	delay INT NOT NULL,
	network TINYINT NOT NULL,
	uuid CHAR(128) NOT NULL,
	version CHAR(16) NOT NULL,
	KEY index_uuid (uuid),
	KEY index_delay (delay),
	KEY index_stime (stime)) ENGINE=MyISAM;

