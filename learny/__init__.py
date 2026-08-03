"""Turn learning into play — build knowledge with joy.

``learny`` collects small, self-contained learning games and the data that
drives them. Today the package is a container for those assets rather than a
Python API: each sub-package holds the game parameters (word groups, quiz
definitions) plus the front-end that renders them.

Sub-packages
------------

``learny.eleven_plus``
    Vocabulary material and a quiz app for the UK 11+ exam. The word/quiz
    parameters are JSON files shipped alongside the package; the player is a
    Vite/React app (``quiz-test/``) with a dependency-free standalone HTML
    build for offline use.

The JSON game-parameter files are the interesting, reusable part: they are
plain data, so they can be loaded by any front-end, notebook, or script.

Because the value of this distribution *is* its data, the one thing worth
asserting is that the data actually ships with the package:

>>> from pathlib import Path
>>> import learny
>>> pkg_dir = Path(learny.__file__).parent
>>> 'eleven_plus' in {p.name for p in pkg_dir.iterdir() if p.is_dir()}
True
>>> any(pkg_dir.joinpath('eleven_plus').glob('*.json'))
True
"""
