"""
Codeforces API return objects.
See https://codeforces.com/apiHelp/objects for a full list and information on each parameter.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from dataclass_wizard import JSONWizard  # type: ignore


# TODO unsafe feature, instead get this working with inheritance
class GlobalJSONMeta(JSONWizard.Meta):
    raise_on_unknown_json_key = True


@dataclass
class CFObject(JSONWizard):
    """Base class for codeforces API return Objects.
    See https://codeforces.com/apiHelp/objects for a full list.
    """

    # TODO get this working with inheritance
    # class Meta(JSONWizard.Meta):
    #     raise_on_unknown_json_key = True


@dataclass
class User(CFObject):
    handle: str
    email: Optional[str] = None
    vkId: Optional[str] = None
    openId: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    organization: Optional[str] = None
    contribution: Optional[int] = None
    rank: Optional[str] = None
    rating: Optional[int] = None
    maxRank: Optional[str] = None
    maxRating: Optional[int] = None
    lastOnlineTimeSeconds: Optional[int] = None
    registrationTimeSeconds: Optional[int] = None
    friendOfCount: Optional[int] = None
    avatar: Optional[str] = None
    titlePhoto: Optional[str] = None


@dataclass
class BlogEntry(CFObject):
    id: int
    originalLocale: str
    creationTimeSeconds: int
    authorHandle: str
    title: str
    locale: str
    allowViewHistory: bool
    tags: list[str]
    rating: int
    content: Optional[str] = None
    modificationTimeSeconds: Optional[int] = None


@dataclass
class Comment(CFObject):
    id: int
    creationTimeSeconds: int
    commentatorHandle: str
    locale: str
    text: str
    rating: int
    parentCommentId: Optional[int] = None


@dataclass
class RecentAction(CFObject):
    timeSeconds: int
    blogEntry: Optional[BlogEntry] = None
    comment: Optional[Comment] = None


@dataclass
class RatingChange(CFObject):
    contestId: int
    contestName: str
    handle: str
    rank: int
    ratingUpdateTimeSeconds: int
    oldRating: int
    newRating: int


class ContestType(Enum):
    CF = "CF"
    IOI = "IOI"
    ICPC = "ICPC"


class ContestPhase(Enum):
    BEFORE = "BEFORE"
    CODING = "CODING"
    PENDING_SYSTEM_TEST = "PENDING_SYSTEM_TEST"
    SYSTEM_TEST = "SYSTEM_TEST"
    FINISHED = "FINISHED"


@dataclass
class Contest(CFObject):
    id: int
    name: str
    type: ContestType
    phase: ContestPhase
    frozen: bool
    durationSeconds: int
    startTimeSeconds: Optional[int] = None
    relativeTimeSeconds: Optional[int] = None
    preparedBy: Optional[str] = None
    websiteUrl: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[int] = None
    kind: Optional[str] = None
    icpcRegion: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    season: Optional[str] = None


@dataclass
class Member(CFObject):
    handle: str
    name: Optional[str] = None


class ParticipantType(Enum):
    CONTESTANT = "CONTESTANT"
    PRACTICE = "PRACTICE"
    VIRTUAL = "VIRTUAL"
    MANAGER = "MANAGER"
    OUT_OF_COMPETITION = "OUT_OF_COMPETITION"


@dataclass
class Party(CFObject):
    members: list[Member]
    participantType: ParticipantType
    contestId: Optional[int] = None
    teamId: Optional[int] = None
    teamName: Optional[str] = None
    ghost: bool = False
    room: Optional[int] = None
    startTimeSeconds: Optional[int] = None


class ProblemType(Enum):
    PROGRAMMING = "PROGRAMMING"
    QUESTION = "QUESTION"


@dataclass
class Problem(CFObject):
    index: str
    name: str
    type: ProblemType
    tags: list[str]
    contestId: Optional[int] = None
    problemsetName: Optional[str] = None
    points: Optional[float] = None
    rating: Optional[int] = None


@dataclass
class ProblemStatistics(CFObject):
    index: str
    solvedCount: int
    contestId: Optional[int] = None


class Verdict(Enum):
    FAILED = "FAILED"
    OK = "OK"
    PARTIAL = "PARTIAL"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    WRONG_ANSWER = "WRONG_ANSWER"
    PRESENTATION_ERROR = "PRESENTATION_ERROR"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    IDLENESS_LIMIT_EXCEEDED = "IDLENESS_LIMIT_EXCEEDED"
    SECURITY_VIOLATED = "SECURITY_VIOLATED"
    CRASHED = "CRASHED"
    INPUT_PREPARATION_CRASHED = "INPUT_PREPARATION_CRASHED"
    CHALLENGED = "CHALLENGED"
    SKIPPED = "SKIPPED"
    TESTING = "TESTING"
    REJECTED = "REJECTED"


class Testset(Enum):
    SAMPLES = "SAMPLES"
    PRETESTS = "PRETESTS"
    TESTS = "TESTS"
    CHALLENGES = "CHALLENGES"
    TESTS1 = "TESTS1"
    TESTS2 = "TESTS2"
    TESTS3 = "TESTS3"
    TESTS4 = "TESTS4"
    TESTS5 = "TESTS5"
    TESTS6 = "TESTS6"
    TESTS7 = "TESTS7"
    TESTS8 = "TESTS8"
    TESTS9 = "TESTS9"
    TESTS10 = "TESTS10"


@dataclass
class Submission(CFObject):
    id: int
    creationTimeSeconds: int
    relativeTimeSeconds: int
    problem: Problem
    author: Party
    programmingLanguage: str
    testset: Testset
    passedTestCount: int
    timeConsumedMillis: int
    memoryConsumedBytes: int
    verdict: Optional[Verdict] = None
    contestId: Optional[int] = None
    points: Optional[float] = None


class HackVerdict(Enum):
    HACK_SUCCESSFUL = "HACK_SUCCESSFUL"
    HACK_UNSUCCESSFUL = "HACK_UNSUCCESSFUL"
    INVALID_INPUT = "INVALID_INPUT"
    GENERATOR_INCOMPILABLE = "GENERATOR_INCOMPILABLE"
    GENERATOR_CRASHED = "GENERATOR_CRASHED"
    IGNORED = "IGNORED"
    TESTING = "TESTING"
    OTHER = "OTHER"


@dataclass
class JudgeProtocol:
    manual: bool
    protocol: str
    verdict: str


@dataclass
class Hack(CFObject):
    id: int
    creationTimeSeconds: int
    hacker: Party
    defender: Party
    problem: Problem
    verdict: Optional[HackVerdict] = None
    test: Optional[str] = None
    judgeProtocol: Optional[JudgeProtocol] = None


class ProblemResultType(Enum):
    FINAL = "FINAL"
    PRELIMINARY = "PRELIMINARY"


@dataclass
class ProblemResult(CFObject):
    points: float
    rejectedAttemptCount: int
    type: ProblemResultType
    penalty: Optional[int] = None
    bestSubmissionTimeSeconds: Optional[int] = None


@dataclass
class RanklistRow(CFObject):
    party: Party
    rank: int
    points: float
    penalty: int
    successfulHackCount: int
    unsuccessfulHackCount: int
    problemResults: list[ProblemResult]
    lastSubmissionTimeSeconds: Optional[int] = None


__all__ = [
    ### Objects
    "User",
    "BlogEntry",
    "Comment",
    "RecentAction",
    "RatingChange",
    "Contest",
    "Party",
    "Member",
    "Problem",
    "ProblemStatistics",
    "Submission",
    "Hack",
    "RanklistRow",
    "ProblemResult",
    ### Enums
    "ContestType",
    "ContestPhase",
    "ParticipantType",
    "ProblemType",
    "ProblemResultType",
    "Testset",
    "Verdict",
    "JudgeProtocol",
    "HackVerdict",
]
