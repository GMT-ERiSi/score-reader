# Product Requirements Document: Frontend Visualizations

## 1. Introduction

This document outlines the requirements for adding web-based visualization features to the Squadrons Screenshot Reader project. The goal is to leverage the existing structured JSON data to provide interactive leaderboards, charts, and other visual representations of the collected statistics.

## 2. Rationale

The project currently processes screenshots and generates structured data (JSON) containing player statistics and ELO ratings. This data format is ideal for consumption by web technologies. Adding visualization features will:
- Provide users with intuitive ways to explore and understand the data.
- Enhance the project's value by presenting insights visually.
- Offer interactive leaderboards and player progression tracking.

## 3. Proposed Solution

### 3.1. Project Structure

A new directory, `web_visualizations/`, will be created within the main project repository. This directory will contain all necessary files for the frontend visualization components.

**Risk Assessment:** Placing all frontend code within a single `web_visualizations/` directory is a standard practice for smaller to medium-sized web components integrated into a larger project.
- **Pros:** Keeps visualization-related code organized and co-located. Simplifies build and deployment processes initially. Easy to manage dependencies for the web part.
- **Cons:** If the visualization component grows significantly complex, the single directory might become cluttered. However, internal structuring (subdirectories for components, assets, etc.) can mitigate this.
- **Conclusion:** For the scope defined (leaderboards, ELO chart), a single top-level directory is appropriate and poses minimal risk to the overall project structure. It promotes modularity by separating the web frontend from the Python backend/data processing logic.

### 3.2. Contents

The `web_visualizations/` directory will include:
- **HTML:** Structure for the web pages.
- **CSS:** Styling for the visualizations and layout.
- **JavaScript:** Logic for fetching data, rendering visualizations, and handling user interactions.
- **Build Script (Optional but Recommended):** A script (e.g., using Node.js tools like Webpack or Vite) to bundle assets, manage dependencies, and potentially generate static pages from the latest JSON data files.

### 3.3. Deployment

The static web application generated will be suitable for deployment on platforms like GitHub Pages.
- **Benefits:** Free hosting, direct integration with the GitHub repository, support for static sites with full JavaScript capabilities.
- **Automation:** Deployment can be automated using GitHub Actions to update the live visualization whenever the underlying data changes (e.g., on pushes to the main branch).

## 4. Development Phases

Development will proceed in phases to deliver value incrementally.

*   **Phase 1 (MVP - Minimum Viable Product):** Focus on core functionality and essential visualizations with basic interactivity. The goal is to establish the foundation and provide initial useful views. Vanilla JavaScript is preferred for simplicity unless a framework significantly simplifies chart integration.
*   **Phase 2 (Enhancements):** Build upon the MVP by adding more interactivity, completing the initial set of leaderboards, and refining the user experience and design.
*   **Phase 3 (Future):** Address items listed in "Future Considerations" based on user feedback and project priorities.

## 5. Functional Requirements

The following table outlines the detailed functional requirements, indicating the planned phase for each.

| Requirement ID | Phase | Description                                      | User Story                                                                                                   | Expected Behavior/Outcome                                                                                                                                                              |
|-----------------|-------|--------------------------------------------------|--------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Phase 1: MVP** |       |                                                  |                                                                                                              |                                                                                                                                                                                        |
| FRF101          | 1     | Basic HTML Structure & Data Load             | As a developer, I need a basic HTML page structure and JavaScript to load the necessary JSON data files (e.g., team/pickup ELO history, stats summaries). | Create `index.html`, `style.css`, `script.js` in `web_visualizations/`. JS successfully fetches and parses relevant JSON data (e.g., `stats_reports/elo_history_team.json`, `elo_reports_pickup/pickup_player_elo_history.json`) upon page load. |
| FRF102          | 1     | Basic Team ELO Ladder Chart                  | As a user, I want a simple chart showing team ELO changes over time so I can see basic team ranking trends.    | Render a non-interactive line chart using a library (e.g., Chart.js) displaying team ELO history from `stats_reports/elo_history_team.json`. Basic styling applied.                       |
| FRF103          | 1     | Basic Pickup Player ELO Ladder Chart         | As a user, I want a simple chart showing player ELO changes over time from pickup matches so I can see basic individual ranking trends. | Render a non-interactive line chart using a library (e.g., Chart.js) displaying player ELO history from `elo_reports_pickup/pickup_player_elo_history.json`. Basic styling applied.      |
| FRF104          | 1     | Display Simple Leaderboard(s)                | As a user, I want to see at least one leaderboard (e.g., Team ELO or Pickup Player ELO) displayed as a simple table so I can view basic rankings. | Render one or two leaderboards (e.g., from `stats_reports/elo_ladder_team.json` or `elo_reports_pickup/pickup_player_elo_ladder.json`) as static HTML tables. No sorting/filtering initially. |
| FRF105          | 1     | Basic Responsive Design                      | As a user, I want the basic layout to be usable on mobile devices.                                           | Implement simple CSS media queries to ensure the page content reflows reasonably on smaller screens. Perfect layout not required in Phase 1.                                          |
| **Phase 2: Enhancements** |       |                                                  |                                                                                                              |                                                                                                                                                                                        |
| FRF201          | 2     | Interactive Leaderboards (Sort/Filter)       | As a user viewing leaderboards, I want to sort by columns and filter the data so I can analyze rankings more effectively. | Implement JavaScript to add client-side sorting to all leaderboard tables. Add basic filtering controls (e.g., text input for player name).                                            |
| FRF202          | 2     | Implement All Initial Leaderboards           | As a user, I want to see all the initially planned leaderboards (AI Kills, Damage, Net Kills, Least Deaths) available. | Add the remaining leaderboards specified in the initial scope (FRF006-FRF009 equivalent) to the web interface, including sorting/filtering from FRF201.                               |
| FRF203          | 2     | Enhanced Chart Interactivity                 | As a user viewing the ELO chart, I want tooltips on hover or other interactions to see specific data points easily. | Configure the charting library to show data values on hover (tooltips). Consider basic zooming/panning if supported easily by the library.                                             |
| FRF204          | 2     | Improved Responsive Design & Styling         | As a user, I want a polished look and feel that works well across devices.                                   | Refine CSS, improve layout adjustments for different screen sizes, ensure consistent styling across all components.
| FRF205          | 2     | Leaderboard-Chart Interaction (Filtering)    | As a user, I want to click on a team/player in the leaderboard table to filter the corresponding ELO chart to show only their history. | Add event listeners to table rows. Clicking a row updates the relevant Chart.js instance to display only the dataset corresponding to the selected team/player. Add a 'Show All' button to reset the chart filter. |                                                                    |

## 6. Non-Functional Requirements

*(Applies across phases)*
- **Technology Stack:** Phase 1: Vanilla JS preferred, Chart.js (or similar). Phase 2+: Consider Vue/React if complexity increases significantly. Use established visualization libraries.
- **Performance:** Ensure visualizations load efficiently and interactions (especially in Phase 2) are smooth.
- **Maintainability:** Write clean, well-documented code. Structure the frontend code logically within the `web_visualizations/` directory.

## 7. Future Considerations

*(Post-Phase 2)*
- Additional stats leaderboards.
- Head-to-head player comparison tools.
- More advanced chart types.
- User accounts or personalization (if scope expands significantly).
- Build script implementation for optimization/bundling.
- Automated deployment via GitHub Actions.