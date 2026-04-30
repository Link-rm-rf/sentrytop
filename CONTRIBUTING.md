# Contributing to SentryTop

First off, thank you for considering contributing to SentryTop! It's people like you that make SentryTop such a great tool.

## Where do I go from here?

If you've noticed a bug or have a feature request, make one! It's generally best if you get confirmation of your bug or approval for your feature request this way before starting to code.

## Fork & create a branch

If this is something you think you can fix, then fork SentryTop and create a branch with a descriptive name.

## Get the test suite running

Make sure you're able to run the integration tests locally. 
```bash
# Run the CLI test mock
python3 test_cli.py
```

## Implement your fix or feature

At this point, you're ready to make your changes. Feel free to ask for help; everyone is a beginner at first.

* For Python TUI changes, ensure you use `typing` module type hints.
* For C Collector changes, ensure memory leaks are checked using `valgrind`.
* For Java Correlator changes, ensure thread-safety.

## Make a Pull Request

At this point, you should switch back to your master branch and make sure it's up to date with SentryTop's master branch.
Then create a pull request with a clear list of what you've done.

Please link the relevant issue if there is one.
