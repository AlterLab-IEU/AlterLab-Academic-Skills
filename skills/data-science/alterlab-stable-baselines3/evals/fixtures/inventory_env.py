"""Single-product inventory environment (periodic review, lost sales).

Each step is one week. The agent sees its stock on hand, the order still in transit
and last week's demand, and chooses how much to order (0, 10, ..., 100 units). Orders
arrive after a one-week lead time. Weekly demand is Poisson with a seasonal mean.

Reward per week = -(holding cost + lost-sales penalty + ordering cost).
An episode is one 52-week year.
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces


class InventoryEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, capacity=500, holding_cost=0.5, lost_sale_cost=4.0,
                 order_fixed_cost=20.0, unit_cost=1.0, horizon=52):
        super().__init__()
        self.capacity = capacity
        self.holding_cost = holding_cost
        self.lost_sale_cost = lost_sale_cost
        self.order_fixed_cost = order_fixed_cost
        self.unit_cost = unit_cost
        self.horizon = horizon

        # order 0, 10, ..., 100 units
        self.action_space = spaces.Discrete(11)
        # [on_hand, in_transit, last_demand]
        self.observation_space = spaces.Box(
            low=0.0, high=float(capacity), shape=(3,), dtype=np.float32
        )

    def _mean_demand(self, week):
        return 40.0 + 15.0 * np.sin(2 * np.pi * week / 52.0)

    def _get_obs(self):
        return np.array([self.on_hand, self.in_transit, self.last_demand])

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.week = 0
        self.on_hand = 100
        self.in_transit = 0
        self.last_demand = 40
        return self._get_obs(), {}

    def step(self, action):
        order_qty = int(action) * 10

        # last week's order arrives (capacity-limited), then demand is served
        self.on_hand = min(self.on_hand + self.in_transit, self.capacity)
        self.in_transit = order_qty
        demand = int(self.np_random.poisson(self._mean_demand(self.week)))
        sold = min(demand, self.on_hand)
        lost = demand - sold
        self.on_hand -= sold
        self.last_demand = min(demand, self.capacity)

        cost = (self.holding_cost * self.on_hand
                + self.lost_sale_cost * lost
                + (self.order_fixed_cost + self.unit_cost * order_qty if order_qty > 0 else 0.0))
        reward = -float(cost)

        self.week += 1
        terminated = False
        truncated = self.week >= self.horizon
        info = {"demand": demand, "lost_sales": lost}
        return self._get_obs(), reward, terminated, truncated, info
