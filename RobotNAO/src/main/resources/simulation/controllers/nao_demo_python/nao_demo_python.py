#!/usr/bin/python

import math
import time
import random
    #!/usr/bin/python
    # Copyright 1996-2021 Cyberbotics Ltd.
    #
    # Licensed under the Apache License, Version 2.0 (the "License");
    # you may not use this file except in compliance with the License.
    # You may obtain a copy of the License at
    #
    #     http://www.apache.org/licenses/LICENSE-2.0
    #
    # Unless required by applicable law or agreed to in writing, software
    # distributed under the License is distributed on an "AS IS" BASIS,
    # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    # See the License for the specific language governing permissions and
    # limitations under the License.
    
    """Example of Python controller for Nao robot.
       This demonstrates how to access sensors and actuators"""
    import math
    import time
    import random
    from controller import Robot, Motion, Motor, PositionSensor, LED, Accelerometer, DistanceSensor, TouchSensor
    from enum import Enum
    from typing import List, Dict
    
    TURN_SPEED = 60 / 4.5  # °/s
    FALLING_P = 0.9
    
    DELTA = 0.001
    TIMEOUT = 15  # s
    
    
    class BodySide(Enum):
        LEFT = 0
        RIGHT = 1
    
    
    class JointMovement(Enum):
        ABSOLUTE = 0
        RELATIVE = 1
    
    
    class Led(Enum):
        EYES = 0,
        LEFTEYE = 1
        RIGHTEYE = 2
        EARS = 3
        LEFTEAR = 4
        RIGHTEAR = 5
        CHEST = 6
        HEAD = 7
        LEFTFOOT = 8
        RIGHTFOOT = 9
        ALL = 10
    
    
    def calculate_newtons(fsv):
        collect = []
        # The coefficients were calibrated against the real
        # robot so as to obtain realistic sensor values.
        collect.append(fsv[2] / 3.4 + 1.5 * fsv[0] + 1.15 * fsv[1])  # Left Foot Front Left
        collect.append(fsv[2] / 3.4 + 1.5 * fsv[0] - 1.15 * fsv[1])  # Left Foot Front Right
        collect.append(fsv[2] / 3.4 - 1.5 * fsv[0] - 1.15 * fsv[1])  # Left Foot Rear Right
        collect.append(fsv[2] / 3.4 - 1.5 * fsv[0] + 1.15 * fsv[1])  # Left Foot Rear Left
        newtons = 0
        for i in range(0, len(collect)):
            collect[i] = max(min(collect[i], 25), 0)
            newtons += collect[i]
        return newtons
    
    
    class Nao(Robot):
        PHALANX_MAX = 8
    
        def __init__(self):
            Robot.__init__(self)
    
            # initialize stuff
            self.find_and_enable_devices()
            self.load_motion_files()
    
        def load_motion_files(self):
            # load motion files
            self.standup = Motion('../../motions/StandUpFromFront.motion')
            self.handWave = Motion('../../motions/HandWave.motion')
            self.taichi = Motion('../../motions/Taichi.motion')
            self.wipeForehead = Motion('../../motions/WipeForehead.motion')
            self.handWave = Motion('../../motions/HandWave.motion')
            self.forwards = Motion('../../motions/Forwards.motion')
            self.reset = Motion('../../motions/Reset.motion')
            self.backwards = Motion('../../motions/Backwards.motion')
            self.sideStepLeft = Motion('../../motions/SideStepLeft.motion')
            self.sideStepRight = Motion('../../motions/SideStepRight.motion')
            self.turnLeft60 = Motion('../../motions/TurnLeft60.motion')
            self.turnRight60 = Motion('../../motions/TurnRight60.motion')
    
        def find_and_enable_devices(self):
            # get the time step of the current world.
            self.timeStep = int(self.getBasicTimeStep())
    
            # accelerometer
            self.accelerometer: Accelerometer = self.getDevice('accelerometer')
            self.accelerometer.enable(self.timeStep)
    
            # gyro
            self.gyro = self.getDevice('gyro')
            self.gyro.enable(self.timeStep)
    
            # gps
            self.gps = self.getDevice('gps')
            self.gps.enable(self.timeStep)
    
            # inertial unit
            self.inertialUnit = self.getDevice('inertial unit')
            self.inertialUnit.enable(self.timeStep)
    
            # ultrasound sensors
            self.ultrasonic_sensors: List[DistanceSensor] = []
            usNames = ['Sonar/Left', 'Sonar/Right']
            for i in range(0, len(usNames)):
                self.ultrasonic_sensors.append(self.getDevice(usNames[i]))
                self.ultrasonic_sensors[i].enable(self.timeStep)
    
            # foot sensors
            self.fsr: List[TouchSensor] = []
            fsrNames = ['LFsr', 'RFsr']
            for i in range(0, len(fsrNames)):
                self.fsr.append(self.getDevice(fsrNames[i]))
                self.fsr[i].enable(self.timeStep)
    
            # foot bumpers
            self.lfootlbumper: TouchSensor = self.getDevice('LFoot/Bumper/Left')
            self.lfootrbumper: TouchSensor = self.getDevice('LFoot/Bumper/Right')
            self.rfootlbumper: TouchSensor = self.getDevice('RFoot/Bumper/Left')
            self.rfootrbumper: TouchSensor = self.getDevice('RFoot/Bumper/Right')
            self.lfootlbumper.enable(self.timeStep)
            self.lfootrbumper.enable(self.timeStep)
            self.rfootlbumper.enable(self.timeStep)
            self.rfootrbumper.enable(self.timeStep)
    
            # there are 7 controlable LED groups in Webots
            self.leds: Dict[Led, List[LED]] = {
                Led.LEFTEYE: [self.getDevice('Face/Led/Left')],
                Led.RIGHTEYE: [self.getDevice('Face/Led/Right')],
                Led.LEFTEAR: [self.getDevice('Ears/Led/Left')],
                Led.RIGHTEAR: [self.getDevice('Ears/Led/Right')],
                Led.LEFTFOOT: [self.getDevice('LFoot/Led')],
                Led.RIGHTFOOT: [self.getDevice('RFoot/Led')],
                Led.CHEST: [self.getDevice('ChestBoard/Led')]
            }
    
            self.leds[Led.EARS] = self.leds[Led.LEFTEAR] + self.leds[Led.RIGHTEAR]
            self.leds[Led.EYES] = self.leds[Led.LEFTEYE] + self.leds[Led.RIGHTEYE]
            self.leds[Led.HEAD] = self.leds[Led.EARS]
            self.leds[Led.ALL] = self.leds[Led.EYES] + self.leds[Led.LEFTFOOT] + self.leds[Led.RIGHTFOOT]
    
            # get phalanx motor tags
            # the real Nao has only 2 motors for RHand/LHand
            # but in Webots we must implement RHand/LHand with 2x8 motors
            self.lphalanx: List[Motor] = []
            self.rphalanx: List[Motor] = []
            self.maxPhalanxMotorPosition = []
            self.minPhalanxMotorPosition = []
            for i in range(0, self.PHALANX_MAX):
                self.lphalanx.append(self.getDevice("LPhalanx%d" % (i + 1)))
                self.rphalanx.append(self.getDevice("RPhalanx%d" % (i + 1)))
    
                # assume right and left hands have the same motor position bounds
                self.maxPhalanxMotorPosition.append(self.rphalanx[i].getMaxPosition())
                self.minPhalanxMotorPosition.append(self.rphalanx[i].getMinPosition())
    
            # shoulder pitch motors
            self.RShoulderPitch = self.getDevice("RShoulderPitch")
            self.LShoulderPitch = self.getDevice("LShoulderPitch")
            
            gps = self.gps.getValues()
            while math.isnan(gps[0]) and self.step(self.timeStep) != -1:
              self.step(self.timeStep)
              gps = self.gps.getValues()
    
        def is_touched(self, position, side):
            self.step(self.timeStep)
            if position == "bumper":
                if side == "left":
                    return self.lfootlbumper.getValue() == 1.0 or self.lfootrbumper.getValue() == 1.0
                if side == "right":
                    return self.rfootlbumper.getValue() == 1.0 or self.rfootrbumper.getValue() == 1.0
            return False
    
        def get_force(self, side: BodySide):
            values = self.fsr[0].getValues() if side == BodySide.LEFT else self.fsr[1].getValues()
            return calculate_newtons(values)
    
        def get_gyro_x(self):
            return self.gyro.getValues()[0]
    
        def get_gyro_y(self):
            return self.gyro.getValues()[1]
    
        def get_accelerometer_x(self):
            return self.accelerometer.getValues()[0]
    
        def get_accelerometer_y(self):
            return self.accelerometer.getValues()[1]
    
        def get_accelerometer_z(self):
            return self.accelerometer.getValues()[2]
    
        def get_ultrasonic(self):
            values = []
            for ultrasonic_sensor in self.ultrasonic_sensors:
                values.append(ultrasonic_sensor.getValue())
            value_m = sum(values) / len(values)
            value_cm = round(value_m * 100)
    
            return value_cm
    
        def move_hand_joint(self, hand: BodySide, radiant, mode=JointMovement.ABSOLUTE):
            phalanx = self.rphalanx if hand == BodySide.RIGHT else self.lphalanx
    
            clamped_angles = []
            for i in range(0, self.PHALANX_MAX):
                sensor: PositionSensor = phalanx[i].getPositionSensor()
    
                if (i < len(phalanx)) and phalanx[i] is not None:
                    sensor.enable(self.timeStep)
    
                clamped_angle = radiant
    
                if mode == JointMovement.RELATIVE:
                    clamped_angle += sensor.getValue()
    
                clamped_angle = min(self.maxPhalanxMotorPosition[i], clamped_angle)
                clamped_angle = max(self.minPhalanxMotorPosition[i], clamped_angle)
    
                if len(phalanx) > i and phalanx[i] is not None:
                    phalanx[i].setPosition(clamped_angle)
    
                clamped_angles.append(clamped_angle)
    
            start_time = self.getTime()
            while self.step(self.timeStep) != -1:
                values_reached = []
                for i in range(0, self.PHALANX_MAX):
                    sensor: PositionSensor = phalanx[i].getPositionSensor()
                    values_reached.append(math.fabs(sensor.getValue() - clamped_angles[i]) <= DELTA)
    
                is_timeout = self.getTime() - start_time >= TIMEOUT
                is_finished = (len([done for done in values_reached if done]) == self.PHALANX_MAX)
                if is_finished or is_timeout:
                    break
    
        def set_led(self, led: Led, rgb):
            for ledActor in self.leds[led]:
                is_only_intensity = ledActor in self.leds[Led.EARS] or ledActor in self.leds[Led.CHEST]
                if is_only_intensity:
                    ledActor.set(rgb & 0xFF)
                else:
                    ledActor.set(rgb)
    
        def led_off(self, led: Led):
            self.set_led(led, 0)
    
        def set_intensity(self, led: Led, intensity):
            self.set_led(led, int((intensity / 100) * 255))
    
        def reset_pose(self):
            self.reset.play()
    
            while self.step(self.timeStep) != -1:
                if self.reset.isOver():
                    break
    
            self.reset.stop()
    
            self.step(self.timeStep)
    
        def move_joint(self, joint_name, degrees, mode: JointMovement):
            """
    
            :param joint_name:
            :param degrees:
            :param mode: 1 for absolute positioning and 2 for relative positioning
             """
    
            if joint_name == "RHand" or joint_name == "LHand":
                return self.move_hand_joint(BodySide.RIGHT if joint_name == "RHand" else BodySide.LEFT, math.radians(degrees), mode)
    
            device: Motor = self.getDevice(joint_name)
            sensor: PositionSensor = device.getPositionSensor()
            sensor.enable(self.timeStep)
    
            self.step(self.timeStep)
    
            rad = math.radians(degrees) if mode == JointMovement.ABSOLUTE else sensor.getValue() + math.radians(degrees)
            rad = min(rad, device.getMaxPosition())
            rad = max(rad, device.getMinPosition())
    
            device.setPosition(rad)
    
            start_time = self.getTime()
            while self.step(self.timeStep) != -1:
                value_reached = math.fabs(sensor.getValue() - rad) <= DELTA
                timeout = self.getTime() - start_time >= TIMEOUT
                if value_reached or timeout:
                    break
    
            sensor.disable()
    
        def close_hand(self, hand: BodySide):
            self.move_hand_joint(hand, 0)
    
        def open_hand(self, hand: BodySide):
            self.move_hand_joint(hand, 1)
    
        def turn(self, degree):
            """
                Turn left to this degree
            """
            turn_motion = self.turnLeft60 if degree > 0 else self.turnRight60
    
            turn_motion.setLoop(True)
            turn_motion.play()
            self.wait((abs(degree) / TURN_SPEED) * 1000)
            turn_motion.stop()
            self.reset_pose()
    
        def walk(self, distance):
            motion = self.forwards
            forwards = True

            if distance < 0:
                motion.setReverse(True)
                distance *= -1
                forwards = False
            
            motion.setLoop(True)
            motion.play()
                
            startPosition = self.gps.getValues() 
            
            while self.step(self.timeStep) != -1:
              currentPosition = self.gps.getValues()
              euclDistance = self.calcDistanceCm(startPosition, currentPosition)
              rpy = self.inertialUnit.getRollPitchYaw()
              if euclDistance >= distance or rpy[1] > FALLING_P:
                break
              if forwards and motion.getTime() == 1360 :  # we reached the end of forward.motion
                motion.setTime(360)
              if not forwards and motion.getTime() == 360 :  # we reached the end of forward.motion
                motion.setTime(1360)
     
            motion.stop()
            self.reset_pose()
        
        def calcDistanceCm(self, p, q):
            a = (p[0] - q[0]) + (p[2] - q[2])
            return math.sqrt(math.pow(a, 2)) * 100
    
        def blink(self):
            pass
        
        def say(self, text, speed=30, pitch=50):
            command = "say:" + str(text) + ":" + str(speed) + ":" + str(pitch) + ":"
            print(command)
            
            while self.step(self.timeStep) != -1:
                message = robot.wwiReceiveText()
                if message.startswith("finish"):
                    break
                    
        def setLanguage(self, lang):
            command = "setLanguage:" + str(lang)
            print(command)
            
        def setVolume(self, volume):
            command = "setVolume:" + str(volume)
            print(command)
            
        def getVolume(self):
            command = "getVolume:"
            print(command)

            while self.step(self.timeStep) != -1:
                message = robot.wwiReceiveText()
                if message.startswith("volume"):
                    return int(message.split(":")[1])
        def perform(self, move):
            if move == "BLINK":
                robot.set_led(Led.ALL, "#ffffff")
                robot.wait(500)
                robot.set_led(Led.ALL, "#000000")
                robot.wait(500)
                robot.set_led(Led.ALL, "#ffffff")
                return
            if move == "TAICHI":
                motion = self.taichi
            elif move == "WAVE":
                motion = handWave
            elif move == "WIPEFOREHEAD":
               motion = wipeForehead
               
               motion.play()
          
            while self.step(self.timeStep) != -1:
                if motion.isOver():
                    break
    
            motion.stop()
            
    
        def wait(self, time):
            """
    
            :param time: time in ms
            """
            start_time = self.getTime()
            while self.step(self.timeStep) != -1:
                if self.getTime() - start_time > (time / 1000):
                    break
                    
                    
                    
                    
                    

def run():
    robot = Nao()
     # robot.turn(180)
    robot.perform("Taichi")
   
    

def main():
    try:
        run()
    except Exception as e:
        raise
    

if __name__ == "__main__":
    main()