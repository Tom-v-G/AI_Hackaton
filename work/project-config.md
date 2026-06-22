# Project Config

This file is the canonical, human-readable source of truth for repo structure, guideline loading, review triggers, and repo-level command rules.

If another repo document conflicts with this file, follow this file.

## Purpose

- Use this file as rule, not background reading.
- Humans read it to understand expected agent behavior.
- Agents read it to decide which guidelines, reviews, and commands apply.

## Repo Structure

- TODO: Document the top-level repo layout and important domain folders.

## Output Rules

- TODO: Define concise response and formatting rules for agents.

## Domain Rules

- TODO: List each domain, its guideline, matching file patterns, and relevant keywords.

## Technology Rules

- TODO: List key technologies and the guideline file for each.

## Review Rules

- TODO: Define review types, trigger keywords, and linked guideline files.

## Loading Rules

### Always Load

- TODO: List guidelines every agent should always load.

### Analysis

- TODO: Define how agents choose guidelines during analysis.

### Implementation

- TODO: Define how agents choose guidelines from affected files.

### Validation

- TODO: Define how agents choose guidelines and review checks during validation.

## Command Rules

- TODO: List repo-level commands agents should use for validation, codegen, or other required checks.

## Agent Usage Rule

- Read this file first when you need repo structure, guideline loading rules, review triggers, or repo-level command rules.
- Load only the guideline files that match the current task.
- Do not invent rules outside this file, `AGENTS.md`, and the loaded guideline files.
