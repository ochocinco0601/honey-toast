# Connect Copilot to GitHub

Copilot can use a connection to get information that isn't in your files. In this unit, you
connect Copilot to GitHub in a practice folder. You ask a question about a public project on GitHub and see Copilot look it up there.

## What a connection gives Copilot

Copilot does its work with tools. A tool is one action it can take, such as reading a file. A
connection adds tools from another service. VS Code calls a connection an MCP server.

When a request needs one of those tools, Copilot uses it, and the chat shows a line for each tool it ran.
The connection in this unit is GitHub's read-only one. Its tools only look things up on GitHub and can't change anything there.

The connection signs in to GitHub with your work GitHub account, the one you use for Copilot. You sign in
once, when VS Code asks. You don't set up anything on GitHub first.

## 1. Have Copilot create a practice folder

Copilot creates an empty folder to hold the connection while you practice.

1. In the chat box, enter:

> Create a new folder named connections-practice in the folder Windows uses as my Documents folder, which may be under OneDrive.
> If connections-practice already exists, don't change it; tell me instead.
> Leave the new folder empty.
> Add or change no other file.

2. If a permission request appears, allow it if it matches what you asked.
3. On the **File** menu, select **Open Folder**. In the window that opens, go to Documents, the same Documents that File Explorer shows on the left. Select `connections-practice`, and then **Select Folder**.
4. If VS Code asks whether you trust the authors of the files, select **Yes, I trust the authors**.
5. If a bar at the top says the folder is in Restricted Mode, select **Manage**, and then **Trust**.

Check: the list on the left shows `CONNECTIONS-PRACTICE`, and a control at the bottom of the chat box shows **Agent**.

<!-- more: If no control shows Agent -->
If no control there shows **Agent**, or the controls show only icons, select the chat box, hold down Ctrl, and press the period key (.). The list of agents opens, with the selected agent marked. Select **Agent**.
<!-- /more -->

## 2. Have Copilot add the GitHub connection

A connection is a few lines in a file named `.mcp.json`. Copilot writes them.

1. Enter:

> In the connections-practice folder, create a file named .mcp.json.
> In it, add one MCP server named github, under mcpServers.
> Set its type to http.
> Set its url to https://api.githubcopilot.com/mcp/readonly.
> If .mcp.json already exists, don't change it; tell me instead.
> Add or change no other file.

2. If a permission request appears, allow it if it creates only that file.
3. In the list on the left, select `.mcp.json`.
4. If a line of small text above `github` in the file says **Start**, select it. This starts the connection.
5. If a message says an MCP server wants to authenticate to GitHub, select **Allow**. If VS Code then asks you to choose an account or sign in, choose your work GitHub account.
6. Wait until the line above `github` says **Running**. It can take a few seconds.

Check: the line above `github` says **Running**.

<!-- more: If the line above github doesn't say Running -->
If it says **Start**, select it, and select **Allow** if asked. If there's no line above `github`
at all, or it still doesn't say **Running**, see [When you're stuck, ask Copilot](../troubleshooting.md#when-you-re-stuck-ask-copilot).
<!-- /more -->

<!-- more: If you don't sign in to GitHub at github.com -->
If the GitHub sign-in page you use for Copilot isn't on github.com, this connection's address is different. See [GitHub Enterprise](https://github.com/github/github-mcp-server#github-enterprise) in GitHub's documentation.
<!-- /more -->

**Important:** this connection is saved in the connections-practice folder, so it works only while
that folder is open in VS Code. To use it in another folder, have Copilot add it there.

## 3. Ask a question that uses the connection

Copilot uses the connection to look up the answer on GitHub, and the chat shows it did. GitHub
calls a project a repository, and each saved change to it a commit.

1. At the top of the chat, select **New Chat** (+).
2. Enter:

> Use the GitHub connection to answer this question.
> List the commits of the public octocat/Hello-World repository on GitHub.
> For the newest commit, tell me its date, its author and its message.

3. If a message says an MCP server wants to authenticate to GitHub, select **Allow**, and choose your work GitHub account.
4. If a permission request appears, allow it if it names github.

Check: the reply shows what Copilot did, one line for each tool it ran. If those lines are folded
under one line, select it to show them. One line says **Ran List commits**, the connection's tool
for listing commits. The answer says the newest commit was made in March 2012 by The Octocat, with
a message that starts "Merge pull request #6".

<!-- more: If no line says Ran List commits -->
Select `.mcp.json` in the list on the left. If the line above `github` doesn't say
**Running**, select **Start** there, select **Allow** if asked, and wait until it says
**Running**. Then select **New Chat** (+) and enter the request again. If it still doesn't work, see [When you're stuck, ask Copilot](../troubleshooting.md#when-you-re-stuck-ask-copilot).
<!-- /more -->

## On your own work

When a request needs information from another service, ask Copilot whether a connection exists
for that service. Copilot sends the service whatever it asks the service to look up. In this unit,
that went to GitHub. Before you add a connection, make sure you're allowed to send that service
what your requests will look up. Add the connection to the folder you work in. It lives in that
folder's `.mcp.json`. To remove it, have Copilot delete it from that file.

## What you did

You added GitHub's read-only connection in a practice folder and saw Copilot use it to look up a
public repository.

Source: [Add and manage MCP servers in VS Code](https://code.visualstudio.com/docs/agent-customization/mcp-servers), Microsoft; [Remote GitHub MCP Server](https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md), GitHub.
