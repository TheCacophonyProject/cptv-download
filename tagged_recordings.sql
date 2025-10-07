 select
	"Recording" .*,
	"Group"."id" as "Group.id",
	"Group"."groupName" as "Group.groupName",
	"Station"."id" as "Station.id",
	"Station"."name" as "Station.name",
	ST_Y("Station"."location") as "Station.lat",
	ST_X("Station"."location") as "Station.lng",

	"Tags"."id" as "Tags.id",
	"Tags"."detail" as "Tags.detail",
	"Tags"."confidence" as "Tags.confidence",
	"Tags"."startTime" as "Tags.startTime",
	"Tags"."duration" as "Tags.duration",
	"Tags"."automatic" as "Tags.automatic",
	"Tags"."version" as "Tags.version",
	"Tags"."createdAt" as "Tags.createdAt",
	"Tags"."taggerId" as "Tags.taggerId",
	"Tags"."comment" as "Tags.comment",
	"Tags->tagger"."userName" as "Tags.tagger.userName",
	"Tags->tagger"."id" as "Tags.tagger.id"
from
	(
	select
		"Recording"."id",
		"Recording"."type",
		"Recording"."recordingDateTime",
		"Recording"."rawMimeType",
		"Recording"."fileMimeType",
		"Recording"."processingState",
		"Recording"."duration",
		ST_Y("Recording"."location") as "lat",
		ST_Y("Recording"."location") as "lng",
		"Recording"."batteryLevel",
		"Recording"."DeviceId",
		"Recording"."GroupId",
		"Recording"."StationId",
		"Recording"."rawFileKey",
		"Recording"."cacophonyIndex",
		"Recording"."processing",
		"Recording"."comment",
		"Recording"."additionalMetadata",
		"Recording"."redacted",
		"Device"."deviceName" as "Device.deviceName",
		"Device"."id" as "Device.id"
	from
		"Recordings" as "Recording"
	inner join "Devices" as "Device" on
		"Recording"."DeviceId" = "Device"."id"
	where
		(("Recording"."type" = '{}'
			and ("Recording"."recordingDateTime" >= '{}')
			and "Recording"."deletedAt" is null)
		and ((
		select
			"Recording"."id"
		from
			"Tracks"
		inner join "TrackTags" as "Tags" on
			"Tracks"."id" = "Tags"."TrackId"
		where
			"Tags".
 "archivedAt" is null
			and "Tracks"."RecordingId" = "Recording".id
			and "Tracks"."archivedAt" is null
			and (not "Tags".automatic)
		limit 1) is not null
			or (
			select
				1
			from
				"Tags"
			where
				"Tags"."RecordingId" = "Recording".id
				and (not "Tags".automatic)
			limit 1) is not null))
	order by
		"recordingDateTime" desc,
		"Recording"."id" desc
	limit {} offset {}) as "Recording"
left outer join "Groups" as "Group" on
	"Recording"."GroupId" = "Group"."id"
left outer join "Stations" as "Station" on
	"Recording"."StationId" = "Station"."id"
left outer join "Tags" as "Tags" on
	"Recording"."id" = "Tags"."RecordingId"
left outer join "Users" as "Tags->tagger" on
	"Tags"."taggerId" = "Tags->tagger"."id"
order by
	"recordingDateTime" desc,
	"Recording"."id" desc;
