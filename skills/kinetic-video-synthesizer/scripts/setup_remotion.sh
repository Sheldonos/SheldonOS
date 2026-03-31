#!/bin/bash
# Setup script for Remotion projects

set -e

PROJECT_NAME=${1:-"my-video"}
TEMPLATE=${2:-"hello-world"}

echo "🎥 Setting up Remotion project: $PROJECT_NAME"

# Create the project
npx create-video@latest "$PROJECT_NAME" --template="$TEMPLATE"

cd "$PROJECT_NAME"

echo "✅ Remotion project '$PROJECT_NAME' created successfully!"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_NAME"
echo "  npm run dev      # Start Remotion Studio"
echo "  npm run build    # Render the video"
