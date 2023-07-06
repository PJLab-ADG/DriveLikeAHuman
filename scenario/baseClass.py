from typing import List, Dict, Tuple, Union
from dataclasses import dataclass, field
from math import sqrt


@dataclass
class Lane:
    id: str
    laneIdx: int
    left_lanes: List[str] = field(default_factory=list)
    right_lanes: List[str] = field(default_factory=list)

    def export2json(self):
        return {
            'id': self.id,
            'lane index': self.laneIdx,
            'left_lanes': self.left_lanes,
            'right_lanes': self.right_lanes,
        }


@dataclass
class Vehicle:
    id: str
    lane_id: str = ''
    x: float = 0.0
    y: float = 0.0
    speedx: float = 0.0
    speedy: float = 0.0
    presence: bool = False

    def clear(self) -> None:
        self.lane_id = ''
        self.x = 0.0
        self.y = 0.0
        self.speedx = 0.0
        self.speedy = 0.0
        self.presence = False

    def updateProperty(
        self, x: float, y: float, vx: float, vy: float
    ) -> None:
        self.x = x
        self.y = y
        self.speedx = vx
        self.speedy = vy
        laneIdx = round(y/4.0)
        self.lane_id = 'lane_' + str(laneIdx)

    @property
    def speed(self) -> float:
        return sqrt(pow(self.speedx, 2) + pow(self.speedy, 2))

    @property
    def lanePosition(self) -> float:
        return self.x

    def export2json(self) -> Dict:
        return {
            'id': self.id,
            'current lane': self.lane_id,
            # float() is used to transfer np.float32 to float, since np.float32
            # can not be serialized by JSON
            'lane position': round(float(self.x), 2),
            'speed': round(float(self.speed), 2),
        }
