import dataclasses
import time
import datetime
import json
from dataclasses import dataclass
import logging

import cfutils.api as cf
import cfutils.icpctools.EventFeed as Feed
from cfutils.icpctools.EventFeed import Event, EventData


class EventFeedError(Exception):
    pass


@dataclass
class ContestTeam:
    Id: str
    name: str
    fullName: str
    """Example format: `TeamName (Member1Name, Member2Name, Member3Name)`"""
    members: list[str]


@dataclass
class CFContestConfig:
    freezeDurationSeconds: int

    regions: list[str]

    include_virtual: bool = False
    include_out_of_comp: bool = False

    def getRegion(self, team: ContestTeam) -> str:
        return self.regions[0]

    # TODO use this to generate awards
    def medalCounts(self, num_teams: int) -> tuple[int, int, int]:
        return 4, 4, 4


class EventFeedFromCFContest:
    config: CFContestConfig
    __contest_events: list[Event]

    __ghost_teams: dict[str, int]
    __individual_teams: dict[str, int]

    def __init__(self, *, config: CFContestConfig):
        self.config = config
        self.__contest_events = []

        self.__ghost_teams = {}
        self.__individual_teams = {}

    @staticmethod
    def __epochToISO(s: int) -> str:
        return (
            datetime.datetime.fromtimestamp(s).isoformat(timespec="milliseconds")
            + "+00"
        )

    @staticmethod
    def __secondsToHHMMSS(s: int) -> str:
        res = str(datetime.timedelta(seconds=s)) + ".000"
        if res[1] == ":":
            res = "0" + res
        return res

    def __populate_teams(self, ranklist: list[cf.RanklistRow]):
        for row in ranklist:
            party = row.party

            if party.teamId is not None:
                continue

            if party.ghost:
                assert party.teamName is not None, "ghosts must have a teamName"
                ix = len(self.__ghost_teams)
                self.__ghost_teams[party.teamName] = ix
                continue

            if len(party.members) == 1:
                user = party.members[0].handle
                ix = len(self.__individual_teams)
                self.__individual_teams[user] = ix
                continue

            raise EventFeedError(
                f"Invalid participant in ranklist (not a CF team, ghost, or individual): {party}"
            )

    def __get_team_info(self, team: cf.Party) -> ContestTeam:
        """Extract team info from a Party.
        For ghosts and individuals, use the generated IDs.

        Ids:
            - cf teams: `team_<id>`
            - ghosts: `ghost_<id>`
            - individual: `user_<id>`
        """

        ## codeforces team
        if team.teamId is not None:
            assert team.teamName is not None, "CF teams must have a team name"

            members = [u.handle for u in team.members]
            fullName = (
                team.teamName + (" (" + ", ".join(members) + ")") if members else ""
            )
            return ContestTeam(
                Id=f"team_{team.teamId}",
                name=team.teamName,
                fullName=fullName,
                members=members,
            )

        ## ghost
        if team.ghost:
            name = team.teamName

            assert name is not None, "ghosts must have a team name"
            assert team.members == []  # TODO fix

            if name not in self.__ghost_teams:
                raise EventFeedError(
                    f"Invalid submission, ghost `{name}` not found in the ranklist!"
                )

            return ContestTeam(
                Id=f"ghost_{self.__ghost_teams[name]}",
                name=name,
                fullName=name,
                members=[],
            )

        ## individual
        if len(team.members) == 1:
            name = team.members[0].handle

            if name not in self.__individual_teams:
                raise EventFeedError(
                    f"Invalid submission, user `{name}` not found in the ranklist!"
                )

            return ContestTeam(
                Id=f"user_{self.__individual_teams[name]}",
                name=name,
                fullName=name,
                members=[name],
            )

        raise EventFeedError(
            "Unable to process participant: not a CF team, ghost, or individual!"
        )

    def __add_event_at(self, ix: str, eventData: EventData):
        """Create/update a sub-object at index `ix`"""
        event = Event(type=eventData.eventType(), id=ix, data=eventData)
        self.__contest_events.append(event)

    def __add_event(self, eventData: EventData):
        """Create/update the entire object with a single event"""
        event = Event(type=eventData.eventType(), id=None, data=eventData)
        self.__contest_events.append(event)

    def __add_events(self, eventsData: list[EventData]):
        """Create/update the entire object with a list of events"""

        for eventData in eventsData:
            self.__add_event(eventData)

        # TODO figure out why data=array-of-events is not working
        # if not eventsData:
        #     return
        # event = Event(type=eventsData[0].eventType(), id=None, data=eventsData)
        # self.contest_events.append(event)

    def __show_contest_state(self, *, contest: cf.Contest, done=False):
        """Event displayed at the start and end, and optionally at standings freeze"""

        tstart = 0
        tfin = contest.durationSeconds
        tfrozen = tfin - self.config.freezeDurationSeconds
        tthaw = tfin + 300  # TODO(magic) why 300?
        tdone = tthaw + 300  # TODO(magic) why 300?

        self.__add_event(
            Feed.State(
                started=self.__epochToISO(tstart),
                frozen=self.__epochToISO(tfrozen),
                ended=self.__epochToISO(tfin) if done else None,
                thawed=self.__epochToISO(tthaw),
                finalized=self.__epochToISO(tdone) if done else None,
                # TODO(magic) why 300?
                end_of_updates=self.__epochToISO(tdone + 300) if done else None,
            )
        )

    def __participantAllowed(self, ptype: cf.ParticipantType) -> bool:
        if ptype == cf.ParticipantType.CONTESTANT:
            return True
        if ptype == cf.ParticipantType.VIRTUAL and self.config.include_virtual:
            return True
        if (
            ptype == cf.ParticipantType.OUT_OF_COMPETITION
            and self.config.include_out_of_comp
        ):
            return True
        return False

    def generate(
        self,
        *,
        contest: cf.Contest,
        problems: list[cf.Problem],
        ranklist: list[cf.RanklistRow],
        submissions: list[cf.Submission],
    ) -> list[str]:
        """Generate event feed JSON for the ICPC resolver tool.

        Caveats:
            This ignores the true submission times, and instead assumes a start time of 0 (epoch). So the generated feed may not work for tools other than the resolver.

        Args:
            contest: CF Contest object. Usually obtained using `contest.standings`.
            problems: CF Problem list. Usually obtained using `contest.standings`.
            ranklist: CF ranklist row list. Usually obtained using `contest.standings`.
            submissions: CF submission list. Usually obtained using `contest.status`.

        Returns:
            A list of stringified JSON events.

        Raises:
            EventFeedError: submission by a team not in the ranklist
            EventFeedError: team is neither a CF team, nor a ghost, nor a CF user.
        """

        ## ignore invalid submissions and participants
        submissions = [
            sub
            for sub in submissions
            if self.__participantAllowed(sub.author.participantType)
        ]
        ranklist = [
            row
            for row in ranklist
            if self.__participantAllowed(row.party.participantType)
        ]

        ## generates unique teamIds for ghosts and individuals.
        self.__populate_teams(ranklist)

        ## contest info
        self.__add_event(
            Feed.Contest(
                id=f"cf_contest_{contest.id}",
                name=contest.name,
                formal_name=contest.name,
                duration=self.__secondsToHHMMSS(contest.durationSeconds),
                scoreboard_type=Feed.ScoreboardType.pass_fail,
                scoreboard_freeze_duration=self.__secondsToHHMMSS(
                    self.config.freezeDurationSeconds
                ),
                start_time=self.__epochToISO(0),
                penalty_time=20,
            )
        )

        ## Add only one language, and extract everything to that
        self.__add_events(
            [
                Feed.Language(
                    id="0", name="lang", entry_point_required=False, extensions=[]
                )
            ]
        )

        ## Contest regions
        self.__add_events(
            [
                Feed.Group(id=str(ix), name=name, icpc_id=str(ix))
                for ix, name in enumerate(self.config.regions)
            ]
        )

        ## Possible verdicts: OK, WA, CE (subsume everything else into WA/CE depending on penalty)
        self.__add_events(
            [
                Feed.JudgementType(
                    id=Feed.JudgementTypeId.AC, name="AC", solved=True, penalty=False
                ),
                Feed.JudgementType(
                    id=Feed.JudgementTypeId.WA, name="WA", solved=False, penalty=True
                ),
                Feed.JudgementType(
                    id=Feed.JudgementTypeId.CE, name="CE", solved=False, penalty=False
                ),
            ]
        )

        ## contest problems
        problem_ids = [problem.index for problem in problems]
        self.__add_events(
            [
                Feed.Problem(
                    id=problem.index,
                    label=problem.index,
                    name=problem.name,
                    ordinal=problem_ids.index(problem.index),
                    test_data_count=1,
                )
                for problem in problems
            ]
        )
        logging.info("#problems: %d", len(problems))

        ## organizations
        # TODO: add support for multiple orgs
        self.__add_events([Feed.Organization(id="org_default", name="DefaultOrg")])

        for row in ranklist:
            team = self.__get_team_info(row.party)

            region = self.config.getRegion(team)
            region = str(self.config.regions.index(region))

            self.__add_event(
                Feed.Team(
                    id=team.Id,
                    name=team.fullName,
                    group_ids=[region],
                    organization_id="org_default",
                )
            )
        logging.info("#teams: %d", len(ranklist))

        ## start the contest
        self.__show_contest_state(contest=contest)

        ## submission data
        ignored_submissions_count = 0
        for sub in submissions:
            if sub.verdict is None or sub.verdict in [
                cf.Verdict.TESTING,
                cf.Verdict.SECURITY_VIOLATED,
            ]:
                ignored_submissions_count += 1
                continue

            sub_id = str(sub.id)
            timestamp = self.__epochToISO(sub.relativeTimeSeconds)
            reltime = self.__secondsToHHMMSS(sub.relativeTimeSeconds)

            self.__add_event(
                Feed.Submission(
                    id=sub_id,
                    language_id="0",
                    problem_id=sub.problem.index,
                    team_id=self.__get_team_info(sub.author).Id,
                    time=timestamp,
                    contest_time=reltime,
                    files=[],
                )
            )

            verdict: Feed.JudgementTypeId
            if sub.verdict == cf.Verdict.OK:
                verdict = Feed.JudgementTypeId.AC
            elif sub.verdict in [
                cf.Verdict.FAILED,
                cf.Verdict.TIME_LIMIT_EXCEEDED,
                cf.Verdict.MEMORY_LIMIT_EXCEEDED,
                cf.Verdict.WRONG_ANSWER,
                cf.Verdict.RUNTIME_ERROR,
                cf.Verdict.CHALLENGED,
                cf.Verdict.IDLENESS_LIMIT_EXCEEDED,
                cf.Verdict.REJECTED,
                cf.Verdict.CRASHED,
                cf.Verdict.PRESENTATION_ERROR,
                cf.Verdict.PARTIAL,
            ]:
                verdict = Feed.JudgementTypeId.WA
            elif sub.verdict in [
                cf.Verdict.COMPILATION_ERROR,
                cf.Verdict.INPUT_PREPARATION_CRASHED,
                cf.Verdict.SKIPPED,
            ]:
                verdict = Feed.JudgementTypeId.CE
            else:
                assert False, f"all verdicts not covered: {sub.verdict}"

            self.__add_event(
                Feed.Judgement(
                    id=sub_id,
                    submission_id=sub_id,
                    start_time=timestamp,
                    end_time=timestamp,
                    start_contest_time=reltime,
                    end_contest_time=reltime,
                    judgement_type_id=verdict,
                )
            )

        logging.info(
            "#submissions: %d, [ignored: %d]",
            len(submissions),
            ignored_submissions_count,
        )

        ## end the contest
        self.__show_contest_state(contest=contest, done=True)

        logging.info("#events: %d", len(self.__contest_events))

        ## IMPORTANT: DO NOT INDENT THE JSON, one event entry per line
        feed_json = [
            json.dumps(
                dataclasses.asdict(
                    event,
                    dict_factory=lambda x: {
                        k: v for (k, v) in x if k in ["id", "icpc_id"] or v is not None
                    },
                ),
            )
            for event in self.__contest_events
        ]
        return feed_json


__all__ = ["CFContestConfig", "EventFeedFromCFContest"]
