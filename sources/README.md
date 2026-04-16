# Sources Directory

This directory contains **raw, immutable source material**. Files here are the original inputs that the wiki is built from.

## Rules

- **Never modify** files in this directory. They are reference material only.
- Claude reads sources during **ingest** operations to generate wiki pages.
- New sources are added here first, then ingested into the wiki.

## Structure

- `obsidian-import/` — Paul's Obsidian notes, copied in their original folder structure
- Additional sources (articles, PDFs, meeting notes) can be added as needed

## How to add new sources

1. Drop the file into the appropriate subdirectory (or create one)
2. Ask Claude to ingest it: "Ingest sources/obsidian-import/work/gep/..." 
3. Claude will read it, generate/update wiki pages, update index.md, and log the operation
