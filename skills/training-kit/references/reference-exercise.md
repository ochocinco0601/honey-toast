# The reference exercise: how a unit is written

An excerpt, unchanged, of a published hands-on exercise: its opening, scenario and first task.
Units in a kit are written in this form (the maintainer guide's "Writing" section says how).
Read it for the form, not the subject.

Source: Microsoft Learning, `mslearn-github-copilot-dev`,
`Instructions/Labs/LAB_AK_15_configure_customize_github_copilot_vscode.md`, commit `5509555`
(2026-07-20). MIT License, Copyright (c) Microsoft Corporation; the license text is the
repository's `LICENSE` file, https://github.com/MicrosoftLearning/mslearn-github-copilot-dev/blob/main/LICENSE.
The excerpt ends partway through a code block, closed here so the page renders.

---


# Configure GitHub Copilot instructions and create custom agents

GitHub Copilot provides powerful AI-assisted coding right out of the box, but its true potential emerges when you customize it to match your team's specific workflows and project requirements. By providing custom instructions and creating specialized agents, you can transform GitHub Copilot from a general-purpose assistant into a set of tailored AI collaborators that understand your codebase, follow your conventions, and handle multi-step development tasks.

In this exercise, you configure the ContosoInventory C# Web API project to use custom GitHub Copilot instructions and create custom agents that collaborate through handoffs to complete a development task end-to-end.

This exercise should take approximately **50** minutes to complete.

> **IMPORTANT**: To complete this exercise, you must provide your own GitHub account and GitHub Copilot subscription. If you don't have a GitHub account, you can <a href="https://github.com/" target="_blank">sign up</a> for a free individual account and use a GitHub Copilot Free plan to complete the exercise. If you have access to a GitHub Copilot Pro, GitHub Copilot Pro+, GitHub Copilot Business, or GitHub Copilot Enterprise subscription from within your lab environment, you can use your existing GitHub Copilot subscription to complete this exercise.

## Before you start

Your lab environment MUST include the following resources:

- Git 2.48 or later.
- The .NET SDK version 9.0 or later.
- Access to a GitHub account with GitHub Copilot enabled.
- Visual Studio Code (version 1.116 or later) with the C# Dev Kit extension.

## Exercise scenario

You're a software developer working for a consulting firm. The firm developed the ContosoInventory web application (a Blazor WebAssembly application with an ASP.NET Core backend) for Contoso's IT department. The application manages inventory categories for tracking equipment used across the organization. The client has specific coding standards, architectural patterns, and review processes, and they've asked you to add a Product Inventory management feature so individual products can be tracked within each category.

You plan to use GitHub Copilot's customization features to accelerate development while ensuring that all code adheres to the client's standards. Your plan includes the following tasks:

1. Create custom instruction files that embed the client's coding standards into GitHub Copilot's behavior so that all AI-generated code follows the established conventions.
1. Define custom agents for specific development roles—a "Planner" that designs implementation plans, an "Implementer" that writes code, and a "Reviewer" that checks code quality.
1. Chain these agents together using handoffs to create a structured multi-step workflow from planning through implementation to review.

This exercise includes the following tasks:

1. Review features of the ContosoInventory application.
1. Create repository-level custom instructions that enforce coding standards.
1. Create path-specific instruction files for targeted guidance.
1. Create a reusable prompt file for a common task.
1. Define a "Planner" custom agent with read-only tools.
1. Define an "Implementer" custom agent with editing capabilities.
1. Define a "Reviewer" custom agent for code quality checks.
1. Run the chained agents workflow to complete a development task end-to-end.

## Review features of the ContosoInventory application

Before adding GitHub Copilot customization files that enforce coding standards and guide development workflows, you need to download and review the ContosoInventory application.

Use the following steps to complete this task:

1. Open a browser window, navigate to the GitHub home page, and then log in to your GitHub account.

    You can log in to your GitHub account using the following URL: <a href="https://github.com/login" target="_blank">GitHub login</a>.

1. Sign in to your GitHub account, and then open your repositories tab.

    You can open your repositories tab by clicking on your profile icon in the top-right corner, then selecting **Repositories**.

1. On the Repositories tab, select the **New** button.

1. Under the **Create a new repository** section, select **Import a repository**.

1. On the **Import your project to GitHub** page, under **Your source repository details**, enter the following URL for the source repository:

    ```plaintext
    https://github.com/MicrosoftLearning/github-copilot-customization-starter-app
    ```

1. Under the **Your new repository details** section, in the **Owner** dropdown, select your GitHub username.

1. In the **Repository name** field, enter **ContosoInventory**

    GitHub automatically checks the availability of the repository name. If this name is already taken, append a unique suffix (for example, your initials or a random number) to the repository name to make it unique.

1. To create your new ContosoInventory repository, select **Private**, and then select **Begin import**.

    GitHub uses the import process to create the new repository in your account. It can take a minute or two for the import process to finish. Wait for the import process to complete before proceeding.

    > **IMPORTANT**: If you're using the GitHub Copilot Free plan, you should create the repository using the **Public** option. When using GitHub Copilot's Free plan, some GitHub Copilot features are only available for public repositories. If you have a Pro, Pro+, Business, or Enterprise subscription, you can create the repository as **Private**.

    GitHub displays a progress indicator and notifies you when the import is complete.

1. Once the import is complete, open your new repository.

    A link to your repository should be displayed. Your repository should be located at: `https://github.com/YOUR-USERNAME/ContosoInventory`.

1. On your ContosoInventory repository page, select the **Code** button, and then copy the HTTPS URL.

    The URL should be similar to: `https://github.com/YOUR-USERNAME/ContosoInventory.git`

1. Open a terminal window in your development environment, and then navigate to the folder location where you want to create a local clone of your repository.

    For example:

    ```powershell
    cd C:\TrainingProjects
    ```

    Replace `C:\TrainingProjects` with your preferred location. You can use any directory where you have write permissions, and you can create a new folder location if needed.

1. To clone your ContosoInventory repository, enter the following command:

    Be sure to replace `YOUR-USERNAME` with your actual GitHub username before running the command.

    ```powershell
    git clone https://github.com/YOUR-USERNAME/ContosoInventory.git
    ```

    You might be prompted to authenticate using your GitHub credentials during the clone operation. You can authenticate using your browser.

1. To open your ContosoInventory repository in Visual Studio Code, enter the following commands:

    ```powershell
    cd ContosoInventory
    code .
    ```

1. In Visual Studio Code's Explorer view, expand the project folders.

    The ContosoInventory application uses a three-project architecture:

    - **ContosoInventory.Server**: ASP.NET Core Web API with Entity Framework Core, Identity authentication, and SQLite.
    - **ContosoInventory.Client**: Blazor WebAssembly SPA that runs in the browser and calls the server API.
    - **ContosoInventory.Shared**: Shared class library containing models, DTOs, and enums.

1. Take a moment to review the project structure.

    Expand the project folders. You should see a folder structure similar to the following example:

    ```plaintext
    ContosoInventory/
    ├── ContosoInventory.Server/
    ```

[The task continues with more steps in the same form.]
