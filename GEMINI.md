# Gemini Assistant Configuration for Project Himalaya

This file contains instructions and preferences for the Gemini AI assistant to follow during all sessions for this project.

## 1. Automatic Inclusion of Design Standards

At the beginning of each session, the assistant should automatically locate and read the latest version of the Design Standard document.

- **Pattern to find the file:** `Docs/Standards/Design Standard v*.md`
- **Action:** Use the `glob` tool to find all matching files and read the most recently modified one. This ensures the latest standard is always in context.

The assistant must acknowledge and adhere to the requirements of the loaded Design Standard, particularly the AI Accountability Framework outlined in v2.1 or later.

## 2. User-Granted Autonomy

The user has granted the assistant permission to perform functions and actions autonomously without seeking explicit confirmation for each step.

- **Preference:** "automatically perform any function without asking"
- **Caveat:** This permission excludes potentially destructive or irreversible system-level commands (e.g., "rm -kill the system").
- **Behavior:** The assistant should proceed directly with implementing solutions, such as fixing code, creating files, and running project-specific commands, while still providing brief explanations for significant actions as per standard operating procedure. The goal is to increase efficiency and reduce conversational overhead.

The assistant should use its judgment to identify actions that are exceptionally risky and might still warrant a confirmation, despite this general permission.
