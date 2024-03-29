import os
import logging
import click
from dotenv import load_dotenv

import cfutils.api as cf
from cfutils.icpctools.feed_generator import CFContestConfig, EventFeedFromCFContest


@click.command()  # type: ignore
@click.argument("contest_id", type=int)
@click.argument("status_file", type=click.Path(dir_okay=False))
@click.argument("standings_file", type=click.Path(dir_okay=False))
@click.argument("feed_file", type=click.Path(dir_okay=False))
@click.option(
    "--unofficial",
    is_flag=True,
    default=False,
    help="also download unofficial submissions and standings",
)
@click.option(
    "--auth", is_flag=True, default=False, help="authorize (sign) the API call"
)
@click.option("--verbose", is_flag=True, default=False, help="display debug messages")
def cli(contest_id, status_file, standings_file, feed_file, unofficial, auth, verbose):
    """Tool to download contest standings and generate feed for ICPC resolver.
    All files above are JSON.

    Example usage:

    `python feed.py ../data/examples/resolverfeed/standings_104491.json ../data/examples/resolverfeed/status_104491.json feed.json`
    """

    logging.basicConfig(
        format="[%(levelname)s]: %(message)s",
        level=logging.DEBUG if verbose else logging.INFO,
    )

    # load API keys if neccessary
    if auth:
        assert load_dotenv()
        assert os.getenv("CODEFORCES_API_KEY") is not None
        assert os.getenv("CODEFORCES_API_SECRET") is not None

    # get contest data from codeforces
    submissions: list[cf.Submission] = cf.Contest_Status(
        contestId=contest_id, From=1, count=25000
    ).get(auth=auth, output_file=status_file, load_from_file=status_file)

    standings: cf.Contest_Standings.Result = cf.Contest_Standings(
        contestId=contest_id, From=1, count=10000, showUnofficial=unofficial
    ).get(auth=auth, output_file=standings_file, load_from_file=standings_file)

    # generate the event feed
    feedGen = EventFeedFromCFContest(
        config=CFContestConfig(
            freezeDurationSeconds=60 * 60,
            include_virtual=unofficial,
            include_out_of_comp=unofficial,
            strict_mode=True,
        )
    )
    feed = feedGen.generate(
        contest=standings.contest,
        problems=standings.problems,
        ranklist=standings.rows,
        submissions=submissions,
    )

    with open(feed_file, "w") as outf:
        for event in feed:
            outf.write(event)
            outf.write("\n")
    logging.info(f"Contest {standings.contest.id} feed generated! Wrote to {feed_file}")


if __name__ == "__main__":
    cli()  # type: ignore
