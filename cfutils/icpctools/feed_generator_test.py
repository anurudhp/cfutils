import cfutils.api as cf
import cfutils.icpctools.feed_generator as feed_gen


def test_feed_generator():
    contest_id = 104491
    submissions: list[cf.Submission] = cf.Contest_Status(
        contestId=contest_id, From=1, count=25000
    ).get(load_from_file="data/examples/resolverfeed/status_104491.json")

    standings: cf.Contest_Standings.Result = cf.Contest_Standings(
        contestId=contest_id, From=1, count=10000, showUnofficial=True
    ).get(load_from_file="data/examples/resolverfeed/standings_104491.json")

    feed_gen.EventFeedFromCFContest(
        config=feed_gen.CFContestConfig(
            freezeDurationSeconds=60 * 60,
            include_virtual=True,
            include_out_of_comp=True,
            strict_mode=True,
        )
    ).generate(
        contest=standings.contest,
        problems=standings.problems,
        ranklist=standings.rows,
        submissions=submissions,
    )
