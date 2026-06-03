#!/usr/bin/env python3
"""
PufferLib Environment Template

This template provides a starting point for creating custom PufferEnv environments.
Customize the observation space, action space, and environment logic for your task.
"""

import numpy as np
import gymnasium
import pufferlib
from pufferlib import PufferEnv


class MyEnvironment(PufferEnv):
    """
    Custom PufferLib environment template.

    This is a simple grid world example. Customize it for your specific task.
    """

    def __init__(self, buf=None, grid_size=10, max_steps=1000):
        """
        Initialize environment.

        Args:
            buf: Shared memory buffer (managed by PufferLib)
            grid_size: Size of the grid world
            max_steps: Maximum steps per episode
        """
        self.grid_size = grid_size
        self.max_steps = max_steps

        # Define spaces and num_agents BEFORE calling super().__init__(buf)

        # Define observation space
        # Option 1: Flat vector observation
        self.single_observation_space = gymnasium.spaces.Box(
            low=-np.inf, high=np.inf, shape=(4,), dtype=np.float32)  # [x, y, goal_x, goal_y]

        # Option 2: Dict observation with multiple components
        # self.single_observation_space = gymnasium.spaces.Dict({
        #     'position': gymnasium.spaces.Box(
        #         low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32),
        #     'goal': gymnasium.spaces.Box(
        #         low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32),
        #     'grid': gymnasium.spaces.Box(
        #         low=0, high=1, shape=(grid_size, grid_size), dtype=np.float32),
        # })

        # Option 3: Image observation
        # self.single_observation_space = gymnasium.spaces.Box(
        #     low=0, high=255, shape=(grid_size, grid_size, 3), dtype=np.uint8)

        # Define action space
        # Option 1: Discrete actions
        self.single_action_space = gymnasium.spaces.Discrete(4)  # 0: up, 1: right, 2: down, 3: left

        # Option 2: Continuous actions
        # self.single_action_space = gymnasium.spaces.Box(
        #     low=-1.0, high=1.0, shape=(2,), dtype=np.float32)  # [dx, dy]

        # Option 3: Multi-discrete actions
        # self.single_action_space = gymnasium.spaces.MultiDiscrete([3, 3])  # Two 3-way choices

        self.num_agents = 1

        # Initialize state
        self.agent_pos = None
        self.goal_pos = None
        self.step_count = 0

        super().__init__(buf)

    def reset(self, seed=None):
        """
        Reset environment to initial state.

        Returns:
            observation: Initial observation
            info: List of info dicts (one per agent); empty list here
        """
        # Reset state
        self.agent_pos = np.array([0, 0], dtype=np.float32)
        self.goal_pos = np.array([self.grid_size - 1, self.grid_size - 1], dtype=np.float32)
        self.step_count = 0

        # Return initial observation and an (empty) info list
        return self._get_observation(), []

    def step(self, action):
        """
        Execute one environment step.

        Args:
            action: Action to take

        Returns:
            observation: New observation
            reward: Reward for this step
            terminal: Whether episode terminated (goal/failure)
            truncation: Whether episode was truncated (time limit)
            info: List of info dicts (one per agent)
        """
        self.step_count += 1

        # Execute action
        self._apply_action(action)

        # Compute reward
        reward = self._compute_reward()

        # Episode terminates on goal; truncates on the step limit
        terminal = self._is_terminated()
        truncation = self.step_count >= self.max_steps

        # Get new observation
        observation = self._get_observation()

        # Additional info (list of dicts, one per agent)
        info = []
        if terminal or truncation:
            # Include episode statistics when episode ends
            info.append({'episode': {
                'r': reward,
                'l': self.step_count
            }})

        return observation, reward, terminal, truncation, info

    def _apply_action(self, action):
        """Apply action to update environment state."""
        # Discrete actions: 0=up, 1=right, 2=down, 3=left
        if action == 0:  # Up
            self.agent_pos[1] = min(self.agent_pos[1] + 1, self.grid_size - 1)
        elif action == 1:  # Right
            self.agent_pos[0] = min(self.agent_pos[0] + 1, self.grid_size - 1)
        elif action == 2:  # Down
            self.agent_pos[1] = max(self.agent_pos[1] - 1, 0)
        elif action == 3:  # Left
            self.agent_pos[0] = max(self.agent_pos[0] - 1, 0)

    def _compute_reward(self):
        """Compute reward for current state."""
        # Distance to goal
        distance = np.linalg.norm(self.agent_pos - self.goal_pos)

        # Reward shaping: negative distance + bonus for reaching goal
        reward = -distance / self.grid_size

        # Goal reached
        if distance < 0.5:
            reward += 10.0

        return reward

    def _is_terminated(self):
        """Check if episode terminated (goal reached). Timeout is a truncation, handled in step()."""
        distance = np.linalg.norm(self.agent_pos - self.goal_pos)
        goal_reached = distance < 0.5

        return goal_reached

    def _get_observation(self):
        """Generate observation from current state."""
        # Return flat vector observation
        observation = np.concatenate([
            self.agent_pos,
            self.goal_pos
        ]).astype(np.float32)

        return observation


class MultiAgentEnvironment(PufferEnv):
    """
    Multi-agent environment template.

    Example: Cooperative navigation task where agents must reach individual goals.
    """

    def __init__(self, buf=None, num_agents=4, grid_size=10, max_steps=1000):
        # Define spaces and num_agents BEFORE calling super().__init__(buf)
        self.num_agents = num_agents
        self.grid_size = grid_size
        self.max_steps = max_steps

        # Per-agent observation space
        self.single_observation_space = gymnasium.spaces.Dict({
            'position': gymnasium.spaces.Box(
                low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32),
            'goal': gymnasium.spaces.Box(
                low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32),
            'others': gymnasium.spaces.Box(
                low=-np.inf, high=np.inf,
                shape=(2 * (num_agents - 1),), dtype=np.float32),  # Positions of other agents
        })

        # Per-agent action space
        self.single_action_space = gymnasium.spaces.Discrete(5)  # 4 directions + stay

        # Initialize state
        self.agent_positions = None
        self.goal_positions = None
        self.step_count = 0

        super().__init__(buf)

    def reset(self):
        """Reset all agents."""
        # Random initial positions
        self.agent_positions = np.random.rand(self.num_agents, 2) * self.grid_size

        # Random goal positions
        self.goal_positions = np.random.rand(self.num_agents, 2) * self.grid_size

        self.step_count = 0

        # Return observations for all agents
        return {
            f'agent_{i}': self._get_obs(i)
            for i in range(self.num_agents)
        }

    def step(self, actions):
        """
        Step all agents.

        Args:
            actions: Dict of {agent_id: action}

        Returns:
            observations: Dict of {agent_id: observation}
            rewards: Dict of {agent_id: reward}
            dones: Dict of {agent_id: done}
            infos: Dict of {agent_id: info}
        """
        self.step_count += 1

        observations = {}
        rewards = {}
        dones = {}
        infos = {}

        # Update all agents
        for agent_id, action in actions.items():
            agent_idx = int(agent_id.split('_')[1])

            # Apply action
            self._apply_action(agent_idx, action)

            # Generate outputs
            observations[agent_id] = self._get_obs(agent_idx)
            rewards[agent_id] = self._compute_reward(agent_idx)
            dones[agent_id] = self._is_done(agent_idx)
            infos[agent_id] = {}

        # Global done condition
        dones['__all__'] = all(dones.values()) or self.step_count >= self.max_steps

        return observations, rewards, dones, infos

    def _apply_action(self, agent_idx, action):
        """Apply action for specific agent."""
        if action == 0:  # Up
            self.agent_positions[agent_idx, 1] += 1
        elif action == 1:  # Right
            self.agent_positions[agent_idx, 0] += 1
        elif action == 2:  # Down
            self.agent_positions[agent_idx, 1] -= 1
        elif action == 3:  # Left
            self.agent_positions[agent_idx, 0] -= 1
        # action == 4: Stay

        # Clip to grid bounds
        self.agent_positions[agent_idx] = np.clip(
            self.agent_positions[agent_idx],
            0,
            self.grid_size - 1
        )

    def _compute_reward(self, agent_idx):
        """Compute reward for specific agent."""
        distance = np.linalg.norm(
            self.agent_positions[agent_idx] - self.goal_positions[agent_idx]
        )
        return -distance / self.grid_size

    def _is_done(self, agent_idx):
        """Check if specific agent is done."""
        distance = np.linalg.norm(
            self.agent_positions[agent_idx] - self.goal_positions[agent_idx]
        )
        return distance < 0.5

    def _get_obs(self, agent_idx):
        """Get observation for specific agent."""
        # Get positions of other agents
        other_positions = np.concatenate([
            self.agent_positions[i]
            for i in range(self.num_agents)
            if i != agent_idx
        ])

        return {
            'position': self.agent_positions[agent_idx].astype(np.float32),
            'goal': self.goal_positions[agent_idx].astype(np.float32),
            'others': other_positions.astype(np.float32)
        }


def test_environment():
    """Test environment to verify it works correctly."""
    print("Testing single-agent environment...")
    env = MyEnvironment()

    obs, info = env.reset()
    print(f"Initial observation shape: {obs.shape}")

    for step in range(10):
        action = env.single_action_space.sample()
        obs, reward, terminal, truncation, info = env.step(action)

        print(f"Step {step}: reward={reward:.3f}, terminal={terminal}, truncation={truncation}")

        if terminal or truncation:
            obs, info = env.reset()
            print("Episode finished, resetting...")

    print("\nTesting multi-agent environment...")
    multi_env = MultiAgentEnvironment(num_agents=4)

    obs = multi_env.reset()
    print(f"Number of agents: {len(obs)}")

    for step in range(10):
        actions = {
            agent_id: multi_env.single_action_space.sample()
            for agent_id in obs.keys()
        }
        obs, rewards, dones, infos = multi_env.step(actions)

        print(f"Step {step}: mean_reward={np.mean(list(rewards.values())):.3f}")

        if dones.get('__all__', False):
            obs = multi_env.reset()
            print("Episode finished, resetting...")

    print("\n✓ Environment tests passed!")


if __name__ == '__main__':
    test_environment()
