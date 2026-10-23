# ISCProof Octopus Architecture
Version: 1.0
Status: FROZEN
Date: 2026-03-24

## Model

One brain. Independent arms. One proof system.

Brain → ISCProof motor + policy
Arms  → specialized agents, each independent

## Brain

The brain does not execute.
The brain defines:
- what is valid
- what must be sealed
- how trust is established
- what chain rules apply

Brain = ISCProof protocol + Trust Foundation

## Arms

Each arm:
- operates independently
- makes its own decisions
- produces its own seal
- references parent seals
- reports to no one — proof speaks

Current arms:
- Ali          → outreach agent
- CEO agent    → reporting agent
- Deploy agent → build/release agent (planned)
- Monitor agent → health agent (planned)
- Spec agent   → documentation agent (planned)

## Properties

Parallel execution:
Arms can run simultaneously.
No arm waits for another.

Independent failure:
One arm fails → others continue.
Failure is local, not systemic.

Shared proof system:
All arms use ISCProof motor.
All seals follow same format.
All decisions follow Agent Decision Model.

Extensible:
New arm = new agent.
No changes to brain required.
No changes to other arms required.

## Chain Rule

Every arm seal MUST:
- identify the agent (who)
- state the reason (why)
- describe the action (what)
- hash the output (output_hash)
- reference prior seals (input_seals)
- carry timestamp (RFC 3161)
- carry signature (Ed25519)

## One Sentence

ISCProof Octopus Architecture:
Independent specialized agents operate autonomously,
each sealing their own decisions and actions,
all connected through one proof motor.

## Implementation Note

Current state:
- Brain → ISCProof V4, Trust Foundation, Agent Decision Model
- Arm 1 → Ali (partial, mail proof added)
- Arm 2 → CEO agent (full, agent proof sealed)

Next arms: Deploy, Monitor, Spec
Full implementation: after laptop
