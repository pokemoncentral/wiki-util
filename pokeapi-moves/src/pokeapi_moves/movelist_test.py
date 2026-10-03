import io
from contextlib import redirect_stdout

from pokeapi_moves.movelist import movelist


def test_sample(snapshot):
    with redirect_stdout(io.StringIO()) as out:
        movelist(move="superpower", game="platinum", wipe_db=False)
    assert out.getvalue() == snapshot
