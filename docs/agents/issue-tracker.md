# Issue Tracker: GitHub

Issues and PRDs for this repo live in GitHub Issues for `chavez-adrian/gdt-tooling-coach`.

Use the `gh` CLI for issue operations. Because the local repo may not have a remote configured yet, pass the repo explicitly:

```powershell
gh issue list --repo chavez-adrian/gdt-tooling-coach
gh issue view <number> --repo chavez-adrian/gdt-tooling-coach --comments
gh issue create --repo chavez-adrian/gdt-tooling-coach --title "..." --body-file <file>
gh issue edit <number> --repo chavez-adrian/gdt-tooling-coach --add-label "ready-for-agent"
```

When a skill says "publish to the issue tracker", create a GitHub issue in this repo.

When a skill says "fetch the relevant ticket", use `gh issue view <number> --repo chavez-adrian/gdt-tooling-coach --comments`.
