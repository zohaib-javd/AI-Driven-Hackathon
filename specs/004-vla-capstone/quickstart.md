# Quickstart Guide: Physical AI & Humanoid Robotics Book

## Overview
This guide provides a quick start for developers and educators to set up, contribute to, and deploy the Physical AI & Humanoid Robotics book project.

## Prerequisites

### System Requirements
- Operating System: Ubuntu 22.04 LTS, Windows 10/11, or macOS 12+
- RAM: 16GB minimum, 32GB recommended
- Storage: 50GB available space
- Python 3.10+ with pip
- Node.js 18+ with npm
- Docker (for containerized development)

### ROS 2 Environment
- ROS 2 Humble Hawksbill installed
- Colcon build tools
- RViz2 for visualization
- Gazebo Garden for simulation

### Optional (for advanced modules)
- NVIDIA Isaac Sim (Module 3)
- Unity 2022.3+ HDRP (Module 2)
- CUDA-compatible GPU with 8GB+ VRAM

## Setting Up the Development Environment

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/physical-ai-humanoid-robotics.git
cd physical-ai-humanoid-robotics
```

### 2. Install Python Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Up Docusaurus Book
```bash
cd book
npm install
```

### 4. Set Up RAG Chatbot
```bash
cd rag-chatbot
pip install -r requirements.txt
```

## Running the Book Locally

### 1. Start Docusaurus Development Server
```bash
cd book
npm start
```
The book will be available at `http://localhost:3000`

### 2. Run RAG Chatbot (Optional)
```bash
cd rag-chatbot
python -m uvicorn app.main:app --reload --port 8000
```
The chatbot API will be available at `http://localhost:8000`

## Contributing Content

### 1. Adding a New Chapter
1. Navigate to the appropriate module directory in `book/docs/`
2. Create a new `.mdx` file with the chapter content
3. Add the chapter to the sidebar configuration in `book/sidebars.js`

### 2. Chapter Structure Template
```mdx
---
title: Chapter Title
description: Brief description of the chapter content
sidebar_position: 1
---

# Chapter Title

## Learning Objectives
- Objective 1
- Objective 2
- Objective 3

## Prerequisites
- Prerequisite knowledge or chapters

## Content
Your chapter content here...

## Code Examples
```python
# Your code example here
```

## Exercises
1. Exercise 1 description
2. Exercise 2 description

## Summary
Chapter summary and key takeaways.
```

### 3. Adding Code Examples
- Place executable code examples in `simulation-examples/` organized by module
- Include setup instructions and expected outputs
- Validate examples in target environments before committing

## Running Simulations

### 1. ROS 2 Examples (Module 1)
```bash
# Source ROS 2 environment
source /opt/ros/humble/setup.bash
source install/setup.bash

# Run example
ros2 run package_name executable_name
```

### 2. Gazebo Simulations (Module 2)
```bash
# Start Gazebo with a world file
ros2 launch gazebo_ros empty_world.launch.py world:=path/to/world.world
```

### 3. Isaac Sim Integration (Module 3)
```bash
# Launch Isaac Sim with ROS 2 bridge
python -m omni.isaac.sim.python_app --exec="path/to/script.py"
```

## Building and Deployment

### 1. Build the Book for Production
```bash
cd book
npm run build
```

### 2. Deploy to GitHub Pages
The repository is configured with GitHub Actions to automatically deploy:
- Push changes to the `main` branch
- GitHub Actions will build and deploy to GitHub Pages
- Site will be available at `https://your-org.github.io/physical-ai-humanoid-robotics`

### 3. Deploy RAG Chatbot
```bash
# Using Docker
docker-compose -f rag-chatbot/docker-compose.yml up -d

# Or deploy to cloud platform of choice
```

## Testing and Validation

### 1. Validate Code Examples
```bash
# Run all validation tests
cd simulation-examples
python -m pytest tests/ -v
```

### 2. Check Docusaurus Build
```bash
cd book
npm run build
# Check for any build errors or warnings
```

### 3. Validate URDF Models
```bash
# Check URDF syntax
check_urdf path/to/model.urdf

# Visualize in RViz
ros2 run rviz2 rviz2
```

## RAG Chatbot Setup

### 1. Initialize Vector Database
```bash
cd rag-chatbot
python scripts/init_vector_db.py
```

### 2. Load Book Content
```bash
python scripts/load_book_content.py
```

### 3. Test Chatbot API
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is ROS 2? How does it work in robotics?"}'
```

## Common Commands

### Development
- `npm start` - Start Docusaurus development server
- `npm run build` - Build production version of the book
- `npm run serve` - Serve built book locally

### Testing
- `pytest` - Run Python tests
- `npm test` - Run JavaScript tests
- `npm run test:watch` - Run tests in watch mode

### Simulation
- `source /opt/ros/humble/setup.bash` - Source ROS 2 environment
- `colcon build` - Build ROS 2 packages
- `ros2 launch package_name launch_file.launch.py` - Launch simulation

## Troubleshooting

### Common Issues

1. **ROS 2 Environment Not Found**
   - Ensure ROS 2 Humble is installed and sourced
   - Check that `setup.bash` path is correct

2. **Docusaurus Build Errors**
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall: `rm -rf node_modules && npm install`

3. **Simulation Performance Issues**
   - Ensure adequate system resources (RAM, GPU)
   - Check that graphics drivers are up to date

### Getting Help
- Check the documentation in `book/docs/` for detailed setup instructions
- Review the troubleshooting guides in each module
- Open an issue in the GitHub repository for technical problems

## Next Steps

1. Review the [Module 1: The Robotic Nervous System](../module-1-ros/) to begin with ROS 2 fundamentals
2. Set up your development environment with the prerequisites
3. Run the first simulation example to verify your setup
4. Contribute to the project by adding content or fixing issues