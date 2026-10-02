# Local conventions

Filled in by the team that uses this skill. The assistant reads this file first, and what is written
here outranks the defaults in SKILL.md. An entry still showing `[YOUR ORGANIZATION: ...]` is
unknown: the assistant asks, and never fills it in with a guess.

## Grafana

- **URL and organisation (namespace):** [YOUR ORGANIZATION: Grafana URL; `default` or `org-<id>`]
- **How the assistant gets a service account token, and from whom:** [YOUR ORGANIZATION: ...]
- **Folders the assistant may change or create dashboards in:** [YOUR ORGANIZATION: ...]
- **Folders and dashboards it must never change:** [YOUR ORGANIZATION: ...]
- **Changes that need someone's approval first, and whose:** [YOUR ORGANIZATION: ...]
- **Last probe** (`python dashio.py probe`): [date, Grafana version, all checks held: yes or no, file]

## Conventions

- **Dashboard names and uids:** [YOUR ORGANIZATION: ...]
- **Panel titles, units, colours and thresholds:** [YOUR ORGANIZATION: ...]
- **Required tags:** [YOUR ORGANIZATION: ...]
- **Standard layout** (rows, what goes at the top): [YOUR ORGANIZATION: ...]
- **Approved data sources** and the variable each dashboard uses for them: [YOUR ORGANIZATION: ...]

## People

- **Default owner of a dashboard's design brief:** [YOUR ORGANIZATION: ...]
- **Who to ask when a convention is unclear:** [YOUR ORGANIZATION: ...]

## References to look up

The assistant consults these when a question falls in their area, and says which one it used.

- **Internal:** [YOUR ORGANIZATION: dashboard standards page; observability guidance; anything else
  the team treats as the rule]
- **Grafana:** the dashboard best practices and maturity levels pages in the Grafana documentation;
  variable syntax and advanced formatting; the dashboard HTTP API (`/apis/dashboard.grafana.app`)
  for your Grafana version. `FOUNDATIONS.md` lists the exact sources behind the skill's facts.
