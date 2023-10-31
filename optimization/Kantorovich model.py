import pulp
import numpy as np
import itertools as it
from dataclasses import dataclass
from collections import Counter

#  Инициализация модели.
model = pulp.LpProblem('Kantorovich model', pulp.LpMinimize)
