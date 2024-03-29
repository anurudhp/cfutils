import logging
import os
import time
import sh  # type: ignore
import click

from cfutils.api.methods_test import methodExamples


@click.command()  # type: ignore
@click.argument("outdir", type=click.Path(exists=True, dir_okay=True, file_okay=False))
def download(outdir):
    """Download API results for the examples used in the unit tests.

    OUTDIR: output directory
    """
    for example in methodExamples.values():
        name = example.method.name()

        json_file = f"{outdir}/{name}.json"
        if not os.path.exists(json_file):
            with open(json_file, "w") as f:
                sh.curl(example.url, _out=f)  # type: ignore
            time.sleep(2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    download()  # type: ignore
