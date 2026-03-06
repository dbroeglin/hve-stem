---
name: foo
description: Fetch and summarise the README of a GitHub repository
---

When asked to summarise a repository, fetch the raw README from
`https://raw.githubusercontent.com/<owner>/<repo>/HEAD/README.md` and
return a concise one-paragraph summary of what the project does.
If no README exists, state that the repository has no README.
