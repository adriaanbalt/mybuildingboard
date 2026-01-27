# Next.js/React/Supabase Cursor Rules

Hey there! I'm **Adriaan Balt** ([www.adriaanbalt.com](https://www.adriaanbalt.com)), and this is my collection of Cursor rules that I've built up while working on real production apps with Next.js, React, and Supabase. Think of it as my engineering playbook—the patterns, standards, and gotchas I've learned the hard way so you don't have to.

I've put this together to showcase my approach to building solid, maintainable applications, and to share what I've learned with the community. These aren't theoretical best practices—they're battle-tested rules extracted from actual codebases that have shipped to production.

## What's Inside

This repo covers the stuff that actually matters when building apps:
- **Development Standards**: The code quality patterns I actually follow (not just preach)
- **Architecture Patterns**: How I structure systems that don't fall apart at scale
- **Security**: Auth, authorization, and keeping data safe (because breaches aren't fun)
- **Infrastructure**: Database migrations, environment config, and all that DevOps-y stuff
- **UI/UX**: Component patterns and design systems that make sense
- **Testing**: How I actually test things (not just "write more tests" platitudes)

## Rule Categories

### Always Applied Rules

These rules are always active regardless of file context:

1. **design-system-tokens.mdc** - Design system token standards
   - Enforces use of CSS variables and semantic tokens
   - Prevents hardcoded colors
   - Supports theme switching

2. **balanced-evaluation.mdc** - Balanced evaluation standards
   - Requires evidence-based evaluations
   - Focuses on advantages, disadvantages, and feasibility
   - Avoids pandering or reassurance

3. **conform-to-existing-structures.mdc** - Conform to existing data structures
   - Ensures new code conforms to existing app data structures

4. **folder-restructuring.mdc** - Folder restructuring standards
   - Prevents code loss during refactoring
   - Mandates git-based moves
   - Requires verification steps

5. **guides-markdown.mdc** - Guide markdown creation standards
   - Template structure for guide files
   - Date handling requirements
   - Frontmatter standards

6. **https-configuration.mdc** - HTTPS configuration
   - Local development HTTPS setup
   - Supabase HTTPS proxy configuration
   - WebSocket and OAuth redirect URI requirements

7. **objective-reasoning.mdc** - Hyper-objective logic engine
   - First principles reasoning
   - Maximum intellectual rigor
   - Evidence-based decision making

8. **cleanup-test-files.mdc** - Test file cleanup
   - Delete test files after use

### Context-Specific Rules

These rules activate when working with matching file patterns:

#### API & Backend

10. **api-routes.mdc** - Next.js API route standards
    - Route handler structure
    - Authentication and authorization
    - Error handling and logging
    - Input validation
    - Webhook signature verification

11. **database-queries.mdc** - Supabase database query standards
    - Client selection (user vs admin)
    - Query patterns and optimization
    - Error handling
    - RLS (Row Level Security) policies
    - UUID validation

12. **security.mdc** - Security standards
    - Authentication and authorization
    - Input validation and sanitization
    - Webhook signature verification
    - Environment variable security
    - Data protection

13. **supabase-migrations.mdc** - Supabase migration standards
    - When migrations are needed
    - Migration workflow and validation
    - Detecting database resets
    - Verifying database objects
    - Production deployment

#### Frontend

14. **dry-components.mdc** - DRY component principles
    - When to extract components
    - Code duplication thresholds
    - Component extraction guidelines
    - Location guidelines

15. **hooks.mdc** - Custom React hooks standards
    - Hook naming conventions
    - Hook structure and patterns
    - Data fetching patterns
    - Error handling
    - Dependency management

16. **typescript-types.mdc** - TypeScript type standards
    - Type organization
    - Interface vs type usage
    - Type safety patterns
    - Type guards
    - Utility types

17. **kanban-drag-system.mdc** - Kanban board drag system
    - Board drag-to-scroll implementation
    - Card dragging coexistence
    - Touch support
    - Performance optimization

#### Infrastructure & Configuration

18. **environment-variables.mdc** - Environment variable standards
    - Naming conventions (NEXT_PUBLIC_ prefix)
    - Variable organization
    - Validation patterns
    - Documentation requirements

19. **oauth-strategy.mdc** - OAuth flow strategy
    - Complete OAuth flow implementation
    - HTTPS requirements
    - Configuration points
    - Common issues and solutions

#### Development Practices

20. **error-handling.mdc** - Error handling standards
    - API route errors
    - Client-side errors
    - Database errors
    - Network errors
    - User-facing error messages

21. **logging-monitoring.mdc** - Logging and monitoring standards
    - Structured logging
    - Log levels
    - Performance monitoring
    - Error tracking

22. **testing.mdc** - Testing standards
    - Test structure and organization
    - Test patterns (API, hooks, components)
    - Mocking strategies
    - Test data management

#### Documentation

23. **rules-system-overview.mdc** - Rules system overview
    - How Cursor reads rules
    - Rule file structure
    - Rule categories
    - Best practices

## Usage

### In Cursor

These rules can be referenced in Cursor by:

1. **Cloning this repository** to your workspace
2. **Linking or copying** rules to your project's `.cursor/rules/` directory
3. **Referencing** specific rules in your project documentation

### Prompt Library

The `prompt-library/` directory contains reusable prompts organized by category. These prompts are **not automatically applied** - they only load when explicitly referenced.

**Usage:**
```
@prompt-library/category prompt-name Your specific request here
```

**Available Categories:**
- `communication` - Communication and confirmation prompts
- `development` - Development workflow prompts
- `strategic-analysis` - Strategic analysis and consulting prompts
- `document-parsing` - Document parsing and text processing
- `refactoring` - Refactoring and code organization
- `problem-analysis` - Problem analysis and debugging

See `prompt-library/README.mdc` for complete documentation and all available prompts.

### Rule File Structure

Each rule file follows this format:

```markdown
---
description: Brief description of what this rule covers
globs: "**/*.ts,**/*.tsx"  # File patterns this rule applies to
alwaysApply: true/false     # Whether to always apply or only when files match
---

# Rule Content
```

## Rule Organization

### Always Applied vs Context-Specific

- **Always Applied**: Rules that should be active regardless of what files you're working with
- **Context-Specific**: Rules that activate when you're working with files matching their glob patterns

### Framework-Specific vs App-Specific

These rules are **framework-specific** (Next.js/React/Supabase) and can be applied to any application using this stack. They:
- Don't reference app-specific business logic
- Don't mention specific routes or features
- Use generic examples and patterns
- Can be adapted to any Next.js/React/Supabase project

## Contributing

When adding new rules:

1. Ensure they are **framework-specific** (Next.js/React/Supabase) but not app-specific
2. Follow the rule file structure
3. Include examples and DO's/DON'Ts
4. Update this README with the new rule
5. Test the rule in a real project context

## Rule Maintenance

- Keep rules up-to-date with framework changes
- Remove outdated patterns
- Consolidate similar rules when appropriate
- Document breaking changes

## Related Resources

- [Cursor Rules Documentation](https://cursor.sh/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [React Documentation](https://react.dev)

## License

These rules are provided as-is for use in any project. Adapt and modify as needed for your specific requirements.

---

**Made by [Adriaan Balt](https://www.adriaanbalt.com)** - Check out my website to see more of my work and projects.

