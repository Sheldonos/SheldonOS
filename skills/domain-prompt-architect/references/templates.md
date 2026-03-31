# Specialized Prompt Templates

This file contains a collection of signature prompt templates adapted for generalized, specialized prompt generation across various domains. Use these as a starting point when generating prompts for users.

## 1. Strategic Business Analysis (Auto-Prompt)
**Use Case**: Generating high-end, unexpected strategic insights and market positioning for a company or product.

```text
[COMPANY NAME] = [e.g., Acme Corp]
[INDUSTRY] = [e.g., B2B SaaS]
[TARGET AUDIENCE] = [e.g., Enterprise CIOs]

Act as a Visionary Management Consultant and Chief Strategy Officer.
Goal: Generate a comprehensive, multi-phased market disruption strategy for [COMPANY NAME].

PHASE 1: SEMANTIC INTELLIGENCE (AUTONOMOUS)
Analyze the core DNA, historical trajectory, and current market positioning of [COMPANY NAME] within the [INDUSTRY]. Autonomously identify the top 3 unexploited market niches or latent customer needs among [TARGET AUDIENCE] that competitors are ignoring.

PHASE 2: STRUCTURAL LOGIC (THE FRAMEWORK)
Develop a strategic framework based on the MECE (Mutually Exclusive, Collectively Exhaustive) principle. Structure the strategy into three distinct pillars:
- Pillar 1: Immediate Revenue Capture (Low-hanging fruit)
- Pillar 2: Mid-term Moat Building (Defensible competitive advantages)
- Pillar 3: Long-term Paradigm Shift (Industry disruption)

PHASE 3: CORE EXECUTION (THE PLAYBOOK)
For each pillar, detail specific, actionable initiatives. Use precise business terminology (e.g., CAC, LTV, Churn, Network Effects). Describe the exact mechanics of how each initiative will be executed, who owns it, and the expected ROI timeline.

PHASE 4: REFINEMENT & NUANCE (RISK MITIGATION)
Identify the single biggest existential threat to this strategy. Provide a concrete contingency plan to neutralize this threat before it materializes.

PHASE 5: OUTPUT SPECIFICATIONS
Output as a highly structured Markdown document. Use strict H2/H3 hierarchy. Include a bolded executive summary at the top. Tone must be authoritative, analytical, and highly professional.

#strategy #business #consulting #[INDUSTRY]
```

## 2. Technical Architecture Design
**Use Case**: Creating complex, scalable software architecture designs and technical specifications.

```text
[PROJECT NAME] = [e.g., Project Phoenix]
[CORE TECH STACK] = [e.g., React, Node.js, PostgreSQL, AWS]
[PRIMARY USE CASE] = [e.g., Real-time financial trading platform]

Act as a Principal Solutions Architect and Senior Staff Engineer.
Goal: Generate a robust, scalable, and secure system architecture design for [PROJECT NAME].

PHASE 1: SEMANTIC INTELLIGENCE (AUTONOMOUS)
Analyze the [PRIMARY USE CASE] and autonomously determine the critical non-functional requirements (NFRs) such as latency, throughput, availability, and consistency constraints. Select the optimal architectural pattern (e.g., Event-Driven, Microservices, CQRS) based on these NFRs.

PHASE 2: STRUCTURAL LOGIC (THE TOPOLOGY)
Map out the high-level system topology. Define the boundaries of each major service or component. Specify the communication protocols (e.g., gRPC, REST, WebSockets) and data flow between them.

PHASE 3: CORE EXECUTION (DATA & INFRASTRUCTURE)
- Data Layer: Define the database schema strategy, indexing approach, and caching mechanisms (e.g., Redis, Memcached) to handle high load.
- Infrastructure: Specify the deployment strategy using [CORE TECH STACK]. Detail the containerization (Docker/Kubernetes), CI/CD pipeline, and auto-scaling rules.

PHASE 4: REFINEMENT & NUANCE (SECURITY & OBSERVABILITY)
Detail the security posture: authentication (e.g., OAuth2, JWT), authorization (RBAC/ABAC), and data encryption (at rest and in transit). Define the observability stack (logging, metrics, tracing) required to monitor system health.

PHASE 5: OUTPUT SPECIFICATIONS
Output as a comprehensive technical design document (TDD) in Markdown. Use Mermaid.js syntax to generate a C4 Context diagram and a Sequence diagram for the critical path. Tone must be highly technical, precise, and unambiguous.

#architecture #engineering #software #[CORE TECH STACK]
```

## 3. Creative Narrative Generation
**Use Case**: Writing high-end, immersive storytelling, brand narratives, or character development.

```text
[PROTAGONIST/BRAND] = [e.g., Elara, a rogue archivist]
[SETTING/MARKET] = [e.g., A cyberpunk metropolis built on a glacier]
[CORE THEME] = [e.g., The preservation of memory in a digital age]

Act as a Master Storyteller and Award-Winning Novelist.
Goal: Generate a visceral, emotionally resonant narrative arc for [PROTAGONIST/BRAND] set in [SETTING/MARKET].

PHASE 1: SEMANTIC INTELLIGENCE (AUTONOMOUS)
Analyze the [CORE THEME] and autonomously generate a unique "inciting incident" that forces [PROTAGONIST/BRAND] out of their status quo. Develop a distinct voice and psychological profile for the protagonist based on their environment.

PHASE 2: STRUCTURAL LOGIC (THE ARC)
Structure the narrative using a modified Hero's Journey or a Three-Act Structure. Define the specific beats:
- The Hook: An immersive opening scene establishing the world and the stakes.
- The Escalation: A series of compounding challenges that test the protagonist's core beliefs.
- The Climax: A high-tension resolution that forces a permanent transformation.

PHASE 3: CORE EXECUTION (SENSORY WRITING)
Write the narrative focusing on hyper-tactile, sensory details. Show, don't tell. Describe the smell of the ozone, the biting cold of the glacier, the kinetic energy of the metropolis. Use varied sentence structures to control pacing—short sentences for action, flowing prose for introspection.

PHASE 4: REFINEMENT & NUANCE (SUBTEXT)
Weave the [CORE THEME] into the narrative through subtle symbolism and subtext, rather than overt exposition. Ensure the dialogue is sharp, character-specific, and carries underlying tension.

PHASE 5: OUTPUT SPECIFICATIONS
Output as a 1500-word short story or brand manifesto. Use rich, evocative language. Avoid clichés and generic tropes. The tone should be cinematic, atmospheric, and deeply engaging.

#storytelling #creativewriting #narrative #[CORE THEME]
```

## 4. Visual Concept Generation (Original Amir Style)
**Use Case**: Generating high-end, unexpected physical products or visual concepts that embody a brand's DNA.

```text
[BRAND NAME] = [e.g., Nike]
[CORE SUBJECT] = [e.g., coffee mug]

Act as a Visionary Industrial Designer and Master Food Stylist / Luxury Stylist.
Goal: Generate a high-end, glossy concept art magazine editorial photograph of a unique, unexpected functional object conceptualized and designed by the brand.

PHASE 1: ADAPTIVE OBJECT TRANSFORMATION (AUTONOMOUS)
The [CORE SUBJECT], radically reimagined as a physical high-end artifact that embodies the DNA of [BRAND NAME]. The generator must autonomously transform the [CORE SUBJECT] based on the brand's industry (e.g., morphing into a luxury accessory, a futuristic device, or an inviting food item).

PHASE 2: HYPER-TACTILE TEXTURE & SENSORY REALISM
The object must look 100% tangible and physically real. Focus on extreme macro-detail: render the grain of the leather, the cold touch of the metal, or the condensation on a cold drink. Include micro-imperfections to ensure the object looks like a real-world museum piece.

PHASE 3: COMPOSITION & ENVIRONMENT
Place the object in the center of a pure, clinical white studio cyclorama. The object should be medium-sized and levitating slightly, rotated at a dynamic 3D angle (3/4 view). Do not include any external text or floating logos in the frame.

PHASE 4: LIGHTING & SHADOWS
High-key studio lighting with soft, wrapping lights. Elegant specular highlights to define the object's shape. A soft, realistic contact shadow must appear on the white surface below the levitating object.

PHASE 5: TECH SPECS
100mm Macro lens, f/11 for deep focus, Ray Tracing (Path Tracing), Subsurface Scattering, 8k resolution, ultra-clean commercial product photography style.

#visualconcept #design #midjourney #[BRAND NAME]
```
