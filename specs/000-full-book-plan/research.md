# Technical Research: Physical AI & Humanoid Robotics Book

**Date**: 2025-12-16
**Purpose**: Technical findings and references for full book implementation

## Technology Stack Verification

### ROS 2 Humble Hawksbill
- **EOL**: May 2027 (5-year support)
- **Ubuntu**: 22.04 LTS (Jammy Jellyfish)
- **Key Packages**: rclpy, nav2, ros2_control, urdf, tf2
- **Documentation**: https://docs.ros.org/en/humble/

### Gazebo Garden
- **Release**: September 2022
- **EOL**: September 2024 (but stable for educational use)
- **Note**: Consider Gazebo Harmonic (2023) for longer support
- **ROS 2 Bridge**: ros_gz_bridge package
- **Documentation**: https://gazebosim.org/docs/garden/

### NVIDIA Isaac Sim
- **Current Version**: 2023.1.1+
- **Requirements**: RTX 2070+ GPU, 32GB RAM recommended
- **ROS 2 Bridge**: Native Humble support
- **USD Format**: Universal Scene Description for robot models
- **Documentation**: https://docs.omniverse.nvidia.com/isaacsim/

### Isaac ROS
- **Version**: 2.0+ (DP3)
- **Key Packages**:
  - isaac_ros_visual_slam (VSLAM)
  - isaac_ros_apriltag
  - isaac_ros_stereo_image_proc
  - isaac_ros_dnn_inference
- **Hardware Acceleration**: CUDA, TensorRT
- **Documentation**: https://nvidia-isaac-ros.github.io/

### Nav2
- **Version**: 1.1.x for Humble
- **Components**:
  - Planner Server (NavFn, SMAC)
  - Controller Server (DWB, TEB)
  - Recovery Server (spin, backup, wait)
  - Behavior Trees (BT.CPP)
- **Documentation**: https://navigation.ros.org/

### Docusaurus
- **Version**: 3.9.2 (latest stable)
- **React**: 19
- **MDX**: 3.x
- **Features**: Versioning, i18n, search, code highlighting
- **Documentation**: https://docusaurus.io/

## Module-Specific Research

### Module 1: ROS 2 Nervous System

**Key Concepts**:
1. DDS Middleware (FastDDS default)
2. QoS Profiles (reliability, durability, history)
3. Node Composition (multi-node in single process)
4. Lifecycle Nodes (managed state transitions)
5. Parameter Server (dynamic reconfiguration)

**Code Example Patterns**:
```python
# Minimal Node Pattern
import rclpy
from rclpy.node import Node

class MinimalNode(Node):
    def __init__(self):
        super().__init__('minimal_node')
        self.timer = self.create_timer(1.0, self.timer_callback)

    def timer_callback(self):
        self.get_logger().info('Timer fired')

def main():
    rclpy.init()
    node = MinimalNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

**URDF Structure**:
```xml
<?xml version="1.0"?>
<robot name="humanoid">
  <link name="base_link">
    <visual>...</visual>
    <collision>...</collision>
    <inertial>...</inertial>
  </link>
  <joint name="torso_joint" type="revolute">
    <parent link="base_link"/>
    <child link="torso_link"/>
    <axis xyz="0 0 1"/>
    <limit lower="-1.57" upper="1.57" effort="100" velocity="1.0"/>
  </joint>
</robot>
```

### Module 2: Digital Twin

**Gazebo-ROS Bridge Topics**:
- `/camera/image_raw` (sensor_msgs/Image)
- `/lidar/scan` (sensor_msgs/LaserScan)
- `/imu/data` (sensor_msgs/Imu)
- `/depth/image_raw` (sensor_msgs/Image)
- `/joint_states` (sensor_msgs/JointState)

**SDF World Structure**:
```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <world name="indoor_world">
    <physics type="ode">
      <real_time_factor>1.0</real_time_factor>
    </physics>
    <light type="directional" name="sun">...</light>
    <include><uri>model://ground_plane</uri></include>
    <model name="humanoid">...</model>
  </world>
</sdf>
```

**Unity-ROS Bridge**:
- Package: ROS-TCP-Connector
- Protocol: TCP/IP messaging
- Message Types: Custom + standard ROS messages
- Latency: <10ms typical

### Module 3: NVIDIA Isaac

**Isaac Sim Workflow**:
1. Import URDF → Convert to USD
2. Add Articulation Controller
3. Configure ROS 2 Bridge
4. Add sensors (camera, LiDAR, IMU)
5. Set up action graphs for control

**Synthetic Data Pipeline**:
```python
# Replicator Pattern
import omni.replicator.core as rep

with rep.trigger.on_frame():
    camera = rep.create.camera(position=(0, 0, 2))
    rep.randomizer.rotation(camera, (0, 360, 0))

    writer = rep.WriterRegistry.get("BasicWriter")
    writer.initialize(
        output_dir="./data",
        rgb=True,
        depth=True,
        semantic_segmentation=True
    )
```

**Isaac ROS VSLAM Config**:
```yaml
visual_slam_node:
  ros__parameters:
    enable_localization_n_mapping: true
    enable_imu_fusion: true
    gyro_noise_density: 0.001
    accel_noise_density: 0.001
    publish_odom_to_base_tf: true
```

### Module 4: Vision-Language-Action

**VLA Pipeline Architecture**:
```
Voice Input (Whisper)
    ↓
Text Command ("bring me the red cup")
    ↓
Intent Parser (slots: action=bring, object=cup, attribute=red)
    ↓
LLM Planner (generates action sequence)
    ↓
Safety Validator (checks constraints)
    ↓
Action Executor
    ├── Nav2 (navigation)
    ├── Perception (object detection)
    └── Manipulation (grasp execution)
```

**Whisper Integration**:
```python
import whisper
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class WhisperNode(Node):
    def __init__(self):
        super().__init__('whisper_node')
        self.model = whisper.load_model("base")
        self.publisher = self.create_publisher(String, '/voice_command', 10)

    def transcribe(self, audio_path):
        result = self.model.transcribe(audio_path)
        msg = String()
        msg.data = result["text"]
        self.publisher.publish(msg)
```

**LLM Planning Prompt Template**:
```
You are a robot task planner. Given a natural language command,
output a JSON action sequence.

Available actions:
- navigate_to(location)
- detect_object(object_type)
- pick_up(object_id)
- place_at(location)
- wait(seconds)

Command: {user_command}
Scene context: {perception_data}

Output JSON only:
```

**Safety Guardrails**:
1. Action whitelist validation
2. Workspace boundary checks
3. Collision prediction
4. Force/torque limits
5. Human proximity detection
6. Emergency stop integration

## RAG Chatbot Architecture

**Embedding Model**: text-embedding-3-small (1536 dimensions)
**Chunk Size**: 500 tokens with 50 token overlap
**Vector DB**: Qdrant (cosine similarity)
**Retrieval**: Top-k=5, reranking optional

**Ingestion Pipeline**:
```python
# MDX Parsing
def parse_mdx(file_path):
    # Extract frontmatter
    # Extract code blocks with language
    # Extract headers for chunking
    # Return structured chunks with metadata
    pass

# Embedding
def embed_chunks(chunks):
    embeddings = openai.embeddings.create(
        model="text-embedding-3-small",
        input=[c.text for c in chunks]
    )
    return embeddings

# Storage
def store_in_qdrant(chunks, embeddings):
    qdrant.upsert(
        collection_name="book_content",
        points=[
            PointStruct(
                id=i,
                vector=emb,
                payload={
                    "text": chunk.text,
                    "module": chunk.module,
                    "chapter": chunk.chapter,
                    "type": chunk.type  # prose, code, diagram
                }
            )
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
    )
```

**Chat Agent Configuration**:
```python
# OpenAI Agent with function calling
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_book",
            "description": "Search the book content for relevant information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "module_filter": {"type": "integer", "enum": [1, 2, 3, 4]}
                },
                "required": ["query"]
            }
        }
    }
]
```

## Deployment Architecture

**GitHub Pages (Static)**:
- Docusaurus build → `build/` directory
- GitHub Actions workflow
- Custom domain optional

**RAG API (Serverless/Container)**:
- FastAPI application
- Docker container
- Deploy to: Vercel Functions, Railway, or Render
- Environment variables for API keys

**CI/CD Pipeline**:
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  build-book:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run build
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./build
```

## Testing Strategy

**Content Validation**:
- MDX lint (eslint-mdx)
- Link checker (broken links)
- Code block syntax validation
- Image reference validation

**Code Example Testing**:
- Docker container with ROS 2 Humble
- Automated `colcon build` for ROS packages
- Python syntax validation
- Expected output verification

**RAG Grounding Tests**:
```python
# Test cases for 90%+ grounding accuracy
test_questions = [
    {
        "question": "How do I create a ROS 2 node?",
        "expected_chapter": "module-1-ros2/03-ros2-nodes",
        "keywords": ["Node", "rclpy", "create_timer"]
    },
    # ... 100 test cases
]
```

## References

### Official Documentation
1. ROS 2 Humble: https://docs.ros.org/en/humble/
2. Nav2: https://navigation.ros.org/
3. Gazebo: https://gazebosim.org/docs/
4. Isaac Sim: https://docs.omniverse.nvidia.com/isaacsim/
5. Isaac ROS: https://nvidia-isaac-ros.github.io/
6. Docusaurus: https://docusaurus.io/
7. OpenAI Whisper: https://github.com/openai/whisper
8. Qdrant: https://qdrant.tech/documentation/

### Books and Papers
1. "Programming Robots with ROS 2" - Various authors
2. "Robotics, Vision and Control" - Peter Corke
3. "Speech and Language Processing" - Jurafsky & Martin

### Community Resources
1. ROS Discourse: https://discourse.ros.org/
2. NVIDIA Developer Forums
3. Robotics Stack Exchange

---

**Research completed**: 2025-12-16
**Next step**: Generate tasks with `/sp.tasks`
