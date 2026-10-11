# Justification

**Commands.** I started every command with `.venv\Scripts\` because flask, pytest and
ruff are only installed in the project's virtual environment, so a plain `pytest`
command wouldn't work. Claude ran the tests and the linter in all three sessions without
having to ask how. Session 3 changed this section the most: the line "Baseline: 6
existing findings" became wrong when the count dropped to 5, so now it just says to run
`ruff check .` first and compare. If I had to cut this section in half, I'd remove the
"Run one file" and "Run server" lines, because Claude never used them.

**Architecture.** I listed the layers (routes → services → repositories) and named
`services/users.py` as the example, so Claude knows where code goes. Session 3 changed this section the most: Claude said `process_order` errors
would become a 404 because v1 wrongly said a route calls it, so now I list exactly which
functions have routes. Session 1 added the rule that one service can call another,
because Claude didn't call `get_user` from `services/tasks.py` when v1 didn't say it was
allowed. If I had to cut this section in half, I'd remove the `utils/errors.py` details,
because the examples in Conventions already show those errors being used.

**Conventions.** I wrote these rules as real code, like `raise NotFoundError("Task")` and
`pytest.raises(NotFoundError)`, because Claude copied those examples exactly in all three
sessions. Session 2 changed this section the most: Claude added a duplicate test instead
of fixing the weak one, so I added a line saying to make the weak test stricter, and in
session 3 it did. The "Undecided — ask, don't guess" line lists questions nobody has
answered yet, so Claude asks instead of making something up. If I had to cut this
section in half, I'd keep the code examples and remove the lines that just repeat them,
like "Follow `services/users.py`."

**Do not touch.** Each rule protects something that would break without an obvious
error: the error handler reads `e.message` and `e.status_code`, the tests need task 2 to
be "Write report" and id 999 to not exist, and the routes and tests call the task
functions by position. I put the reason next to each rule, and Claude didn't break
any of them. If I had to cut this
section in half, I'd keep the rules about the sample data and the function signatures,
because breaking those makes the tests fail right away.

**Team project.** If three people were working on this, I'd make two changes. First, I'd
move my Windows-only `.venv\Scripts\` commands into a personal `CLAUDE.local.md` file,
because teammates on Mac or Linux would need different commands, and keep the shared
`CLAUDE.md` for rules everyone agrees on. Second, I'd make someone responsible for
answering each "Undecided" question, and have every change to `CLAUDE.md` reviewed in a
pull request like normal code. Session 3 showed that Claude repeats whatever the file
says, even when it's wrong, so one person's mistake could affect everyone.
