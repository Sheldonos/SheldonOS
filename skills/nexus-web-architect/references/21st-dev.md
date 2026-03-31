# 21st.dev Reference

This document provides a guide to using 21st.dev's Magic tool for generating production-ready React components.

## Setting up the Magic Component Platform (MCP) Server

To use Magic, you first need to set up the MCP server in your IDE.

1.  **Generate an API Key:** Visit the [21st.dev Magic Console](https://21st.dev/magic) to generate a new API key.

2.  **Install the CLI:** Use the following command to install the 21st.dev CLI and configure your IDE:

    ```bash
    npx @21st-dev/cli@latest install <client> --api-key <key>
    ```

    Replace `<client>` with your IDE (e.g., `cursor`, `windsurf`, `cline`, `claude`) and `<key>` with your API key.

For manual configuration, refer to the [magic-mcp GitHub repository](https://github.com/21st-dev/magic-mcp).

## Generating Components

Once the MCP server is running, you can generate components from your IDE's chat interface.

1.  **Use the `/ui` command:** Start your prompt with `/ui` to trigger the component generation.

2.  **Describe Your Component:** Provide a detailed description of the component you need. Include details about:

    *   **Functionality:** What should the component do?
    *   **Style:** How should it look?
    *   **Responsiveness:** How should it behave on different screen sizes?

**Example Prompt:**

> `/ui create a testimonial card with a user avatar, name, and a quote. The card should have a subtle shadow and a border-radius of 8px.`

## Browsing and Selecting Components

Magic will generate several variations of the component based on your prompt. You can browse these variations and select the one that best fits your design. The selected component will be automatically added to your project.

## Using 3D and Animated Components

For more advanced use cases, you can explore the [21st.dev component library](https://21st.dev/community/components/s/3d). This library contains a wide range of 3D and animated components that you can use in your projects.
