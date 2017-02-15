CREATE DATABASE photoshare;
USE photoshare;
DROP TABLE Pictures CASCADE;
DROP TABLE Users CASCADE;

CREATE TABLE Users (
	user_ID int4,
	firstName varchar(255),
	lastName varchar(255),
	email varchar(255),
	birthDate varchar(255),
    password varchar(255),
	CONSTRAINT users_pk PRIMARY KEY (user_id) );


CREATE TABLE Friends (	
	user1 integer,
	user2 integer,
	PRIMARY KEY (user1, user2),
	FOREIGN KEY (user1) REFERENCES Users(user_id),
	FOREIGN KEY (user2) REFERENCES Users(user_id) );

CREATE TABLE Albums (
	albumid	INTEGER auto_increment,
	uid	INTEGER,
	aname VARCHAR(255),
	created	DATE,
	PRIMARY KEY (albumid),
	FOREIGN KEY (uid) REFERENCES Users(user_id) )

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  imgdata longblob ,
  caption VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);

CREATE TABLE Comments (
	cid	int4 AUTO_INCREMENT,
	commenter int4,
	pid	int4,
	body VARCHAR(255),
	dp DATE, 
	PRIMARY KEY (cid),
    FOREIGN KEY (commenter) REFERENCES Users(user_id),
    FOREIGN KEY (pid) REFERENCES Pictures(picture_id) );
    
CREATE TABLE Likes
(
	userID int4,albumid
	picture_id int4,
	albumid int4,
	PRIMARY KEY (userID,picture_id,albumid),
	FOREIGN KEY (userID) REFERENCES Users(user_ID),
	FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id),
	FOREIGN KEY (albumid) REFERENCES Albums(albumid) );
    
