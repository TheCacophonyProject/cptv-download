select
	"Track"."id",
	"Track"."filtered",
	"Track"."startSeconds",
	"Track"."endSeconds",
	"Track"."RecordingId",
	"TrackTags"."id" as "Tra
ckTags.id",
	"TrackTags"."what" as "TrackTags.what",
	"TrackTags"."path" as "TrackTags.path",
	"TrackTags"."automatic" as "TrackTags.automatic",
	"TrackTags"."TrackId" as "TrackTags.TrackId",
	"TrackTags"."confidence" as "TrackTags.confidence",
	"TrackTags"."UserId" as "TrackTags.UserId",
	"TrackTags"."model" as "TrackTags.model",
	"TrackTags->User"."userName" as "TrackTags.User.userName",
	"TrackTags->User"."id" as "TrackTags.User.id"
from
	"Tracks" as "Track"
left outer join "TrackTags" as "TrackTags" on
	"Track"."id" = "TrackTags"."TrackId"
	and "TrackTags"."archivedAt" is null
left outer join "Users" as "TrackTags->User" on
	"TrackTags"."UserId" = "TrackTags->User"."id"
where
	("Track"."RecordingId" in ({})
		and "Track"."archivedAt" is null);
