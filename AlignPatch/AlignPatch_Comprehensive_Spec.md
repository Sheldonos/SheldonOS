# AlignPatch System: Comprehensive Product Specification & Technical Architecture

## 1. Executive Summary

The **AlignPatch System** is a revolutionary wearable postural correction device inspired by the form factor, adhesive technology, and continuous monitoring capabilities of Continuous Glucose Monitors (CGMs). Moving away from bulky, uncomfortable, and socially visible braces, this system utilizes a network of low-profile, skin-adhering sensor patches connected by a dynamic micro-tensioning filament network. 

By creating a symmetrical, biomechanical web across the upper body, the system provides both passive mechanical support and active proprioceptive feedback to continuously train and correct spinal alignment. It is designed as a professional enterprise medical technology, suitable for both clinical rehabilitation and premium consumer wellness markets.

![AlignPatch Hero Render](./alignpatch_hero_render.png)
*Figure 1: The AlignPatch System worn on the back, showing the five-node tensegrity web.*

---

## 2. Placement Architecture & Biomechanics

The system relies on a five-node architecture, strategically placed along key biomechanical anchor points to create a "tensegrity" structure across the user's back and shoulders. This design mimics the body's natural fascial lines.

![Node Placement Diagram](./alignpatch_node_diagram.png)
*Figure 2: Anatomical placement of the five AlignPatch nodes.*

*   **Node 1 & Node 2 (The Lateral Anchors):** Placed symmetrically on the lateral aspect of the upper arms (deltoid/triceps junction). These act as the lateral tension points, anchoring the system to the appendicular skeleton.
*   **Node 3 (The Epicenter Hub):** Placed at the epicenter of the upper spine (between the scapulae, approximately at the T3-T4 vertebrae). This is the central processing unit and the primary mechanical junction where all tensioning filaments converge.
*   **Node 4 (The Cervical Node):** Placed at the bottom of the neck (C7 vertebra prominence). This node monitors forward head posture and provides upward cervical tension to counteract "tech neck."
*   **Node 5 (The Thoracic Node):** Placed in the mid-back (T8-T10 vertebrae). This node anchors the lower end of the thoracic curve, preventing excessive kyphosis (slouching) and supporting the lumbar transition.

---

## 3. Component Specifications

### 3.1. The Dermal Patches (Nodes)
Each node is designed with a multi-layer architecture similar to advanced medical wearables, prioritizing long-term wearability and skin health.

*   **Adhesive Base:** A hypoallergenic, medical-grade acrylic adhesive designed for 10-14 day continuous wear. It is waterproof, highly breathable, and flexible to move with the skin without causing shear stress or irritation.
*   **Micro-Housing:** A low-profile (under 4mm thick for peripheral nodes, 8mm for the Hub) biocompatible polymer casing that houses the internal components.
*   **Filament Retractor/Anchor:** A micro-mechanical spooling or anchoring mechanism that securely holds the tensioning string. The Epicenter Hub contains an active micro-motor for dynamic tension adjustment, while the peripheral nodes contain passive locking anchors.

![Epicenter Hub Exploded View](./alignpatch_exploded_hub.png)
*Figure 3: Exploded technical view of the Epicenter Hub showing internal layers.*

### 3.2. The Tensioning Filament ("The String")
The core innovation is the physical connection between the patches, creating a wearable web that transmits mechanical force and sensory feedback.

*   **Material:** A proprietary Shape Memory Alloy (SMA) core wrapped in a soft, skin-friendly elastomeric polymer (e.g., medical-grade silicone). This ensures the string is comfortable against the skin while maintaining high tensile strength and dynamic elasticity.
*   **Functionality:** The filament acts as an artificial fascia. When the user slouches, the distance between the nodes increases, causing the filament to pull taut. This provides immediate, subconscious proprioceptive feedback (a gentle tug on the skin) prompting the user to straighten up.

![Filament Close-up](./alignpatch_filament_closeup.png)
*Figure 4: Macro view of the tensioning filament connecting to a peripheral node.*

### 3.3. The Epicenter Hub (Central Processing Unit)
The Epicenter patch is the brain of the system, handling sensing, processing, and actuation.

*   **Microcontroller:** Ultra-low-power ARM Cortex-M4 processor.
*   **Connectivity:** Bluetooth Low Energy (BLE) 5.2 for smartphone synchronization and real-time data streaming.
*   **Actuation:** A micro-stepper motor that can dynamically tighten or loosen the filaments based on the user's posture data and selected training mode.
*   **Battery:** Rechargeable flexible solid-state battery, providing up to 7 days of continuous active tensioning.

---

## 4. Technical Architecture & Data Flow

The AlignPatch system operates on a closed-loop biofeedback architecture, integrating hardware sensors, edge processing, and cloud-connected application layers.

![Technical Architecture](./alignpatch_tech_architecture.png)
*Figure 5: System architecture diagram showing hardware, firmware, and application layers.*

1.  **Sensing:** The 6-axis IMU in the Epicenter Hub continuously samples the user's spinal angle and 3D spatial orientation at 50Hz.
2.  **Processing:** The onboard ARM Cortex-M4 processes the raw IMU data using a proprietary posture-estimation algorithm. It determines if the user has deviated from their calibrated "ideal" posture for more than a user-defined threshold (e.g., 10 seconds).
3.  **Actuation (Active Mode):** If poor posture is detected, the Epicenter Hub's micro-motor subtly retracts the filaments, increasing tension across the web. This physical pull on the arm and neck patches physically cues the user to correct their stance.
4.  **Feedback (Passive Mode):** Even without the motor, the static elasticity of the SMA filaments provides continuous mechanical resistance against slouching.

---

## 5. Clinical Efficacy & User Experience

The primary mechanism of action is **proprioceptive neuromuscular facilitation**. By providing a constant, subtle physical cue on the skin, the system trains the user's nervous system to recognize and maintain proper alignment autonomously, leading to long-term postural correction rather than dependency on a rigid brace.

![Posture Comparison](./alignpatch_posture_comparison.png)
*Figure 6: Biomechanical impact of the AlignPatch system on cervical and thoracic alignment.*

### 5.1. The Companion App
The system is managed via a premium iOS/Android companion app that serves as a digital physical therapist.

*   **Real-time Dashboard:** Displays current posture score and node tension status.
*   **Analytics:** Tracks posture quality over time, identifying specific times of day or activities where slouching occurs.
*   **Training Modes:** Allows users to adjust the sensitivity and tension levels, progressing from "Support" mode to "Active Training" mode.

![Mobile App UI](./alignpatch_app_ui.png)
*Figure 7: The AlignPatch companion app interface.*

### 5.2. Lifestyle Integration
Designed to be completely invisible under standard clothing, the AlignPatch allows users to maintain perfect posture during everyday activities without the social stigma or physical discomfort of traditional braces.

![Lifestyle Integration](./alignpatch_lifestyle.png)
*Figure 8: The AlignPatch system is discreet and comfortable for all-day wear in professional settings.*

---

## 6. Patentable Novelty & Intellectual Property

The AlignPatch System presents several highly patentable innovations:

1.  **Distributed Dermal Anchor Tensegrity System:** The use of multiple, distributed adhesive patches (nodes) connected by superficial tensioning filaments to create a wearable biomechanical web for posture correction. This is a novel departure from circumferential bracing.
2.  **Dynamic SMA Filament Actuation:** The integration of a central hub with a micro-motor that dynamically adjusts the tension of Shape Memory Alloy filaments based on real-time IMU posture data.
3.  **Skin-Shear Proprioceptive Feedback Mechanism:** Utilizing the specific sensation of skin-shear (pulling on the dermal layer via the adhesive patches) as a primary biofeedback mechanism for postural training, as opposed to vibration or rigid mechanical blocking.

![Product Flatlay](./alignpatch_product_flatlay.png)
*Figure 9: The complete AlignPatch system components.*
