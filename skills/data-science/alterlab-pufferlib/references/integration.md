# PufferLib Integration Guide

## Overview

PufferLib provides an emulation layer that enables seamless integration with popular RL frameworks including Gymnasium, OpenAI Gym, PettingZoo, and many specialized environment libraries. The emulation layer flattens observation and action spaces for efficient vectorization while maintaining compatibility.

## Gymnasium Integration

### Basic Gymnasium Environments

```python
import gymnasium as gym
import pufferlib.emulation
import pufferlib.vector

# PufferLib has no string registry -- pass an environment constructor
# (callable) to `pufferlib.vector.make`. There is no top-level
# `pufferlib.emulate`/`pufferlib.make`; wrap Gymnasium envs with
# `pufferlib.emulation.GymnasiumPufferEnv`, then vectorize.

# Method 1: Wrap a single Gymnasium env, then vectorize
def cartpole_creator():
    return pufferlib.emulation.GymnasiumPufferEnv(
        env_creator=lambda: gym.make('CartPole-v1'))

env = pufferlib.vector.make(cartpole_creator, num_envs=256)

# Method 2: Same pattern with an inline creator
env = pufferlib.vector.make(
    lambda: pufferlib.emulation.GymnasiumPufferEnv(
        env_creator=lambda: gym.make('CartPole-v1')),
    num_envs=256,
)

# Method 3: Custom Gymnasium environment
class MyGymEnv(gym.Env):
    def __init__(self):
        self.observation_space = gym.spaces.Box(low=-1, high=1, shape=(4,))
        self.action_space = gym.spaces.Discrete(2)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        return self.observation_space.sample(), {}

    def step(self, action):
        obs = self.observation_space.sample()
        reward = 1.0
        terminated = False
        truncated = False
        info = {}
        return obs, reward, terminated, truncated, info

# Wrap custom environment (MyGymEnv is a gym.Env, so emulate it)
env = pufferlib.vector.make(
    lambda: pufferlib.emulation.GymnasiumPufferEnv(env_creator=MyGymEnv),
    num_envs=128,
)
```

### Atari Environments

```python
import functools
import gymnasium as gym
from gymnasium.wrappers import AtariPreprocessing, FrameStack
import pufferlib.emulation
import pufferlib.vector

# Standard Atari setup -- a plain Gymnasium creator
def make_atari_env(env_name='ALE/Pong-v5'):
    env = gym.make(env_name)
    env = AtariPreprocessing(env, frame_skip=4)
    env = FrameStack(env, num_stack=4)
    return env

# Wrap in a GymnasiumPufferEnv, then vectorize
def atari_creator():
    return pufferlib.emulation.GymnasiumPufferEnv(env_creator=make_atari_env)

env = pufferlib.vector.make(atari_creator, num_envs=256)

# Bind a specific game via functools.partial on the Gymnasium creator
pong_creator = lambda: pufferlib.emulation.GymnasiumPufferEnv(
    env_creator=functools.partial(make_atari_env, env_name='ALE/Pong-v5'))
env = pufferlib.vector.make(pong_creator, num_envs=256)
```

### Complex Observation Spaces

```python
import numpy as np
import gymnasium as gym
from gymnasium.spaces import Dict, Box, Discrete
import pufferlib.emulation
import pufferlib.vector

class ComplexObsEnv(gym.Env):
    def __init__(self):
        # Dict observation space
        self.observation_space = Dict({
            'image': Box(low=0, high=255, shape=(84, 84, 3), dtype=np.uint8),
            'vector': Box(low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32),
            'discrete': Discrete(5)
        })
        self.action_space = Discrete(4)

    def reset(self, seed=None, options=None):
        return {
            'image': np.zeros((84, 84, 3), dtype=np.uint8),
            'vector': np.zeros(10, dtype=np.float32),
            'discrete': 0
        }, {}

    def step(self, action):
        obs = {
            'image': np.random.randint(0, 256, (84, 84, 3), dtype=np.uint8),
            'vector': np.random.randn(10).astype(np.float32),
            'discrete': np.random.randint(0, 5)
        }
        return obs, 1.0, False, False, {}

# PufferLib automatically flattens and unflattens complex spaces
env = pufferlib.vector.make(
    lambda: pufferlib.emulation.GymnasiumPufferEnv(env_creator=ComplexObsEnv),
    num_envs=128,
)
```

## PettingZoo Integration

### Parallel Environments

```python
from pettingzoo.butterfly import pistonball_v6
import pufferlib.emulation
import pufferlib.vector

# Multi-agent envs are wrapped with PettingZooPufferEnv, then vectorized.
# PufferLib has no string registry -- pass the constructor (callable).
def pistonball_creator():
    return pufferlib.emulation.PettingZooPufferEnv(
        env_creator=lambda: pistonball_v6.parallel_env())

env = pufferlib.vector.make(pistonball_creator, num_envs=128)
```

### AEC (Agent Environment Cycle) Environments

```python
from pettingzoo.classic import chess_v5
from pettingzoo.utils import aec_to_parallel
import pufferlib.emulation
import pufferlib.vector

# Convert AEC to a parallel env, wrap with PettingZooPufferEnv, then vectorize.
# PufferLib has no string registry -- pass the constructor (callable).
def chess_creator():
    return pufferlib.emulation.PettingZooPufferEnv(
        env_creator=lambda: aec_to_parallel(chess_v5.env()))

env = pufferlib.vector.make(chess_creator, num_envs=64)
```

### Multi-Agent Training

```python
import pufferlib.emulation
import pufferlib.vector
from pufferlib.pufferl import PuffeRL

# Create multi-agent environment.
# PufferLib has no string registry -- pass an environment constructor
# (callable). `kaz_creator` is a placeholder that wraps a PettingZoo env
# (e.g. knights_archers_zombies) with PettingZooPufferEnv.
env = pufferlib.vector.make(kaz_creator, num_envs=128)

# Shared policy for all agents
policy = create_policy(env.observation_space, env.action_space)

# Train
trainer = PuffeRL(env=env, policy=policy)

for iteration in range(num_iterations):
    # Observations are dicts: {agent_id: batch_obs}
    rollout = trainer.evaluate()

    # Train on multi-agent data
    trainer.train()
    trainer.mean_and_log()
```

## Third-Party Environments

### Procgen

```python
import functools
import pufferlib.vector

# PufferLib has no string registry -- pass an environment constructor
# (callable). `make_coinrun` is a placeholder for the Procgen env creator you
# provide (e.g. wrapping the third-party Procgen env); bind kwargs with
# functools.partial.
env = pufferlib.vector.make(
    functools.partial(make_coinrun, distribution_mode='easy'),
    num_envs=256,
)

# Custom configuration
env = pufferlib.vector.make(
    functools.partial(
        make_coinrun,
        num_levels=200,  # Number of unique levels
        start_level=0,   # Starting level seed
        distribution_mode='hard',
    ),
    num_envs=256,
)
```

### NetHack

```python
import pufferlib.vector

# Pass a constructor callable -- there is no string registry.
# make_nethack / make_minihack_* are placeholders for the env creators you
# provide (functions that build the corresponding env).

# NetHack Learning Environment
env = pufferlib.vector.make(make_nethack, num_envs=128)

# MiniHack variants
env = pufferlib.vector.make(make_minihack_corridor, num_envs=128)
env = pufferlib.vector.make(make_minihack_room, num_envs=128)
```

### Minigrid

```python
import pufferlib.vector

# Pass a constructor callable -- there is no string registry.
# make_minigrid_* are placeholders for the env creators you provide.
env = pufferlib.vector.make(make_minigrid_empty_8x8, num_envs=256)
env = pufferlib.vector.make(make_minigrid_doorkey_8x8, num_envs=256)
env = pufferlib.vector.make(make_minigrid_multiroom, num_envs=256)
```

### Neural MMO

```python
import functools
import pufferlib.vector

# Large-scale multi-agent environment.
# Pass a constructor callable -- there is no string registry. `make_neuralmmo`
# is a placeholder for the env creator you provide; bind kwargs with partial.
env = pufferlib.vector.make(
    functools.partial(
        make_neuralmmo,
        num_agents=128,  # Agents per environment
        map_size=128,
    ),
    num_envs=64,
)
```

### Crafter

```python
import pufferlib.vector

# Open-ended crafting environment.
# Pass a constructor callable -- there is no string registry. `make_crafter`
# is a placeholder for the env creator you provide.
env = pufferlib.vector.make(make_crafter, num_envs=128)
```

### GPUDrive

```python
import functools
import pufferlib.vector

# GPU-accelerated driving simulator.
# Pass a constructor callable -- there is no string registry. `make_gpudrive`
# is a placeholder for the env creator you provide; bind kwargs with partial.
env = pufferlib.vector.make(
    functools.partial(make_gpudrive, num_vehicles=8),
    num_envs=1024,  # Can handle many environments on GPU
)
```

### MicroRTS

```python
import functools
import pufferlib.vector

# Real-time strategy game.
# Pass a constructor callable -- there is no string registry. `make_microrts`
# is a placeholder for the env creator you provide; bind kwargs with partial.
env = pufferlib.vector.make(
    functools.partial(make_microrts, map_size=16, max_steps=2000),
    num_envs=128,
)
```

### Griddly

```python
import pufferlib.vector

# Grid-based games.
# Pass a constructor callable -- there is no string registry. make_griddly_*
# are placeholders for the env creators you provide.
env = pufferlib.vector.make(make_griddly_clusters, num_envs=256)
env = pufferlib.vector.make(make_griddly_sokoban, num_envs=256)
```

## Custom Wrappers

### Observation Wrappers

```python
import numpy as np
import pufferlib
from pufferlib import PufferEnv

class NormalizeObservations(pufferlib.Wrapper):
    """Normalize observations to zero mean and unit variance."""

    def __init__(self, env):
        super().__init__(env)
        self.obs_mean = np.zeros(env.observation_space.shape)
        self.obs_std = np.ones(env.observation_space.shape)
        self.count = 0

    def reset(self):
        obs = self.env.reset()
        return self._normalize(obs)

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        return self._normalize(obs), reward, done, info

    def _normalize(self, obs):
        # Update running statistics
        self.count += 1
        delta = obs - self.obs_mean
        self.obs_mean += delta / self.count
        self.obs_std = np.sqrt(((self.count - 1) * self.obs_std ** 2 + delta * (obs - self.obs_mean)) / self.count)

        # Normalize
        return (obs - self.obs_mean) / (self.obs_std + 1e-8)
```

### Reward Wrappers

```python
class RewardShaping(pufferlib.Wrapper):
    """Add shaped rewards to environment."""

    def __init__(self, env, shaping_fn):
        super().__init__(env)
        self.shaping_fn = shaping_fn

    def step(self, action):
        obs, reward, done, info = self.env.step(action)

        # Add shaped reward
        shaped_reward = reward + self.shaping_fn(obs, action)

        return obs, shaped_reward, done, info

# Usage
def proximity_shaping(obs, action):
    """Reward agent for getting closer to goal."""
    goal_pos = np.array([10, 10])
    agent_pos = obs[:2]
    distance = np.linalg.norm(goal_pos - agent_pos)
    return -0.1 * distance

# Pass a constructor callable -- there is no string registry. `make_env`
# is a placeholder for your env creator.
env = pufferlib.vector.make(make_env, num_envs=128)
env = RewardShaping(env, proximity_shaping)
```

### Frame Stacking

```python
class FrameStack(pufferlib.Wrapper):
    """Stack frames for temporal context."""

    def __init__(self, env, num_stack=4):
        super().__init__(env)
        self.num_stack = num_stack
        self.frames = None

    def reset(self):
        obs = self.env.reset()

        # Initialize frame stack
        self.frames = np.repeat(obs[np.newaxis], self.num_stack, axis=0)

        return self._get_obs()

    def step(self, action):
        obs, reward, done, info = self.env.step(action)

        # Update frame stack
        self.frames = np.roll(self.frames, shift=-1, axis=0)
        self.frames[-1] = obs

        if done:
            self.frames = None

        return self._get_obs(), reward, done, info

    def _get_obs(self):
        return self.frames
```

### Action Repeat

```python
class ActionRepeat(pufferlib.Wrapper):
    """Repeat actions for multiple steps."""

    def __init__(self, env, repeat=4):
        super().__init__(env)
        self.repeat = repeat

    def step(self, action):
        total_reward = 0.0
        done = False

        for _ in range(self.repeat):
            obs, reward, done, info = self.env.step(action)
            total_reward += reward

            if done:
                break

        return obs, total_reward, done, info
```

## Space Conversion

### Flattening Spaces

PufferLib automatically flattens complex observation/action spaces:

```python
from gymnasium.spaces import Dict, Box, Discrete
import pufferlib

# Complex space
original_space = Dict({
    'image': Box(0, 255, (84, 84, 3), dtype=np.uint8),
    'vector': Box(-np.inf, np.inf, (10,), dtype=np.float32),
    'discrete': Discrete(5)
})

# Automatically flattened by PufferLib
# Observations are presented as flat arrays for efficient processing
# But can be unflattened when needed for policy processing
```

### Unflattening for Policies

```python
from pufferlib.pytorch import unflatten_observations

class PolicyWithUnflatten(nn.Module):
    def __init__(self, observation_space, action_space):
        super().__init__()
        self.observation_space = observation_space
        # ... policy architecture ...

    def forward(self, flat_observations):
        # Unflatten to original structure
        observations = unflatten_observations(
            flat_observations,
            self.observation_space
        )

        # Now observations is a dict with 'image', 'vector', 'discrete'
        image_features = self.image_encoder(observations['image'])
        vector_features = self.vector_encoder(observations['vector'])
        # ...
```

## Environment Lookup

### Mapping Names to Constructors

PufferLib has no string registry and no `pufferlib.register`/`pufferlib.make`.
If you want name-based lookup, keep your own mapping of names to environment
constructors (callables) and pass the resolved constructor to
`pufferlib.vector.make`:

```python
import functools
import pufferlib.vector
from my_package.envs import MyEnvironment

# Your own registry: name -> constructor (callable)
ENV_REGISTRY = {
    'my-custom-env': functools.partial(MyEnvironment, param1='value1'),
}

# Resolve the name to a constructor, then vectorize
env_creator = ENV_REGISTRY['my-custom-env']
env = pufferlib.vector.make(env_creator, num_envs=256)
```

### Sharing Constructors

To make an environment easy for others to use, simply expose its constructor
(a `PufferEnv` subclass, or a function/`functools.partial` that returns one)
from your package and document the kwargs:

```python
# In my_package/envs.py
def make_my_env(default_param='default_value'):
    return MyEnvironment(param1=default_param)
```

## Compatibility Patterns

### Gymnasium to PufferLib

```python
import gymnasium as gym
import pufferlib.emulation
import pufferlib.vector

# Standard Gymnasium environment
class GymEnv(gym.Env):
    def reset(self, seed=None, options=None):
        return observation, info

    def step(self, action):
        return observation, reward, terminated, truncated, info

# Wrap with GymnasiumPufferEnv, then vectorize (pass a constructor callable)
env = pufferlib.vector.make(
    lambda: pufferlib.emulation.GymnasiumPufferEnv(env_creator=GymEnv),
    num_envs=128,
)
```

### PettingZoo to PufferLib

```python
from pettingzoo import ParallelEnv
import pufferlib.emulation
import pufferlib.vector

# PettingZoo parallel environment
class PZEnv(ParallelEnv):
    def reset(self, seed=None, options=None):
        return {agent: obs for agent, obs in ...}, {agent: info for agent in ...}

    def step(self, actions):
        return observations, rewards, terminations, truncations, infos

# Wrap with PettingZooPufferEnv, then vectorize (pass a constructor callable)
env = pufferlib.vector.make(
    lambda: pufferlib.emulation.PettingZooPufferEnv(env_creator=PZEnv),
    num_envs=128,
)
```

### Legacy Gym (v0.21) to PufferLib

```python
import gym  # Old gym
import pufferlib.emulation
import pufferlib.vector

# Legacy gym environment (returns done instead of terminated/truncated)
class LegacyEnv(gym.Env):
    def reset(self):
        return observation

    def step(self, action):
        return observation, reward, done, info

# Wrap with GymnasiumPufferEnv, then vectorize (pass a constructor callable)
env = pufferlib.vector.make(
    lambda: pufferlib.emulation.GymnasiumPufferEnv(env_creator=LegacyEnv),
    num_envs=128,
)
```

## Performance Considerations

### Efficient Integration

```python
import gymnasium as gym
import pufferlib.emulation
import pufferlib.vector

# Fast: a native PufferEnv constructor (no emulation layer).
# `make_coinrun` is a placeholder for your PufferEnv creator.
env = pufferlib.vector.make(make_coinrun, num_envs=256)

# Slower: Generic Gymnasium wrapper (still fast, but emulation overhead)
env = pufferlib.vector.make(
    lambda: pufferlib.emulation.GymnasiumPufferEnv(
        env_creator=lambda: gym.make('CartPole-v1')),
    num_envs=256,
)

# Slowest: Nested wrappers add overhead
def nested_creator():
    gym_env = gym.make('CartPole-v1')
    gym_env = SomeWrapper(gym_env)
    gym_env = AnotherWrapper(gym_env)
    return pufferlib.emulation.GymnasiumPufferEnv(env_creator=lambda: gym_env)

env = pufferlib.vector.make(nested_creator, num_envs=256)
```

### Minimize Wrapper Overhead

```python
import pufferlib.emulation
import pufferlib.vector

# BAD: Too many wrappers
def bad_creator():
    env = gym.make('CartPole-v1')
    env = Wrapper1(env)
    env = Wrapper2(env)
    env = Wrapper3(env)
    return pufferlib.emulation.GymnasiumPufferEnv(env_creator=lambda: env)

env = pufferlib.vector.make(bad_creator, num_envs=256)

# GOOD: Combine wrapper logic
class CombinedWrapper(gym.Wrapper):
    def step(self, action):
        obs, reward, done, truncated, info = self.env.step(action)
        # Apply all transformations at once
        obs = self._transform_obs(obs)
        reward = self._transform_reward(reward)
        return obs, reward, done, truncated, info

def good_creator():
    env = CombinedWrapper(gym.make('CartPole-v1'))
    return pufferlib.emulation.GymnasiumPufferEnv(env_creator=lambda: env)

env = pufferlib.vector.make(good_creator, num_envs=256)
```

## Debugging Integration

### Verify Environment Compatibility

```python
def test_environment(env, num_steps=100):
    """Test environment for common issues."""
    # Test reset
    obs = env.reset()
    assert env.observation_space.contains(obs), "Invalid initial observation"

    # Test steps
    for _ in range(num_steps):
        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)

        assert env.observation_space.contains(obs), "Invalid observation"
        assert isinstance(reward, (int, float)), "Invalid reward type"
        assert isinstance(done, bool), "Invalid done type"
        assert isinstance(info, dict), "Invalid info type"

        if done:
            obs = env.reset()

    print("✓ Environment passed compatibility test")

# Test before vectorizing
test_environment(MyEnvironment())
```

### Compare Outputs

```python
# Verify PufferLib emulation matches original
import gymnasium as gym
import pufferlib.emulation
import pufferlib.vector
import numpy as np

gym_env = gym.make('CartPole-v1')
puffer_env = pufferlib.vector.make(
    lambda: pufferlib.emulation.GymnasiumPufferEnv(
        env_creator=lambda: gym.make('CartPole-v1')),
    num_envs=1,
)

# Test with same seed
gym_env.reset(seed=42)
puffer_obs = puffer_env.reset()

for _ in range(100):
    action = gym_env.action_space.sample()

    gym_obs, gym_reward, gym_done, gym_truncated, gym_info = gym_env.step(action)
    puffer_obs, puffer_reward, puffer_done, puffer_info = puffer_env.step(np.array([action]))

    # Compare outputs (accounting for batch dimension)
    assert np.allclose(gym_obs, puffer_obs[0])
    assert gym_reward == puffer_reward[0]
    assert gym_done == puffer_done[0]
```
