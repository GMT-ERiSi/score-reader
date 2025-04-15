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

## 4. Functional Requirements

The following table outlines the detailed functional requirements for the frontend visualization features.

| Requirement ID | Description                                      | User Story                                                                                                   | Expected Behavior/Outcome                                                                                                                                                              |
|-----------------|--------------------------------------------------|--------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Core Features** |                                                  |                                                                                                              |                                                                                                                                                                                        |
| FRF001          | Display Interactive Leaderboards                 | As a user, I want to view interactive leaderboards based on processed game data so I can see rankings for various stats. | The web interface should display tables showing player rankings for specified metrics, loaded from the project's JSON data.                                                              |
| FRF002          | Visualize Player ELO Progression                 | As a user, I want to see a visual representation of player ELO changes over time so I can track skill progression. | The web interface should display a chart (e.g., line chart) showing the ELO history for selected players, loaded from the ELO history JSON data.                                         |
| FRF003          | Data Sorting and Filtering                       | As a user viewing leaderboards or charts, I want to sort and filter the data so I can focus on specific information or players. | Leaderboard tables should allow sorting by any column. Filtering options (e.g., by player name, date range) should be available for both leaderboards and charts where applicable.        |
| FRF004          | Responsive Design                                | As a user, I want to view the visualizations correctly on different devices (desktop, mobile) so I can access the information anywhere. | The web interface layout and visualizations should adapt to various screen sizes, ensuring readability and usability on both desktop browsers and mobile devices.                             |
| **Specific Visualizations (Initial Scope)** |                                                  |                                                                                                              |                                                                                                                                                                                        |
| FRF005          | Interactive ELO Ladder Chart                     | As a user, I want an interactive chart specifically showing ELO changes for players over time or matches so I can analyze rating trends. | The system will render a line chart displaying ELO values on the Y-axis and time/match sequence on the X-axis, potentially allowing hovering for details or zooming.                     |
| FRF006          | AI Kills Leaderboard                             | As a user, I want to see a leaderboard ranking players by their average AI Kills per game so I can identify top objective players. | A table will display players ranked by their calculated AI Kills per game statistic, sortable and filterable.                                                                        |
| FRF007          | Damage Dealt Leaderboard                         | As a user, I want to see a leaderboard ranking players by their average Damage Dealt per game so I can identify high-impact players. | A table will display players ranked by their calculated Damage Dealt per game statistic, sortable and filterable.                                                                      |
| FRF008          | Net Kills Leaderboard                            | As a user, I want to see a leaderboard ranking players by their average Net Kills (Kills - Deaths) per game so I can identify efficient fraggers. | A table will display players ranked by their calculated Net Kills per game statistic, sortable and filterable.                                                                         |
| FRF009          | Least Deaths Leaderboard                         | As a user, I want to see a leaderboard ranking players by their average Least Deaths per game so I can identify survivable players. | A table will display players ranked by their calculated Least Deaths per game statistic, sortable and filterable.                                                                      |

## 5. Non-Functional Requirements

- **Technology Stack:** Utilize modern web frameworks (e.g., Vue.js, React, or even vanilla JS depending on complexity) and established visualization libraries (e.g., Chart.js, D3.js, Plotly.js).
- **Performance:** Ensure visualizations load efficiently and interactions are smooth.
- **Maintainability:** Write clean, well-documented code. Structure the frontend code logically within the `web_visualizations/` directory.

## 6. Future Considerations

- Additional stats leaderboards.
- Head-to-head player comparison tools.
- More advanced chart types.
- User accounts or personalization (if scope expands significantly).