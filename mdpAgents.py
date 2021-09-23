# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util

class MDPAgent(Agent):

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print "Starting up MDPAgent!"
        name = "Pacman"
        self.discount = 0.6
        self.generalCost = -0.01 # Default cost for empty states

        self.foodReward = 0.0
        self.captulesReward = 0.0
        self.hungryGhostReward = -5.0
        self.nextToHungryGhostReward = -3.0
        self.aboutHungryGhostReward = -2.0
        self.nextToAboutHungryGhostReward = -1.0

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        print "Running registerInitialState for MDPAgent!"
        print "I'm at:"
        print api.whereAmI(state)
        
    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"


    def getAction(self, state):
        currentPosition = api.whereAmI(state)
        food = api.food(state)
        capsules = api.capsules(state)
        walls = api.walls(state)
        corners = api.corners(state)
        ghosts = api.ghosts(state)
        ghostStates = api.ghostStatesWithTimes(state)

        ### Build an empty map
        maxX = 0
        maxY = 0
        for i in range(len(corners)):
            xCoordinate = corners[i][0]
            yCoordinate = corners[i][1]

            maxX = xCoordinate if xCoordinate >= maxX else maxX
            maxY = yCoordinate if yCoordinate >= maxY else maxY    
        #Include walls in the coordinates.
        maxX += 1
        maxY += 1
        entryMap = self.createEmptyMap(maxX, maxY, self.generalCost)

        ### Give rewards/costs to each cell in the entryMap
        entryMap = self.populateEntryMap(entryMap, food, capsules, walls, ghosts, ghostStates)


        ### Get valueMap to base decisions on.
        valueMap = self.valueIteration(entryMap)
        
        ### Get Legal actions
        legal = api.legalActions(state)

        ### Based on the valueMap take the best action
        bestAction = None 
        for action in legal:
            if action == Directions.NORTH:
                if bestAction is None or valueMap[currentPosition[0]][currentPosition[1]+1] > bestAction[1]:
                    bestAction = (action , valueMap[currentPosition[0]][currentPosition[1]+1])
            if action == Directions.SOUTH:
                if bestAction is None or valueMap[currentPosition[0]][currentPosition[1]-1] > bestAction[1]:
                    bestAction = (action , valueMap[currentPosition[0]][currentPosition[1]-1])
            if action == Directions.EAST:
                if bestAction is None or valueMap[currentPosition[0]+1][currentPosition[1]] > bestAction[1]:
                    bestAction = (action , valueMap[currentPosition[0]+1][currentPosition[1]])
            if action == Directions.WEST:
                if bestAction is None or valueMap[currentPosition[0]-1][currentPosition[1]] > bestAction[1]:
                    bestAction = (action , valueMap[currentPosition[0]-1][currentPosition[1]])
            if action == Directions.STOP:
                if bestAction is None or valueMap[currentPosition[0]][currentPosition[1]] > bestAction[1]:
                    bestAction = (action , valueMap[currentPosition[0]][currentPosition[1]])

        return api.makeMove(bestAction[0], legal)


    def valueIteration(self, entryMap):
        """ Function that applies value iteration over the entry map to calculate the utility the of 
            each cell in pacman's world. 
            This is needed to solve the MDP

        Args:
            entryMap ([[int/None]]): The entry map that holds the rewards in pacman world. 
            It is a 2D-Matrix where each element is indexed by its coordinate and holds either an integer 
            representing the reward/cost of a cell or None if that coordinate is not a legal move (it is a wall)

        Returns:
            values ([[int/None]]): Returns a 2D-Matrix that holds the utilities of each cell (cooridnate) 
            in pacman's world.
        """        
        #Initialize the values to be a copy of entryMap. This is so to skip the first step in the iteration phase below.
        values = [row[:] for row in entryMap]

        #Iterate till no state (value) will change anymore
        while True:
            # Make a copy of values before iterating once again.
            oldValues = [row[:] for row in values]

            for i in range(len(values)-1):
                for j in range(len(values[i])-1):

                        if values[i][j] is not None:
                            # Extract legal actions in this state
                            possibleActions = self.getPossibleActions(i, j, values)

                            # Find the action that would render the highest sum(P(s'|s,a) * Ucopy(s')) among all of the actions
                            bestActionUtility = self.getActionWithHighestUtility(i, j, possibleActions, oldValues)

                            newUtility = entryMap[i][j] + self.discount * bestActionUtility
                            values[i][j] = newUtility

            #Check if this new value matrix is the same as the old one
            different = False
            for i in range(len(values)-1):
                for j in range(len(values[i])-1):
                    if values[i][j] is not None and float(values[i][j]) != float(oldValues[i][j]):
                        different = True
                        break

            if not different:
                return values



    def getPossibleActions(self, posX, posY, world):
        """Functions that returns a list of possible directions that can be taken from a given 
           position (it descards all the directions that would lead to an illegal state).

        Args:
            posX (int): X coordinate
            posY (int): Y coordinate
            world ([[float]]): A 2D-Matrix representing pacman's world where the illegal states (walls) have a value of None.

        Returns:
            ([Directions]): A list of directions that can be taken from the position (posX,posY)
        """        
        possibleActions = []
        if posY + 1 < len(world[posX])-1 and world[posX][posY + 1] is not None:
            possibleActions.append(Directions.NORTH)
        if posY - 1 >= 0 and world[posX][posY - 1] is not None:
            possibleActions.append(Directions.SOUTH)
        if posX + 1 < len(world)-1 and world[posX + 1][posY] is not None:
            possibleActions.append(Directions.EAST)
        if posX - 1 >= 0 and world[posX - 1][posY] is not None:
            possibleActions.append(Directions.WEST)
        possibleActions.append(Directions.STOP)
        
        return possibleActions

    def getActionWithHighestUtility(self, posX, posY, actions, utilities):  
        """ Function that returns the utility of the best action that can be taken.
            In short, it returns the highest sum(P(s'|s,a) * Ucopy(s')) among all of the actions.

        Args:
            posX (int): X coordinate
            posY (int): Y coordinate
            actions ([Directions]): A list of legal Directions that pacman can take.
            utilities ([[float/None]]): A 2D-Matrix representing pacman's world where the illegal states (walls) have a value of None, 
                                      while the rest hold an integer reppresenting their utilities.

        Returns:
            bestActionUtility (float): the utility of the best action that can be taken. The highest 
                                       sum(P(s'|s,a) * Ucopy(s')) among all of the actions.
        """               
        bestActionUtility = 0
        for action in actions:
            # If the action is North check if the action to its left and to its right are legal. 
            # If some of them are not, their probability would go to the action of staying still (STOPPED)
            if action == Directions.NORTH:
                if all([Directions.EAST, Directions.WEST]) in actions:
                    actionUtility = 0.8 * utilities[posX][posY+1] + 0.1 * utilities[posX+1][posY] + 0.1 * utilities[posX-1][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue
                
                if Directions.EAST in actions:
                    actionUtility = 0.8 * utilities[posX][posY+1] + 0.1 * utilities[posX+1][posY] + 0.1 * utilities[posX][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue

                if Directions.WEST in actions:
                    actionUtility = 0.8 * utilities[posX][posY+1] + 0.1 * utilities[posX-1][posY] + 0.1 * utilities[posX][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue

                else:
                    actionUtility = 0.8 * utilities[posX][posY+1] + 0.2 * utilities[posX][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue  

            # If the action is South check if the action to its left and to its right are legal. 
            # If some of them are not, their probability would go to the action of staying still (STOPPED)
            if action == Directions.SOUTH:
                if all([Directions.EAST, Directions.WEST]) in actions:
                    actionUtility = 0.8 * utilities[posX][posY-1] + 0.1 * utilities[posX+1][posY] + 0.1 * utilities[posX-1][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue
                                    
                if Directions.EAST in actions:
                    actionUtility = 0.8 * utilities[posX][posY-1] + 0.1 * utilities[posX+1][posY] + 0.1 * utilities[posX][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue

                if Directions.WEST in actions:
                    actionUtility = 0.8 * utilities[posX][posY-1] + 0.1 * utilities[posX-1][posY] + 0.1 * utilities[posX][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue

                else:
                    actionUtility = 0.8 * utilities[posX][posY-1] + 0.2 * utilities[posX][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue

            # If the action is East check if the action to its left and to its right are legal. 
            # If some of them are not, their probability would go to the action of staying still (STOPPED)
            if action == Directions.EAST:
                if all([Directions.NORTH, Directions.SOUTH]) in actions:
                    actionUtility = 0.8 * utilities[posX+1][posY] + 0.1 * utilities[posX+1][posY] + 0.1 * utilities[posX-1][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue
                
                if Directions.NORTH in actions:
                    actionUtility = 0.8 * utilities[posX+1][posY] + 0.1 * utilities[posX][posY+1] + 0.1 * utilities[posX][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue

                if Directions.SOUTH in actions:
                    actionUtility = 0.8 * utilities[posX+1][posY] + 0.1 * utilities[posX][posY-1] + 0.1 * utilities[posX][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue

                else:
                    actionUtility = 0.8 * utilities[posX+1][posY] + 0.2 * utilities[posX][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue

            # If the action is West check if the action to its left and to its right are legal. 
            # If some of them are not, their probability would go to the action of staying still (STOPPED)
            if action == Directions.WEST:
                if all([Directions.NORTH, Directions.SOUTH]) in actions:
                    actionUtility = 0.8 * utilities[posX-1][posY] + 0.1 * utilities[posX+1][posY] + 0.1 * utilities[posX-1][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue
                                    
                if Directions.NORTH in actions:
                    actionUtility = 0.8 * utilities[posX-1][posY] + 0.1 * utilities[posX][posY+1] + 0.1 * utilities[posX][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue

                if Directions.SOUTH in actions:
                    actionUtility = 0.8 * utilities[posX-1][posY] + 0.1 * utilities[posX][posY-1] + 0.1 * utilities[posX][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue

                else:
                    actionUtility = 0.8 * utilities[posX-1][posY] + 0.2 * utilities[posX][posY]
                    if actionUtility > bestActionUtility or bestActionUtility == 0:
                        bestActionUtility = actionUtility
                    continue

            # If the action is Stop, there will be no indeterminism. Hence, that action has a utility equal to the current cell.
            if action == Directions.STOP:
                actionUtility = utilities[posX][posY]
                if actionUtility > bestActionUtility or bestActionUtility == 0:
                    bestActionUtility = actionUtility

        return bestActionUtility

    def createEmptyMap(self, rowCount, colCount, value):
        """ Function that initializes an entryMap (a 2D-Matrix) and fills it with a given value.

        Args:
            rowCount (int): Number of rows
            colCount (int): Number of columns
            value (float): Values to give to all non-wall cells. It is the default cost of all normal cells.

        Returns:
            mat [[float]]: entryMap (a 2D-Matrix) representing pacman's world. Here all the cells are set to a default cost. 
        """        
        mat = []
        for i in range(rowCount):
            rowList = []
            for j in range(colCount):
                rowList.append(value)
            mat.append(rowList)
        return mat
    
    def populateEntryMap(self, entryMap, food, capsules, walls, ghosts, ghostStates):
        """ Function that set all the non-wall cells' reward/cost in pacman's world (entryMap) to the right value based on what there's in that cell.

        Args:
            entryMap ([[float/None]]): a 2D-Matrix representing pacman's world. Here walls are set to None 
                                       and all the other cells are set to a default cost value.
            food ([(int, int)]): list of coordinates for all the food in pacman's world
            capsules ([(int, int)]): list of coordinates for all the capsules in pacman's world
            walls ([(int, int)]): list of coordinates for all the walls in pacman's world
            ghosts ([(int, int)]): list of coordinates for all the ghosts in pacman's world
            ghostStates ([((int,int),int)]): A list of ghost states.

        Returns:
            entryMap ([[float/None]]): A modified entryMap with the right reward/cost values in it. Walls are set to None.
        """        
        ### Add reward of 0 for food in entryMap
        for f in food:
            entryMap[f[0]][f[1]] = self.foodReward
        
        ### Add reward of 0 to capsules
        for capsule in capsules:
            entryMap[int(capsule[0])][int(capsule[1])] = self.captulesReward


        ### Add some cost values to ghosts in the map.
        for ghost in ghosts:
            scaredTime = 0
            for i, g in enumerate(ghostStates):
                if g == ghost:
                    scaredTime = ghostStates[i][1]
                    break
            # If a ghost has a scared time < 2, it will be assigned a cost value of -5 in the entryMap
            if scaredTime < 2:
                entryMap[int(ghost[0])][int(ghost[1])] = self.hungryGhostReward
                # # What stays one cell close to them will have cost of -3
                entryMap[int(ghost[0]) + 1][int(ghost[1])] = self.nextToHungryGhostReward if entryMap[int(ghost[0]) + 1][int(ghost[1])] is not None else None
                entryMap[int(ghost[0]) - 1][int(ghost[1])] = self.nextToHungryGhostReward if entryMap[int(ghost[0]) - 1][int(ghost[1])] is not None else None
                entryMap[int(ghost[0])][int(ghost[1]) + 1] = self.nextToHungryGhostReward if entryMap[int(ghost[0])][int(ghost[1]) + 1] is not None else None
                entryMap[int(ghost[0])][int(ghost[1]) - 1] = self.nextToHungryGhostReward if entryMap[int(ghost[0])][int(ghost[1]) - 1] is not None else None
                continue
            # If a ghost has a scared time equal to 2, it will be assigned a cost value of -1 in the entryMap
            if scaredTime == 2:
                entryMap[int(ghost[0])][int(ghost[1])] = self.aboutHungryGhostReward
                # # What stays one cell close to them will have cost of -10
                entryMap[int(ghost[0]) + 1][int(ghost[1])] = self.nextToAboutHungryGhostReward if entryMap[int(ghost[0]) + 1][int(ghost[1])] is not None else None
                entryMap[int(ghost[0]) - 1][int(ghost[1])] = self.nextToAboutHungryGhostReward if entryMap[int(ghost[0]) - 1][int(ghost[1])] is not None else None
                entryMap[int(ghost[0])][int(ghost[1]) + 1] = self.nextToAboutHungryGhostReward if entryMap[int(ghost[0])][int(ghost[1]) + 1] is not None else None
                entryMap[int(ghost[0])][int(ghost[1]) - 1] = self.nextToAboutHungryGhostReward if entryMap[int(ghost[0])][int(ghost[1]) - 1] is not None else None
                continue
            # If a ghost has a scared time > 2, it will be ignored
            if scaredTime > 2:
                continue
        
        ### Set walls in the entryMap to be None.
        for wall in walls:
            entryMap[int(wall[0])][int(wall[1])] = None
        
        return entryMap

    def prettyPrintMatrix(self, mat):
        """ Debugging function to print out a matrix in a nice way.

        Args:
            mat ([[number]]): matrix to be printed.
        """        
        print('\n'.join([''.join(['{:6}'.format(float('%.1g' %item)) if item is not None else '{:6}'.format(item) for item in row]) for row in mat]))
    