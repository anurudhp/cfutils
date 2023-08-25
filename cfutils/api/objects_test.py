from cfutils.api.objects import (
    User,
    Problem,
    ProblemType,
    Member,
    Party,
    ParticipantType,
)


def test_object_User():
    data = """{
      "lastName": "Peduri",
      "country": "India",
      "lastOnlineTimeSeconds": 1692657290,
      "rating": 1974,
      "friendOfCount": 2274,
      "titlePhoto": "https://userpic.codeforces.org/100074/title/4ca7345e3cb73be2.jpg",
      "handle": "codelegend",
      "avatar": "https://userpic.codeforces.org/100074/avatar/f1c8cf3f1b9cc8d5.jpg",
      "firstName": "Anurudh",
      "contribution": 9,
      "organization": "Ruhr University Bochum (RUB)",
      "rank": "candidate master",
      "maxRating": 2475,
      "registrationTimeSeconds": 1366650521,
      "maxRank": "grandmaster"
    }"""

    user = User.from_json(data)
    assert user.handle == "codelegend"


def test_object_Problem():
    data = """{
        "contestId": 1860,
        "index": "F",
        "name": "Evaluate RBS",
        "type": "PROGRAMMING",
        "tags": ["data structures", "geometry", "implementation", "math", "sortings"]
    }"""
    problem = Problem.from_json(data)
    assert problem.contestId == 1860
    assert problem.index == "F"
    assert problem.name == "Evaluate RBS"
    assert problem.type == ProblemType.PROGRAMMING
    assert problem.tags == [
        "data structures",
        "geometry",
        "implementation",
        "math",
        "sortings",
    ]


def test_object_Party():
    data = """{
        "contestId": 100,
        "members": [
            {"handle": "member1"},
            {"handle": "member2", "name": "Person Two"}
        ],
        "participantType": "CONTESTANT"
    }"""

    party = Party.from_json(data)
    assert party == Party(
        contestId=100,
        members=[Member(handle="member1"), Member(handle="member2", name="Person Two")],
        participantType=ParticipantType.CONTESTANT,
    )
