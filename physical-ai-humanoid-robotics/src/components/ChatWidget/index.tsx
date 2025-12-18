/**
 * ChatWidget - AI-Powered Chatbot for Physical AI & Humanoid Robotics
 *
 * A floating chat widget that provides intelligent Q&A about
 * ROS 2, Gazebo, Isaac Sim, and VLA robotics concepts.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import styles from './styles.module.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// Knowledge base for the chatbot
const knowledgeBase: Record<string, string> = {
  // ROS 2 Topics
  'ros2': `**ROS 2 (Robot Operating System 2)** is a flexible framework for writing robot software. Key features include:

• **Nodes** - Independent processes that perform computation
• **Topics** - Named buses for publish/subscribe communication
• **Services** - Request/response communication pattern
• **Actions** - Long-running tasks with feedback
• **DDS** - Data Distribution Service for real-time communication

ROS 2 uses a distributed architecture where nodes can run on different machines and communicate seamlessly.`,

  'node': `**ROS 2 Nodes** are the fundamental building blocks of a ROS 2 system:

• Each node is an independent process
• Nodes communicate via topics, services, and actions
• Created using \`rclpy\` (Python) or \`rclcpp\` (C++)
• Example: \`ros2 run my_package my_node\`

\`\`\`python
import rclpy
from rclpy.node import Node

class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        self.get_logger().info('Hello ROS 2!')
\`\`\``,

  'topic': `**ROS 2 Topics** enable publish/subscribe communication:

• **Publisher** - Sends messages to a topic
• **Subscriber** - Receives messages from a topic
• Topics are typed (e.g., \`sensor_msgs/Image\`)
• Multiple publishers/subscribers per topic

Commands:
• \`ros2 topic list\` - List all topics
• \`ros2 topic echo /topic_name\` - View messages
• \`ros2 topic info /topic_name\` - Topic details`,

  'urdf': `**URDF (Unified Robot Description Format)** defines robot structure:

• XML format describing links and joints
• **Links** - Rigid bodies with visual/collision geometry
• **Joints** - Connections between links (revolute, prismatic, fixed)
• Used for visualization in RViz and simulation in Gazebo

\`\`\`xml
<robot name="my_robot">
  <link name="base_link">
    <visual>
      <geometry><box size="0.5 0.5 0.1"/></geometry>
    </visual>
  </link>
</robot>
\`\`\``,

  'service': `**ROS 2 Services** provide request/response communication:

• Synchronous communication pattern
• Client sends request, server sends response
• Defined using \`.srv\` files
• Good for quick, one-time operations

\`\`\`python
from example_interfaces.srv import AddTwoInts

# Service callback
def add_callback(request, response):
    response.sum = request.a + request.b
    return response
\`\`\``,

  // Gazebo & Digital Twin
  'gazebo': `**Gazebo** is a powerful robot simulation environment:

• **Physics Engine** - ODE, Bullet, DART, Simbody
• **Sensor Simulation** - Cameras, LiDAR, IMU, GPS
• **World Building** - Create complex environments
• **ROS 2 Integration** - Direct communication with ROS nodes

Gazebo Harmonic (latest) features:
• Improved rendering with Ogre 2
• Better plugin architecture
• Enhanced sensor models`,

  'digital twin': `**Digital Twin** is a virtual replica of a physical robot:

• Real-time synchronization with physical system
• Used for testing, monitoring, and prediction
• Reduces hardware testing costs
• Enables "what-if" scenario analysis

Components:
• **Physical Entity** - Real robot/system
• **Virtual Model** - Simulation in Gazebo/Unity
• **Data Connection** - Sensors and actuators
• **Services** - Analytics, monitoring, control`,

  'unity': `**Unity for Robotics** provides high-fidelity simulation:

• **HDRP** - High Definition Render Pipeline for photorealism
• **Physics** - NVIDIA PhysX integration
• **ROS-Unity Bridge** - Communication with ROS 2
• **Perception Package** - Synthetic data generation

Unity is excellent for:
• Human-robot interaction scenarios
• Photorealistic training data
• VR/AR robotics applications`,

  'sensor': `**Sensor Simulation** in robotics covers:

**Camera Sensors:**
• RGB cameras - Color images
• Depth cameras - Distance information
• Stereo cameras - 3D perception

**Range Sensors:**
• LiDAR - 360° point clouds
• Ultrasonic - Short-range detection
• Radar - Velocity and distance

**Proprioceptive:**
• IMU - Orientation and acceleration
• Encoders - Joint positions
• Force/Torque - Contact sensing`,

  // NVIDIA Isaac
  'isaac': `**NVIDIA Isaac** is a platform for AI-powered robotics:

**Isaac Sim:**
• Built on Omniverse
• Photorealistic rendering
• Domain randomization
• Synthetic data generation

**Isaac ROS:**
• GPU-accelerated perception
• VSLAM (Visual SLAM)
• Object detection
• Navigation integration

**Key Features:**
• RTX ray tracing
• PhysX 5 physics
• USD scene format`,

  'isaac sim': `**Isaac Sim** is NVIDIA's robot simulation platform:

• **Omniverse Platform** - Collaborative, physically accurate
• **RTX Rendering** - Real-time ray tracing
• **PhysX 5** - Advanced physics simulation
• **USD Format** - Universal Scene Description

Capabilities:
• Import URDF/MJCF robots
• Generate synthetic training data
• Test navigation algorithms
• Simulate warehouse environments`,

  'nav2': `**Nav2 (Navigation 2)** is the ROS 2 navigation stack:

**Core Components:**
• **Planner** - Global path planning (NavFn, Smac)
• **Controller** - Local trajectory following (DWB, TEB)
• **Recovery** - Stuck robot behaviors
• **BT Navigator** - Behavior tree orchestration

**Key Features:**
• Costmap 2D - Obstacle representation
• AMCL - Localization
• Waypoint following
• Dynamic obstacle avoidance`,

  'vslam': `**Visual SLAM** (Simultaneous Localization and Mapping):

• Uses camera images for localization
• Creates 3D maps of environment
• Isaac ROS VSLAM uses GPU acceleration

**Algorithms:**
• ORB-SLAM3 - Feature-based
• LSD-SLAM - Direct method
• RTAB-Map - RGB-D SLAM

**Isaac ROS VSLAM:**
• Stereo camera support
• GPU-accelerated
• Real-time performance`,

  'perception': `**Robot Perception** involves understanding the environment:

**Computer Vision:**
• Object detection (YOLO, Detectron2)
• Semantic segmentation
• Pose estimation
• Depth estimation

**Isaac ROS Perception:**
• DNN Inference
• AprilTag detection
• Occupancy grid
• Point cloud processing

**Sensors Used:**
• RGB-D cameras
• Stereo cameras
• LiDAR`,

  // VLA (Vision-Language-Action)
  'vla': `**VLA (Vision-Language-Action)** integrates AI for autonomous robots:

**Components:**
• **Vision** - Camera perception, object detection
• **Language** - LLM for task understanding
• **Action** - Robot motion execution

**Pipeline:**
1. Voice/text command input
2. LLM parses intent and plans tasks
3. Vision identifies objects/locations
4. Action system executes movements

**Applications:**
• Service robots
• Warehouse automation
• Assistive robotics`,

  'llm': `**LLMs in Robotics** enable natural language robot control:

**Capabilities:**
• Task decomposition
• Intent understanding
• Error recovery planning
• Human-robot dialogue

**Integration:**
• OpenAI GPT-4 / Claude
• Local models (LLaMA, Mistral)
• Prompt engineering for robotics

**Example Tasks:**
• "Pick up the red cup"
• "Navigate to the kitchen"
• "Find and bring me my keys"`,

  'whisper': `**OpenAI Whisper** for voice-controlled robots:

**Features:**
• Multilingual speech recognition
• Noise-robust transcription
• Real-time processing possible

**Integration:**
\`\`\`python
import whisper
model = whisper.load_model("base")
result = model.transcribe("audio.wav")
command = result["text"]
\`\`\`

**Robot Voice Pipeline:**
1. Audio capture
2. Whisper transcription
3. LLM intent parsing
4. Action execution`,

  'manipulation': `**Robot Manipulation** for humanoid robots:

**Components:**
• **Arm Control** - Trajectory planning
• **Gripper** - End-effector control
• **Inverse Kinematics** - Joint angle calculation

**MoveIt 2:**
• Motion planning framework
• Collision avoidance
• Grasp planning

**Key Concepts:**
• Task space vs joint space
• Motion primitives
• Force control`,

  'safety': `**Safety in Autonomous Robots:**

**Guardrails:**
• Workspace limits
• Force/torque limits
• Emergency stop
• Human detection zones

**Software Safety:**
• Action validation
• Command sanity checks
• Watchdog timers
• Graceful degradation

**Standards:**
• ISO 10218 - Industrial robots
• ISO 13482 - Service robots
• ISO 15066 - Collaborative robots`,
};

// Find best matching response from knowledge base
function findResponse(query: string): string {
  const lowerQuery = query.toLowerCase();

  // Direct keyword matching
  for (const [key, value] of Object.entries(knowledgeBase)) {
    if (lowerQuery.includes(key)) {
      return value;
    }
  }

  // Fuzzy matching for common questions
  if (lowerQuery.includes('what is') || lowerQuery.includes('explain') || lowerQuery.includes('tell me about')) {
    for (const [key, value] of Object.entries(knowledgeBase)) {
      if (lowerQuery.includes(key)) {
        return value;
      }
    }
  }

  // Greeting responses
  if (lowerQuery.match(/^(hi|hello|hey|greetings)/)) {
    return `Hello! I'm your Physical AI assistant. I can help you learn about:

• **ROS 2** - Nodes, topics, services, URDF
• **Gazebo & Unity** - Robot simulation
• **NVIDIA Isaac** - AI-powered robotics
• **VLA** - Vision-Language-Action systems

What would you like to know?`;
  }

  // Help response
  if (lowerQuery.includes('help') || lowerQuery.includes('what can you')) {
    return `I can answer questions about humanoid robotics topics:

**Module 1 - ROS 2:**
• Nodes, Topics, Services, Actions
• URDF robot description
• Launch files, Parameters

**Module 2 - Simulation:**
• Gazebo physics simulation
• Unity for robotics
• Digital twins, Sensors

**Module 3 - NVIDIA Isaac:**
• Isaac Sim overview
• Nav2 navigation
• VSLAM, Perception

**Module 4 - VLA:**
• Voice commands (Whisper)
• LLM planning
• Manipulation, Safety

Try asking: "What is ROS 2?" or "Explain VLA"`;
  }

  // Navigation specific
  if (lowerQuery.includes('navigation') || lowerQuery.includes('navigate')) {
    return knowledgeBase['nav2'];
  }

  // Robot/humanoid general
  if (lowerQuery.includes('humanoid') || lowerQuery.includes('robot')) {
    return `**Humanoid Robotics** combines multiple systems:

**Perception:**
• Cameras, LiDAR, IMU
• Object detection & tracking
• SLAM for mapping

**Cognition:**
• LLM-based task planning
• Behavior trees
• State machines

**Action:**
• Bipedal locomotion
• Arm manipulation
• Gripper control

**Frameworks:**
• ROS 2 for communication
• Nav2 for navigation
• MoveIt 2 for manipulation

This book covers all these topics across 4 modules!`;
  }

  // Default response
  return `I don't have specific information about that topic. Try asking about:

• **ROS 2** - nodes, topics, services, urdf
• **Gazebo** - simulation, sensors, physics
• **Isaac Sim** - NVIDIA robotics platform
• **Nav2** - robot navigation
• **VLA** - vision-language-action
• **Whisper** - voice recognition
• **LLM** - language models for robots

Or type "help" for a full list of topics!`;
}

export default function ChatWidget(): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Focus input when chat opens
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
          content:
            "Hello! I'm your **Physical AI Assistant**. I can help you learn about:\n\n" +
            "• **ROS 2** - Nodes, topics, services, URDF\n" +
            "• **Gazebo & Unity** - Simulation and digital twins\n" +
            "• **NVIDIA Isaac** - Perception and navigation\n" +
            "• **VLA** - Voice-controlled autonomous robots\n\n" +
            "What would you like to learn about?",
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

    // Simulate typing delay for natural feel
    await new Promise((resolve) => setTimeout(resolve, 500 + Math.random() * 1000));

    const response = findResponse(userQuery);

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
    // Simple markdown-like formatting
    let formatted = content
      // Code blocks
      .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
      // Inline code
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // Bold
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Line breaks
      .replace(/\n/g, '<br />');

    // Convert bullet points
    formatted = formatted.replace(/• /g, '<span class="bullet">•</span> ');

    return formatted;
  };

  const quickQuestions = [
    "What is ROS 2?",
    "Explain URDF",
    "What is VLA?",
    "Tell me about Nav2",
  ];

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        className={styles.chatToggle}
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        {isOpen ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path
              d="M18 6L6 18M6 6l12 12"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className={styles.chatWindow}>
          {/* Header */}
          <div className={styles.chatHeader}>
            <div className={styles.headerInfo}>
              <span className={styles.headerTitle}>Physical AI Assistant</span>
              <span className={styles.headerStatus}>
                {isTyping ? 'Typing...' : 'Online'}
              </span>
            </div>
            <button
              className={styles.closeButton}
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              ×
            </button>
          </div>

          {/* Messages */}
          <div className={styles.messagesContainer}>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`${styles.message} ${
                  message.role === 'user' ? styles.userMessage : styles.assistantMessage
                }`}
              >
                <div
                  className={styles.messageContent}
                  dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
                />
              </div>
            ))}
            {isTyping && (
              <div className={`${styles.message} ${styles.assistantMessage}`}>
                <div className={styles.loadingDots}>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions */}
          {messages.length <= 1 && (
            <div className={styles.quickQuestions}>
              {quickQuestions.map((q, i) => (
                <button
                  key={i}
                  className={styles.quickQuestion}
                  onClick={() => {
                    setInput(q);
                    setTimeout(() => sendMessage(), 100);
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className={styles.inputContainer}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about ROS 2, Gazebo, Isaac, VLA..."
              className={styles.input}
              disabled={isTyping}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isTyping}
              className={styles.sendButton}
              aria-label="Send message"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path
                  d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
