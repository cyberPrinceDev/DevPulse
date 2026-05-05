# DevPulse: Engineering Workspace Manager

Video Demo: [Link to your YouTube Video]

## Description

DevPulse is a lightweight, high-velocity project management tool designed for software engineers. It bridges the gap between high-level project tracking and daily task execution. Unlike traditional tools that feel cluttered, DevPulse focuses on a clean, "Linear-inspired" interface that allows developers to manage their project lifecycles from initiation to completion.

## Key Features

- **Dynamic Dashboard**: Provides real-time metrics on active projects, pending tasks, and overall completion statistics.
- **Project Lifecycles**: Users can create project workspaces, track their progress via an automated progress bar, and mark projects as "Completed" or delete them.
- **Kanban Task Boards**: Each project features a dedicated workspace with a "Todo," "In Progress," and "Done" workflow.
- **Relational Data Mapping**: Built using a SQL backend to maintain strict relationships between users, projects, and tasks.

## Technical Implementation

The application is built using a Flask web framework and a SQLite3 database.

- **app.py**: The core controller handling routing, session management, and database queries. It includes custom logic for calculating project progress percentages via SQL subqueries.
- **Database Schema**: Consists of three relational tables: users (authentication), projects (workspace containers), and tasks (individual units of work).
- **Frontend**: Utilizes Jinja2 templating for dynamic content rendering and Bootstrap 5 for a responsive, modern UI. Custom CSS was used to achieve the minimalist "Engineering" aesthetic.
- **Authentication**: Implements secure password hashing and `@login_required` decorators to protect user data.

## Challenges Overcome

During development, I faced challenges with routing conflicts where the browser would cache old redirects. I solved this by implementing strict session clearing and explicit redirect logic in the Flask routes. Additionally, I optimized the database queries to calculate task progress server-side to ensure a fast user experience on the frontend.

## How to Run

1. Install dependencies: `pip install flask cs50`
2. Initialize the database: `sqlite3 devpulse.db < schema.sql` (or however you set it up)
3. Start the server: `flask run`