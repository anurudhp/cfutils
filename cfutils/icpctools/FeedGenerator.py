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
class CFContestConfig:
    freezeDurationSeconds: int
    regions: list[str]
    include_virtual: bool = False
    include_out_of_comp: bool = False

    def getRegion(self, teamId, teamName, members) -> str:
        return self.regions[0]

    # TODO use this to generate awards
    def medalCounts(self, num_teams: int) -> tuple[int, int, int]:
        return 4, 4, 4


class EventFeedFromCFContest:
    config: CFContestConfig
    __contest_events: list[Event]

    def __init__(self, *, config: CFContestConfig):
        self.config = config
        self.__contest_events = []

    @staticmethod
    def __epochToISO(s: int) -> str:
        return (
            datetime.datetime.fromtimestamp(s).isoformat(timespec="milliseconds")
            + "+00"
        )

    @staticmethod
    def __secondsToHHMMSS(s) -> str:
        res = str(datetime.timedelta(seconds=int(s))) + ".000"
        if res[1] == ":":
            res = "0" + res
        return res

    def __extract_team_list(self, submissions: list[cf.Submission]) -> list[cf.Party]:
        """Run through all the submissions to get list of participating teams.
        For individual accounts, treat them as a team with one member.
        """
        teams: dict[int, cf.Party] = {}

        individuals: dict[str, int] = {}
        ghosts: dict[str, int] = {}

        for sub in submissions:
            author = sub.author

            if author.teamId is None:
                # not a CF team, must be either a single user or a ghost
                user: str
                if author.ghost:
                    if author.teamName is not None:
                        # TODO
                        pass
                    else:
                        # TODO
                        pass
                else:
                    assert len(author.members) == 1
                    user = author.members[0].handle
                    if user not in individuals:
                        ix = len(individuals)
                        individuals[user] = ix

                    ix = individuals[user]
                    author.teamId = 10**6 + ix  # TODO is this index safe?
                    author.teamName = user

            assert author.teamId is not None
            teams[author.teamId] = author

        return list(teams.values())

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

    def __show_contest_state(self, *, contest: cf.Contest, ended=False, done=False):
        """Event displayed at the start and end, and optionally at standings freeze"""
        tstart = contest.startTimeSeconds
        assert tstart is not None

        tfin = tstart + contest.durationSeconds
        tfrozen = tfin - self.config.freezeDurationSeconds
        tthaw = tfin + 300  # TODO(magic) why 300?
        tdone = int(time.time())

        self.__add_event(
            Feed.State(
                started=self.__epochToISO(tstart),
                ended=self.__epochToISO(tfin) if ended or done else None,
                finalized=self.__epochToISO(tdone) if done else None,
                # TODO(magic) why 60?
                end_of_updates=self.__epochToISO(tdone + 60) if done else None,
                frozen=self.__epochToISO(tfrozen),
                thawed=self.__epochToISO(tthaw),
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
        submissions: list[cf.Submission],
    ) -> list[str]:
        """Generate event feed JSON for the ICPC resolver tool.
        TODO docstring
        """

        ## ignore invalid submissions
        submissions = [
            sub
            for sub in submissions
            if self.__participantAllowed(sub.author.participantType)
        ]

        ## contest info
        if contest.startTimeSeconds is None:
            raise EventFeedError("Contest: start time not provided")
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
                start_time=self.__epochToISO(contest.startTimeSeconds),
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

        ## Contest regions - use it to form different contestant prize groups.
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

        # teams
        teams = self.__extract_team_list(submissions)

        for team in teams:
            assert team.teamId is not None
            assert team.teamName is not None

            memberHandles = [user.handle for user in team.members]
            fullTeamName = f"{team.teamName} ({', '.join(memberHandles)})"

            region = self.config.getRegion(team.teamId, team.teamName, memberHandles)
            region = str(self.config.regions.index(region))

            self.__add_event(
                Feed.Team(
                    id=str(team.teamId),
                    name=fullTeamName,
                    group_ids=[region],
                    organization_id="org_default",
                )
            )
        logging.info("#teams: %d", len(teams))

        ## start the contest
        self.__show_contest_state(contest=contest)

        ## submission data
        ignored_submissions_count = 0
        for sub in submissions:
            if sub.verdict is None:
                ignored_submissions_count += 1
                continue

            sub_id = str(sub.id)
            timestamp = self.__epochToISO(sub.creationTimeSeconds)
            reltime = self.__secondsToHHMMSS(sub.relativeTimeSeconds)

            self.__add_event(
                Feed.Submission(
                    id=sub_id,
                    language_id="0",
                    problem_id=sub.problem.index,
                    team_id=str(sub.author.teamId),
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
