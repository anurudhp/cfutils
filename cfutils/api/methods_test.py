import typing
from dataclasses import dataclass
import pytest

from cfutils.api.methods import (
    APIMethod,
    BlogEntry_Comments,
    BlogEntry_View,
    Contest_List,
    Contest_RatingChanges,
    Contest_Standings,
    Contest_Status,
    Contest_Hacks,
    Problemset_Problems,
    Problemset_RecentStatus,
    RecentActions,
    User_BlogEntries,
    User_Friends,
    User_RatedList,
    User_Rating,
    User_Status,
    User_Info,
)


@dataclass
class MethodExample:
    method: APIMethod
    url: str


methodExamples: dict[str, MethodExample] = {
    "blogEntry.comments": MethodExample(
        BlogEntry_Comments(blogEntryId=79),
        "https://codeforces.com/api/blogEntry.comments?blogEntryId=79",
    ),
    "blogEntry.view": MethodExample(
        BlogEntry_View(blogEntryId=79),
        "https://codeforces.com/api/blogEntry.view?blogEntryId=79",
    ),
    "contest.hacks": MethodExample(
        Contest_Hacks(contestId=566),
        "https://codeforces.com/api/contest.hacks?asManager=False&contestId=566",
    ),
    "contest.list": MethodExample(
        Contest_List(gym=True), "https://codeforces.com/api/contest.list?gym=True"
    ),
    "constes.ratingChanges": MethodExample(
        Contest_RatingChanges(contestId=566),
        "https://codeforces.com/api/contest.ratingChanges?contestId=566",
    ),
    "contest.standings": MethodExample(
        Contest_Standings(contestId=566, From=1, count=5, showUnofficial=True),
        "https://codeforces.com/api/contest.standings?asManager=False&contestId=566&count=5&from=1&showUnofficial=True",
    ),
    "contest.status": MethodExample(
        Contest_Status(contestId=566, From=34500, count=200),
        "https://codeforces.com/api/contest.status?asManager=False&contestId=566&count=200&from=34500",
    ),
    "problemset.problems": MethodExample(
        Problemset_Problems(tags=["implementation"]),
        "https://codeforces.com/api/problemset.problems?tags=implementation",
    ),
    "problemset.recentStatus": MethodExample(
        Problemset_RecentStatus(count=50),
        "https://codeforces.com/api/problemset.recentStatus?count=50",
    ),
    "recentActions": MethodExample(
        RecentActions(maxCount=100),
        "https://codeforces.com/api/recentActions?maxCount=100",
    ),
    "user.blogEntries": MethodExample(
        User_BlogEntries(handle="Um_nik"),
        "https://codeforces.com/api/user.blogEntries?handle=Um_nik",
    ),
    # user friends requires auth, the below method only tests the local file
    "user.friends": MethodExample(
        User_Friends(onlyOnline=True),
        "https://codeforces.com/api/user.friends?onlyOnline=True",
    ),
    "user.info": MethodExample(
        User_Info(handles=["DmitriyH", "Fefer_Ivan", "codelegend"]),
        "https://codeforces.com/api/user.info?handles=DmitriyH;Fefer_Ivan;codelegend",
    ),
    "user.ratedList": MethodExample(
        User_RatedList(),
        "https://codeforces.com/api/user.ratedList?activeOnly=True&includeRetired=False",
    ),
    "user.rating": MethodExample(
        User_Rating(handle="codelegend"),
        "https://codeforces.com/api/user.rating?handle=codelegend",
    ),
    "user.status": MethodExample(
        User_Status(handle="Fefer_Ivan", From=1, count=10),
        "https://codeforces.com/api/user.status?count=10&from=1&handle=Fefer_Ivan",
    ),
}


@pytest.mark.parametrize("example", methodExamples.values(), ids=methodExamples.keys())
def test_method(example: MethodExample):
    method = example.method
    assert issubclass(type(example.method), APIMethod)
    assert method.buildAPICallURL() == example.url

    data_file = f"data/examples/api/{method.name()}.json"
    obj = method.get(load_from_file=data_file)

    resultType = method.resultType()
    if typing.get_origin(resultType) == list:
        baseType = typing.get_args(resultType)[0]
        # assert baseType.Meta.raise_on_unknown_json_key
        assert isinstance(obj, list)
        assert all([isinstance(elem, baseType) for elem in obj])
    else:
        # assert resultType.Meta.raise_on_unknown_json_key  # type: ignore
        assert isinstance(obj, resultType)
