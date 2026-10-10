# `.github/workflows/deploy.yml`

Moved out of the file. Unreviewed.

## 1

Above `workflow_dispatch:`

Lets sync-cablecast.yml trigger a rebuild on weeks when the catalog did
not change but a featured item needs to expire.

## 2

Above `env:`

Lifted to the job so the deploy steps below can test whether it is set.
Secrets cannot be referenced directly in an `if:` expression.

## 3

Above `ruby-version: .ruby-version`

Read from .ruby-version rather than pinned here. Cloudflare Pages
reads that same file, so CI and the live build cannot drift onto
different Ruby versions and start disagreeing about whether the
site builds.
`.ruby-version` is a magic literal to this action, not a path — it
resolves it inside `working-directory`. Writing `site/.ruby-version`
gets parsed as an engine name and fails with "Unknown engine".

## 4

Above `- name: Build`

The build runs unconditionally. It is the part worth checking on every
pull request, and it does not need any credentials.

## 5

Above `- name: Deploy to Azure Static Web Apps`

Deployment is skipped until someone creates the Azure Static Web App
and adds its token as a repository secret. Until then the build still
gates every pull request, and CI stays green rather than failing on
infrastructure that does not exist yet.
