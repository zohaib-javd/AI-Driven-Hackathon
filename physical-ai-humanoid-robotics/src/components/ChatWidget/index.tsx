/**
 * ChatWidget - AI-Powered Chatbot for Physical AI & Humanoid Robotics
 *
 * A floating chat widget that provides intelligent Q&A about
 * ROS 2, Gazebo, Isaac Sim, and VLA robotics concepts.
 * Knowledge is sourced directly from the book content.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import styles from './styles.module.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface KnowledgeEntry {
  keywords: string[];
  content: string;
  priority: number;
}

// Comprehensive knowledge base from the book content
const knowledgeBase: KnowledgeEntry[] = [
  // === MODULE 1: ROS 2 ===
  {
    keywords: ['ros2', 'ros 2', 'robot operating system', 'what is ros'],
    priority: 10,
    content: `**ROS 2 (Robot Operating System 2)** is the nervous system of robots - a middleware framework that coordinates communication between all robot components.

**Key Features:**
• **Communication Infrastructure** - Message passing between processes
• **Hardware Abstraction** - Standardized interfaces for sensors/actuators
• **Package Management** - Reusable software modules
• **Tools & Utilities** - Visualization, debugging, simulation

**Improvements over ROS 1:**
| Feature | ROS 1 | ROS 2 |
|---------|-------|-------|
| Real-time | Not supported | Built-in support |
| Security | No encryption | DDS security |
| Multi-robot | Difficult | Native support |
| Reliability | Best-effort | Quality of Service (QoS) |

ROS 2 uses **DDS (Data Distribution Service)** for real-time, secure communication. The recommended distribution is **ROS 2 Humble** on Ubuntu 22.04.`
  },
  {
    keywords: ['node', 'nodes', 'rclpy', 'building block'],
    priority: 9,
    content: `**ROS 2 Nodes** are the fundamental building blocks - each node is an independent process performing a specific function.

**Creating a Node:**
\`\`\`python
import rclpy
from rclpy.node import Node

class MinimalNode(Node):
    def __init__(self):
        super().__init__('minimal_node')
        self.get_logger().info('Node started!')

def main():
    rclpy.init()
    node = MinimalNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
\`\`\`

**Key Concepts:**
• **Single Responsibility** - Each node does one thing well
• **Timers** - Execute callbacks periodically
• **Executors** - Control how callbacks are processed
• **Lifecycle Nodes** - Managed state transitions (Unconfigured → Inactive → Active)

**Commands:**
• \`ros2 node list\` - List running nodes
• \`ros2 node info /node_name\` - Get node details`
  },
  {
    keywords: ['topic', 'topics', 'publish', 'subscribe', 'pubsub', 'publisher', 'subscriber'],
    priority: 9,
    content: `**ROS 2 Topics** enable decoupled, asynchronous publish-subscribe communication.

**Publisher Example:**
\`\`\`python
from sensor_msgs.msg import JointState

class JointPublisher(Node):
    def __init__(self):
        super().__init__('joint_publisher')
        self.publisher = self.create_publisher(JointState, 'joint_states', 10)
        self.timer = self.create_timer(0.02, self.publish_joints)
\`\`\`

**Subscriber Example:**
\`\`\`python
self.subscription = self.create_subscription(
    JointState, 'joint_states', self.callback, 10)
\`\`\`

**QoS Profiles:**
• **RELIABLE** - For commands (must not lose messages)
• **BEST_EFFORT** - For high-frequency sensors
• **TRANSIENT_LOCAL** - For latched topics

**Commands:**
• \`ros2 topic list\` - List topics
• \`ros2 topic echo /topic\` - View messages
• \`ros2 topic hz /topic\` - Check publishing rate`
  },
  {
    keywords: ['service', 'services', 'request', 'response'],
    priority: 8,
    content: `**ROS 2 Services** provide synchronous request-response communication.

\`\`\`python
from example_interfaces.srv import AddTwoInts

# Service callback
def add_callback(request, response):
    response.sum = request.a + request.b
    return response

# Create service
self.srv = self.create_service(AddTwoInts, 'add_two_ints', add_callback)
\`\`\`

**When to use Services:**
• Quick, one-time operations
• Configuration changes
• State queries

**Commands:**
• \`ros2 service list\` - List services
• \`ros2 service call /srv_name srv_type "{data}"\``
  },
  {
    keywords: ['action', 'actions', 'goal', 'feedback', 'long running'],
    priority: 8,
    content: `**ROS 2 Actions** handle long-running tasks with progress feedback.

**Use Cases:**
• Navigation to a goal
• Arm movement trajectories
• Any task needing progress updates

**Action Structure:**
• **Goal** - What to achieve
• **Feedback** - Progress updates (25%, 50%, 75%...)
• **Result** - Final outcome

Actions are ideal when you need to monitor progress and potentially cancel tasks.`
  },
  {
    keywords: ['urdf', 'robot description', 'links', 'joints', 'xml'],
    priority: 9,
    content: `**URDF (Unified Robot Description Format)** defines robot structure in XML.

\`\`\`xml
<robot name="humanoid">
  <link name="base_link">
    <visual>
      <geometry><box size="0.5 0.5 0.1"/></geometry>
    </visual>
    <collision>
      <geometry><box size="0.5 0.5 0.1"/></geometry>
    </collision>
    <inertial>
      <mass value="10.0"/>
      <inertia ixx="0.1" iyy="0.1" izz="0.1"/>
    </inertial>
  </link>

  <joint name="shoulder" type="revolute">
    <parent link="torso"/>
    <child link="upper_arm"/>
    <axis xyz="0 1 0"/>
    <limit lower="-1.57" upper="1.57" effort="100" velocity="1.0"/>
  </joint>
</robot>
\`\`\`

**Components:**
• **Links** - Rigid bodies with visual/collision geometry
• **Joints** - Connections (revolute, prismatic, fixed, continuous)
• Used in **RViz** for visualization and **Gazebo** for simulation`
  },
  {
    keywords: ['dds', 'data distribution', 'middleware', 'qos', 'quality of service'],
    priority: 7,
    content: `**DDS (Data Distribution Service)** is the communication layer powering ROS 2.

**Key Features:**
• **Discovery** - Nodes find each other automatically
• **QoS Policies** - Control reliability, durability, history
• **Security** - Built-in encryption and authentication

**QoS Profiles:**
| Profile | Reliability | Use Case |
|---------|-------------|----------|
| Sensor Data | Best Effort | Camera, LiDAR |
| Parameters | Reliable + Transient | Configuration |
| Commands | Reliable | Motor commands |

**Available DDS Implementations:**
• Fast DDS (default)
• Cyclone DDS
• Connext DDS`
  },

  // === MODULE 2: DIGITAL TWIN & GAZEBO ===
  {
    keywords: ['digital twin', 'virtual replica', 'simulation', 'physical digital'],
    priority: 10,
    content: `**Digital Twin** is a virtual replica of a physical robot with bidirectional real-time synchronization.

**Core Components:**
1. **Physical Entity** - Real robot with sensors/actuators
2. **Virtual Entity** - Simulation model (Gazebo/Unity)
3. **Data Connection** - Real-time sensor streaming
4. **Services** - Analytics, monitoring, prediction

**Digital Twin vs Simulation:**
| Aspect | Simulation | Digital Twin |
|--------|------------|--------------|
| Connection | One-way | Bidirectional |
| Data | Synthetic | Live sensors |
| Purpose | What-if analysis | Continuous monitoring |
| Updates | Manual | Automatic sync |

**Applications:**
• Virtual testing before hardware trials
• Predictive maintenance
• Training AI models safely
• Remote monitoring and control`
  },
  {
    keywords: ['gazebo', 'simulator', 'physics engine', 'world'],
    priority: 10,
    content: `**Gazebo** is a powerful robot simulation environment for ROS 2.

**Key Features:**
• **Physics Engines** - ODE, Bullet, DART, Simbody
• **Sensor Simulation** - Cameras, LiDAR, IMU, GPS
• **World Building** - Complex environments
• **ROS 2 Integration** - Direct communication with nodes

**Gazebo Harmonic Features:**
• Improved Ogre 2 rendering
• Better plugin architecture
• Enhanced sensor models

**Usage:**
\`\`\`bash
# Launch Gazebo with ROS 2
ros2 launch gazebo_ros gazebo.launch.py

# Spawn a robot
ros2 run gazebo_ros spawn_entity.py -entity robot -file model.urdf
\`\`\``
  },
  {
    keywords: ['unity', 'hdrp', 'game engine', 'photorealistic'],
    priority: 8,
    content: `**Unity for Robotics** provides high-fidelity simulation with game engine capabilities.

**Features:**
• **HDRP** - High Definition Render Pipeline for photorealism
• **NVIDIA PhysX** - Physics integration
• **ROS-Unity Bridge** - Communication with ROS 2
• **Perception Package** - Synthetic data generation

**Use Cases:**
• Human-robot interaction scenarios
• Photorealistic training data
• VR/AR robotics applications
• Complex environment simulation`
  },
  {
    keywords: ['sensor', 'sensors', 'camera', 'lidar', 'imu', 'depth'],
    priority: 8,
    content: `**Sensor Simulation** in robotics covers multiple modalities:

**Camera Sensors:**
• RGB cameras - Color images
• Depth cameras - Distance information (ToF, Structured Light)
• Stereo cameras - 3D perception
• Fisheye cameras - Wide field of view

**Range Sensors:**
• **LiDAR** - 360° point clouds (Velodyne, Ouster)
• Ultrasonic - Short-range detection
• Radar - Velocity and distance

**Proprioceptive Sensors:**
• **IMU** - Orientation/acceleration (accelerometer + gyroscope)
• Encoders - Joint positions
• Force/Torque - Contact sensing

All sensors can be simulated in Gazebo and Isaac Sim with realistic noise models.`
  },

  // === MODULE 3: NVIDIA ISAAC ===
  {
    keywords: ['isaac', 'isaac sim', 'nvidia', 'omniverse'],
    priority: 10,
    content: `**NVIDIA Isaac Sim** is a scalable robotics simulation platform built on Omniverse.

**Key Features:**
| Feature | Description |
|---------|-------------|
| **Photorealistic Rendering** | RTX ray-tracing |
| **Accurate Physics** | PhysX 5.0 |
| **Sensor Simulation** | Cameras, LiDAR, IMU |
| **ROS 2 Integration** | Native bridge |
| **Synthetic Data** | Training data generation |
| **Parallel Simulation** | Thousands of environments |

**Foundation Technologies:**
• **USD** - Universal Scene Description (from Pixar)
• **RTX** - Real-time ray tracing
• **PhysX 5** - Advanced physics

**Sim-to-Real Pipeline:**
Domain randomization bridges the reality gap by varying lighting, textures, physics, and sensor noise during training.`
  },
  {
    keywords: ['nav2', 'navigation', 'navigate', 'path planning', 'autonomous'],
    priority: 10,
    content: `**Nav2 (Navigation 2)** is the ROS 2 navigation stack for autonomous mobile robots.

**Core Components:**
1. **Map Server** - Provides static map
2. **AMCL** - Localization (particle filter)
3. **Global Planner** - Plans path (NavFn, SMAC, Theta*)
4. **Local Controller** - Follows path (DWB, Pure Pursuit, MPPI)
5. **Costmap 2D** - Obstacle representation
6. **Recovery Behaviors** - Handles stuck situations

**Behavior Trees** orchestrate navigation:
\`\`\`
Root → RateController → RecoveryNode
         ├── ComputePath → FollowPath
         └── Recovery (Spin, Wait, BackUp)
\`\`\`

**Commands:**
\`\`\`bash
ros2 launch nav2_bringup navigation_launch.py
\`\`\`

**Planner Selection:**
• NavFn - Holonomic robots
• SMAC Hybrid-A* - Car-like robots
• Theta* - Smooth any-angle paths`
  },
  {
    keywords: ['vslam', 'slam', 'localization', 'mapping', 'visual slam'],
    priority: 8,
    content: `**Visual SLAM** (Simultaneous Localization and Mapping) uses cameras for robot localization.

**How it Works:**
• Creates 3D maps from camera images
• Tracks features to estimate position
• GPU-accelerated in Isaac ROS

**Algorithms:**
• **ORB-SLAM3** - Feature-based
• **LSD-SLAM** - Direct method
• **RTAB-Map** - RGB-D SLAM

**Isaac ROS VSLAM:**
• Stereo camera support
• GPU-accelerated processing
• Real-time performance
• ROS 2 native integration`
  },
  {
    keywords: ['perception', 'object detection', 'computer vision', 'yolo', 'detection'],
    priority: 8,
    content: `**Robot Perception** enables understanding of the environment.

**Computer Vision Capabilities:**
• **Object Detection** - YOLO, Detectron2, DETR
• **Semantic Segmentation** - Mask R-CNN
• **Pose Estimation** - MediaPipe, OpenPose
• **Depth Estimation** - Stereo, monocular

**Isaac ROS Perception:**
• DNN Inference on GPU
• AprilTag detection
• Occupancy grid generation
• Point cloud processing

**Sensors:**
• RGB-D cameras (RealSense, Kinect)
• Stereo cameras
• LiDAR`
  },

  // === MODULE 4: VLA ===
  {
    keywords: ['vla', 'vision language action', 'vision-language-action'],
    priority: 10,
    content: `**VLA (Vision-Language-Action)** integrates AI for natural human-robot interaction.

**The Three Pillars:**

**1. Vision (Perception):**
• Camera feeds, depth sensors
• Object detection, scene understanding

**2. Language (Cognition):**
• Speech recognition (Whisper)
• LLM task planning (GPT-4, Claude)
• Intent understanding

**3. Action (Execution):**
• Motion planning (MoveIt2)
• Navigation (Nav2)
• Manipulation control

**VLA Pipeline:**
1. Voice/text command input
2. LLM parses intent and plans tasks
3. Vision identifies objects/locations
4. Action system executes movements
5. Feedback updates perception

**Applications:**
• Service robots
• Warehouse automation
• Healthcare assistance
• Home assistants`
  },
  {
    keywords: ['llm', 'large language model', 'gpt', 'claude', 'language model', 'ai planning'],
    priority: 9,
    content: `**LLMs in Robotics** enable natural language robot control and task planning.

**Capabilities:**
• **Task Decomposition** - Break complex commands into steps
• **Intent Understanding** - Parse natural language
• **Error Recovery** - Plan alternative actions
• **Human-Robot Dialogue** - Conversational interaction

**Integration Pattern:**
\`\`\`python
class VLAAgent:
    def __init__(self):
        self.vision = VisionEncoder()
        self.language = LLMPlanner()  # GPT-4, Claude
        self.action = MotionController()

    async def execute(self, command, camera):
        scene = self.vision.analyze(camera)
        plan = await self.language.plan(command, scene)
        for step in plan:
            await self.action.execute(step)
\`\`\`

**Example Commands:**
• "Pick up the red cup on the table"
• "Navigate to the kitchen"
• "Find and bring me my keys"`
  },
  {
    keywords: ['whisper', 'speech', 'voice', 'speech recognition', 'transcription'],
    priority: 9,
    content: `**OpenAI Whisper** enables voice-controlled robots with robust speech recognition.

**Features:**
• Multilingual support (99 languages)
• Noise-robust transcription
• Multiple model sizes (tiny to large)

**Integration:**
\`\`\`python
import whisper

model = whisper.load_model("base")
result = model.transcribe("audio.wav")
command = result["text"]
\`\`\`

**Robot Voice Pipeline:**
1. **Audio Capture** - Microphone input
2. **Whisper Transcription** - Speech to text
3. **LLM Intent Parsing** - Understand command
4. **Action Execution** - Robot movement

**Model Sizes:**
| Model | Parameters | Speed |
|-------|-----------|-------|
| tiny | 39M | Fastest |
| base | 74M | Fast |
| small | 244M | Balanced |
| medium | 769M | Accurate |
| large | 1.5B | Most accurate |`
  },
  {
    keywords: ['manipulation', 'grasp', 'gripper', 'arm', 'moveit', 'pick'],
    priority: 8,
    content: `**Robot Manipulation** for humanoid robot arms and hands.

**Components:**
• **Arm Control** - Trajectory planning
• **Gripper Control** - End-effector operation
• **Inverse Kinematics** - Joint angle calculation

**MoveIt 2:**
• Motion planning framework for ROS 2
• Collision avoidance
• Grasp planning
• Multiple planning algorithms (OMPL, CHOMP)

**Key Concepts:**
• **Task Space** - End-effector position/orientation
• **Joint Space** - Individual joint angles
• **Motion Primitives** - Basic movement patterns
• **Force Control** - Adaptive gripping

**Manipulation Pipeline:**
1. Detect object with vision
2. Plan grasp pose
3. Compute arm trajectory
4. Execute motion with collision checking`
  },
  {
    keywords: ['safety', 'guardrail', 'guardrails', 'safe', 'emergency'],
    priority: 8,
    content: `**Safety in Autonomous Robots** is critical for real-world deployment.

**Hardware Guardrails:**
• Workspace limits
• Force/torque limits
• Emergency stop buttons
• Human detection zones

**Software Safety:**
• Action validation before execution
• Command sanity checks
• Watchdog timers
• Graceful degradation

**LLM Safety Guardrails:**
• Filter harmful commands
• Verify action feasibility
• Check physical constraints
• Require confirmation for risky actions

**Standards:**
• **ISO 10218** - Industrial robots
• **ISO 13482** - Service robots
• **ISO 15066** - Collaborative robots`
  },

  // General/Help
  {
    keywords: ['help', 'what can you', 'how to use', 'commands'],
    priority: 5,
    content: `I'm your **Physical AI & Humanoid Robotics** assistant! I can answer questions from the book.

**Module 1 - ROS 2 Nervous System:**
• Nodes, Topics, Services, Actions
• URDF robot description
• DDS communication, QoS

**Module 2 - Digital Twin Simulation:**
• What is a Digital Twin?
• Gazebo simulation
• Unity for robotics
• Sensor simulation

**Module 3 - Isaac AI Brain:**
• NVIDIA Isaac Sim
• Nav2 navigation
• VSLAM localization
• Perception pipelines

**Module 4 - VLA Capstone:**
• Vision-Language-Action
• Whisper voice commands
• LLM task planning
• Robot manipulation
• Safety guardrails

**Try asking:**
• "What is ROS 2?"
• "How do topics work?"
• "Explain digital twins"
• "What is VLA?"
• "How does Nav2 work?"`
  },
  {
    keywords: ['humanoid', 'robot', 'robotics'],
    priority: 6,
    content: `**Humanoid Robotics** combines multiple systems covered in this book:

**Perception Layer:**
• Cameras (RGB, depth, stereo)
• LiDAR, IMU sensors
• Object detection & tracking
• SLAM for mapping

**Cognition Layer:**
• LLM-based task planning
• Behavior trees
• State machines
• Natural language understanding

**Action Layer:**
• Bipedal locomotion
• Arm manipulation
• Gripper control
• Balance control

**Software Stack:**
• **ROS 2** - Communication framework
• **Nav2** - Navigation
• **MoveIt 2** - Motion planning
• **Isaac Sim** - Simulation

This book covers all four modules to build complete autonomous humanoid robots!`
  },
  {
    keywords: ['costmap', 'obstacle', 'path'],
    priority: 7,
    content: `**Costmap 2D** represents obstacles and navigation costs in Nav2.

**Layers:**
• **Static Layer** - From map
• **Obstacle Layer** - From sensors
• **Inflation Layer** - Safety margins
• **Voxel Layer** - 3D obstacles

**Cost Values:**
• 0 = Free space
• 253 = Inscribed (robot edge)
• 254 = Lethal (collision)
• 255 = Unknown

**Configuration:**
\`\`\`yaml
inflation_layer:
  plugin: "nav2_costmap_2d::InflationLayer"
  cost_scaling_factor: 3.0
  inflation_radius: 0.55
\`\`\``
  },
  {
    keywords: ['behavior tree', 'bt', 'navigation logic'],
    priority: 7,
    content: `**Behavior Trees** in Nav2 orchestrate navigation logic.

**Structure:**
\`\`\`
Root (Sequence)
└── RecoveryNode
    ├── PipelineSequence
    │   ├── ComputePathToPose
    │   └── FollowPath
    └── RecoveryFallback
        ├── Spin
        ├── Wait
        └── BackUp
\`\`\`

**Advantages over State Machines:**
• Modular and reusable
• Easy to extend
• Visual debugging with Groot
• Hierarchical organization

**Node Types:**
• **Sequence** - All children must succeed
• **Fallback** - First success wins
• **Decorator** - Modify child behavior`
  },
  {
    keywords: ['launch', 'launch file', 'parameter', 'config'],
    priority: 6,
    content: `**ROS 2 Launch Files** configure and start multiple nodes.

\`\`\`python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_package',
            executable='my_node',
            name='my_node',
            parameters=[{'param': 'value'}]
        )
    ])
\`\`\`

**Parameters:**
\`\`\`bash
# Set at launch
ros2 run pkg node --ros-args -p rate:=10.0

# Set at runtime
ros2 param set /node param_name value
\`\`\``
  }
];

// Improved search function with better matching
function findBestResponse(query: string): string {
  const lowerQuery = query.toLowerCase();
  const words = lowerQuery.split(/\s+/);

  // Score each knowledge entry
  const scored = knowledgeBase.map(entry => {
    let score = 0;

    // Check keyword matches
    for (const keyword of entry.keywords) {
      if (lowerQuery.includes(keyword)) {
        score += 10 + keyword.length; // Longer matches are more specific
      }
      // Partial word matching
      for (const word of words) {
        if (word.length > 3 && keyword.includes(word)) {
          score += 3;
        }
      }
    }

    // Boost by priority
    score += entry.priority;

    return { entry, score };
  });

  // Sort by score and get best match
  scored.sort((a, b) => b.score - a.score);

  // If best score is reasonable, return it
  if (scored[0].score > 10) {
    return scored[0].entry.content;
  }

  // Greeting detection
  if (lowerQuery.match(/^(hi|hello|hey|greetings|good morning|good evening)/)) {
    return `Hello! I'm your **Physical AI & Humanoid Robotics** assistant.

I can help you learn about:
• **ROS 2** - The robot nervous system
• **Digital Twins** - Virtual robot replicas
• **NVIDIA Isaac** - AI-powered simulation
• **VLA** - Voice-controlled autonomous robots

What would you like to know? Try asking about any topic from the book!`;
  }

  // Thanks detection
  if (lowerQuery.match(/(thank|thanks|thx)/)) {
    return `You're welcome! Feel free to ask more questions about robotics.

Topics I can help with:
• ROS 2 nodes, topics, services
• Gazebo and Unity simulation
• Nav2 navigation
• VLA and LLM integration`;
  }

  // Default fallback with suggestions
  return `I found several related topics. Here's what I can help you with:

**Most Popular Questions:**
• "What is ROS 2?" - Learn about the robot operating system
• "How do nodes work?" - Understanding ROS 2 building blocks
• "Explain digital twins" - Virtual robot replicas
• "What is VLA?" - Vision-Language-Action systems
• "How does Nav2 work?" - Robot navigation

**Or ask about:**
• Topics, Services, Actions, URDF
• Gazebo, Unity, Isaac Sim
• SLAM, Perception, LLMs
• Whisper, Manipulation, Safety

Just type your question and I'll find the relevant information from the book!`;
}

// Trigger deployment
export default function ChatWidget(): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  // Welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: `Welcome to the **Physical AI & Humanoid Robotics** assistant!

I can answer questions from the textbook about:
• **Module 1:** ROS 2 - Nodes, Topics, Services, URDF
• **Module 2:** Digital Twins - Gazebo, Unity, Sensors
• **Module 3:** NVIDIA Isaac - Sim, Nav2, Perception
• **Module 4:** VLA - Voice Commands, LLMs, Manipulation

**Try asking:** "What is ROS 2?" or "How does Nav2 work?"`,
          timestamp: new Date(),
        },
      ]);
    }
  }, [messages.length]);

  const sendMessage = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const userQuery = input.trim();
    setInput('');
    setIsTyping(true);

    // Simulate thinking delay
    await new Promise((resolve) => setTimeout(resolve, 600 + Math.random() * 800));

    const response = findBestResponse(userQuery);

    const assistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: response,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);
    setIsTyping(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (content: string) => {
    let formatted = content
      .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br />');
    formatted = formatted.replace(/• /g, '<span class="bullet">•</span> ');
    return formatted;
  };

  const quickQuestions = [
    "What is ROS 2?",
    "Explain VLA",
    "How does Nav2 work?",
    "What is a Digital Twin?",
  ];

  return (
    <>
      <button
        className={styles.chatToggle}
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        {isOpen ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )}
      </button>

      {isOpen && (
        <div className={styles.chatWindow}>
          <div className={styles.chatHeader}>
            <div className={styles.headerInfo}>
              <span className={styles.headerTitle}>Physical AI Assistant</span>
              <span className={styles.headerStatus}>{isTyping ? 'Typing...' : 'Online'}</span>
            </div>
            <div className={styles.headerButtons}>
              <button
                className={styles.clearButton}
                onClick={() => {
                  setMessages([]);
                  // Add back the welcome message
                  setMessages([
                    {
                      id: 'welcome',
                      role: 'assistant',
                      content: `Welcome to the **Physical AI & Humanoid Robotics** assistant!

I can answer questions from the textbook about:
• **Module 1:** ROS 2 - Nodes, Topics, Services, URDF
• **Module 2:** Digital Twins - Gazebo, Unity, Sensors
• **Module 3:** NVIDIA Isaac - Sim, Nav2, Perception
• **Module 4:** VLA - Voice Commands, LLMs, Manipulation

**Try asking:** "What is ROS 2?" or "How does Nav2 work?"`,
                      timestamp: new Date(),
                    },
                  ]);
                }}
                aria-label="Clear chat"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
              <button className={styles.closeButton} onClick={() => setIsOpen(false)} aria-label="Close chat">×</button>
            </div>
          </div>

          <div className={styles.messagesContainer}>
            {messages.map((message) => (
              <div key={message.id} className={`${styles.message} ${message.role === 'user' ? styles.userMessage : styles.assistantMessage}`}>
                <div className={styles.messageContent} dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}/>
              </div>
            ))}
            {isTyping && (
              <div className={`${styles.message} ${styles.assistantMessage}`}>
                <div className={styles.loadingDots}><span></span><span></span><span></span></div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {messages.length <= 1 && (
            <div className={styles.quickQuestions}>
              {quickQuestions.map((q, i) => (
                <button key={i} className={styles.quickQuestion} onClick={() => { setInput(q); setTimeout(() => sendMessage(), 100); }}>{q}</button>
              ))}
            </div>
          )}

          <div className={styles.inputContainer}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about ROS 2, VLA, Nav2, Isaac..."
              className={styles.input}
              disabled={isTyping}
            />
            <button onClick={sendMessage} disabled={!input.trim() || isTyping} className={styles.sendButton} aria-label="Send message">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
