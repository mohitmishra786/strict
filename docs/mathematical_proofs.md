# Mathematical Foundations

This document provides the mathematical proofs and derivations for the core formulas implemented in Rough.

---

## 1. Validation Function

### Definition

The validation function transforms raw input into a validated model:

$$
\text{Output} = f_{\text{validate}}(\text{Model}(x), \text{Schema})
$$

Where:
- $x$ is the raw input (dictionary, JSON, etc.)
- $\text{Model}(x)$ is the attempt to construct a model from $x$
- $\text{Schema}$ is the Pydantic model class defining valid structure
- $\text{Output}$ is either the validated model or an error

### Formal Definition

Let $\mathcal{X}$ be the space of all possible raw inputs, and $\mathcal{M}$ be the space of valid models.

The validation function $f_{\text{validate}}: \mathcal{X} \times \mathcal{S} \to \mathcal{M} \cup \{\bot\}$ is defined as:

$$
f_{\text{validate}}(x, S) = 
\begin{cases}
m & \text{if } x \text{ satisfies all constraints in } S \\
\bot & \text{otherwise}
\end{cases}
$$

Where $\bot$ represents validation failure with associated error messages.

### Properties

1. **Idempotence**: $f_{\text{validate}}(f_{\text{validate}}(x, S), S) = f_{\text{validate}}(x, S)$
2. **Determinism**: Same input always produces same output
3. **Type Safety**: Output is guaranteed to satisfy schema constraints

---

## 2. System Success Probability

### Derivation

For a system with cloud and local redundancy:

$$
P(\text{System Success}) = 1 - P(\text{System Failure})
$$

System fails only if both cloud AND local fail:

$$
P(\text{System Failure}) = P(\text{Cloud Fail}) \times P(\text{Local Fail})
$$

Therefore:

$$
\boxed{P(\text{System Success}) = 1 - (P(\text{Cloud Fail}) \times P(\text{Local Fail}))}
$$

### Example Calculation

Given:
- $P(\text{Cloud Fail}) = 0.01$ (1% failure rate)
- $P(\text{Local Fail}) = 0.05$ (5% failure rate)

Then:
$$
\begin{align}
P(\text{System Success}) &= 1 - (0.01 \times 0.05) \\
&= 1 - 0.0005 \\
&= 0.9995 \\
&= 99.95\%
\end{align}
$$

### Assumptions

1. Cloud and local failures are independent events
2. Failover mechanism itself has negligible failure probability
3. Detection of cloud failure is instantaneous

---

## 3. Nyquist Criterion

### Statement

To accurately sample a signal with maximum frequency $f_{\text{max}}$:

$$
f_s > 2 \cdot f_{\text{max}}
$$

Where $f_s$ is the sampling rate.

### Nyquist Frequency

The Nyquist frequency is the highest frequency that can be accurately represented:

$$
f_{\text{Nyquist}} = \frac{f_s}{2}
$$

### Implementation Constraint

In Rough, we enforce:

$$
f_s > 2 \cdot f_{\text{signal}}
$$

This is validated in the `SignalConfig` model via `@model_validator`.

---

## 4. System Availability

### Single Component

For a single component with Mean Time Between Failures (MTBF) and Mean Time To Repair (MTTR):

$$
A = \frac{\text{MTBF}}{\text{MTBF} + \text{MTTR}}
$$

### Parallel (Redundant) Systems

For $n$ components in parallel, the combined availability is:

$$
A_{\text{parallel}} = 1 - \prod_{i=1}^{n}(1 - A_i)
$$

The system fails only if ALL components fail.

### Series Systems

For $n$ components in series, the combined availability is:

$$
A_{\text{series}} = \prod_{i=1}^{n} A_i
$$

The system fails if ANY component fails.

---

## 5. Token-Based Routing

### Decision Rule

The processor routing decision is based on token count $t$ and threshold $\tau$:

$$
\text{Processor} = 
\begin{cases}
\text{cloud} & \text{if } t > \tau \\
\text{local} & \text{if } t \leq \tau
\end{cases}
$$

Default threshold: $\tau = 500$ tokens.

### Rationale

- Cloud processors (e.g., GPT-4) handle long contexts better
- Local processors (e.g., spaCy) are faster for short inputs
- Threshold balances latency and capability

---

## References

1. Shannon, C.E. (1949). "Communication in the Presence of Noise"
2. Pydantic V2 Documentation: https://docs.pydantic.dev/latest/
3. "Parse, Don't Validate" by Alexis King
