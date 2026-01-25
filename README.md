# My Building Board

**Email-to-QA System with RAG (Retrieval Augmented Generation)**

Transform email inboxes into a searchable knowledge base with semantic search and natural language Q&A.

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- Supabase account (for database and auth)
- GCP account (for Cloud Functions and Cloud Run)
- OpenAI API key (for embeddings and LLM)

### Installation

```bash
# Install dependencies
yarn install

# Copy environment variables
cp .env.example .env.local

# Edit .env.local with your credentials
# - Supabase URL and keys
# - OpenAI API key
# - GCP project ID

# Start development server
yarn dev
```

Visit `http://localhost:3000` to see the marketing website.

---

## 📁 Project Structure

```
MyBuildingBoard/
├── app/                    # Next.js application
│   ├── (marketing)/        # Public marketing site
│   ├── (app)/              # Logged-in dashboard (to be implemented)
│   └── api/                # API routes
├── components/             # React component library
├── lib/                    # Shared code (types, hooks, utils)
├── services/               # Backend services (to be implemented)
├── infrastructure/         # Local development infrastructure
└── docs/                   # Documentation
```

See [docs/technical-roadmap/folder-structure-guide.md](./app/docs/technical-roadmap/folder-structure-guide.md) for detailed structure.

---

## ✅ Current Status

### Phase 0: Infrastructure Setup (In Progress)

- ✅ Root folder structure created
- ✅ package.json with dependencies
- ✅ TypeScript configuration
- ✅ Next.js configuration
- ✅ Tailwind CSS with design tokens
- ✅ ESLint and Prettier setup
- ✅ Environment configuration template

### Phase 0.5: Marketing Website (Complete)

- ✅ Marketing layout with header and footer
- ✅ Homepage with hero, features, and how it works
- ✅ Features page
- ✅ Pricing page
- ✅ Sign up page (UI only, auth pending)
- ✅ Login page (UI only, auth pending)
- ✅ Privacy and Terms pages (placeholders)

### Next Steps

1. **Phase 0.6:** Set up component library structure (ui/, layout/, forms/)
2. **Phase 0.7:** Set up lib/ structure (types/, database/, hooks/, utils/)
3. **Phase 1:** Foundation (Database Schema, Auth, Multi-Tenant Routing)

See [docs/technical-roadmap/00-implementation-roadmap.md](./app/docs/technical-roadmap/00-implementation-roadmap.md) for full roadmap.

---

## 🛠️ Development

### Available Scripts

```bash
# Development
yarn dev              # Start Next.js dev server
yarn dev:https        # Start with HTTPS (for OAuth)
yarn dev:all          # Start all services (when implemented)

# Building
yarn build            # Build for production
yarn start            # Start production server

# Code Quality
yarn lint             # Run ESLint
yarn type-check       # TypeScript type checking
yarn format           # Format code with Prettier
yarn test             # Run tests (when implemented)

# Supabase
yarn supabase:local   # Start local Supabase
yarn supabase:stop    # Stop local Supabase
```

---

## 📚 Documentation

- **[System Architecture](./app/docs/system-architecture.md)** - Complete system design
- **[Technical Roadmap](./app/docs/technical-roadmap/00-implementation-roadmap.md)** - Implementation plan
- **[Folder Structure Guide](./app/docs/technical-roadmap/folder-structure-guide.md)** - Project organization
- **[Component Library Spec](./app/docs/technical-roadmap/specs/component-library-specification.md)** - Component standards

---

## 🏗️ Architecture

**Tech Stack:**
- **Frontend:** Next.js 14 (App Router), React 18, TypeScript
- **Styling:** Tailwind CSS with design tokens
- **Database:** Supabase (PostgreSQL + pgvector)
- **Auth:** Supabase Auth
- **State Management:** React Query (TanStack Query), React Context
- **Backend:** FastAPI (query service), GCP Cloud Functions (email processing)
- **AI:** OpenAI (embeddings, LLM)

**Architecture Pattern:**
- Multi-tenant SaaS (like Markense)
- Provider-agnostic design (email providers, embedding providers)
- Repository pattern for data access
- Service interfaces for external dependencies

---

## 🔐 Environment Variables

See `.env.example` for required environment variables:

- **Supabase:** URL, anon key, service role key
- **OpenAI:** API key
- **GCP:** Project ID, service account
- **Email Provider:** Gmail API credentials (or other providers)

---

## 📝 License

[To be determined]

---

## 🤝 Contributing

[To be added]

---

**Last Updated:** January 25, 2026
