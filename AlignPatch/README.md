# AlignPatch System

![AlignPatch Hero Render](./alignpatch_hero_render.png)

## Overview

The **AlignPatch System** is a revolutionary wearable postural correction device inspired by the form factor, adhesive technology, and continuous monitoring capabilities of Continuous Glucose Monitors (CGMs). 

Moving away from bulky, uncomfortable, and socially visible braces, this system utilizes a network of low-profile, skin-adhering sensor patches connected by a dynamic micro-tensioning filament network. By creating a symmetrical, biomechanical web across the upper body, the system provides both passive mechanical support and active proprioceptive feedback to continuously train and correct spinal alignment.

## The Five-Node Architecture

The system relies on a five-node architecture, strategically placed along key biomechanical anchor points to create a "tensegrity" structure across the user's back and shoulders.

![Node Placement Diagram](./alignpatch_node_diagram.png)

| Node | Location | Function |
|---|---|---|
| **Node 1 & 2** | Left & Right Deltoid (upper arms) | Lateral tension anchors |
| **Node 3** | T3-T4 vertebrae (between shoulder blades) | **Epicenter Hub** — brain of the system |
| **Node 4** | C7 vertebra (base of neck) | Cervical / forward-head correction |
| **Node 5** | T8-T10 vertebrae (mid-back) | Thoracic kyphosis prevention |

## Core Components

### The Epicenter Hub
The Hub is the central processing unit of the system. It contains a 6-axis IMU, an ARM Cortex-M4 microcontroller, BLE 5.2 connectivity, and a micro-stepper motor that dynamically adjusts the tension of the filaments based on real-time posture data.

![Epicenter Hub Exploded View](./alignpatch_exploded_hub.png)

### The Tensioning Filament
A proprietary Shape Memory Alloy (SMA) core wrapped in a soft, skin-friendly elastomeric polymer. When the user slouches, the distance between the nodes increases, causing the filament to pull taut. This provides immediate, subconscious proprioceptive feedback (a gentle tug on the skin) prompting the user to straighten up.

![Filament Close-up](./alignpatch_filament_closeup.png)

## Clinical Efficacy & User Experience

The primary mechanism of action is **proprioceptive neuromuscular facilitation**. By providing a constant, subtle physical cue on the skin, the system trains the user's nervous system to recognize and maintain proper alignment autonomously, leading to long-term postural correction rather than dependency on a rigid brace.

![Posture Comparison](./alignpatch_posture_comparison.png)

### Companion App
The system is managed via a premium iOS/Android companion app that serves as a digital physical therapist, offering real-time posture scoring, tension control, and historical analytics.

![Mobile App UI](./alignpatch_app_ui.png)

## System Architecture

The AlignPatch system operates on a closed-loop biofeedback architecture, integrating hardware sensors, edge processing, and cloud-connected application layers.

![Technical Architecture](./alignpatch_tech_architecture.png)

## Patentable Innovations

1. **Distributed Dermal Anchor Tensegrity System:** The use of multiple, distributed adhesive patches (nodes) connected by superficial tensioning filaments to create a wearable biomechanical web for posture correction.
2. **Dynamic SMA Filament Actuation:** The integration of a central hub with a micro-motor that dynamically adjusts the tension of Shape Memory Alloy filaments based on real-time IMU posture data.
3. **Skin-Shear Proprioceptive Feedback Mechanism:** Utilizing the specific sensation of skin-shear (pulling on the dermal layer via the adhesive patches) as a primary biofeedback mechanism for postural training.

## Repository Contents

*   `AlignPatch_Comprehensive_Spec.md`: Full product specification and technical architecture document.
*   `README.md`: This overview document.
*   `*.png`: High-resolution visual renderings of the product, architecture, and UI.

![Product Flatlay](./alignpatch_product_flatlay.png)
