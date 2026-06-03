# PufferLib Environments Guide

## Overview

PufferLib provides the PufferEnv API for creating high-performance custom environments, and the Ocean suite containing 20+ pre-built environments. Environments support both single-agent and multi-agent scenarios with native vectorization.

## PufferEnv API

### Core Characteristics

PufferEnv is designed for performance through in-place operations:
- Observations, actions, and rewards are initialized from a shared buffer object
- All operations happen in-place to avoid creating and copying arrays
- Native support for both single-agent and multi-agent environments
- Flat observation/action spaces for efficient vectorization

### Creating a PufferEnv

```python
import numpy as np
import gymnasium
import pufferlib
from pufferlib import PufferEnv

class MyEnvironment(PufferEnv):
    def __init__(self, buf=None):
        # Define observation and action spaces BEFORE super().__init__(buf)
        self.single_observation_space = gymnasium.spaces.Dict({
            'image': gymnasium.spaces.Box(
                low=0, high=255, shape=(84, 84, 3), dtype=np.uint8),
            'vector': gymnasium.spaces.Box(
                low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32),
        })
        self.single_action_space = gymnasium.spaces.Discrete(4)  # 4 discrete actions
        self.num_agents = 1

        super().__init__(buf)

    def reset(self, seed=None):
        """Reset environment to initial state. Returns (obs, info-list)."""
        # Reset internal state
        self.agent_pos = np.array([0, 0])
        self.step_count = 0

        # Return initial observation and an (empty) info list
        obs = {
            'image': np.zeros((84, 84, 3), dtype=np.uint8),
            'vector': np.zeros(10, dtype=np.float32)
        }

        return obs, []

    def step(self, action):
        """Execute one environment step. Returns 5 values."""
        # Update state based on action
        self.step_count += 1

        # Calculate reward
        rewards = self._compute_reward()

        # Check termination vs. truncation
        terminals = self._is_done()
        truncations = self.step_count >= 1000

        # Generate observation
        obs = self._get_observation()

        # Additional info (list of dicts, one per agent)
        info = [{'episode': {'r': rewards, 'l': self.step_count}}] if truncations else []

        return obs, rewards, terminals, truncations, info

    def _compute_reward(self):
        """Compute reward for current state."""
        return 1.0

    def _get_observation(self):
        """Generate observation from current state."""
        return {
            'image': np.random.randint(0, 256, (84, 84, 3), dtype=np.uint8),
            'vector': np.random.randn(10).astype(np.float32)
        }
```

### Observation Spaces

Define spaces directly with `gymnasium.spaces` and assign them to
`self.single_observation_space` / `self.single_action_space` before calling
`super().__init__(buf)`.

#### Discrete Spaces

```python
import gymnasium

# Single discrete value
self.single_observation_space = gymnasium.spaces.Discrete(10)  # Values 0-9

# Dict with discrete values
self.single_observation_space = gymnasium.spaces.Dict({
    'position': gymnasium.spaces.Box(
        low=-np.inf, high=np.inf, shape=(1,), dtype=np.float32),  # Continuous
    'type': gymnasium.spaces.Discrete(5),  # Discrete
})
```

#### Continuous Spaces

```python
import gymnasium

# Box spaces (continuous)
self.single_observation_space = gymnasium.spaces.Dict({
    'image': gymnasium.spaces.Box(
        low=0, high=255, shape=(84, 84, 3), dtype=np.uint8),       # Image
    'vector': gymnasium.spaces.Box(
        low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32),  # Vector
    'scalar': gymnasium.spaces.Box(
        low=-np.inf, high=np.inf, shape=(1,), dtype=np.float32),   # Single value
})
```

#### Multi-Discrete Spaces

```python
import gymnasium

# Multiple discrete values
self.single_observation_space = gymnasium.spaces.MultiDiscrete([3, 5, 2])  # 3 values, 5 values, 2 values
```

### Action Spaces

```python
import gymnasium

# Discrete actions
self.single_action_space = gymnasium.spaces.Discrete(4)  # 4 actions: 0, 1, 2, 3

# Continuous actions
self.single_action_space = gymnasium.spaces.Box(
    low=-1.0, high=1.0, shape=(3,), dtype=np.float32)  # 3D continuous action

# Multi-discrete actions
self.single_action_space = gymnasium.spaces.MultiDiscrete([3, 3])  # Two 3-way discrete choices
```

## Multi-Agent Environments

PufferLib has native multi-agent support, treating single-agent and multi-agent environments uniformly.

### Multi-Agent PufferEnv

```python
import gymnasium

class MultiAgentEnv(PufferEnv):
    def __init__(self, num_agents=4, buf=None):
        # Define spaces and num_agents BEFORE super().__init__(buf)
        self.num_agents = num_agents

        # Per-agent observation space
        self.single_observation_space = gymnasium.spaces.Dict({
            'position': gymnasium.spaces.Box(
                low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32),
            'velocity': gymnasium.spaces.Box(
                low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32),
            'global': gymnasium.spaces.Box(
                low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32),
        })

        # Per-agent action space
        self.single_action_space = gymnasium.spaces.Discrete(5)

        super().__init__(buf)

    def reset(self):
        """Reset all agents."""
        self.agents = {f'agent_{i}': Agent(i) for i in range(self.num_agents)}

        # Return observations for all agents
        return {
            agent_id: self._get_obs(agent)
            for agent_id, agent in self.agents.items()
        }

    def step(self, actions):
        """Step all agents."""
        # actions is a dict: {agent_id: action}
        observations = {}
        rewards = {}
        dones = {}
        infos = {}

        for agent_id, action in actions.items():
            agent = self.agents[agent_id]

            # Update agent
            agent.update(action)

            # Generate results
            observations[agent_id] = self._get_obs(agent)
            rewards[agent_id] = self._compute_reward(agent)
            dones[agent_id] = agent.is_done()
            infos[agent_id] = {}

        # Check for global done condition
        dones['__all__'] = all(dones.values())

        return observations, rewards, dones, infos
```

## Ocean Environment Suite

PufferLib provides the Ocean suite with 20+ pre-built environments:

### Available Environments

#### Arcade Games
- **Atari**: Classic Atari 2600 games via Arcade Learning Environment
- **Procgen**: Procedurally generated games for generalization testing

#### Grid-Based
- **Minigrid**: Partially observable gridworld environments
- **Crafter**: Open-ended survival crafting game
- **NetHack**: Classic roguelike dungeon crawler
- **MiniHack**: Simplified NetHack variants

#### Multi-Agent
- **PettingZoo**: Multi-agent environment suite (including Butterfly)
- **MAgent**: Large-scale multi-agent scenarios
- **Neural MMO**: Massively multi-agent survival game

#### Specialized
- **Pokemon Red**: Classic Pokemon game environment
- **GPUDrive**: High-performance driving simulator
- **Griddly**: Grid-based game engine
- **MicroRTS**: Real-time strategy game

### Using Ocean Environments

```python
import functools
import pufferlib.vector

# Vectorize an env-constructor callable
env = pufferlib.vector.make(make_coinrun_env, num_envs=256)

# With custom configuration (bind constructor kwargs via functools.partial)
env = pufferlib.vector.make(
    functools.partial(make_pong_env, frameskip=4, framestack=4),
    num_envs=128,
)

# Multi-agent environment
env = pufferlib.vector.make(make_knights_archers_zombies_env, num_envs=4)
```

## Custom Environment Development

### Development Workflow

1. **Prototype in Python**: Start with pure Python PufferEnv
2. **Optimize Critical Paths**: Identify bottlenecks
3. **Implement in C**: Rewrite performance-critical code in C
4. **Create Bindings**: Use Python C API
5. **Compile**: Build as extension module
6. **Register**: Add to Ocean suite

### Performance Benchmarks

- **Pure Python**: 100k-500k steps/second
- **C Implementation**: 100M+ steps/second
- **Training with Python env**: ~400k total SPS
- **Training with C env**: ~4M total SPS

### Python Optimization Tips

```python
# Use NumPy operations instead of Python loops
# Bad
for i in range(len(array)):
    array[i] = array[i] * 2

# Good
array *= 2

# Pre-allocate arrays instead of appending
# Bad
observations = []
for i in range(n):
    observations.append(generate_obs())

# Good
observations = np.empty((n, obs_shape), dtype=np.float32)
for i in range(n):
    observations[i] = generate_obs()

# Use in-place operations
# Bad
new_state = state + delta

# Good
state += delta
```

### C Extension Example

```c
// my_env.c
#include <Python.h>
#include <numpy/arrayobject.h>

// Fast environment step implementation
static PyObject* fast_step(PyObject* self, PyObject* args) {
    PyArrayObject* state;
    int action;

    if (!PyArg_ParseTuple(args, "O!i", &PyArray_Type, &state, &action)) {
        return NULL;
    }

    // High-performance C implementation
    // ...

    return Py_BuildValue("Ofi", obs, reward, done);
}

static PyMethodDef methods[] = {
    {"fast_step", fast_step, METH_VARARGS, "Fast environment step"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "my_env_c",
    NULL,
    -1,
    methods
};

PyMODINIT_FUNC PyInit_my_env_c(void) {
    import_array();
    return PyModule_Create(&module);
}
```

## Third-Party Environment Integration

### Gymnasium Environments

```python
import gymnasium as gym
import pufferlib.emulation
import pufferlib.vector

# Wrap a Gymnasium env in a GymnasiumPufferEnv, then vectorize
def env_creator():
    return pufferlib.emulation.GymnasiumPufferEnv(
        env_creator=lambda: gym.make('CartPole-v1'))

env = pufferlib.vector.make(env_creator, num_envs=256)
```

### PettingZoo Environments

```python
from pettingzoo.butterfly import pistonball_v6
import pufferlib.emulation
import pufferlib.vector

# Wrap a PettingZoo env in a PettingZooPufferEnv, then vectorize
def env_creator():
    return pufferlib.emulation.PettingZooPufferEnv(
        env_creator=lambda: pistonball_v6.parallel_env())

env = pufferlib.vector.make(env_creator, num_envs=128)
```

### Custom Wrappers

```python
class CustomWrapper(pufferlib.PufferEnv):
    """Wrapper to modify environment behavior."""

    def __init__(self, base_env, buf=None):
        super().__init__(buf)
        self.base_env = base_env
        self.observation_space = base_env.observation_space
        self.action_space = base_env.action_space

    def reset(self):
        obs = self.base_env.reset()
        # Modify observation
        return self._process_obs(obs)

    def step(self, action):
        # Modify action
        modified_action = self._process_action(action)

        obs, reward, done, info = self.base_env.step(modified_action)

        # Modify outputs
        obs = self._process_obs(obs)
        reward = self._process_reward(reward)

        return obs, reward, done, info
```

## Environment Best Practices

### State Management

```python
# Store minimal state, compute on demand
class EfficientEnv(PufferEnv):
    def __init__(self, buf=None):
        super().__init__(buf)
        self.agent_pos = np.zeros(2)  # Minimal state

    def _get_observation(self):
        # Compute full observation on demand
        observation = np.zeros((84, 84, 3), dtype=np.uint8)
        self._render_scene(observation, self.agent_pos)
        return observation
```

### Reward Scaling

```python
# Normalize rewards to reasonable range
def step(self, action):
    # ... environment logic ...

    # Scale large rewards
    raw_reward = compute_raw_reward()
    reward = np.clip(raw_reward / 100.0, -10, 10)

    return obs, reward, done, info
```

### Episode Termination

```python
def step(self, action):
    # ... environment logic ...

    # Multiple termination conditions
    timeout = self.step_count >= self.max_steps
    success = self._check_success()
    failure = self._check_failure()

    done = timeout or success or failure

    info = {
        'TimeLimit.truncated': timeout,
        'success': success
    }

    return obs, reward, done, info
```

### Memory Efficiency

```python
# Reuse buffers instead of allocating new ones
class MemoryEfficientEnv(PufferEnv):
    def __init__(self, buf=None):
        super().__init__(buf)

        # Pre-allocate observation buffer
        self._obs_buffer = np.zeros((84, 84, 3), dtype=np.uint8)

    def _get_observation(self):
        # Reuse buffer, modify in place
        self._render_scene(self._obs_buffer)
        return self._obs_buffer  # Return view, not copy
```

## Debugging Environments

### Validation Checks

```python
# Add assertions to catch bugs
def step(self, action):
    assert self.action_space.contains(action), f"Invalid action: {action}"

    obs, reward, done, info = self._step_impl(action)

    assert self.observation_space.contains(obs), "Invalid observation"
    assert np.isfinite(reward), "Non-finite reward"

    return obs, reward, done, info
```

### Rendering

```python
class DebuggableEnv(PufferEnv):
    def __init__(self, buf=None, render_mode=None):
        super().__init__(buf)
        self.render_mode = render_mode

    def render(self):
        """Render environment for debugging."""
        if self.render_mode == 'human':
            # Display to screen
            self._display_scene()
        elif self.render_mode == 'rgb_array':
            # Return image
            return self._render_to_array()
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def step(self, action):
    logger.debug(f"Step {self.step_count}: action={action}")

    obs, reward, done, info = self._step_impl(action)

    if done:
        logger.info(f"Episode finished: reward={self.total_reward}")

    return obs, reward, done, info
```
