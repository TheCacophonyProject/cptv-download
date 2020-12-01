--test-groups
INSERT INTO "Groups" ("id","groupname","createdAt","updatedAt") VALUES (DEFAULT,'test-group','2019-03-14 20:15:23.423 +00:00','2019-03-14 20:15:23.423 +00:00');
INSERT INTO "Groups" ("id","groupname","createdAt","updatedAt") VALUES (DEFAULT,'test-group-2','2019-03-14 20:15:23.423 +00:00','2019-03-14 20:15:23.423 +00:00');

--test-password
INSERT INTO "Devices" ("id","devicename","password","public","createdAt","updatedAt","GroupId") VALUES (DEFAULT,'test-device','$2a$10$LWL.Sr0767v0RmWqcgAKduBXSE2G9T2oIn.W5V1ohtgZQA4kKgR06',false,'2019-03-14 20:17:45.636 +00:00','2019-03-14 20:17:45.636 +00:00',1);

--test-user
INSERT INTO "Users" (username, email, password, "globalPermission", "createdAt", "updatedAt") VALUES ('go-api-user-test', 'go-api@email.com', '$2a$10$gYAi/taZNA5y5rN8cgu0oOW30iHxTXXDoAwDv7cnyTDPPyWZK847K', 'read', now(), now());


