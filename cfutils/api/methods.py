"""
Helpers for `Codeforces API Methods <https://codeforces.com/apiHelp/methods>`_.
"""
import secrets
import time
import hashlib
import os
import logging
import json
import typing
from typing import Optional, Any
from abc import abstractmethod, ABC
from dataclasses import dataclass, is_dataclass, asdict
import sh  # type: ignore
from io import StringIO
from dataclass_wizard import JSONWizard  # type: ignore

from cfutils.api.objects import (
    User,
    BlogEntry,
    Comment,
    RecentAction,
    RatingChange,
    Contest,
    Problem,
    ProblemStatistics,
    Submission,
    Hack,
    RanklistRow,
    CFObject,
)


class CFAPIError(Exception):
    pass


class APIMethod(ABC):
    """Base class for codeforces API methods.
    See https://codeforces.com/apiHelp/methods for the full list and information on each parameter.

    Each class that inherits from this must also be marked as a `dataclass`.
    Use the dataclass parameters to define the API arguments.
    Allowed argument types:

    .. code::

        T ::= int | str | bool | list[T] | Optional[T]

    Caveats:
        - As `from` is a keyword in python, we instead use `From` for API parameters. This works as the API keys are case insensitive.
    """

    @staticmethod
    @abstractmethod
    def name() -> str:
        """API method name"""

    @staticmethod
    @abstractmethod
    def resultType() -> type:
        """
        Must be `dataclass | list[dataclass] | list[str] | list[int]`
        """

    def auth_required(self) -> bool:
        """
        Returns:
            True if the method call requires authorization
        """
        return False

    def __serialize(self, value: str | int | list[str | int]) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, int):
            return str(value)
        if isinstance(value, list):
            return ";".join(map(str, value))

        raise AssertionError(
            f"type {type(value)} not allowed as a API parameter, cannot serialize."
        )

    def __parse(self, data):
        resultType = self.resultType()

        if typing.get_origin(resultType) == list:
            baseType = typing.get_args(resultType)[0]
            if baseType == str or baseType == int:
                return data
            return [baseType.from_dict(elem) for elem in data]

        if issubclass(resultType, JSONWizard):
            return resultType.from_dict(data)  # type: ignore

        assert f"invalid resultType {resultType}"

    def __get_opts(self) -> dict[str, Any]:
        assert is_dataclass(self) and not isinstance(self, type)
        return asdict(self)

    def buildAPICallURL(self, *, auth: bool = False):
        """Build the URL to call the CF API

        Args:
            auth: authorized API call, signed using your API key.

        Raises:
            CFAPIError: when `auth=True` but API key/secret is not provided.

        Returns:
            URL string
        """
        opts = self.__get_opts()

        # Hack to correctly serialize parameter `from`, which is a keyword in python.
        if "From" in opts:
            opts["from"] = opts["From"]
            del opts["From"]

        if auth:
            # add key and time
            api_key = os.getenv("CODEFORCES_API_KEY")
            if api_key is None:
                raise CFAPIError("CODEFORCES_API_KEY not provided")

            opts["apiKey"] = api_key
            opts["time"] = str(int(time.time()))

        opts_list: list[tuple[str, str | int]] = [
            (k, self.__serialize(v)) for k, v in opts.items() if v is not None
        ]
        opts_list.sort()
        opts_str = "&".join([f"{k}={v}" for k, v in opts_list])

        call: str = self.name()
        if opts_str != "":
            call = f"{call}?{opts_str}"

        if auth:
            # sign the call string
            api_secret = os.getenv("CODEFORCES_API_SECRET")
            if api_secret is None:
                raise CFAPIError("CODEFORCES_API_SECRET not provided")

            rnd = "".join([secrets.choice("123456789") for _ in range(6)])
            secret = f"{rnd}/{call}#{api_secret}"
            hash_value = hashlib.sha512(secret.encode("utf-8")).hexdigest()

            call = f"{call}&apiSig={rnd}{hash_value}"

        return f"https://codeforces.com/api/{call}"

    def get(
        self,
        *,
        auth: bool = False,
        delay: float = 2.0,
        output_file: str | None = None,
        load_from_file: str | None = None,
    ):
        """Execute an API call to codeforces

        Args:
            auth: authorized API call, signed using your API key.
            delay (optional): number of seconds to wait before executing the call. Default is 2s.
            output_file (optional): write raw API response to file.
            load_from_file (optional): If this file exists, load data from it instead of running the API. Useful if you've already called the API or called it from a different source and saved the response.

        Raises:
            CFAPIError: when API call fails.
            CFAPIError: when `auth=True` but API key/secret is not provided.

        Returns:
            "result" component of the API data returned, parsed appropriately into an object of type `self.resultType()`.
        """

        if load_from_file is not None and os.path.isfile(load_from_file):
            logging.info("API(%s) load from file: %s", self.name(), load_from_file)
            with open(load_from_file) as inf:
                data = json.load(inf)
        else:
            if self.auth_required() and not auth:
                raise CFAPIError("API call requires authorization")

            # run API call
            time.sleep(delay)
            url = self.buildAPICallURL(auth=auth)
            logging.info("API(%s) call: %s", self.name(), url)

            buf = StringIO()
            sh.curl(url, _out=buf)  # type: ignore
            data = json.loads(buf.getvalue())

        if data["status"] != "OK":
            raise CFAPIError(data["comment"])

        if output_file is not None and (
            output_file != load_from_file or not os.path.isfile(output_file)
        ):
            logging.info("API(%s) saving to file: %s", self.name(), output_file)
            with open(output_file, "w") as outf:
                json.dump(data, outf, indent=2)

        return self.__parse(data["result"])


@dataclass
class BlogEntry_Comments(APIMethod):
    """Returns a list of comments to the specified blog entry."""

    blogEntryId: int

    @staticmethod
    def name() -> str:
        return "blogEntry.comments"

    @staticmethod
    def resultType() -> type:
        return list[Comment]


@dataclass
class BlogEntry_View(APIMethod):
    """Returns blog entry."""

    blogEntryId: int

    @staticmethod
    def name() -> str:
        return "blogEntry.view"

    @staticmethod
    def resultType() -> type:
        return BlogEntry


@dataclass
class Contest_Hacks(APIMethod):
    """
    Returns list of hacks in the specified contests.
    Full information about hacks is available only after some time after the contest end.
    During the contest user can see only own hacks.
    """

    contestId: int
    asManager: bool = False

    @staticmethod
    def name() -> str:
        return "contest.hacks"

    @staticmethod
    def resultType() -> type:
        return list[Hack]

    def auth_required(self) -> bool:
        return self.asManager


@dataclass
class Contest_List(APIMethod):
    """Returns information about all available contests.
    If this method is called not anonymously, then all available contests for a calling user will be returned too, including mashups and private gyms.
    """

    gym: bool = False

    @staticmethod
    def name() -> str:
        return "contest.list"

    @staticmethod
    def resultType() -> type:
        return list[Contest]


@dataclass
class Contest_RatingChanges(APIMethod):
    """Returns rating changes after the contest."""

    contestId: int

    @staticmethod
    def name() -> str:
        return "contest.ratingChanges"

    @staticmethod
    def resultType() -> type:
        return list[RatingChange]


@dataclass
class Contest_Standings(APIMethod):
    """Returns the description of the contest and the requested part of the standings."""

    contestId: int
    From: int
    count: int
    asManager: bool = False
    showUnofficial: bool = False
    room: Optional[int] = None

    @dataclass
    class Result(CFObject):
        contest: Contest
        problems: list[Problem]
        rows: list[RanklistRow]

    @staticmethod
    def name():
        return "contest.standings"

    @staticmethod
    def resultType() -> type:
        return Contest_Standings.Result


@dataclass
class Contest_Status(APIMethod):
    """Returns submissions for specified contest.
    Optionally can return submissions of specified user.
    """

    contestId: int
    From: int
    count: int
    asManager: bool = False
    handle: Optional[str] = None

    @staticmethod
    def name() -> str:
        return "contest.status"

    @staticmethod
    def resultType() -> type:
        return list[Submission]

    def auth_required(self) -> bool:
        return self.asManager


@dataclass
class Problemset_Problems(APIMethod):
    """Returns all problems from problemset.
    Problems can be filtered by tags.
    """

    tags: list[str]
    problemsetName: Optional[str] = None

    @dataclass
    class Result(JSONWizard):
        problems: list[Problem]
        problemStatistics: list[ProblemStatistics]

    @staticmethod
    def name() -> str:
        return "problemset.problems"

    @staticmethod
    def resultType() -> type:
        return Problemset_Problems.Result


@dataclass
class Problemset_RecentStatus(APIMethod):
    count: int
    problemsetName: Optional[str] = None

    @staticmethod
    def name() -> str:
        return "problemset.recentStatus"

    @staticmethod
    def resultType() -> type:
        return list[Submission]


@dataclass
class RecentActions(APIMethod):
    maxCount: int
    """can be up to 100"""

    @staticmethod
    def name() -> str:
        return "recentActions"

    @staticmethod
    def resultType() -> type:
        return list[RecentAction]


@dataclass
class User_BlogEntries(APIMethod):
    handle: str

    @staticmethod
    def name() -> str:
        return "user.blogEntries"

    @staticmethod
    def resultType() -> type:
        return list[BlogEntry]


@dataclass
class User_Friends(APIMethod):
    onlyOnline: bool = False

    @staticmethod
    def name() -> str:
        return "user.friends"

    @staticmethod
    def resultType() -> type:
        return list[str]

    def auth_required(self) -> bool:
        return True


@dataclass
class User_Info(APIMethod):
    handles: list[str]

    @staticmethod
    def name():
        return "user.info"

    @staticmethod
    def resultType() -> type:
        return list[User]


@dataclass
class User_RatedList(APIMethod):
    activeOnly: bool = True
    includeRetired: bool = False

    @staticmethod
    def name() -> str:
        return "user.ratedList"

    @staticmethod
    def resultType() -> type:
        return list[User]


@dataclass
class User_Rating(APIMethod):
    """Rating history of the specified user."""

    handle: str

    @staticmethod
    def name() -> str:
        return "user.rating"

    @staticmethod
    def resultType() -> type:
        return list[RatingChange]


@dataclass
class User_Status(APIMethod):
    """Submissions of specified user."""

    handle: str
    From: int
    count: int

    @staticmethod
    def name() -> str:
        return "user.status"

    @staticmethod
    def resultType() -> type:
        return list[Submission]


__all__ = [
    "APIMethod",
    "CFAPIError",
    "BlogEntry_Comments",
    "BlogEntry_View",
    "Contest_Hacks",
    "Contest_List",
    "Contest_RatingChanges",
    "Contest_Standings",
    "Contest_Status",
    "Problemset_Problems",
    "Problemset_RecentStatus",
    "RecentActions",
    "User_BlogEntries",
    "User_Friends",
    "User_Info",
    "User_RatedList",
    "User_Rating",
    "User_Status",
]
