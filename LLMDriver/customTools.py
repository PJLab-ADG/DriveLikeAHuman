from scenario.scenario import Scenario
from typing import Any


def prompts(name, description):
    def decorator(func):
        func.name = name
        func.description = description
        return func

    return decorator


ACTIONS_ALL = {
    0: 'LANE_LEFT',
    1: 'IDLE',
    2: 'LANE_RIGHT',
    3: 'FASTER',
    4: 'SLOWER'
}

ACTIONS_DESCRIPTION = {
    0: 'change lane to the left of the current lane,',
    1: 'remain in the current lane with current speed',
    2: 'change lane to the right of the current lane',
    3: 'accelerate the vehicle',
    4: 'decelerate the vehicle'
}


class getAvailableActions:
    def __init__(self, env: Any) -> None:
        self.env = env

    @prompts(name='Get Available Actions',
             description="""Useful before you make decisions, this tool let you know what are your available actions in this situation. The input to this tool should be 'ego'.""")
    def inference(self, input: str) -> str:
        outputPrefix = 'You can ONLY use one of the following actions: \n'
        availableActions = self.env.get_available_actions()
        for action in availableActions:
            outputPrefix += ACTIONS_ALL[action] + \
                '--' + ACTIONS_DESCRIPTION[action] + '; \n'
        if 1 in availableActions:
            outputPrefix += 'You should check idle action as FIRST priority. '
        if 0 in availableActions or 2 in availableActions:
            outputPrefix += 'For change lane action, CAREFULLY CHECK the safety of vehicles on target lane. '
        if 3 in availableActions:
            outputPrefix += 'Consider acceleration action carefully. '
        if 4 in availableActions:
            outputPrefix += 'The deceleration action is LAST priority. '
        outputPrefix += """\nTo check decision safety you should follow steps:
        Step 1: Get the vehicles in this lane that you may affect. Acceleration, deceleration and idle action affect the current lane, while left and right lane changes affect the corresponding lane.
        Step 2: If there are vehicles, check safety between ego and all vehicles in the action lane ONE by ONE.
        Remember to use the proper tools mentioned in the tool list ONCE a time.
        """
        return outputPrefix


class isActionSafe:
    def __init__(self) -> None:
        pass

    # @prompts(name='Check Action Safety',
    #          description="""Use this tool when you want to check the proposed action's safety. The input to this tool should be a string, which is ONLY the action name.""")
    @prompts(name='Decision-making Instructions',
             description="""This tool gives you a brief intruduction about how to ensure that the action you make is safe. The input to this tool should be a string, which is ONLY the action name.""")
    def inference(self, action: str) -> str:
        return f"""To check action safety you should follow three steps:
        Step 1: Identify the lanes affected by this action. Acceleration, deceleration and idle affect the current lane, while left and right lane changes affect the corresponding lane.
        Step 2:(Optional) Get the vehicles in this lane that you may affect, ONLY when you don't know.
        Step 3: If there are vehicles, check safety between ego and all vehicles in the action lane ONE by ONE.
        Follow the instructions and remember to use the proper tools mentioned in the tool list once a time.
        """


class getAvailableLanes:
    def __init__(self, sce: Scenario) -> None:
        self.sce = sce

    @prompts(name='Get Available Lanes',
             description="""useful when you want to know the available lanes of the vehicles. like: I want to know the available lanes of the vehicle `ego`. The input to this tool should be a string, representing the id of the vehicle.""")
    def inference(self, vid: str) -> str:
        veh = self.sce.vehicles[vid]
        currentLaneID = veh.lane_id
        laneIdx = self.sce.lanes[currentLaneID].laneIdx
        if laneIdx == 3:
            leftLane = 'lane_2'
            return f"""The availabel lane of `{vid}` is `{leftLane}` and `{currentLaneID}`. `{leftLane}` is to the left of the current lane. `{currentLaneID}` is the current lane."""
        elif laneIdx == 0:
            rightLane = 'lane_1'
            return f"""The availabel lane of `{vid}` is `{currentLaneID}` and `{rightLane}`. `{currentLaneID}` is the current lane. `{rightLane}` is to the right of the current lane."""
        else:
            leftLane = 'lane_' + str(laneIdx-1)
            rightLane = 'lane_' + str(laneIdx+1)
            return f"""The availabel lane of `{vid}` is `{currentLaneID}`, `{rightLane}` and {leftLane}. `{currentLaneID}` is the current lane. `{rightLane}` is to the right of the current lane. `{leftLane}` is to the left of the current lane."""


class getLaneInvolvedCar:
    def __init__(self, sce: Scenario) -> None:
        self.sce = sce

    @prompts(name='Get Lane Involved Car',
             description="""useful whent want to know the cars may affect your action in the certain lane. Make sure you have use tool `Get Available Lanes` first. The input is a string, representing the id of the specific lane you want to drive on, DONNOT input multiple lane_id once.""")
    def inference(self, laneID: str) -> str:
        if laneID not in {'lane_0', 'lane_1', 'lane_2', 'lane_3'}:
            return "Not a valid lane id! Make sure you have use tool `Get Available Lanes` first."
        ego = self.sce.vehicles['ego']
        laneVehicles = []
        for vk, vv in self.sce.vehicles.items():
            if vk != 'ego':
                if vv.lane_id == laneID:
                    laneVehicles.append((vv.id, vv.lanePosition))
        laneVehicles.sort(key=lambda x: x[1])
        leadingCarIdx = -1
        for i in range(len(laneVehicles)):
            vp = laneVehicles[i]
            if vp[1] >= ego.lanePosition:
                leadingCarIdx = i
                break
        if leadingCarIdx == -1:
            try:
                rearingCar = laneVehicles[-1][0]
            except IndexError:
                return f'There is no car driving on {laneID},  This lane is safe, you donot need to check for any vehicle for safety! you can drive on this lane as fast as you can.'
            return f"{rearingCar} is driving on {laneID}, and it's driving behind ego car. You need to make sure that your actions do not conflict with each of the vehicles mentioned."
        elif leadingCarIdx == 0:
            leadingCar = laneVehicles[0][0]
            distance = round(laneVehicles[0][1] - ego.lanePosition, 2)
            leading_car_vel = round(self.sce.vehicles[leadingCar].speed,1)
            return f"{leadingCar} is driving at {leading_car_vel}m/s on {laneID}, and it's driving in front of ego car for {distance} meters. You need to make sure that your actions do not conflict with each of the vehicles mentioned."
        else:
            leadingCar = laneVehicles[leadingCarIdx][0]
            rearingCar = laneVehicles[leadingCarIdx-1][0]
            distance = round(laneVehicles[leadingCarIdx][1] - ego.lanePosition, 2)
            leading_car_vel = round(self.sce.vehicles[leadingCar].speed,1)
            return f"{leadingCar} and {rearingCar} is driving on {laneID}, and {leadingCar} is driving at {leading_car_vel}m/s in front of ego car for {distance} meters, while {rearingCar} is driving behind ego car. You need to make sure that your actions do not conflict with each of the vehicles mentioned."


class isChangeLaneConflictWithCar:
    def __init__(self, sce: Scenario) -> None:
        self.sce = sce
        self.TIME_HEAD_WAY = 3.0
        self.VEHICLE_LENGTH = 5.0

    @prompts(name='Is Change Lane Confict With Car',
             description="""useful when you want to know whether change lane to a specific lane is confict with a specific car, ONLY when your decision is change_lane_left or change_lane_right. The input to this tool should be a string of a comma separated string of two, representing the id of the lane you want to change to and the id of the car you want to check.""")
    def inference(self, inputs: str) -> str:
        laneID, vid = inputs.replace(' ', '').split(',')
        if vid not in self.sce.vehicles:
            return "Your input is not a valid vehicle id, make sure you use `Get Lane Involved Car` tool first!"
        veh = self.sce.vehicles[vid]
        ego = self.sce.vehicles['ego']
        if veh.lanePosition >= ego.lanePosition:
            relativeSpeed = ego.speed - veh.speed
            if veh.lanePosition - ego.lanePosition - self.VEHICLE_LENGTH > self.TIME_HEAD_WAY * relativeSpeed:
                return f"change lane to `{laneID}` is safe with `{vid}`."
            else:
                return f"change lane to `{laneID}` may be conflict with `{vid}`, which is unacceptable."
        else:
            relativeSpeed = veh.speed - ego.speed
            if ego.lanePosition - veh.lanePosition - self.VEHICLE_LENGTH > self.TIME_HEAD_WAY * relativeSpeed:
                return f"change lane to `{laneID}` is safe with `{vid}`."
            else:
                return f"change lane to `{laneID}` may be conflict with `{vid}`, which is unacceptable."


class isAccelerationConflictWithCar:
    def __init__(self, sce: Scenario) -> None:
        self.sce = sce
        self.TIME_HEAD_WAY = 5.0
        self.VEHICLE_LENGTH = 5.0
        self.acceleration = 4.0

    @prompts(name='Is Acceleration Conflict With Car',
             description="""useful when you want to know whether acceleration is safe with a specific car, ONLY when your decision is accelerate. The input to this tool should be a string, representing the id of the car you want to check.""")
    def inference(self, vid: str) -> str:
        if vid not in self.sce.vehicles:
            return "Your input is not a valid vehicle id, make sure you use `Get Lane Involved Car` tool first!"
        if vid == 'ego':
            return "You are checking the acceleration of ego car, which is meaningless, input a valid vehicle id please!"
        veh = self.sce.vehicles[vid]
        ego = self.sce.vehicles['ego']
        if veh.lane_id != ego.lane_id:
            return f'{vid} is not in the same lane with ego, please call `Get Lane Involved Car` and rethink your input.'
        if veh.lane_id == ego.lane_id:
            if veh.lanePosition >= ego.lanePosition:
                relativeSpeed = ego.speed + self.acceleration - veh.speed
                distance = veh.lanePosition - ego.lanePosition - self.VEHICLE_LENGTH * 2
                if distance > self.TIME_HEAD_WAY * relativeSpeed:
                    return f"acceleration is safe with `{vid}`."
                else:
                    return f"acceleration may be conflict with `{vid}`, which is unacceptable."
            else:
                return f"acceleration is safe with {vid}"
        else:
            return f"acceleration is safe with {vid}"


class isKeepSpeedConflictWithCar:
    def __init__(self, sce: Scenario) -> None:
        self.sce = sce
        self.TIME_HEAD_WAY = 5.0
        self.VEHICLE_LENGTH = 5.0

    @prompts(name='Is Keep Speed Conflict With Car',
             description="""useful when you want to know whether keep speed is safe with a specific car, ONLY when your decision is keep_speed. The input to this tool should be a string, representing the id of the car you want to check.""")
    def inference(self, vid: str) -> str:
        if vid not in self.sce.vehicles:
            return "Your input is not a valid vehicle id, make sure you use `Get Lane Involved Car` tool first!"
        if vid == 'ego':
            return "You are checking the acceleration of ego car, which is meaningless, input a valid vehicle id please!"
        veh = self.sce.vehicles[vid]
        ego = self.sce.vehicles['ego']
        if veh.lane_id != ego.lane_id:
            return f'{vid} is not in the same lane with ego, please call `Get Lane Involved Car` and rethink your input.'
        if veh.lane_id == ego.lane_id:
            if veh.lanePosition >= ego.lanePosition:
                relativeSpeed = ego.speed - veh.speed
                distance = veh.lanePosition - ego.lanePosition - self.VEHICLE_LENGTH * 2
                if distance > self.TIME_HEAD_WAY * relativeSpeed:
                    return f"keep lane with current speed is safe with {vid}"
                else:
                    return f"keep lane with current speed may be conflict with {vid}, you need consider decelerate"
            else:
                return f"keep lane with current speed is safe with {vid}"
        else:
            return f"keep lane with current speed is safe with {vid}"


class isDecelerationSafe:
    def __init__(self, sce: Scenario) -> None:
        self.sce = sce
        self.TIME_HEAD_WAY = 3.0
        self.VEHICLE_LENGTH = 5.0
        self.deceleration = 3.0

    @prompts(name='Is Deceleration Safe',
             description="""useful when you want to know whether deceleration is safe, ONLY when your decision is decelerate.The input to this tool should be a string, representing the id of the car you want to check.""")
    def inference(self, vid: str) -> str:
        if vid not in self.sce.vehicles:
            return "Your input is not a valid vehicle id, make sure you use `Get Lane Involved Car` tool first!"
        if vid == 'ego':
            return "You are checking the acceleration of ego car, which is meaningless, input a valid vehicle id please!"
        veh = self.sce.vehicles[vid]
        ego = self.sce.vehicles['ego']
        if veh.lane_id != ego.lane_id:
            return f'{vid} is not in the same lane with ego, please call `Get Lane Involved Car` and rethink your input.'
        if veh.lane_id == ego.lane_id:
            if veh.lanePosition >= ego.lanePosition:
                relativeSpeed = ego.speed - veh.speed - self.deceleration
                distance = veh.lanePosition - ego.lanePosition - self.VEHICLE_LENGTH
                if distance > self.TIME_HEAD_WAY * relativeSpeed:
                    return f"deceleration with current speed is safe with {vid}"
                else:
                    return f"deceleration with current speed may be conflict with {vid}, if you have no other choice, slow down as much as possible"
            else:
                return f"deceleration with current speed is safe with {vid}"
        else:
            return f"deceleration with current speed is safe with {vid}"
