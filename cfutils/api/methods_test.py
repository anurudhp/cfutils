import typing
from typing import Any
from dataclasses import dataclass
import pytest

from cfutils.api.methods import (
    APIMethod,
    Contest_Standings,
    Contest_Status,
    User_Info,
)


@dataclass
class MethodExample:
    methodClass: type
    opts: dict[str, Any]
    url: str


methodExamples: dict[str, MethodExample] = {
    # MethodExample(
    #     BlogEntry_Comments,
    #     {},
    #     "https://codeforces.com/api/blogEntry.comments?blogEntryId=79",
    # ),
    # MethodExample(
    #     BlogEntry_View, {}, "https://codeforces.com/api/blogEntry.view?blogEntryId=79"
    # ),
    # MethodExample(
    #     Contest_Hacks, {}, "https://codeforces.com/api/contest.hacks?contestId=566"
    # ),
    # MethodExample(Contest_List, {}, "https://codeforces.com/api/contest.list?gym=true"),
    # MethodExample(
    #     Contest_RatingChanges,
    #     {},
    #     "https://codeforces.com/api/contest.ratingChanges?contestId=566",
    # ),
    "contest.standings": MethodExample(
        Contest_Standings,
        {"contestId": 566, "From": 1, "count": 5, "showUnofficial": True},
        "https://codeforces.com/api/contest.standings?asManager=False&contestId=566&count=5&from=1&showUnofficial=True",
    ),
    "contest.status": MethodExample(
        Contest_Status,
        {"contestId": 566, "From": 34500, "count": 200},
        "https://codeforces.com/api/contest.status?contestId=566&count=200&from=34500",
    ),
    # MethodExample(
    #     Problemset_Problems,
    #     {},
    #     "https://codeforces.com/api/problemset.problems?tags=implementation",
    # ),
    # MethodExample(
    #     Problemset_RecentStatus,
    #     {},
    #     "https://codeforces.com/api/problemset.recentStatus?count=50",
    # ),
    # MethodExample(
    #     RecentActions, {}, "https://codeforces.com/api/recentActions?maxCount=100"
    # ),
    # MethodExample(
    #     User_BlogEntries,
    #     {},
    #     "https://codeforces.com/api/user.blogEntries?handle=Um_nik",
    # ),
    # MethodExample(
    #     User_Friends, {}, "https://codeforces.com/api/user.friends?onlyOnline=true"
    # ),
    "user.info": MethodExample(
        User_Info,
        {"handles": ["DmitriyH", "Fefer_Ivan", "codelegend"]},
        "https://codeforces.com/api/user.info?handles=DmitriyH;Fefer_Ivan;codelegend",
    ),
    # MethodExample(
    #     User_RatedList,
    #     {},
    #     "https://codeforces.com/api/user.ratedList?activeOnly=true&includeRetired=false",
    # ),
    # MethodExample(
    #     User_Rating, {}, "https://codeforces.com/api/user.rating?handle=codelegend"
    # ),
    # MethodExample(
    #     User_Status,
    #     {},
    #     "https://codeforces.com/api/user.status?handle=Fefer_Ivan&from=1&count=10",
    # ),
}


@pytest.mark.parametrize("example", methodExamples.values(), ids=methodExamples.keys())
def test_method(example: MethodExample):
    assert issubclass(example.methodClass, APIMethod)

    method = example.methodClass(**example.opts)
    assert method.buildAPICallURL() == example.url

    data_file = f"data/examples/api/{method.name()}.json"
    obj = method.get(load_from_file=data_file)

    resultType = method.resultType()
    if typing.get_origin(resultType) == list:
        baseType = typing.get_args(resultType)[0]
        assert baseType.Meta.raise_on_unknown_json_key
        assert isinstance(obj, list)
        assert all([isinstance(elem, baseType) for elem in obj])
    else:
        assert resultType.Meta.raise_on_unknown_json_key  # type: ignore
        assert isinstance(obj, resultType)
