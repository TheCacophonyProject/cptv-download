--test-groups
INSERT INTO "Groups" ("id","groupName","createdAt","updatedAt") VALUES (DEFAULT,'test-group','2019-03-14 20:15:23.423 +00:00','2019-03-14 20:15:23.423 +00:00');
INSERT INTO "Groups" ("id","groupName","createdAt","updatedAt") VALUES (DEFAULT,'test-group-2','2019-03-14 20:15:23.423 +00:00','2019-03-14 20:15:23.423 +00:00');

--test-password
INSERT INTO "Devices" ("id","deviceName","password","public","createdAt","updatedAt","GroupId",uuid,"saltId") VALUES (DEFAULT,'test-device','$2a$10$LWL.Sr0767v0RmWqcgAKduBXSE2G9T2oIn.W5V1ohtgZQA4kKgR06',false,'2019-03-14 20:17:45.636 +00:00','2019-03-14 20:17:45.636 +00:00',1,0,0);

INSERT INTO public."DeviceHistory"
("location", "fromDateTime", "setBy", "deviceName", uuid, "saltId", "stationId", "DeviceId", "GroupId")
VALUES('POINT(-71.060316 48.432044)', NOW(), 'user', 'test-device', 0, 0, 0, 1, 1);

--test-user
INSERT INTO "Users" ("userName", email, "password", "globalPermission", "createdAt", "updatedAt") VALUES ('go-api-user-test', 'go-api@email.com', '$2a$10$gYAi/taZNA5y5rN8cgu0oOW30iHxTXXDoAwDv7cnyTDPPyWZK847K', 'read', now(), now());
