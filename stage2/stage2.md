
# Project AXIOGEN: Stage 2 Report
**Topic:** Emergence of Intrinsic Motivation and Spatial Memory (The Hippocampus Simulation).
**Date:** January 2026
**Status:** Stage 2 Complete (Exploration & Mapping Solved)

---

## 1. Abstract
In Stage 2 of **Project AXIOGEN**, the objective was to shift the agent's behavior from a "Narrow Specialist" (the Stage 1 Wolf) to a "General Explorer" (the Stage 2 Scientist). By removing external food rewards and replacing them with a **Novelty-Seeking Fitness Function**, we observed the emergence of systematic area-coverage patterns. This stage confirms that curiosity—modeled as a drive to minimize uncertainty in a spatial map—can be evolved as a core "Base Code" instinct.

---

## 2. Methodology & Architecture

### The Curiosity Engine
*   **Environment:** A procedurally generated maze with random internal walls, ensuring the agent cannot memorize a single static map.
*   **Memory Grid (The Hippocampus):** The world was divided into a $20 \times 20$ pixel grid. 
*   **Fitness Function (Intrinsic Reward):** 
    *   `+15` points for every **unique** grid sector visited.
    *   `-0.05` points per frame for retreading old ground (Boredom).
    *   `-1.0` point for wall collisions (Pain).

### The Boredom Timer (Stagnation Logic)
To prevent "Wall Hugging" or "Camping," a **Stagnation Timer** was implemented. If an agent failed to discover a new grid sector within 150 frames (~2.5 seconds), it was terminated. This forced a "Permanent Exploration" state.

---

## 3. The Transfer Learning Experiment

A critical component of Stage 2 was the injection of the **Stage 1 "Wolf" Brain** into the new **Explorer** population.

### Observation: Sensor Inversion Shock
Initial attempts at transfer learning resulted in high mortality rates. Because the Stage 1 brain interpreted high sensor values as "Target/Food," the agents initially charged directly into walls (Suicide). 

### Adaptation: The Bumper Physics Phase
To allow the neural network to "re-wire" its logic without instant extinction, we implemented **Bumper Physics** (non-lethal wall repulsion). This allowed the agents to survive long enough to realize that a sensor spike now represented **Obstacles**, not **Opportunities**. Within 10 generations of this adjustment, the agents successfully inverted their logic, moving from "Target Seeking" to "Obstacle Avoidance" while maintaining their superior motor control.

---

## 4. Data Analysis & Results

### Evolutionary Progress
| Generation | Max Exploration | Behavior Observed |
| :--- | :--- | :--- |
| **Gen 1** | ~78 | High-speed crashes, chaotic bouncing. |
| **Gen 2** | **4033.0** | **Convergence Spike.** Systemic room clearing. |
| **Gen 5** | -174 | Catastrophic Mutation (Species-wide collapse). |
| **Gen 9** | **3567.2** | Stable recovery. Mastery of complex maze navigation. |

### The "Roomba" Phenomenon
By Gen 9, the agents developed a high-efficiency scanning pattern. They utilized their inherited Stage 1 speed to sprint through corridors, using a "Wall-Following" heuristic to ensure no corner of the grid remained unpainted (Blue). The max fitness of **4033** represents a near-total coverage of the available 2D space within the 20-second time limit.

---

## 5. Conclusion of Stage 2
We have successfully evolved a **"Digital Scientist."**
The saved model (`axiogen_stage2_AUTOSAVE.pkl`) has successfully integrated its Stage 1 "Motor Cortex" with a new Stage 2 "Spatial Memory."

**Key Findings:**
1.  **Instinct Persistence:** The motor skills (drifting, acceleration) from Stage 1 remained intact despite the change in goal.
2.  **Curiosity as a Survival Drive:** By making "Boredom" lethal, we forced the emergence of a scanning algorithm that outperforms human-designed heuristic search in this environment.
3.  **Logical Re-wiring:** The brain proved capable of re-interpreting the *meaning* of its sensors (Food $\rightarrow$ Wall) while keeping the *syntax* of the math (Trigonometry/Physics) consistent.

---

## 6. Next Steps: Stage 3 (The Architect)
Stage 1 and 2 were "Reactive." Stage 3 introduces **Conditional Logic**.
*   **Objective:** Solve a sequential puzzle (The Switch and the Gate).
*   **New Input:** Internal State (Binary bit: 0 = Searching for Switch, 1 = Searching for Goal).
*   **Goal:** To evolve the "Kernel Logic" of the OS—the ability to hold a mental state and change behavior based on that state.