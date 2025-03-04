#!/usr/bin/env python

import os, sys, time
import optparse
import json
import uuid
import datetime

try:
    import thread
except ImportError:
    import _thread as thread

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # noqa
import traci  # noqa

from abstract_player import AbstractPlayer # Import file


class SumoPlayer(AbstractPlayer):

    # Constants
    TEMPL_PLACEHOLDER_CHILDS = "$CHILDS$"

    # Global variable
    step_ratio = 3
    #steps_limit = 250
    stopped = False
    lane_length = 100

    #sleep = 1.0
    config_name = ""
    templates = {}

    step = 0
    step2 = 0

    rows_pos = {}
    lane_mappings = {}


    def __init__(self, sumo_config, template_dict):  # __init__
        self.streamID = sumo_config
        #self.templateID = template_path
        self.templates = template_dict

    def stop(self):

        self.stopped = True
        print("SUMO is stopped")

    def getkb(self):


        if "backgroundKB" in self.templates:
            kbName = self.templates["backgroundKB"]
            f = open(kbName)
            kbText = f.read()
            f.close()
            return kbText
        else:
            return ""

    #def start(self, freq_in_ms):

    def start(self, freq_in_ms, replay, aggregate):


        self.frequency = freq_in_ms # / 100 # Set to milliseconds * 10
        self.stopped = False
        self.step = 0
        self.step2 = 0
        self.replay = replay
        self.aggregate = aggregate

        # Inits
        count_vehicles = 0
        count = 0

        # traffic light only changes every 4 steps not every single time
        tlChange = 4
        tlCount = tlChange

        # Open template file
        #print(str(self.templates))
        tempVehName = self.templates["subStreamVehicles"]
        #templ_file1 = open(tempVehName) #self.templateID
        templ_vehicles = open(tempVehName).read()

        # Template has to be split into platfrom/sensor parts using $CHILDS$
        tempTLName = self.templates["subStreamTrafficLights"]
        #templ_file2a = open(tempTLName)
        templ_TLs = open(tempTLName).read()

        if("subStreamTrafficLightsChilds" in self.templates):
            tempTLName = self.templates["subStreamTrafficLightsChilds"]
            templ_TLs_Child = open(tempTLName).read()
        else:
            templ_TLs_Child = ""

        # Load tl positions from local dir
        file1 = open("src/tl_mappings.config", "r")
        lines = file1.readlines()
        self.loadTLPositions(lines)

        # Open Sumo config file
        #config_file = open(self.streamID) # config_file
        #config_str = config_file.read()
        self.config_name = self.streamID

        #if options.nogui: #not
        sumoBinary = checkBinary('sumo')
        #else:
        #    sumoBinary = checkBinary('sumo-gui')

        while True:

            print("SUMO is starting with ratio: " + str(self.step_ratio) + " and " + self.config_name)
            #print("Limit steps: " + str(self.steps_limit))

            # this is the normal way of using traci. sumo is started as a
            # subprocess and then the python script connects and runs
            sumoCmd = [sumoBinary, "-S", "-Q", "-c", self.config_name ]

            traci.start(sumoCmd)

            # TraCI control loop
            while traci.simulation.getMinExpectedNumber() > 0:

                # Check if stopped
                if(self.stopped):
                    break

                # Active simulation step
                traci.simulationStep()

                self.step = self.step + 1
                time.sleep(self.frequency / 1000) # sleep

                #if(self.steps_limit < self.step):
                #    break

                if(self.step % self.step_ratio != 0):
                    continue

                self.step2 = int(self.step / self.step_ratio)

                aggregateMsg = ""

                print("Step: " + str(self.step) + " / " + str(self.step2))

                vehicle_id_list = traci.vehicle.getIDList()
                print("Nr. of vehicles: " +  str(len(vehicle_id_list)))

                # Vehicles
                vehicles_ids=traci.vehicle.getIDList();

                lc = lambda s: s[:1].lower() + s[1:] if s else ''

                for veh_id in vehicles_ids:
                    #traci.vehicle.setSpeedMode(veh_id,0)
                    #traci.vehicle.setSpeed(veh_id,15) #sets the speed of vehicles to 15 (m/s)

                    replaceValues = {}
                    replaceValues["$VehicleID$"] = str(veh_id)
                    replaceValues["$ObsID$"] = "O_" + str(veh_id) + "-" + str(self.step)
                    replaceValues["$Timestamp$"] = str(self.step)

                    veh_speed = round(traci.vehicle.getSpeed(veh_id), 3)
                    replaceValues["$Speed$"] = str(veh_speed)
                    veh_type = traci.vehicle.getTypeID(veh_id)
                    replaceValues["$Type$"] = lc(str(veh_type))
                    veh_acc = round(traci.vehicle.getAcceleration(veh_id), 4)
                    replaceValues["$Accel$"] = str(veh_acc)
                    veh_angle_str = traci.vehicle.getAngle(veh_id)

                    if not veh_angle_str is None:
                        veh_angle = round(veh_angle_str, 4)
                    else:
                        veh_angle = 0

                    replaceValues["$Orient_Heading$"] = str(veh_angle)
                    veh_pos = traci.vehicle.getPosition(veh_id)
                    #veh_pos = veh_pos.replace('(','').replace('','').strip()

                    # Lane id needs to be map to asp encoding
                    #veh_laneID = str(traci.vehicle.getLaneID(veh_id))
                    veh_laneID = str(traci.vehicle.getRoadID(veh_id))
                    veh_lanePos = float(traci.vehicle.getLanePosition(veh_id))
                    # Map lanePos to 0 (start-middle) or 1 (middle-end) of lanes
                    veh_lanePos01 = 0 # Default is begin of
                    if(self.lane_length / 2) <= veh_lanePos:
                        veh_lanePos01 = 0
                    else:
                        veh_lanePos01 = 1

                    lanePosKey = veh_laneID + "#" + str(veh_lanePos01)
                    #print("D2: " + lanePosKey)
                    if lanePosKey in self.lane_mappings:
                        laneTuple = self.lane_mappings[lanePosKey] # (sumo id, asp id, asp orientation)
                        replaceValues["$LaneID_From$"] = laneTuple[1]
                        replaceValues["$LaneID_To$"] = laneTuple[2]
                        replaceValues["$LaneOrient$"] = laneTuple[3]
                    else:
                        print("No lane mapping: " + str(lanePosKey))
                        replaceValues["$LaneID_From$"] = "_" # "_"
                        replaceValues["$LaneID_To$"] = "_" # "_"
                        replaceValues["$LaneOrient$"] = "_"

                    # X,Y Position
                    #posXY = veh_pos.split(',')
                    replaceValues["$Position_X$"] = str(round(veh_pos[0],5))
                    replaceValues["$Position_Y$"] = str(round(veh_pos[1],5))

                    veh_signals = traci.vehicle.getSignals(veh_id)
                    veh_lane = str(traci.vehicle.getLaneID(veh_id)) + ";" + str(round(traci.vehicle.getLanePosition(veh_id), 4))


                    # Speed
                    msg1 = templ_vehicles
                    for key, val in replaceValues.items():
                        msg1 = msg1.replace(key,val)
                    # print(msg1)

                    if not msg1 is None:
                        if self.aggregate == True:
                            aggregateMsg = aggregateMsg + "\n" + msg1
                        else:
                            yield msg1


                # Lanes
                lane_id_list = traci.lane.getIDList()

                # Traffic lights
                tl_id_list = traci.trafficlight.getIDList()

                print("Intersections with TLs: " +  str(len(tl_id_list)))

                # Group of traffic lights
                for intersID in tl_id_list:

                    msg2 = templ_TLs.replace("$IntersectionID$",str(intersID))
                    msg2_Childs = ""

                    hasChildTemplate = False
                    if(self.TEMPL_PLACEHOLDER_CHILDS in msg2):
                        hasChildTemplate = True


                    replaceValues2 = {}
                    tlIDcheck = {}
                    #replaceValues2["$IntersectionID$"] = str(intersID)
                    replaceValues2["$Timestamp$"] = str(self.step)

                    # Get signals for one intersection
                    tl_states = traci.trafficlight.getRedYellowGreenState(intersID)
                    #msg3 = "tlPhase(" + str(self.step2) + "," + str(intersID) + "," + tl_states + ")"
                    #print(msg3)

                    if(intersID in self.rows_pos):
                        row_pos_values = self.rows_pos[intersID]

                        # Find tlight for position
                        for rowPosDict in row_pos_values: # row_pos is at tuple (tlid positions)
                            tlID = rowPosDict["lane"]
                            tlPositions = rowPosDict["pos"]
                            #print(str(tlID) + str(tlPositions))


                            for i in range(0, len(tl_states)): # each char is one signal state

                                tlState = tl_states[i]
                                if str(i+1) in tlPositions:
                                    replaceValues2["$TrafficLightID$"] = str(tlID)
                                    replaceValues2["$SignalState$"] = str(tlState)

                                    # Assure that it gets only added once
                                    if (tlID in tlIDcheck):
                                        continue

                                    if(hasChildTemplate):
                                        msg2_Temp = templ_TLs_Child

                                        for key, val in replaceValues2.items():
                                            msg2_Temp = msg2_Temp.replace(key,val)

                                        if(len(msg2_Childs) > 0):
                                            msg2_Childs = msg2_Childs + ","
                                        msg2_Childs = msg2_Childs + msg2_Temp
                                    else:
                                        msg3 = msg2
                                        for key, val in replaceValues2.items():
                                            msg3 = msg3.replace(key,val)
                                        if self.aggregate == True:
                                            aggregateMsg = aggregateMsg + "\n" + msg3
                                        else:
                                            yield msg3

                                    tlIDcheck[tlID] = ""


                    # Case with child template (e.g., RDF)
                    if(hasChildTemplate):
                        msg2 = msg2.replace(self.TEMPL_PLACEHOLDER_CHILDS, str(msg2_Childs))
                        if self.aggregate == True:
                            aggregateMsg = aggregateMsg + "\n" + msg2
                        else:
                            yield msg2


                # Case with single template (e.g., ASP) is handled in loop

                if (self.aggregate == True) and (not aggregateMsg is None):
                    yield aggregateMsg

            print("Simulation finished.")

            traci.close(False) # Immediate close

            if not self.replay or self.stopped:
                break
            else:
                print("Simulation restart.")
                time.sleep(1)

        sys.stdout.flush()


    def modify(self, freq_in_ms):
        self.frequency = freq_in_ms

        print("Frequency set to: " + str(freq_in_ms) + " ms")

    def loadTLPositions(self, linesBasePlan): #  namePlan, nameChg factor,

        for line1 in  linesBasePlan: # f_open1:

            line1=line1.strip()

            if len(line1) == 0:
                continue

            # Only handle "tmap" and "lmap"
            if line1.find("map") >= 0:

                hlength = 4
                predName = line1[0:hlength]

                posHead2 = hlength + 1 # Include bracket
                posEnd2 = len(line1) - 2
                lineData2 = line1[posHead2:posEnd2]

                lineDataSplit = lineData2.split(',')

                if(predName == "tmap"):

                    intersID = lineDataSplit[0].strip()
                    laneID = lineDataSplit[1].strip()
                    posString = lineDataSplit[2].strip()
                    posDict = {}
                    for x in posString.split(";"):
                        posDict[x] = ""

                    row = {'lane': laneID,  'pos': posDict } # 'inters': insID,

                    if intersID in self.rows_pos:
                        self.rows_pos[intersID].append(row)
                    else:
                        rows = []
                        rows.append(row)
                        self.rows_pos[intersID] = rows

                if(predName == "lmap"):

                        laneIdSumo = lineDataSplit[0].strip()
                        lanePosIdSumo = lineDataSplit[1].strip()
                        laneKey = laneIdSumo + "#" + str(lanePosIdSumo)
                        laneTuple = (laneKey, lineDataSplit[2].strip(), lineDataSplit[3].strip(), lineDataSplit[4].strip())

                        if not laneKey in self.lane_mappings:
                            self.lane_mappings[laneKey] = laneTuple

        #print("D1: " + str(self.lane_mappings))



#####
# main(argv) is only used for testing, in deployement it is called externaly via start()
#####
def main(argv):


    #parser = optparse.OptionParser()
    #parser.add_option('--nogui', action="store_true", dest="nogui", default=False, help="Run the commandline version of sumo")

    templates = {}
    templates["subStreamVehicles"] = "stream-templates/traffic/vehicle_template.asp" # json
    templates["subStreamTrafficLights"] = "stream-templates/traffic/traffic_light_template.asp" # json
    # templates["subStreamTrafficLightsChilds"] = "../stream-templates/traffic/traffic_light_template2.json"

    player = SumoPlayer("stream-log-files/sumo/testASP_180.sumocfg", templates)

    print("Start streaming...")

    time.sleep(2)

    for msg in player.start(1, True): # False
        print(msg)

    print("Stop streaming.")

    player.close()

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
